#!/usr/bin/env python3
"""
build.py — runs/ 의 스윕 CSV 들을 읽어 지표를 뽑고 격자표·대시보드 데이터를 만든다.

★ 이 스크립트 하나가 전부다. (예전의 extract.py + merge.py 를 합친 것)

입력  runs/<이름>_<스윕이름>.csv      long 형식: run_id,Vg,Id_lin,Id_sat
출력  analysis/grid.csv               격자점 하나당 한 줄 (지표)
      analysis/status.json            대시보드용

사용법
    python analysis/build.py
    python analysis/build.py --metric Ion_A_um     # 격자표에 다른 지표 보기
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis" / "config.yaml"
PARAMS = ROOT / "baseline" / "params.yaml"
OUT_CSV = ROOT / "analysis" / "grid.csv"
OUT_JSON = ROOT / "analysis" / "status.json"

REQUIRED = ["run_id", "Vg", "Id_lin", "Id_sat"]
XCHECK_TOL = 0.05          # 교차검증 허용 편차


# ----------------------------------------------------------------------
def parse_run_id(rid):
    """'D36_N100' -> (36.0, 1.00)"""
    try:
        p = str(rid).split("_")
        return float(p[0].lstrip("Dd")), float(p[1].lstrip("Nn")) / 100.0
    except Exception:
        return float("nan"), float("nan")


def interp_vg_at_current(vg, idd, i_crit):
    idd = np.abs(idd)
    above = np.where(idd >= i_crit)[0]
    if len(above) == 0:
        return np.nan
    k = above[0]
    if k == 0:
        return float(vg[0])
    y0, y1 = np.log10(idd[k - 1]), np.log10(idd[k])
    if y1 == y0:
        return float(vg[k])
    return float(vg[k - 1] + (np.log10(i_crit) - y0) * (vg[k] - vg[k - 1]) / (y1 - y0))


def interp_current_at_vg(vg, idd, v):
    if v < vg.min() or v > vg.max():
        return np.nan
    return float(np.interp(v, vg, np.abs(idd)))


def compute_ss(vg, idd, i_min, i_max, use_min=True):
    idd = np.abs(idd)
    m = (idd >= i_min) & (idd <= i_max) & (idd > 0)
    if m.sum() < 3:
        return np.nan
    v, logi = vg[m], np.log10(idd[m])
    if use_min:
        dv, dl = np.diff(v), np.diff(logi)
        ok = dl > 0
        if ok.sum() == 0:
            return np.nan
        return float(np.min(dv[ok] / dl[ok]) * 1000.0)
    s = np.polyfit(v, logi, 1)[0]
    return float(1000.0 / s) if s > 0 else np.nan


def metrics_for(run_id, g, cfg, owner, source):
    g = g.sort_values("Vg")
    vg = g["Vg"].to_numpy(float)
    il = g["Id_lin"].to_numpy(float)
    isat = g["Id_sat"].to_numpy(float)

    warn = ""
    if np.any(np.abs(isat) > 1e-1):
        warn = "전류가 0.1 A/um 초과 — 폭 정규화(A/um) 누락 의심"

    ic = float(cfg["vth"]["I_crit_A_per_um"])
    vth_l = interp_vg_at_current(vg, il, ic)
    vth_s = interp_vg_at_current(vg, isat, ic)
    ss = compute_ss(vg, il,
                    float(cfg["ss"]["fit_I_min_A_per_um"]),
                    float(cfg["ss"]["fit_I_max_A_per_um"]),
                    bool(cfg["ss"].get("use_min_slope", True)))
    vdl, vds = float(cfg["dibl"]["Vd_lin"]), float(cfg["dibl"]["Vd_sat"])
    dibl = (((vth_l - vth_s) / (vds - vdl)) * 1000.0
            if np.isfinite(vth_l) and np.isfinite(vth_s) else np.nan)
    gidl = interp_current_at_vg(vg, isat, float(cfg["gidl"]["V_gidl"]))
    ion = interp_current_at_vg(vg, isat, float(cfg["ion"]["Vg"]))
    ioff = interp_current_at_vg(vg, isat, float(cfg["ioff"]["Vg"]))
    d, n = parse_run_id(run_id)

    return {
        "run_id": run_id, "owner": owner, "source": source,
        "D_BCAT_nm": d, "doping_multiplier": n,
        "Vth_lin_V": vth_l, "Vth_sat_V": vth_s, "SS_mV_dec": ss,
        "DIBL_mV_V": dibl, "I_GIDL_A_um": gidl,
        "Ion_A_um": ion, "Ioff_A_um": ioff,
        "Ion_Ioff_ratio": (ion / ioff if np.isfinite(ion) and np.isfinite(ioff)
                           and ioff > 0 else np.nan),
        "n_points": len(g), "warn": warn,
    }



# ----------------------------------------------------------------------
#  Sentaurus Workbench 변수표(gtree export) 읽기
#  → SWB 에서 "Export Variables" 로 뽑은 CSV 를 그대로 쓸 수 있다.
#
#  구조: 1행=툴이름, 2행=노드이름, 3행=파라미터/변수 이름, 4행~=실험조건
# ----------------------------------------------------------------------
def looks_like_swb(path):
    with open(path, encoding="utf-8-sig") as f:
        first = f.readline()
    return "run_id" not in first and ("sprocess" in first or "sdevice" in first)


def read_swb(path, cfg):
    import csv as _csv
    rows = list(_csv.reader(open(path, encoding="utf-8-sig")))
    if len(rows) < 4:
        raise ValueError("SWB 변수표 형식인데 실험 행이 없다 (4행 이상 필요)")
    names, data = rows[2], rows[3:]

    sw = cfg.get("swb", {})
    xp, yp = sw.get("x_param", "DBCAT"), sw.get("y_param", "Nmult")
    mapping = sw.get("map", {})

    def col(nm):
        return names.index(nm) if nm in names else None

    ix, iy = col(xp), col(yp)
    missing = []
    if ix is None: missing.append(xp)
    if iy is None: missing.append(yp)
    if missing:
        raise ValueError(
            f"SWB 파라미터 컬럼 {missing} 을 못 찾았다.\n"
            f"    이 파일에 있는 이름: {[n for n in names if n]}\n"
            f"    → SWB 에서 파라미터 이름을 '{xp}' / '{yp}' 로 바꾸거나,\n"
            f"      analysis/config.yaml 의 swb.x_param / y_param 을 실제 이름으로 고칠 것.")

    def num(v):
        try:
            f = float(v)
            return f if np.isfinite(f) else np.nan
        except Exception:
            return np.nan          # 'x', 'xx', '' = 아직 안 돌아간 셀

    out, pending = [], 0
    for r in data:
        d, n = num(r[ix]), num(r[iy])
        if not (np.isfinite(d) and np.isfinite(n)):
            continue
        rec = {"D_BCAT_nm": d, "doping_multiplier": n,
               "run_id": f"D{int(round(d))}_N{int(round(n*100)):03d}"}
        empty = True
        for our, swb_name in mapping.items():
            i = col(swb_name)
            v = num(r[i]) if i is not None and i < len(r) else np.nan
            rec[our] = v
            if np.isfinite(v):
                empty = False
        if empty:
            pending += 1
        rec["_pending"] = empty
        out.append(rec)
    return out, pending


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="I_GIDL_A_um")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(CONFIG, encoding="utf-8"))
    doe = yaml.safe_load(open(PARAMS, encoding="utf-8"))["doe"]
    xl = [float(v) for v in doe["x_levels"]]
    yl = [float(v) for v in doe["y_levels"]]

    files = sorted(p for p in (ROOT / "runs").glob("*.csv")
                   if not p.stem.startswith("_"))
    if not files:
        print("runs/ 에 CSV 가 없다. runs/README.md 의 형식을 참고할 것.", file=sys.stderr)
        return 1

    print("=" * 66)
    print(" 1. 파일 읽기")
    print("=" * 66)
    rows, problems = [], []
    for f in files:
        owner = f.stem.split("_")[0]

        # --- Sentaurus Workbench 변수표 형식 ---
        if looks_like_swb(f):
            try:
                recs, pending = read_swb(f, cfg)
            except Exception as e:
                print(f"  [실패] {f.name}: {e}"); problems.append(f.name); continue
            if not recs:
                print(f"  [건너뜀] {f.name}: 유효한 실험 행이 없다"); continue
            for r in recs:
                r.update({"owner": owner, "source": f.name, "n_points": 0, "warn": "",
                          "SS_mV_dec": r.get("SS_mV_dec", np.nan),
                          "DIBL_mV_V": r.get("DIBL_mV_V", np.nan)})
                rows.append(r)
            tag = f" (아직 안 돌아간 조건 {pending}개)" if pending else ""
            print(f"  [OK] {f.name:32s} {owner:8s} SWB 변수표 · 조건 {len(recs)}개{tag}")
            print(f"        {', '.join(r['run_id'] for r in recs)}")
            continue

        # --- Id-Vg 원시 곡선 형식 ---
        try:
            df = pd.read_csv(f, comment="#")
        except Exception as e:
            print(f"  [실패] {f.name}: {e}"); problems.append(f.name); continue
        miss = [c for c in REQUIRED if c not in df.columns]
        if miss:
            print(f"  [실패] {f.name}: 컬럼 {miss} 누락. 발견={list(df.columns)}")
            print(f"          → 컬럼명은 정확히 run_id,Vg,Id_lin,Id_sat (대소문자 구분)")
            problems.append(f.name); continue
        ids = list(dict.fromkeys(df["run_id"]))
        for rid in ids:
            rows.append(metrics_for(rid, df[df.run_id == rid], cfg, owner, f.name))
        print(f"  [OK] {f.name:32s} {owner:8s} 격자점 {len(ids)}개  {', '.join(map(str,ids))}")

    if not rows:
        print("\n읽을 수 있는 데이터가 없다.", file=sys.stderr); return 1
    m = pd.DataFrame(rows)

    for w in m[m.warn != ""].itertuples():
        print(f"  [경고] {w.run_id} ({w.source}): {w.warn}")

    # --- 2. 교차검증 -----------------------------------------------------
    print()
    print("=" * 66)
    print(" 2. 교차검증 (같은 격자점을 두 사람이 돌린 경우)")
    print("=" * 66)
    xcheck = []
    dup = m[m.duplicated("run_id", keep=False)]
    if dup.empty:
        print("  중복 실행 없음. → docs/ROLES.md 의 교차검증 3점을 아직 안 돌렸다.")
    else:
        for rid, g in dup.groupby("run_id"):
            v = g["I_GIDL_A_um"].to_numpy(float)
            owners = list(g["owner"])
            sp = (float((v.max() - v.min()) / abs(v.mean()))
                  if np.all(np.isfinite(v)) and v.mean() != 0 else None)
            ok = sp is not None and sp <= XCHECK_TOL
            xcheck.append({"run_id": rid, "owners": owners, "spread": sp, "ok": ok})
            tag = "OK  " if ok else "불일치"
            print(f"  [{tag}] {rid:12s} 편차 {('%5.1f%%'%(sp*100)) if sp is not None else '  ?  '}"
                  f"  ({' vs '.join(owners)})")
        bad = [x for x in xcheck if not x["ok"]]
        if bad:
            print(f"\n  ★ {len(bad)}개가 허용치({XCHECK_TOL*100:.0f}%)를 넘었다.")
            print("    환경 차이(버전/정규화 폭/모델 파라미터)를 의심할 것.")
            print("    원인 규명 전에는 등고선을 그리지 말 것.")

    mu = m.drop_duplicates("run_id", keep="first")

    # --- 3. 진행률 -------------------------------------------------------
    print()
    print("=" * 66)
    print(" 3. DoE 격자 진행률")
    print("=" * 66)
    have = {(round(r.D_BCAT_nm, 1), round(r.doping_multiplier, 3)) for r in mu.itertuples()}
    planned = [(round(x, 1), round(y, 3)) for x in xl for y in yl]
    missing = [p for p in planned if p not in have]
    done = len(planned) - len(missing)
    print(f"  [{'#'*int(30*done/len(planned)):<30s}] {done}/{len(planned)} "
          f"({done/len(planned)*100:.0f}%)")
    if missing:
        print("  남은 격자점: " + ", ".join(f"D{int(x)}_N{int(round(y*100)):03d}"
                                            for x, y in missing[:12])
              + (" …" if len(missing) > 12 else ""))

    # --- 4. 격자표 -------------------------------------------------------
    print()
    print("=" * 66)
    print(f" 4. 격자표 — {args.metric}")
    print("=" * 66)
    if args.metric in mu.columns:
        pv = mu.pivot_table(index="doping_multiplier", columns="D_BCAT_nm",
                            values=args.metric).sort_index(ascending=False)
        with pd.option_context("display.float_format", lambda v: f"{v:.3e}"):
            print(pv.to_string())

    # --- 5. 저장 ---------------------------------------------------------
    mu.sort_values(["D_BCAT_nm", "doping_multiplier"]).to_csv(OUT_CSV, index=False)

    owner_of = {}
    for r in mu.itertuples():
        owner_of[round(r.D_BCAT_nm, 1)] = r.owner
    points = []
    for x in xl:
        for y in yl:
            rid = f"D{int(x)}_N{int(round(y*100)):03d}"
            hit = mu[mu.run_id == rid]
            rec = {"run_id": rid, "D": x, "N": y, "done": not hit.empty,
                   "owner": owner_of.get(round(x, 1), "")}
            if not hit.empty:
                r = hit.iloc[0]
                for k in ["I_GIDL_A_um", "Vth_sat_V", "SS_mV_dec", "DIBL_mV_V", "Ion_A_um"]:
                    v = r.get(k)
                    rec[k] = float(v) if v is not None and np.isfinite(v) else None
            points.append(rec)

    json.dump({"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
               "x_levels": xl, "y_levels": yl, "done": done, "total": len(planned),
               "points": points, "xcheck": xcheck,
               "files": [f.name for f in files], "problems": problems},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\n저장: analysis/grid.csv ({len(mu)}행) · analysis/status.json")
    print("다음: python analysis/contour.py --all-figures")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
