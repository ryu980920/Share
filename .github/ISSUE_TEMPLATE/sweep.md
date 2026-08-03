---
name: "① 격자점 실행 (스윕 과제)"
about: "DoE 격자점 하나를 돌리는 작업"
title: "[?] D??_N??? 실행"
labels: ["sweep", "phase-2"]
assignees: ""
---

## 담당 / 격자점

- 담당자: <!-- A / B / C -->
- Run ID: <!-- 예: D36_N100 -->
- Phase: <!-- P1 단독스윕 / P2 2차원DoE -->

## 고정 조건 (baseline — 절대 건드리지 않는다)

`baseline/params.yaml` 을 그대로 쓴다. 아래는 확인용 요약이다.

| 항목 | 값 |
|---|---|
| Lgate | 20 nm |
| 리세스 깊이 | 120 nm |
| 게이트 산화막 | 5 nm |
| 게이트 일함수 | 4.8 eV (W) |
| BTBT 모델 | NonlocalPath |
| Vd (선형/포화) | 0.1 V / 1.0 V |
| Vg 스윕 | -1.0 → +2.8 V, 0.05 V step |

## 이번에 바꾸는 것 (딱 두 개)

| 변수 | 값 | baseline 대비 |
|---|---|---|
| DBCAT (질화막 두께) | ___ nm | ___ |
| S/D 도핑 배수 | ×___ | ___ |

> **다른 값을 함께 바꾸면 두 변수의 효과가 섞여서 그 격자점은 버려야 한다.**
> 수렴 때문에 어쩔 수 없이 바꿨다면 `run.yaml` 의 `deviations_from_baseline` 에 전부 적을 것.

## 산출물 체크리스트

- [ ] `runs/<RUN_ID>/run.yaml` 채움 (버전, 모델, 수렴 여부 포함)
- [ ] `runs/<RUN_ID>/idvg.csv` — 컬럼 `Vg, Id_lin, Id_sat`, 단위 A/µm
- [ ] `python analysis/extract.py runs/<RUN_ID>` 실행 → `metrics.csv` 생성
- [ ] `runs/<RUN_ID>/plot.png` — Id-Vg log 스케일
- [ ] `runs/<RUN_ID>/README.md` — 3줄 요약
- [ ] PR 생성 (제목: `[담당자] <RUN_ID> 완료`)

## 완료 판정 기준

- [ ] 수렴 실패 없음 (또는 실패 조건이 `run.yaml` 에 기록됨)
- [ ] GIDL 구간(Vg < 0)에서 전류가 실제로 증가하는 형태가 보임 — 안 보이면 BTBT 모델이 안 켜진 것
- [ ] Vth 가 baseline 대비 상식적 범위 (±0.2 V 이내)
- [ ] `metrics.csv` 에 nan 이 없음

## 결과 (완료 후 여기에 채운다)

| 지표 | 값 | baseline 대비 |
|---|---|---|
| I_GIDL [A/µm] | | |
| Vth_sat [V] | | |
| SS [mV/dec] | | |
| DIBL [mV/V] | | |
| Ion [A/µm] | | |

한 줄 소견:
