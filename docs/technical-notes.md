# 기술 결정 및 검증 기록 — 최종 상태

이 문서는 `Share` 저장소에서 **현재 유효한 기술 판단과 검증 결과**만 빠르게 확인하기 위한 문서다.

주제 선정 과정, 폐기된 방법론, 당시의 판단 변화는 [`ryu980920/competition`](https://github.com/ryu980920/competition)의 `docs/devlog.md`, `docs/topic-selection-history.md`, `docs/retrospective.md`에서 확인한다.

---

## 1. 최종 연구 프레이밍

최종 연구 질문은 다음과 같다.

> Embedded SiGe S/D에 투입되는 명목 응력 중 실제 FinFET pMOS 채널까지 전달되는 비율은 얼마이며, 그 전달 효율을 Ge 조성과 리세스 깊이(FR) 중 어떤 변수가 지배하는가?

초기의 People–Bean/Luryi–Suhir 임계두께 기반 결함 경계 프레이밍은 baseline fin 치수에서 계획한 변수 범위에 충분한 판별력을 주지 못해 폐기됐다.

현재 분석은 **Stress Transfer Efficiency(STE)**를 사용한다.

---

## 2. 최종 STE 정의

`STE = |stress_GPa| / (180 × 0.042 × x)`

- `x = Ge_percent / 100`
- `stress_GPa = SlFin_MPa / 1000`
- `SlFin`: ChFin 영역의 채널 길이 방향 체적평균 응력
- `M = 180 GPa`: 본 연구에서 사용한 이축탄성계수
- Vegard 계수: 0.042

코드 구현의 단일 기준은 `baseline/params.yaml`과 `analysis/build.py`다.

### 왜 체적평균인가

초기에는 다음 두 방식을 병행 수집했다.

- `SlFin`: ChFin 체적평균
- `SlFin_pt`: 게이트 계면 인접 단일점 근사

최종 데이터에서:

- 체적평균 응력은 다섯 Ge 조건 각각에서 `gmSat`과 +0.95 이상의 상관
- 계면 단일점 방식은 평균 약 -0.207의 상관

STE는 응력이 실제 성능으로 이어지는 효율을 나타내야 하므로 **체적평균 `SlFin`을 최종 채택**했다.

따라서 과거 문서의 `provisional`, `후보 1/2`, `최종 결정 예정` 표현은 더 이상 현재 상태가 아니다.

---

## 3. 최종 baseline

| 항목 | 값 |
|---|---:|
| Gate length | 25 nm |
| Fin height | 35 nm |
| Fin width (top / bottom) | 15 nm |
| Esd | 7.5 nm |
| S/D Boron concentration | 2 × 10²⁰ cm⁻³ |
| Channel concentration | 2 × 10¹⁸ cm⁻³ |
| Vdd | 0.8 V |
| Gate workfunction | 4.623 eV |
| Channel / substrate orientation | ⟨110⟩ / (100) |

본 25점 DoE에서는 Ge 조성과 FR만 변화시키고 나머지 조건을 고정했다.

---

## 4. DoE와 추가 검증

### 본 격자

- Ge: 30 / 40 / 50 / 60 / 70 %
- FR: 0 / 10 / 20 / 30 / 35 nm
- 총 25점

### 추가 검증

- Ge=50%, FR=15/22 nm: 설계창 경계 확인
- Ge=50%, Strain_Impact ON/OFF FR 전 구간: 형상 효과와 응력 전기효과 분리
- Fin width 15→7.5 nm, Ge=60/70%, FR 전 구간: 스케일링 민감도

추가 검증점은 본 5×5 회귀 격자에 섞지 않는다.

---

## 5. 사전 검증

### 5.1 응력–전기 결합

`Strain_Impact=1/0` 비교에서 G50_F0의 `IdSat_norm`이 약 +227% 차이를 보였다.

→ SDevice의 응력–전기 결합이 실제로 활성화되어 있음을 확인했다.

증빙: `baseline/verification_strain_impact_G50F0.csv`

### 5.2 FR 구조 반영

FR=15 nm 조건을 실제 실행하고 좌표축 단면을 비교해 baseline 대비 의도한 15 nm 추가 식각을 확인했다.

### 5.3 재현성

동일 조건 격자점 4쌍을 독립 재실행해 대조한 결과 편차 0.0%였다.

---

## 6. 지표 분리 원칙

서로 다른 현상을 한 지표로 뭉치지 않는다.

| 현상 | 지표 |
|---|---|
| 채널 응력 | `SlFin` / `stress_GPa` |
| 응력 전달 효율 | `ste` |
| 이동도 변화 | `gmSat` |
| 구동 성능 | `IdSat_norm` |
| 게이트 정전제어 | `SSlin` |
| 누설 | `Ioff_norm` |
| 숏채널 효과 | `DIBL_mV_V` |

`SSSat`은 게이트 제어와 drain-junction leakage가 섞인 값이므로 이상적 60 mV/dec 기준과 직접 비교하지 않는다.

---

## 7. 본 DoE의 최종 통계 결과

### 절대 응력

- Ge coefficient: -0.9888, `t = -61.78`
- FR coefficient: -0.1225, `t = -7.97`
- interaction: `t = -1.57`
- `R² = 0.9947`

→ **절대 응력은 Ge 조성이 지배한다.**

### STE

- intercept: 0.6492
- Ge coefficient: 0.0013, `t = 0.32`
- FR coefficient: 0.0333, `t = 8.41`
- interaction: `t = -0.82`

→ **정규화된 전달 효율은 FR이 지배한다.**

두 기준 모두 교호작용이 유의하지 않았다.

---

## 8. STE 25점 지도

| FR (nm) | Ge 30 | Ge 40 | Ge 50 | Ge 60 | Ge 70 |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.593 | 0.596 | 0.598 | 0.602 | 0.607 |
| 10 | 0.649 | 0.647 | 0.648 | 0.650 | 0.654 |
| 20 | 0.672 | 0.667 | 0.667 | 0.668 | 0.671 |
| 30 | 0.677 | 0.671 | 0.670 | 0.670 | 0.673 |
| 35 | 0.676 | 0.670 | 0.668 | 0.668 | 0.670 |

Ge 방향 변화는 매우 작고 FR 방향 변화가 크다.

---

## 9. Ge 조성의 역할

형상이 동일한 FR=0 조건에서 Ge 30→70% 증가 시:

- 채널 압축응력 증가
- `gmSat` 증가
- `IdSat_norm` 증가
- `SSlin`, `DIBL`은 큰 변화 없음
- `Ioff_norm`은 약 6배 증가

따라서 Ge 조성은 **응력의 양과 절대 성능을 높이는 재료 변수**이며, 주요 비용은 누설 증가다.

---

## 10. FR 설계창 확정

Ge=50%에서 FR=15/22 nm를 추가 검증했다.

| FR | STE | SSlin | Ioff_norm | gmSat |
|---:|---:|---:|---:|---:|
| 15 | 0.6595 | 82.15 | 5.26e-10 | 1.143e-4 |
| 20 | 0.6669 | 84.70 | 9.68e-10 | 1.149e-4 |
| 22 | 0.6680 | 87.47 | 1.93e-9 | 1.131e-4 |

- FR 15→20: `STE 이득 / SSlin 손실` = 2.91
- FR 20→22: 0.38
- 약 7.6배 급락
- gmSat은 FR=20에서 최대 후 감소
- Ioff는 FR=22에서 1e-9 초과

최종 실용 설계창: **FR 약 15~20 nm**

증빙: `baseline/verification_FR_refine_G50.csv`

---

## 11. 깊은 리세스 열화의 원인

Ge=50%에서 Strain_Impact ON/OFF FR 스윕을 비교했다.

FR 0→35 nm:

| 지표 | ON | OFF |
|---|---:|---:|
| SSlin | +44% | +31% |
| DIBL | +64% | +21% |
| Ioff | +43,497% | +4,136% |
| IdSat | +17% | +14% |

응력의 전기적 영향이 꺼져 있어도 정전제어와 누설 열화가 크게 남는다.

최종 해석:

1. 깊은 리세스가 채널 하부의 anti-punchthrough/channel-stop 영역을 제거한다.
2. 그 자리를 고농도 p+ SiGe가 채운다.
3. 게이트가 충분히 통제하지 못하는 하부 누설 경로가 열린다.
4. 응력/밴드구조 변화가 누설을 2차적으로 증폭한다.

증빙: `baseline/verification_strain_impact_G50_FRsweep.csv`

---

## 12. Fin-width 민감도

Fin width 15→7.5 nm 검증 결과:

### 얕은 FR

- SSlin 약 65~66 mV/dec
- DIBL 약 60% 감소
- STE 약 +10%

### 깊은 FR

Ge=60%, FR=35 nm:

| 지표 | 7.5 nm | 15 nm |
|---|---:|---:|
| SSlin | 222.3 | 104.5 |
| Ioff_norm | 4.97e-6 | 8.00e-8 |
| |VtiSat| | 0.070 V | 0.346 V |

→ **미세화될수록 FR 상한은 더 엄격해진다.**

증빙: `baseline/verification_finwidth_half_G60_G70.xlsx`

---

## 13. 분석 파이프라인

### `analysis/build.py`

- SWB export 인식
- Ge 몰분율 → % 변환
- FR µm → nm 변환
- `SlFin_MPa → stress_GPa`
- 최종 공식으로 STE 자동 계산
- DIBL 계산
- 팀원 결과 병합 및 교차검증
- `grid.csv`, `status.json` 생성

### `analysis/contour.py`

- 2차원 지도 생성
- 2FI 회귀
- 주효과·교호작용 정량화

`grid.csv`, `status.json`, `analysis/figures/`는 원본 데이터가 아니라 파이프라인 생성물이다.

---

## 14. 적용 범위

- Ge: 30~70%
- FR: 0~35 nm
- 이 범위 밖으로 수치 외삽하지 않는다.
- STE 절대값은 `M=180 GPa` 가정에 의존한다.
- Ge 효과는 70%에서도 포화하지 않았다.
- FinFET의 수치를 GAA에 직접 적용하지 않는다.

다른 구조로 가져갈 수 있는 것은 수치가 아니라 다음 방법론이다.

- 입력량과 전달효율 분리
- 정전제어·누설·성능 지표 분리
- 효율 포화와 비용 급증 사이에서 설계창 결정
- 물리 모델 ON/OFF로 열화 메커니즘 분리

---

## 15. 폐기된 과거 방법론

People–Bean/Luryi–Suhir 임계두께 기반 defect-boundary 접근은 **현재 분석 기준이 아니다.**

기록을 삭제하지 않고 Git 이력 및 `competition` 저장소에 보존한 이유는, 프로젝트가 어떤 검증을 통해 질문 자체를 바꿨는지 추적할 수 있게 하기 위해서다.

`Share`의 현재 기준은 오직 **최종 STE 정의 + 최종 baseline + 실제 실행 데이터**다.
