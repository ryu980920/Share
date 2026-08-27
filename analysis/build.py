#!/usr/bin/env python3
"""
build.py — runs/ 의 스윕 CSV 들을 읽어 지표를 정리하고 격자표·대시보드 데이터를 만든다.

최종 STE 정의 (2026-08-27):
    STE = |stress_GPa| / (M * 0.042 * x)
    x = Ge_percent / 100
    M = 180 GPa
    stress_GPa = SlFin_MPa / 1000

SlFin은 ChFin 영역의 채널 길이 방향 체적평균 응력이다. 25점 데이터에서
모든 Ge 조건에 대해 gmSat과 +0.95 이상의 상관을 보여 최종 STE 분자로 채택했다.
계면 인접 단일점 SlFin_pt는 검증용 원자료로 보존하지만 STE 계산에는 사용하지 않는다.

입력  runs/<이름>_<스윕이름>.csv      wide 형식: 한 줄 = 한 격자점
      run_id, stress_GPa [, 기타 지표 ...]
      또는 Sentaurus Workbench Export Variables CSV
      runs/attachments/<run_id>/{사진 파일들, notes.md}   (선택)
출력  analysis/grid.csv               격자점 하나당 한 줄
      analysis/status.json            대시보드용

사용법
    python analysis/build.py
    python analysis/build.py --metric ste
"""

import argparse
import json
import re
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

REQUIRED = ["run_id", "stress_GPa"]
XCHECK_TOL = 0.05
XCHECK_METRIC = "stress_GPa"
DVD_FOR_DIBL = 0.75        # Vdd(0.8) - Vlin(0.05) [V]

MU_COLUMNS = ["run_id", "Ge_percent", "FR_nm", "owner"]


# ----------------------------------------------------------------------
def parse_run_id(rid):
    """'G50_F10' -> (50.0, 10.0)   (Ge%, FR_nm)"""
    try:
        p = str(rid).split("_")
        return float(p[0].lstrip("Gg")), float(p[1].lstrip("Ff"))
    except Exception:
        return float("nan"), float("nan")


def make_run_id(ge, fr):
    return f"G{int(round(ge))}_F{int(round(fr))}"


def compute_ste(stress_gpa, ge_percent, pmeta):
    """최종 보고서 정의로 STE를 계산한다. 유효하지 않은 입력은 NaN."""
    try:
        s = float(stress_gpa)
        g = float(ge_percent)
    except (TypeError, ValueError):
        return np.nan
    if not (np.isfinite(s) and np.isfinite(g)) or g <= 0:
        return np.nan

    scfg = pmeta.get("stress_transfer_efficiency", {})
    M = float(scfg.get("biaxial_modulus_GPa", 180.0))
    vegard = float(scfg.get("vegard_coefficient", 0.042))
    denom = M * vegard * (g / 100.0)
    if not np.isfinite(denom) or denom <= 0:
        return np.nan
    return abs(s) / denom


# ----------------------------------------------------------------------
# 첨부물(사진/메모) 스캔 — runs/attachments/<run_id>/
# ----------------------------------------------------------------------
def scan_attachments(run_id, acfg):
    d = ROOT / acfg.get("dir", "runs/attachments") / run_id
    out = {"has_photo": False, "n_photos": 0, "has_notes": False, "notes_preview": ""}
    if not d.is_dir():
        return out
    nfile = d / acfg.get("notes_file", "notes.md")
    photos = [p for p in d.iterdir() if p.is_file() and p.name != nfile.name]
    out["n_photos"] = len(photos)
    out["has_photo"] = len(photos) > 0
    if nfile.exists():
        out["has_notes"] = True
        try:
            txt = nfile.read_text(encoding="utf-8").strip()
            n = int(acfg.get("notes_preview_chars", 160))
            out["notes_preview"] = (txt[:n] + "…") if len(txt) > n else txt
        except Exception:
            pass
    return out


