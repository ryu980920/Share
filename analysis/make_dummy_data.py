#!/usr/bin/env python3
"""
make_dummy_data.py — 가짜 데이터로 파이프라인을 시험한다.

★ Sentaurus 결과가 나오기 전에 build.py → contour.py 가 도는지 확인하는 용도.
   여기서 나온 숫자는 물리적 의미가 전혀 없다.
★ 실제 데이터를 넣기 전에 반드시 지울 것:  python analysis/make_dummy_data.py --clean

★ x_levels/y_levels 는 baseline/params.yaml 의 값(지금은 placeholder)을 그대로
  읽어서 쓴다. 실제 스윕 값이 확정되면 자동으로 그 값 기준으로 더미가 생성된다.

★ 2026-08-05: Y축 변수명이 리세스 깊이(Recess_nm) → FR(FR_nm)로 바뀌었고,
  지표가 mobility_gain_pct → ste(Stress Transfer Efficiency)로 바뀌었다.
  ste 정규화 방법은 아직 팀 확정 전이므로, 여기서 만드는 ste 는 순전히
  파이프라인 시험용 가짜 비율(0~1 근방)일 뿐 실제 계산식이 아니다.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
PARAMS = ROOT / "baseline" / "params.yaml"

# 담당자 → 맡은 Ge% 열 (params.yaml 의 x_levels 를 3등분해서 낮은/중간/높은 순으로 채움)
OWNERS = ["유용성", "주수빈", "남다연"]


def synth_point(ge_pct, fr_nm, rng):
    """단순 합성 모델. 교호작용(+0.35) 을 일부러 심어서 contour.py 가 시너지로 판정하게 한다."""
    x = (ge_pct - 50.0) / 20.0    # 공칭 Ge% 50% 기준
    y = (fr_nm - 20.0) / 20.0     # 공칭 FR 근방 기준 (예시)
    stress = 1.4 + 0.55 * x + 0.35 * y + 0.35 * x * y            # GPa, 교호작용 삽입
    ste = 0.5 + 0.10 * x + 0.07 * y + 0.05 * x * y                # ★가짜 비율 — 실제 STE 계산식 아님
    noise_s = rng.normal(0, 0.03)
    noise_e = rng.normal(0, 0.02)
    return max(stress + noise_s, 0.01), min(max(ste + noise_e, 0.0), 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args()

    if a.clean:
        n = 0
        for p in RUNS.glob("*.csv"):
            if p.stem.startswith("_"):
                continue
            if "DUMMY" in p.read_text(encoding="utf-8")[:200]:
                p.unlink(); n += 1
        print(f"더미 {n}개 파일 삭제")
        return 0

    doe = yaml.safe_load(open(PARAMS, encoding="utf-8"))["doe"]
    xl = [float(v) for v in doe["x_levels"]]
    yl = [float(v) for v in doe["y_levels"]]
    if not doe.get("values_confirmed", False):
        print("[알림] doe.values_confirmed=false — 지금 x_levels/y_levels 는 placeholder 다.")
        print("       더미는 그 placeholder 값 기준으로 만들어진다 (파이프라인 시험용이므로 무방).")

    # 낮은→높은 순서를 유지한 채 거의 균등한 3덩어리로 자른다 (contiguous, np.array_split 과 동일한 방식).
    n = len(OWNERS)
    q, rem = divmod(len(xl), n)
    chunks, start = [], 0
    for i in range(n):
        size = q + (1 if i < rem else 0)
        chunk = xl[start:start + size] or xl[-1:]
        chunks.append(chunk)
        start += size
    cols_by_owner = dict(zip(OWNERS, chunks))

    rng = np.random.default_rng(42)
    made = 0
    for owner, cols in cols_by_owner.items():
        path = RUNS / f"{owner}_dummy.csv"
        with open(path, "w", encoding="utf-8") as f:
            f.write("# DUMMY — 파이프라인 시험용. 실제 결과 아님\n")
            f.write("run_id,stress_GPa,ste\n")
            for g in cols:
                for r in yl:
                    rid = f"G{int(round(g))}_F{int(round(r))}"
                    stress, ste = synth_point(float(g), float(r), rng)
                    f.write(f"{rid},{stress:.4f},{ste:.4f}\n")
        made += 1
        print(f"  생성: runs/{path.name}")

    print(f"\n더미 {made}개 파일 생성")
    print("다음: python analysis/build.py  →  python analysis/contour.py --all-figures")
    print("(회귀 판정이 '(b) 시너지' 로 나오면 정상 — 더미에 교호작용을 심어뒀다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
