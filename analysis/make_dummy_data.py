#!/usr/bin/env python3
"""
make_dummy_data.py — 가짜 Id-Vg 데이터로 분석 파이프라인을 시험한다.

★ 용도: Sentaurus 결과가 나오기 전(W1)에 extract -> merge -> contour 전체가
   제대로 도는지 확인하기 위한 것. 여기서 나온 숫자는 물리적 의미가 전혀 없다.

★ 실제 데이터를 넣기 전에 반드시 runs/ 의 더미 폴더를 지울 것:
      python analysis/make_dummy_data.py --clean

사용법
    python analysis/make_dummy_data.py           # 25개 격자점 더미 생성
    python analysis/make_dummy_data.py --clean   # 더미 삭제
"""

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
PARAMS = ROOT / "baseline" / "params.yaml"

MARKER = "DUMMY_DATA"   # run.yaml 에 남겨서 실제 데이터와 구분


def synth_idvg(d_nm, nmult, rng):
    """물리적으로 그럴듯한 모양만 흉내낸 Id-Vg. 교호작용을 일부러 심어둔다."""
    vg = np.arange(-1.0, 2.801, 0.05)

    d = (d_nm - 36.0) / 12.0          # [-1, 1]
    n = (nmult - 0.65) / 0.35         # [-1, 1]

    # --- GIDL: Vg=-0.5 에서의 값. 교호작용항 +0.40 을 의도적으로 삽입 ---
    log_gidl = -12.0 - 0.60 * d + 0.90 * n + 0.40 * d * n
    gidl_ref = 10 ** log_gidl
    gidl = gidl_ref * 10 ** (2.2 * (-vg - 0.5))
    gidl = np.where(vg < 0.3, gidl, 0.0)

    # --- 채널 전류: 서브스레숄드와 온전류를 조화평균으로 부드럽게 연결 ---
    vth_lin = 0.45 + 0.05 * d + 0.08 * n
    dibl_shift = 0.030 + 0.010 * d          # 포화에서 Vth 가 이만큼 낮아짐
    ss_dec = 0.075 + 0.004 * d              # [V/dec]

    def channel(vth):
        sub = 1e-7 * 10 ** ((vg - vth) / ss_dec)     # Vg=Vth 에서 정확히 1e-7
        on = 3e-5 * np.clip(vg - vth, 0, None)
        on = np.where(on > 0, on, np.inf)
        return 1.0 / (1.0 / sub + 1.0 / on)

    ch_lin = channel(vth_lin)
    ch_sat = channel(vth_lin - dibl_shift)

    id_lin = 0.14 * ch_lin + 0.12 * gidl
    id_sat = ch_sat + gidl

    noise = 1 + rng.normal(0, 0.005, size=vg.shape)
    return vg, np.abs(id_lin * noise), np.abs(id_sat * noise)


def owner_of(d_nm):
    if d_nm in (24, 30):
        return "A"
    if d_nm in (36, 42):
        return "B"
    return "C"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="더미 폴더 삭제")
    args = ap.parse_args()

    if args.clean:
        n = 0
        for p in RUNS.iterdir():
            if p.is_dir() and (p / "run.yaml").exists():
                txt = (p / "run.yaml").read_text(encoding="utf-8")
                if MARKER in txt:
                    shutil.rmtree(p)
                    n += 1
        print(f"더미 {n}개 삭제")
        return 0

    with open(PARAMS, encoding="utf-8") as f:
        doe = yaml.safe_load(f)["doe"]

    rng = np.random.default_rng(42)
    made = 0
    for d in doe["x_levels"]:
        for nm in doe["y_levels"]:
            run_id = f"D{int(d)}_N{int(round(nm*100)):03d}"
            rd = RUNS / run_id
            rd.mkdir(parents=True, exist_ok=True)

            vg, il, isat = synth_idvg(float(d), float(nm), rng)
            with open(rd / "idvg.csv", "w", encoding="utf-8") as f:
                f.write("Vg,Id_lin,Id_sat\n")
                for a, b, c in zip(vg, il, isat):
                    f.write(f"{a:.4f},{b:.6e},{c:.6e}\n")

            (rd / "run.yaml").write_text(
                f"# {MARKER} — 실제 결과 아님\n"
                f"run_id: {run_id}\n"
                f"owner: {owner_of(int(d))}\n"
                f"D_BCAT_nm: {int(d)}\n"
                f"doping_multiplier: {nm}\n"
                f"btbt_model: NonlocalPath\n"
                f"sentaurus_version: DUMMY\n"
                f"date: 2026-08-03\n"
                f"status: dummy\n", encoding="utf-8")

            (rd / "README.md").write_text(
                f"# {run_id}\n\n**{MARKER} — 파이프라인 시험용. 물리적 의미 없음.**\n",
                encoding="utf-8")
            made += 1

    print(f"더미 {made}개 생성 -> runs/")
    print("다음:")
    print("  python analysis/extract.py --all")
    print("  python analysis/merge.py")
    print("  python analysis/contour.py --all-figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
