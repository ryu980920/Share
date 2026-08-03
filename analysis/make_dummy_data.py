#!/usr/bin/env python3
"""
make_dummy_data.py — 가짜 데이터로 파이프라인을 시험한다.

★ Sentaurus 결과가 나오기 전에 build.py → contour.py 가 도는지 확인하는 용도.
   여기서 나온 숫자는 물리적 의미가 전혀 없다.
★ 실제 데이터를 넣기 전에 반드시 지울 것:  python analysis/make_dummy_data.py --clean
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
PARAMS = ROOT / "baseline" / "params.yaml"

# 담당자 → 맡은 DBCAT 열
OWNERS = {"유용성": [24, 30], "주수빈": [36, 42], "남다연": [48]}


def synth(d_nm, nmult, rng):
    vg = np.arange(-1.0, 2.801, 0.05)
    d = (d_nm - 36.0) / 12.0
    n = (nmult - 0.65) / 0.35
    gidl_ref = 10 ** (-12.0 - 0.60 * d + 0.90 * n + 0.40 * d * n)   # 교호작용 +0.40 삽입
    gidl = np.where(vg < 0.3, gidl_ref * 10 ** (2.2 * (-vg - 0.5)), 0.0)

    vth = 0.45 + 0.05 * d + 0.08 * n
    ss = 0.075 + 0.004 * d

    def ch(vt):
        sub = 1e-7 * 10 ** ((vg - vt) / ss)
        on = 3e-5 * np.clip(vg - vt, 0, None)
        return 1.0 / (1.0 / sub + 1.0 / np.where(on > 0, on, np.inf))

    noise = 1 + rng.normal(0, 0.005, vg.shape)
    return vg, np.abs((0.14 * ch(vth) + 0.12 * gidl) * noise), \
           np.abs((ch(vth - 0.030 - 0.010 * d) + gidl) * noise)


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
    rng = np.random.default_rng(42)
    made = 0
    for owner, cols in OWNERS.items():
        for d in cols:
            if float(d) not in [float(v) for v in doe["x_levels"]]:
                continue
            path = RUNS / f"{owner}_D{d}.csv"
            with open(path, "w", encoding="utf-8") as f:
                f.write("# DUMMY — 파이프라인 시험용. 실제 결과 아님\n")
                f.write("run_id,Vg,Id_lin,Id_sat\n")
                for nm in doe["y_levels"]:
                    rid = f"D{int(d)}_N{int(round(float(nm)*100)):03d}"
                    vg, il, isat = synth(float(d), float(nm), rng)
                    for v, b, c in zip(vg, il, isat):
                        f.write(f"{rid},{v:.4f},{b:.6e},{c:.6e}\n")
            made += 1
            print(f"  생성: runs/{path.name}")
    print(f"\n더미 {made}개 파일 생성")
    print("다음: python analysis/build.py  →  python analysis/contour.py --all-figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
