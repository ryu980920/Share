#!/usr/bin/env python3
"""
plt2csv.py — Sentaurus 전류 파일(.plt, DF-ISE xyplot)을 idvg.csv 로 변환한다.

★ Sentaurus 는 선형/포화 스윕을 별도 .plt 로 뱉는다. 두 개를 합쳐 하나의 csv 로 만든다.

사용법
    python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt -o runs/D36_N100/idvg.csv
    python analysis/plt2csv.py --list IdVg_lin_des.plt        # 데이터셋 이름만 확인

★ 데이터셋 이름이 버전/설정마다 다르다. 처음 한 번은 --list 로 확인하고
  --vg / --id 옵션으로 정확한 이름을 지정할 것. 확인한 이름은 팀에 공유해서
  3명이 같은 컬럼을 쓰도록 한다.
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np


def parse_plt(path):
    """DF-ISE xyplot 파일 → (datasets, data array). 실패 시 예외."""
    txt = Path(path).read_text(errors="ignore")

    m = re.search(r"datasets\s*=\s*\[(.*?)\]", txt, re.S)
    if not m:
        raise ValueError(f"{path}: 'datasets = [...]' 를 찾지 못함. "
                         f"DF-ISE xyplot 형식이 맞는지 확인할 것.")
    datasets = re.findall(r'"([^"]+)"', m.group(1))

    dm = re.search(r"Data\s*\{(.*)\}", txt, re.S)
    if not dm:
        raise ValueError(f"{path}: 'Data {{ ... }}' 블록을 찾지 못함.")
    nums = np.array([float(v) for v in
                     re.findall(r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?",
                                dm.group(1).replace("D", "E"))])

    ncol = len(datasets)
    if ncol == 0 or len(nums) % ncol != 0:
        raise ValueError(f"{path}: 데이터 개수({len(nums)})가 "
                         f"컬럼 수({ncol})로 나누어떨어지지 않음.")
    return datasets, nums.reshape(-1, ncol)


def pick(datasets, patterns, what):
    for p in patterns:
        for i, d in enumerate(datasets):
            if re.search(p, d, re.I):
                return i
    raise ValueError(
        f"{what} 컬럼을 자동으로 찾지 못했다.\n"
        f"  사용 가능한 데이터셋: {datasets}\n"
        f"  → --vg / --id 옵션으로 이름을 직접 지정할 것."
    )


def load(path, vg_name, id_name):
    datasets, data = parse_plt(path)
    iv = (datasets.index(vg_name) if vg_name
          else pick(datasets, [r"gate.*OuterVoltage", r"gate.*Voltage"], "Vg"))
    ii = (datasets.index(id_name) if id_name
          else pick(datasets, [r"drain.*TotalCurrent", r"drain.*Current"], "Id"))
    return data[:, iv], data[:, ii]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lin_plt", help="선형영역(Vd=0.1V) .plt")
    ap.add_argument("sat_plt", nargs="?", help="포화영역(Vd=1.0V) .plt")
    ap.add_argument("-o", "--out", default="idvg.csv")
    ap.add_argument("--vg", default=None, help="Vg 데이터셋 이름 직접 지정")
    ap.add_argument("--id", dest="idname", default=None, help="Id 데이터셋 이름 직접 지정")
    ap.add_argument("--width-um", type=float, default=1.0,
                    help="전류 정규화 폭 [um]. baseline/params.yaml 의 device_width_um 와 같게")
    ap.add_argument("--list", action="store_true", help="데이터셋 이름만 출력하고 종료")
    args = ap.parse_args()

    if args.list:
        ds, data = parse_plt(args.lin_plt)
        print(f"{args.lin_plt}  ({data.shape[0]}행 x {data.shape[1]}열)")
        for i, d in enumerate(ds):
            print(f"  [{i:2d}] {d}")
        return 0

    vg_l, id_l = load(args.lin_plt, args.vg, args.idname)
    if args.sat_plt:
        vg_s, id_s = load(args.sat_plt, args.vg, args.idname)
    else:
        print("[경고] 포화 .plt 를 안 줬다. Id_sat 을 Id_lin 으로 채운다 — "
              "DIBL/GIDL/Ion 이 전부 틀린 값이 된다.", file=sys.stderr)
        vg_s, id_s = vg_l, id_l

    # 선형 스윕의 Vg 격자를 기준으로 포화 전류를 보간
    o = np.argsort(vg_l)
    vg_l, id_l = vg_l[o], id_l[o]
    o2 = np.argsort(vg_s)
    id_s_i = np.interp(vg_l, vg_s[o2], np.abs(id_s[o2]))

    w = args.width_um
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("Vg,Id_lin,Id_sat\n")
        for a, b, c in zip(vg_l, np.abs(id_l) / w, id_s_i / w):
            f.write(f"{a:.4f},{b:.6e},{c:.6e}\n")

    print(f"저장: {out}  ({len(vg_l)}점, Vg {vg_l.min():.2f} ~ {vg_l.max():.2f} V)")
    print(f"다음: python analysis/extract.py {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
