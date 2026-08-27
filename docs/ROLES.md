# 역할 분담 및 완료 기록

> **상태: 경진대회 본 프로젝트 완료**
>
> 이 문서는 초기 4주 계획표가 아니라 **실제로 어떻게 분담하고 어떤 검증을 완료했는지**를 남기는 최종 기록이다. 과거 일정·TODO의 상세 변화는 Git 이력과 `competition/docs/devlog.md`에서 확인한다.

---

## 1. 팀 구성

- 유용성
- 주수빈
- 남다연

본 5×5 DoE는 Ge 조성 열(column)을 기준으로 분담했다.

| 담당 | Ge 조성 | FR 조건 |
|---|---|---|
| 주수빈 | 30%, 40% | 0 / 10 / 20 / 30 / 35 nm |
| 유용성 | 50% | 0 / 10 / 20 / 30 / 35 nm |
| 남다연 | 60%, 70% | 0 / 10 / 20 / 30 / 35 nm |

총 25개 본 격자점을 완료했다.

---

## 2. 공통 실행 규칙

세 사람의 결과를 하나의 지도와 회귀에 합치기 위해 다음 조건은 공통으로 유지했다.

- Gate length: 25 nm
- Fin height: 35 nm
- Fin width: 15 nm
- Esd: 7.5 nm
- Nsd: 2 × 10²⁰ cm⁻³ Boron
- Nch: 2 × 10¹⁸ cm⁻³
- Vdd: 0.8 V
- Gate workfunction: 4.623 eV
- Channel / substrate orientation: ⟨110⟩ / (100)

최종 수치 기준은 `baseline/params.yaml`이다.

---

## 3. 본 DoE 완료 상태

- Ge 30/40/50/60/70% × FR 0/10/20/30/35 nm
- **25/25 완료**
- 팀원별 export를 `runs/`에 병합
- 동일 조건 독립 재실행 4쌍 대조
- **재현성 편차 0.0%**

본 격자의 역할은 절대 응력과 STE에 대한 Ge·FR 주효과 및 교호작용을 정량화하는 것이다.

---

## 4. 공통 검증

### 응력–전기 결합

`Strain_Impact=1/0` G50_F0 비교로 결합 활성 여부를 확인했다.

- IdSat_norm 약 +227% 차이
- 결론: 응력 모델이 전기 특성에 실제 반영됨

증빙: `baseline/verification_strain_impact_G50F0.csv`

### FR 구조 검증

FR=15 nm 조건을 실행해 좌표축 단면에서 의도한 추가 식각을 확인했다.

### STE 정의 확정

본 스윕 동안 `SlFin`과 `SlFin_pt`를 병행 수집하고, 최종 데이터에서 실제 이동도 프록시 `gmSat`과의 상관을 비교했다.

- `SlFin` 체적평균: 모든 Ge 조건에서 +0.95 이상
- 계면 단일점: 평균 약 -0.207

→ **체적평균 `SlFin`을 최종 STE 분자로 채택**

---

## 5. 후속 검증 분담

### 유용성 — FR 설계창 경계 보강 및 분석 통합

Ge=50%에서 본 격자 사이의 경계를 확인하기 위해 FR=15 nm, 22 nm 추가 결과를 분석에 반영했다.

최종 판단:

- FR 15→20 이득/대가 비율: 2.91
- FR 20→22: 0.38
- FR=20을 경계로 약 7.6배 급락
- 실용 설계창: **약 15~20 nm**

증빙: `baseline/verification_FR_refine_G50.csv`

### 남다연 — Fin width 민감도

Fin width를 15→7.5 nm로 줄이고 Ge=60/70%에서 FR 전 구간을 비교했다.

최종 판단:

- 얕은 FR: SSlin·DIBL·STE 개선
- 깊은 FR: 정전제어와 누설이 크게 악화되어 관계 역전
- **미세화될수록 FR 상한이 더 엄격해짐**

증빙: `baseline/verification_finwidth_half_G60_G70.xlsx`

### 팀 공통 — Strain_Impact FR 스윕 해석

Ge=50%에서 Strain_Impact ON/OFF FR 스윕을 비교해 깊은 리세스의 전기적 열화가 응력 자체인지 형상 변화인지 분리했다.

최종 판단:

- 응력 전기효과 OFF에서도 SSlin·DIBL·Ioff 열화 재현
- **형상 변화가 1차 원인**, 응력/밴드구조 변화는 2차 증폭 요인

증빙: `baseline/verification_strain_impact_G50_FRsweep.csv`

---

## 6. 분석 파이프라인 역할

팀원이 직접 STE를 제각각 계산하지 않는다.

`analysis/build.py`가 다음을 공통 처리한다.

1. SWB export 파싱
2. Ge 몰분율 → % 변환
3. FR µm → nm 변환
4. `SlFin` MPa → GPa 변환
5. 최종 공식으로 STE 계산
6. DIBL 계산
7. 결과 병합·교차검증
8. `analysis/grid.csv`, `analysis/status.json` 생성

`analysis/contour.py`는 병합 데이터로 지도와 2FI 회귀를 생성한다.

---

## 7. 최종 프로젝트 결론과 역할의 연결

| 결론 | 주된 근거 작업 |
|---|---|
| 절대 응력은 Ge 조성이 지배 | 25점 본 DoE |
| STE는 FR이 지배 | 25점 본 DoE + 최종 STE 정의 |
| Ge×FR 교호작용 없음 | 2FI 회귀 |
| Ge 조성의 비용은 누설 | FR=0 Ge sweep 비교 |
| 실용 FR 설계창 15~20 nm | FR=15/22 추가 검증 |
| 깊은 FR 열화는 형상 효과가 1차 | Strain_Impact ON/OFF FR sweep |
| 미세화될수록 FR 상한이 엄격 | Fin width 7.5 nm 민감도 |

---

## 8. 초기 계획 문서에 대하여

이 파일의 과거 버전에는 P0~P3, W1~W4 일정과 미완료 체크리스트가 있었다. 그것은 **프로젝트 시작 시점의 실행 계획**이며 현재 작업 상태가 아니다.

최종 상태를 확인할 때는 다음 순서를 따른다.

1. `README.md` — 현재 프로젝트 상태
2. `baseline/params.yaml` — 최종 공통 조건
3. `docs/technical-notes.md` — 최종 기술 판단
4. `analysis/grid.csv` — 본 격자 병합 결과
5. `competition/docs/reports/경진대회_보고서.docx` — 최종 제출 결과

초기 계획과 변경 과정이 필요하면 Git 이력 또는 `competition` 저장소의 기록을 사용한다.
