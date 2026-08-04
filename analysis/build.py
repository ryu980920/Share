#!/usr/bin/env python3
"""
build.py — runs/ 의 스윕 CSV 들을 읽어 지표를 정리하고 격자표·대시보드 데이터를 만든다.

★ 이 스크립트 하나가 전부다.

입력  runs/<이름>_<스윕이름>.csv      wide 형식: 한 줄 = 한 격자점
      run_id, stress_GPa, mobility_gain_pct [, Vth_V, Ion_A_um ...]
      runs/attachments/<run_id>/{structure.png, idvg_curve.png, notes.md}   (선택)
출력  analysis/grid.csv               격자점 하나당 한 줄
      analysis/status.json            대시보드용 (체크리스트 진행률은 progress.json 이 별도)

사용법
    python analysis/build.py
    python analysis/build.py --metric mobility_gain_pct
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

REQUIRED = ["run_id", "stress_GPa", "mobility_gain_pct"]
XCHECK_TOL = 0.05          # 교차검증 허용 편차 (주 지표 stress_GPa 기준)
XCHECK_METRIC = "stress_GPa"


# ----------------------------------------------------------------------
def parse_run_id(rid):
    """'G30_R50' -> (30.0, 50.0)   (Ge%, 리세스 깊이 nm)"""
    try:
        p = str(rid).split("_")
        return float(p[0].lstrip("Gg")), float(p[1].lstrip("Rr"))
    except Exception:
        return float("nan"), float("nan")


def make_run_id(ge, recess):
    return f"G{int(round(ge))}_R{int(round(recess))}"


# ----------------------------------------------------------------------
#  첨부물(사진/커브/메모) 스캔 — runs/attachments/<run_id>/
# ----------------------------------------------------------------------
def scan_attachments(run_id, acfg):
    d = ROOT / acfg.get("dir", "runs/attachments") / run_id
    out = {"has_structure": False, "has_curve": False, "has_defect": False,
           "has_notes": False, "n_extra": 0, "notes_preview": ""}
    if not d.is_dir():
        return out
    sfile = d / acfg.get("structure_image", "structure.png")
    cfile = d / acfg.get("curve_image", "idvg_curve.png")
    dfile = d / acfg.get("defect_image", "defect_check.png")
    nfile = d / acfg.get("notes_file", "notes.md")
    out["has_structure"] = sfile.exists()
    out["has_curve"] = cfile.exists()
    out["has_defect"] = dfile.exists()
    out["n_extra"] = len(list(d.glob("extra_*")))
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
#  Sentaurus Workbench 변수표(gtree export) 읽기
#  → SWB 에서 "Export Variables" 로 뽑은 CSV 를 그대로 쓸 수 있다.
#
#  구조: 1행=툴이름, 2행=노드이름, 3행=파라미터/변수 이름, 4행~=실험조건
# ----------------------------------------------------------------------
def looks_like_swb(path):
    with open(path, encoding="utf-8-sig") as f:
        first = f.readline()
    return "run_id" not in first and ("sprocess" in first or "sdevice" in first or "sde" in first)


def read_swb(path, cfg):
    import csv as _csv
    rows = list(_csv.reader(open(path, encoding="utf-8-sig")))
    if len(rows) < 4:
        raise ValueError("SWB 변수표 형식인데 실험 행이 없다 (4행 이상 필요)")
    names, data = rows[2], rows[3:]

    sw = cfg.get("swb", {})
    xp, yp = sw.get("x_param", "GePercent"), sw.get("y_param", "Recess_nm")
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
        g, rc = num(r[ix]), num(r[iy])
        if not (np.isfinite(g) and np.isfinite(rc)):
            continue
        rec = {"Ge_percent": g, "Recess_nm": rc, "run_id": make_run_id(g, rc)}
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
        print("   Ge%/리세스 깊이 스윕 값이 아직 확정되지 않았다는 뜻이다.")
        print("   지금 나오는 격자표/등고선은 참고용이며, 확정 전에 결론 내지 말 것.")
        print("=" * 66)
        print()

    files = sorted(p for p in (ROOT / "runs").glob("*.csv")
                   if not p.stem.startswith("_"))
    if not files:
        print("runs/ 에 CSV 가 없다. README.md 의 형식을 참고할 것.", file=sys.stderr)
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
                r.update({"owner": owner, "source": f.name, "warn": ""})
                r.update(scan_attachments(r["run_id"], acfg))
                rows.append(r)
            tag = f" (아직 안 돌아간 조건 {pending}개)" if pending else ""
            print(f"  [OK] {f.name:32s} {owner:8s} SWB 변수표 · 조건 {len(recs)}개{tag}")
            print(f"        {', '.join(r['run_id'] for r in recs)}")
            continue

        # --- wide 형식: 한 줄 = 한 격자점 ---
        try:
            df = pd.read_csv(f, comment="#")
        except Exception as e:
            print(f"  [실패] {f.name}: {e}"); problems.append(f.name); continue
        miss = [c for c in REQUIRED if c not in df.columns]
        if miss:
            print(f"  [실패] {f.name}: 컬럼 {miss} 누락. 발견={list(df.columns)}")
            print(f"          → 컬럼명은 정확히 run_id,stress_GPa,mobility_gain_pct (대소문자 구분)")
            problems.append(f.name); continue

        ids = []
        for _, r in df.iterrows():
            rid = r["run_id"]
            ge, rc = parse_run_id(rid)
            warn = ""
            if pd.notna(r.get("stress_GPa")) and abs(float(r["stress_GPa"])) > 10:
                warn = "응력이 10 GPa 초과 — 단위/부호 확인 의심"
            rec = {"run_id": rid, "owner": owner, "source": f.name,
                   "Ge_percent": ge, "Recess_nm": rc, "warn": warn}
            for extra in df.columns:
                if extra == "run_id":
                    continue
                rec[extra] = r[extra]
            rec.update(scan_attachments(rid, acfg))
            rows.append(rec)
            ids.append(rid)
        print(f"  [OK] {f.name:32s} {owner:8s} 격자점 {len(ids)}개  {', '.join(map(str, ids))}")

    if not rows:
        print("\n읽을 수 있는 데이터가 없다.", file=sys.stderr); return 1
    m = pd.DataFrame(rows)

    for w in m[m.warn != ""].itertuples():
        print(f"  [경고] {w.run_id} ({w.source}): {w.warn}")

    # --- 2. 교차검증 -----------------------------------------------------
    print()
    print("=" * 66)
    print(f" 2. 교차검증 (같은 격자점을 두 사람이 돌린 경우, 기준 지표: {XCHECK_METRIC})")
    print("=" * 66)
    xcheck = []
    dup = m[m.duplicated("run_id", keep=False)]
    if dup.empty:
        print("  중복 실행 없음. → docs/ROLES.md 의 교차검증 1점씩을 아직 안 돌렸다.")
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
            print("    환경 차이(버전/추출 위치 정의/모델 파라미터)를 의심할 것.")
            print("    원인 규명 전에는 등고선을 그리지 말 것.")

    mu = m.drop_duplicates("run_id", keep="first")

    # --- 3. 진행률 -------------------------------------------------------
    print()
    print("=" * 66)
    print(" 3. DoE 격자 진행률")
    print("=" * 66)
    have = {(round(r.Ge_percent, 1), round(r.Recess_nm, 1)) for r in mu.itertuples()}
    planned = [(round(x, 1), round(y, 1)) for x in xl for y in yl]
    missing = [p for p in planned if p not in have]
    done = len(planned) - len(missing)
    print(f"  [{'#'*int(30*done/len(planned)):<30s}] {done}/{len(planned)} "
          f"({done/len(planned)*100:.0f}%)")
    if missing:
        print("  남은 격자점: " + ", ".join(make_run_id(x, y) for x, y in missing[:12])
              + (" …" if len(missing) > 12 else ""))

    # --- 4. 격자표 -------------------------------------------------------
    print()
    print("=" * 66)
    print(f" 4. 격자표 — {args.metric}")
    print("=" * 66)
    if args.metric in mu.columns:
        pv = mu.pivot_table(index="Recess_nm", columns="Ge_percent",
                            values=args.metric).sort_index(ascending=False)
        with pd.option_context("display.float_format", lambda v: f"{v:.3e}"):
            print(pv.to_string())
    else:
        print(f"  ({args.metric} 컬럼이 아직 없다)")

    # --- 5. 저장 ---------------------------------------------------------
    mu.sort_values(["Ge_percent", "Recess_nm"]).to_csv(OUT_CSV, index=False)

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
                for k in ["stress_GPa", "mobility_gain_pct", "Vth_V", "Ion_A_um",
                          "has_structure", "has_curve", "has_defect", "n_extra",
                          "has_notes", "notes_preview"]:
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
    print("다음: python analysis/contour.py --all-figures")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
