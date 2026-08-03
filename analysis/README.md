# analysis/ — 공용 분석 스크립트

> **지표 정의가 여기 한 곳에만 있다.** 손으로 계산하지 않는다.

## 전체 흐름

```
Sentaurus .plt          →  idvg.csv     →  metrics.csv  →  grid.csv  →  등고선
             plt2csv.py       extract.py       merge.py       contour.py
```

## 준비

```bash
pip install -r analysis/requirements.txt
```

## 1) Sentaurus 결과 → idvg.csv

처음 한 번은 데이터셋 이름을 확인한다. **버전/설정마다 다르므로 팀에 공유할 것.**

```bash
python analysis/plt2csv.py --list IdVg_lin_des.plt
```

확인했으면 변환한다.

```bash
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       -o runs/D36_N100/idvg.csv --width-um 1.0
```

자동 인식이 안 되면 이름을 직접 준다.

```bash
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       -o runs/D36_N100/idvg.csv \
       --vg "gate OuterVoltage" --id "drain TotalCurrent"
```

## 2) 지표 추출

```bash
python analysis/extract.py runs/D36_N100     # 한 개
python analysis/extract.py --all             # 전체 재추출
```

`config.yaml` 을 바꿨다면 **반드시 `--all` 로 전부 다시 뽑는다.** 안 그러면 정의가 섞인다.

## 3) 병합 + 검증

```bash
python analysis/merge.py
python analysis/merge.py --metric Ion_A_um
```

출력에서 세 가지를 확인한다.

1. **교차검증** — 같은 격자점을 두 사람이 돌린 경우 편차가 5% 이내인가
2. **진행률** — 빠진 격자점이 무엇인가
3. **격자표** — 값이 단조로운가, 튀는 점은 없는가

## 4) 등고선 + 상호작용 판정

```bash
python analysis/contour.py                   # GIDL
python analysis/contour.py --all-figures     # Ion/DIBL/SS 까지
```

출력되는 것:

- **교호작용 회귀** — 등고선이 휘었는지를 눈이 아니라 t값/p값으로 판정
- **판정** — 기획서 4-4절의 (a) 독립 / (b) 시너지 / (c) 트레이드오프
- **시너지 정량화** — 개별 최적화 대비 결합 최적화의 추가 개선분 [dex]
- `figures/contour_*.png`

**시너지 표의 숫자가 발표 결론 문장에 그대로 들어간다.**

## 5) 실제 데이터 전에 파이프라인 시험하기

Sentaurus 결과가 없어도 전체 흐름을 미리 돌려볼 수 있다. **W1에 반드시 한 번 해볼 것.**

```bash
python analysis/make_dummy_data.py
python analysis/extract.py --all
python analysis/merge.py
python analysis/contour.py --all-figures
python analysis/make_dummy_data.py --clean    # ★ 실제 데이터 넣기 전 반드시 삭제
```

더미에는 교호작용이 일부러 심어져 있어서, `contour.py` 가 "(b) 시너지"를 맞게 판정하는지로
파이프라인이 정상인지 확인할 수 있다. 더미 숫자 자체에는 물리적 의미가 없다.
