#!/usr/bin/env python3
"""
extract.py — idvg.csv 에서 소자 지표를 뽑아 metrics.csv 로 저장한다.

★ 팀 전원이 이 스크립트로만 지표를 뽑는다. 손으로 계산하지 않는다.
   Vth 정의가 사람마다 다르면 등고선의 굴곡이 물리가 아니라 정의 차이가 된다.

사용법
    python analysis/extract.py runs/D36_N100      # 한 격자점
    python analysis/extract.py --all              # runs/ 전체 재추출
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "analysis" / "config.yaml"

REQUIRED_COLS = ["Vg", "Id_lin", "Id_sat"]


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def interp_vg_at_current(vg, idd, i_crit):
    """전류가 i_crit 를 처음 넘는 지점의 Vg 를 로그공간 선형보간으로 구한다."""
    idd = np.abs(idd)
    above = np.where(idd >= i_crit)[0]
    if len(above) == 0:
        return np.nan
    k = above[0]
    if k == 0:
        return float(vg[0])
    y0, y1 = np.log10(idd[k - 1]), np.log10(idd[k])
    x0, x1 = vg[k - 1], vg[k]
    if y1 == y0:
        return float(x1)
    return float(x0 + (np.log10(i_crit) - y0) * (x1 - x0) / (y1 - y0))


def interp_current_at_vg(vg, idd, v_target):
    if v_target < vg.min() or v_target > vg.max():
        return np.nan
    return float(np.interp(v_target, vg, np.abs(idd)))


def compute_ss(vg, idd, i_min, i_max, use_min_slope=True):
    """서브스레숄드 스윙 [mV/dec]."""
    idd = np.abs(idd)
    mask = (idd >= i_min) & (idd <= i_max) & (idd > 0)
    if mask.sum() < 3:
        return np.nan
    v = vg[mask]
    logi = np.log10(idd[mask])
    if use_min_slope:
        dv = np.diff(v)
        dl = np.diff(logi)
        valid = dl > 0
        if valid.sum() == 0:
            return np.nan
        ss_pts = (dv[valid] / dl[valid]) * 1000.0
        return float(np.min(ss_pts))
    slope = np.polyfit(v, logi, 1)[0]
    return float(1000.0 / slope) if slope > 0 else np.nan


def max_negative_vg_current(vg, idd):
    mask = vg < 0
    if mask.sum() == 0:
        return np.nan
    return float(np.max(np.abs(idd[mask])))


def parse_run_id(run_id):
    """'D36_N100' -> (36.0, 1.00)"""
    try:
        head = run_id.split("_")
        d = float(head[0].lstrip("Dd"))
        n = float(head[1].lstrip("Nn")) / 100.0
        return d, n
    except Exception:
        return float("nan"), float("nan")


def extract_one(run_dir, cfg):
    run_dir = Path(run_dir)
    csv_path = run_dir / "idvg.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} 없음. CONTRIBUTING.md 파일 규격 확인.")

    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"컬럼 {missing} 누락. 발견된 컬럼: {list(df.columns)}\n"
            f"    → 컬럼명은 정확히 Vg, Id_lin, Id_sat (대소문자 구분)"
        )

    df = df.sort_values("Vg").reset_index(drop=True)
    vg = df["Vg"].to_numpy(dtype=float)
    id_lin = df["Id_lin"].to_numpy(dtype=float)
    id_sat = df["Id_sat"].to_numpy(dtype=float)

    if np.any(np.abs(id_lin) > 1e-1) or np.any(np.abs(id_sat) > 1e-1):
        print(f"  [경고] {run_dir.name}: 전류가 0.1 A/um 초과. "
              f"폭 정규화(A/um) 누락 의심.", file=sys.stderr)

    i_crit = float(cfg["vth"]["I_crit_A_per_um"])
    vth_lin = interp_vg_at_current(vg, id_lin, i_crit)
    vth_sat = interp_vg_at_current(vg, id_sat, i_crit)

    ss = compute_ss(vg, id_lin,
                    float(cfg["ss"]["fit_I_min_A_per_um"]),
                    float(cfg["ss"]["fit_I_max_A_per_um"]),
                    bool(cfg["ss"].get("use_min_slope", True)))

    vd_lin = float(cfg["dibl"]["Vd_lin"])
    vd_sat = float(cfg["dibl"]["Vd_sat"])
    dibl = (((vth_lin - vth_sat) / (vd_sat - vd_lin)) * 1000.0
            if np.isfinite(vth_lin) and np.isfinite(vth_sat) else np.nan)

    v_gidl = float(cfg["gidl"]["V_gidl"])
    i_gidl = interp_current_at_vg(vg, id_sat, v_gidl)
    i_gidl_max = (max_negative_vg_current(vg, id_sat)
                  if cfg["gidl"].get("report_max_negative", True) else np.nan)

    ion = interp_current_at_vg(vg, id_sat, float(cfg["ion"]["Vg"]))
    ioff = interp_current_at_vg(vg, id_sat, float(cfg["ioff"]["Vg"]))
    ion_ioff = (ion / ioff if (np.isfinite(ion) and np.isfinite(ioff) and ioff > 0)
                else np.nan)

    meta = {}
    meta_path = run_dir / "run.yaml"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

    run_id = run_dir.name
    d_parsed, n_parsed = parse_run_id(run_id)
    return {
        "run_id": run_id,
        "owner": meta.get("owner", ""),
        "D_BCAT_nm": meta.get("D_BCAT_nm") or d_parsed,
        "doping_multiplier": meta.get("doping_multiplier") or n_parsed,
        "Vth_lin_V": vth_lin,
        "Vth_sat_V": vth_sat,
        "SS_mV_dec": ss,
        "DIBL_mV_V": dibl,
        "I_GIDL_A_um": i_gidl,
        "I_GIDL_max_A_um": i_gidl_max,
        "Ion_A_um": ion,
        "Ioff_A_um": ioff,
        "Ion_Ioff_ratio": ion_ioff,
        "n_points": len(df),
        "btbt_model": meta.get("btbt_model", ""),
        "sentaurus_version": meta.get("sentaurus_version", ""),
    }


def fmt(v, spec):
    return format(v, spec) if isinstance(v, float) and np.isfinite(v) else "  nan  "


def main():
    ap = argparse.ArgumentParser(description="Id-Vg 에서 소자 지표 추출")
    ap.add_argument("run_dir", nargs="?", help="예: runs/D36_N100")
    ap.add_argument("--all", action="store_true", help="runs/ 전체 재추출")
    args = ap.parse_args()

    cfg = load_config()

    if args.all:
        targets = sorted(p for p in (ROOT / "runs").iterdir()
                         if p.is_dir() and not p.name.startswith("_"))
    elif args.run_dir:
        targets = [Path(args.run_dir)]
    else:
        ap.error("run_dir 를 주거나 --all 을 쓸 것")

    ok = fail = 0
    for t in targets:
        try:
            m = extract_one(t, cfg)
            pd.DataFrame([m]).to_csv(t / "metrics.csv", index=False)
            print(f"[OK] {t.name:16s} GIDL={fmt(m['I_GIDL_A_um'],'.3e')} "
                  f"Vth={fmt(m['Vth_sat_V'],'.4f')} SS={fmt(m['SS_mV_dec'],'.1f')} "
                  f"Ion={fmt(m['Ion_A_um'],'.3e')}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] {t.name}: {e}", file=sys.stderr)
            fail += 1

    print(f"\n완료: {ok}개 성공, {fail}개 실패")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
