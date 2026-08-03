#!/usr/bin/env python3
"""
plt2csv.py — Sentaurus 전류 파일(.plt)을 스윕 CSV 에 한 줄씩 쌓는다.

★ 격자점 하나를 돌릴 때마다 이 명령을 한 번씩 실행하면,
  같은 CSV 파일에 계속 누적된다. 스윕이 끝나면 그 파일 하나만 올리면 된다.

사용법
    # 처음 (파일 새로 만들기)
    python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
           --run-id D24_N030 --out runs/유용성_D24.csv

    # 이후 (같은 파일에 덧붙이기)
    python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
           --run-id D24_N050 --out runs/유용성_D24.csv --append

    # 데이터셋 이름 확인 (처음 한 번은 반드시)
    python analysis/plt2csv.py IdVg_lin_des.plt --list
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np


def parse_plt(path):
    txt = Path(path).read_text(errors="ignore")
    m = re.search(r"datasets\s*=\s*\[(.*?)\]", txt, re.S)
    if not m:
        raise ValueError(f"{path}: 'datasets = [...]' 없음. DF-ISE xyplot 형식이 맞는지 확인.")
    ds = re.findall(r'"([^"]+)"', m.group(1))
    dm = re.search(r"Data\s*\{(.*)\}", txt, re.S)
    if not dm:
        raise ValueError(f"{path}: 'Data {{ ... }}' 블록 없음.")
    nums = np.array([float(v) for v in re.findall(
        r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?", dm.group(1).replace("D", "E"))])
    if not ds or len(nums) % len(ds) != 0:
        raise ValueError(f"{path}: 데이터({len(nums)})가 컬럼({len(ds)})으로 안 나눠짐.")
    return ds, nums.reshape(-1, len(ds))


def pick(ds, pats, what):
    for p in pats:
        for i, d in enumerate(ds):
            if re.search(p, d, re.I):
                return i
    raise ValueError(f"{what} 컬럼 자동 인식 실패.\n  사용 가능: {ds}\n"
                     f"  → --vg / --id 로 이름을 직접 지정할 것.")


def load(path, vgn, idn):
    ds, data = parse_plt(path)
    iv = ds.index(vgn) if vgn else pick(ds, [r"gate.*OuterVoltage", r"gate.*Voltage"], "Vg")
    ii = ds.index(idn) if idn else pick(ds, [r"drain.*TotalCurrent", r"drain.*Current"], "Id")
    return data[:, iv], data[:, ii]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lin_plt")
    ap.add_argument("sat_plt", nargs="?")
    ap.add_argument("--run-id", help="예: D24_N030")
    ap.add_argument("-o", "--out", help="예: runs/유용성_D24.csv")
    ap.add_argument("--append", action="store_true", help="기존 파일에 덧붙이기")
    ap.add_argument("--vg"); ap.add_argument("--id", dest="idname")
    ap.add_argument("--width-um", type=float, default=1.0,
                    help="전류 정규화 폭. baseline/params.yaml 의 device_width_um 와 같게")
    ap.add_argument("--list", action="store_true", help="데이터셋 이름만 출력")
    a = ap.parse_args()

    if a.list:
        ds, data = parse_plt(a.lin_plt)
        print(f"{a.lin_plt}  ({data.shape[0]}행 x {data.shape[1]}열)")
        for i, d in enumerate(ds):
            print(f"  [{i:2d}] {d}")
        return 0

    if not a.run_id or not a.out:
        ap.error("--run-id 와 --out 이 필요하다")
    if not re.fullmatch(r"D\d+_N\d{3}(_\w+)?", a.run_id):
        print(f"[경고] run-id '{a.run_id}' 가 규칙(D36_N100)과 다르다. "
              f"이대로면 격자에 안 올라간다.", file=sys.stderr)

    vgl, idl = load(a.lin_plt, a.vg, a.idname)
    if a.sat_plt:
        vgs, ids = load(a.sat_plt, a.vg, a.idname)
    else:
        print("[경고] 포화 .plt 가 없다. DIBL/GIDL/Ion 이 전부 틀린 값이 된다.", file=sys.stderr)
        vgs, ids = vgl, idl

    o = np.argsort(vgl); vgl, idl = vgl[o], idl[o]
    o2 = np.argsort(vgs)
    ids_i = np.interp(vgl, vgs[o2], np.abs(ids[o2]))

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    exists = out.exists() and a.append
    if exists:
        old = out.read_text(encoding="utf-8")
        if f"\n{a.run_id}," in old:
            print(f"[중단] {out.name} 에 {a.run_id} 가 이미 있다. "
                  f"다시 넣으려면 해당 줄을 지우고 실행할 것.", file=sys.stderr)
            return 1

    w = a.width_um
    with open(out, "a" if exists else "w", encoding="utf-8") as f:
        if not exists:
            f.write("run_id,Vg,Id_lin,Id_sat\n")
        for v, b, c in zip(vgl, np.abs(idl) / w, ids_i / w):
            f.write(f"{a.run_id},{v:.4f},{b:.6e},{c:.6e}\n")

    n = sum(1 for _ in open(out, encoding="utf-8")) - 1
    ids_in = set()
    for line in open(out, encoding="utf-8"):
        if "," in line and not line.startswith("run_id"):
            ids_in.add(line.split(",")[0])
    print(f"{'덧붙임' if exists else '새로 만듦'}: {out}  "
          f"({a.run_id} {len(vgl)}점 추가 · 파일 전체 {len(ids_in)}개 격자점 / {n}줄)")
    print(f"현재 들어 있는 격자점: {', '.join(sorted(ids_in))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