# ----------------------------------------------------------------------
# Sentaurus Workbench 변수표(gtree export) 읽기
# ----------------------------------------------------------------------
_NODE_TAG_RE = re.compile(r"^\[n\d+\]:\s*(.*)$")


def _strip_node_tag(v):
    """'[n12]: 0.4' -> '0.4'. 노드 태그가 없으면 그대로 반환."""
    v = (v or "").strip()
    m = _NODE_TAG_RE.match(v)
    return m.group(1).strip() if m else v


def looks_like_swb(path):
    with open(path, encoding="utf-8-sig") as f:
        lines = [f.readline() for _ in range(3)]
    first, second = lines[0], (lines[1] if len(lines) > 1 else "")
    if "run_id" in first:
        return False
    if "sprocess" in first or "sdevice" in first or "sde" in first:
        return True
    return bool(re.search(r"\[n\d+\]:", second))


def read_swb(path, cfg, pmeta):
    import csv as _csv
    rows = list(_csv.reader(open(path, encoding="utf-8-sig")))
    if len(rows) < 2:
        raise ValueError("SWB 변수표 형식인데 실험 행이 없다 (최소 2행 필요)")

    if len(rows) > 2 and any(tok in rows[1] for tok in ("sprocess", "sdevice", "svisual", "sde")):
        names, data = rows[2], rows[3:]
    else:
        names, data = rows[0], rows[1:]
    names = [n.strip() for n in names]

    sw = cfg.get("swb", {})
    xp, yp = sw.get("x_param", "Ge"), sw.get("y_param", "FR")
    mapping = sw.get("map", {})

    def col(nm):
        return names.index(nm) if nm in names else None

    ix, iy = col(xp), col(yp)
    missing = []
    if ix is None:
        missing.append(xp)
    if iy is None:
        missing.append(yp)
    if missing:
        raise ValueError(
            f"SWB 파라미터 컬럼 {missing} 을 못 찾았다.\n"
            f"    이 파일에 있는 이름: {[n for n in names if n]}\n"
            f"    → SWB 파라미터 이름 또는 analysis/config.yaml 의 swb 매핑을 확인할 것.")

    def num(v):
        v = _strip_node_tag(v)
        try:
            f = float(v)
            return f if np.isfinite(f) else np.nan
        except Exception:
            return np.nan

    out, pending = [], 0
    last_g, last_fr = np.nan, np.nan
    for r in data:
        if not any(c.strip() for c in r):
            continue
        g_cell = _strip_node_tag(r[ix]) if ix < len(r) else ""
        fr_cell = _strip_node_tag(r[iy]) if iy < len(r) else ""

        if g_cell == "":
            g_raw = last_g
        else:
            g_raw = num(r[ix])
            if np.isfinite(g_raw):
                last_g = g_raw

        if fr_cell == "":
            fr_raw = last_fr
        else:
            fr_raw = num(r[iy])
            if np.isfinite(fr_raw):
                last_fr = fr_raw

        if not (np.isfinite(g_raw) and np.isfinite(fr_raw)):
            continue

        # 현재 SWB export: Ge는 몰분율(0~1), FR은 um 단위.
        g, fr = g_raw * 100.0, fr_raw * 1000.0
        rec = {"Ge_percent": g, "FR_nm": fr, "run_id": make_run_id(g, fr)}
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

        # 최종 STE 분자: SlFin 체적평균 응력.
        if np.isfinite(rec.get("SlFin_MPa", np.nan)):
            rec["stress_GPa"] = rec["SlFin_MPa"] / 1000.0
            rec["ste"] = compute_ste(rec["stress_GPa"], g, pmeta)

        # DIBL = (|VtiLin| - |VtiSat|) / ΔVd [mV/V]
        vl, vs = rec.get("VtiLin", np.nan), rec.get("VtiSat", np.nan)
        if np.isfinite(vl) and np.isfinite(vs):
            rec["DIBL_mV_V"] = (abs(vl) - abs(vs)) / DVD_FOR_DIBL * 1000.0
        out.append(rec)
    return out, pending


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="stress_GPa")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(CONFIG, encoding="utf-8"))
    pmeta = yaml.safe_load(open(PARAMS, encoding="utf-8"))
    doe = pmeta["doe"]
    xl = [float(v) for v in doe["x_levels"]]
    yl = [float(v) for v in doe["y_levels"]]
    acfg = cfg.get("attachments", {})

    if not doe.get("values_confirmed", False):
        print("=" * 66)
        print(" ⚠ 경고: baseline/params.yaml 의 doe.values_confirmed 가 false 다.")
        print("   Ge%/FR 스윕 값이 아직 확정되지 않았다.")
        print("=" * 66)
        print()

    files = sorted(p for p in (ROOT / "runs").glob("*.csv")
                   if not p.stem.startswith("_"))

    problems, xcheck = [], []
    mu = pd.DataFrame(columns=MU_COLUMNS)

    if not files:
        print("runs/ 에 스윕 CSV 가 없다 — 첨부물 상태만으로 status.json 을 만든다.")
        print()
    else:
        print("=" * 66)
        print(" 1. 파일 읽기")
        print("=" * 66)
        rows = []
        for f in files:
            owner = f.stem.split("_")[0]

            if looks_like_swb(f):
                try:
                    recs, pending = read_swb(f, cfg, pmeta)
                except Exception as e:
                    print(f"  [실패] {f.name}: {e}")
                    problems.append(f.name)
                    continue
                if not recs:
                    print(f"  [건너뜀] {f.name}: 유효한 실험 행이 없다")
                    continue
                for r in recs:
                    r.update({"owner": owner, "source": f.name, "warn": ""})
                    r.update(scan_attachments(r["run_id"], acfg))
                    rows.append(r)
                tag = f" (아직 안 돌아간 조건 {pending}개)" if pending else ""
                print(f"  [OK] {f.name:32s} {owner:8s} SWB 변수표 · 조건 {len(recs)}개{tag}")
                print(f"        {', '.join(r['run_id'] for r in recs)}")
                continue

            # wide 형식: 한 줄 = 한 격자점
            try:
                df = pd.read_csv(f, comment="#")
            except Exception as e:
                print(f"  [실패] {f.name}: {e}")
                problems.append(f.name)
                continue
            miss = [c for c in REQUIRED if c not in df.columns]
            if miss:
                print(f"  [실패] {f.name}: 컬럼 {miss} 누락. 발견={list(df.columns)}")
                print("          → 필수 컬럼은 run_id,stress_GPa. ste 는 build.py가 다시 계산한다.")
                problems.append(f.name)
                continue

            ids = []
            for _, r in df.iterrows():
                rid = r["run_id"]
                ge, fr = parse_run_id(rid)
                warn = ""
                if pd.notna(r.get("stress_GPa")) and abs(float(r["stress_GPa"])) > 10:
                    warn = "응력이 10 GPa 초과 — 단위/부호 확인 의심"
                rec = {"run_id": rid, "owner": owner, "source": f.name,
                       "Ge_percent": ge, "FR_nm": fr, "warn": warn}
                for extra in df.columns:
                    if extra == "run_id":
                        continue
                    rec[extra] = r[extra]

                # CSV에 기존 ste가 있더라도 최종 공통 정의로 다시 계산해 일관성을 보장한다.
                rec["ste"] = compute_ste(rec.get("stress_GPa"), ge, pmeta)
                rec.update(scan_attachments(rid, acfg))
                rows.append(rec)
                ids.append(rid)
            print(f"  [OK] {f.name:32s} {owner:8s} 격자점 {len(ids)}개  {', '.join(map(str, ids))}")

        if not rows:
            print("\n읽을 수 있는 데이터가 없다 — 첨부물만 있는 상태로 계속 진행한다.",
                  file=sys.stderr)
        else:
            m = pd.DataFrame(rows)

            for w in m[m.warn != ""].itertuples():
                print(f"  [경고] {w.run_id} ({w.source}): {w.warn}")

            print()
            print("=" * 66)
            print(f" 2. 교차검증 (같은 격자점을 두 사람이 돌린 경우, 기준 지표: {XCHECK_METRIC})")
            print("=" * 66)
            dup = m[m.duplicated("run_id", keep=False)]
            if dup.empty:
                print("  중복 실행 없음.")
            elif XCHECK_METRIC not in m.columns:
                print(f"  {XCHECK_METRIC} 컬럼이 없어 교차검증을 계산할 수 없다.")
            else:
                for rid, g in dup.groupby("run_id"):
                    v = g[XCHECK_METRIC].to_numpy(float)
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
                    print("    환경 차이(버전/모델 파라미터)를 확인할 것.")

            mu = m.drop_duplicates("run_id", keep="first")

            print()
            print("=" * 66)
            print(" 3. DoE 격자 진행률")
            print("=" * 66)
            have = {(round(r.Ge_percent, 1), round(r.FR_nm, 1)) for r in mu.itertuples()}
            planned = [(round(x, 1), round(y, 1)) for x in xl for y in yl]
            missing = [p for p in planned if p not in have]
            done_now = len(planned) - len(missing)
            print(f"  [{'#'*int(30*done_now/len(planned)):<30s}] {done_now}/{len(planned)} "
                  f"({done_now/len(planned)*100:.0f}%)")
            if missing:
                print("  남은 격자점: " + ", ".join(make_run_id(x, y) for x, y in missing[:12])
                      + (" …" if len(missing) > 12 else ""))

            print()
            print("=" * 66)
            print(f" 4. 격자표 — {args.metric}")
            print("=" * 66)
            if args.metric in mu.columns:
                pv = mu.pivot_table(index="FR_nm", columns="Ge_percent",
                                    values=args.metric).sort_index(ascending=False)
                with pd.option_context("display.float_format", lambda v: f"{v:.3e}"):
                    print(pv.to_string())
            else:
                print(f"  ({args.metric} 컬럼이 없다)")

    planned = [(round(x, 1), round(y, 1)) for x in xl for y in yl]
    have = {(round(r.Ge_percent, 1), round(r.FR_nm, 1)) for r in mu.itertuples()}
    done = len(planned) - len([p for p in planned if p not in have])

    mu.sort_values(["Ge_percent", "FR_nm"]).to_csv(OUT_CSV, index=False)

    owner_of = {}
    for r in mu.itertuples():
        owner_of[round(r.Ge_percent, 1)] = r.owner
    points = []
    for x in xl:
        for y in yl:
            rid = make_run_id(x, y)
            hit = mu[mu.run_id == rid]
            rec = {"run_id": rid, "G": x, "R": y, "done": not hit.empty,
                   "owner": owner_of.get(round(x, 1), "")}
            if not hit.empty:
                r = hit.iloc[0]
                for k in ["stress_GPa", "ste", "Vth_V", "Ion_A_um",
                          "has_photo", "n_photos", "has_notes", "notes_preview"]:
                    v = r.get(k)
                    if isinstance(v, (bool, str)):
                        rec[k] = v
                    else:
                        rec[k] = float(v) if v is not None and np.isfinite(v) else None
            else:
                rec.update(scan_attachments(rid, acfg))
            points.append(rec)

    json.dump({"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
               "x_levels": xl, "y_levels": yl, "done": done, "total": len(planned),
               "values_confirmed": doe.get("values_confirmed", False),
               "points": points, "xcheck": xcheck,
               "files": [f.name for f in files], "problems": problems},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\n저장: analysis/grid.csv ({len(mu)}행) · analysis/status.json")
    print("다음: python analysis/contour.py --metric ste")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
