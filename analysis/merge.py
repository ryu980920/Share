#!/usr/bin/env python3
"""
merge.py — runs/**/metrics.csv 를 모아 하나의 DoE 격자표(grid.csv)로 만든다.

★ 이 스크립트가 3명의 결과를 하나로 합치는 지점이다.
   빠진 격자점과 교차검증 불일치를 여기서 잡아낸다.

사용법
    python analysis/merge.py
    python analysis/merge.py --metric I_GIDL_A_um     # 피벗표로 볼 지표 지정
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
PARAMS = ROOT / "baseline" / "params.yaml"
OUT_CSV = ROOT / "analysis" / "grid.csv"

# 교차검증 허용 오차 (상대). 이걸 넘으면 경고.
XCHECK_TOL = 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="I_GIDL_A_um", help="피벗표로 출력할 지표")
    args = ap.parse_args()

    with open(PARAMS, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    doe = params["doe"]
    x_levels = [float(v) for v in doe["x_levels"]]
    y_levels = [float(v) for v in doe["y_levels"]]

    files = sorted((ROOT / "runs").glob("*/metrics.csv"))
    if not files:
        print("metrics.csv 가 하나도 없다. 먼저 extract.py 를 돌릴 것.", file=sys.stderr)
        return 1

    rows = []
    for f in files:
        try:
            rows.append(pd.read_csv(f))
        except Exception as e:
            print(f"[SKIP] {f}: {e}", file=sys.stderr)
    df = pd.concat(rows, ignore_index=True)

    # ------------------------------------------------------------------
    # 1) 교차검증 — 같은 (D, N) 조합이 2회 이상 있으면 값이 일치하는지 확인
    # ------------------------------------------------------------------
    print("=" * 68)
    print(" 1. 교차검증 (같은 격자점을 두 사람이 돌린 경우)")
    print("=" * 68)
    df["_key"] = df["D_BCAT_nm"].round(1).astype(str) + "/" + \
                 df["doping_multiplier"].round(3).astype(str)
    dup = df[df.duplicated("_key", keep=False)].sort_values("_key")
    if dup.empty:
        print("  중복 실행 없음. → docs/ROLES.md 의 교차검증 3점을 아직 안 돌렸다.")
    else:
        problem = 0
        for key, g in dup.groupby("_key"):
            vals = g["I_GIDL_A_um"].to_numpy(dtype=float)
            owners = ", ".join(str(o) for o in g["owner"])
            if np.all(np.isfinite(vals)) and np.mean(vals) != 0:
                spread = (np.max(vals) - np.min(vals)) / np.abs(np.mean(vals))
                flag = "OK  " if spread <= XCHECK_TOL else "불일치"
                if spread > XCHECK_TOL:
                    problem += 1
                print(f"  [{flag}] D/N={key:14s} 편차={spread*100:5.1f}%  "
                      f"({owners})  값={vals}")
            else:
                print(f"  [값없음] D/N={key}")
        if problem:
            print(f"\n  ★ {problem}개 격자점이 {XCHECK_TOL*100:.0f}% 허용치를 넘었다.")
            print("    환경 차이(버전/정규화 폭/모델 파라미터)를 의심할 것.")
            print("    즉시 Issue 를 열고, 원인 규명 전에는 등고선을 그리지 말 것.")

    # 중복은 평균내지 않고 첫 번째(담당자 것)를 채택
    df_u = df.drop_duplicates("_key", keep="first").drop(columns=["_key"])

    # ------------------------------------------------------------------
    # 2) 진행률 — 계획된 격자 대비 얼마나 채워졌나
    # ------------------------------------------------------------------
    print()
    print("=" * 68)
    print(" 2. DoE 격자 진행률")
    print("=" * 68)
    have = {(round(float(r.D_BCAT_nm), 1), round(float(r.doping_multiplier), 3))
            for r in df_u.itertuples()}
    planned = [(round(x, 1), round(y, 3)) for x in x_levels for y in y_levels]
    missing = [p for p in planned if p not in have]
    done = len(planned) - len(missing)
    bar = "#" * int(30 * done / len(planned))
    print(f"  [{bar:<30s}] {done}/{len(planned)}  ({done/len(planned)*100:.0f}%)")
    if missing:
        print(f"  남은 격자점 {len(missing)}개:")
        for x, y in missing:
            print(f"    - D{int(x)}_N{int(round(y*100)):03d}")

    # ------------------------------------------------------------------
    # 3) 피벗표
    # ------------------------------------------------------------------
    print()
    print("=" * 68)
    print(f" 3. 격자표 — {args.metric}")
    print("=" * 68)
    if args.metric not in df_u.columns:
        print(f"  '{args.metric}' 컬럼 없음. 사용 가능: "
              f"{[c for c in df_u.columns if c.endswith(('_um','_V','_dec','_ratio'))]}")
    else:
        pv = df_u.pivot_table(index="doping_multiplier",
                              columns="D_BCAT_nm",
                              values=args.metric)
        pv = pv.sort_index(ascending=False)
        with pd.option_context("display.float_format", lambda v: f"{v:.3e}"):
            print(pv.to_string())

    # ------------------------------------------------------------------
    # 4) 저장
    # ------------------------------------------------------------------
    df_u = df_u.sort_values(["D_BCAT_nm", "doping_multiplier"])
    df_u.to_csv(OUT_CSV, index=False)
    print(f"\n저장: {OUT_CSV.relative_to(ROOT)}  ({len(df_u)}행)")

    # ------------------------------------------------------------------
    # 5) 대시보드용 status.json  (dashboard/index.html 이 읽는다)
    # ------------------------------------------------------------------
    xcheck = []
    for key, g in dup.groupby("_key") if not dup.empty else []:
        vals = g["I_GIDL_A_um"].to_numpy(dtype=float)
        if np.all(np.isfinite(vals)) and np.mean(vals) != 0:
            spread = float((np.max(vals) - np.min(vals)) / abs(np.mean(vals)))
        else:
            spread = None
        xcheck.append({"key": key,
                       "owners": [str(o) for o in g["owner"]],
                       "spread": spread,
                       "ok": (spread is not None and spread <= XCHECK_TOL)})

    def owner_of(d):
        return "A" if d in (24, 30) else ("B" if d in (36, 42) else "C")

    points = []
    for x in x_levels:
        for y in y_levels:
            rid = f"D{int(x)}_N{int(round(y*100)):03d}"
            hit = df_u[(np.isclose(df_u.D_BCAT_nm, x)) &
                       (np.isclose(df_u.doping_multiplier, y))]
            rec = {"run_id": rid, "D": x, "N": y,
                   "owner": owner_of(int(x)), "done": not hit.empty}
            if not hit.empty:
                r = hit.iloc[0]
                for k in ["I_GIDL_A_um", "Vth_sat_V", "SS_mV_dec",
                          "DIBL_mV_V", "Ion_A_um"]:
                    v = r.get(k, None)
                    rec[k] = (float(v) if v is not None and np.isfinite(v) else None)
                rec["owner_actual"] = str(r.get("owner", ""))
            points.append(rec)

    status = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "x_levels": x_levels, "y_levels": y_levels,
        "done": done, "total": len(planned),
        "points": points, "xcheck": xcheck,
    }
    out_json = ROOT / "analysis" / "status.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)
    print(f"저장: {out_json.relative_to(ROOT)}  (대시보드용)")

    print("다음: python analysis/contour.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
