# FinFET pMOS Embedded SiGe S/D — 팀 실행·결과 공유 저장소

차세대반도체 경진대회 프로젝트의 **공통 baseline, Sentaurus 결과, 검증 데이터, 분석 파이프라인을 팀원이 동일한 기준으로 공유하기 위한 저장소**다.

최종 프로젝트 제목:

> **FinFET pMOS Embedded SiGe S/D의 응력 전달 효율(STE) 특성화 및 실용적 공정 마진 도출**

프로젝트의 주제선정 과정·판단 이력·회고는 [`ryu980920/competition`](https://github.com/ryu980920/competition)에 보존한다. 이 저장소는 과거 의사결정 기록을 중복하는 대신 **현재 기준의 실행 조건과 결과**에 집중한다.

---

## 현재 상태

- 본 DoE: **Ge 30/40/50/60/70% × FR 0/10/20/30/35 nm = 25/25 완료**
- 동일 조건 독립 재실행: **4쌍, 편차 0.0%**
- STE 정의: **최종 확정**
- STE 분자: **ChFin 체적평균 채널 길이 방향 응력 `SlFin`**
- 추가 경계 검증: **Ge=50%, FR=15/22 nm 완료**
- Strain_Impact ON/OFF FR 스윕: **완료**
- Fin width 15→7.5 nm 민감도: **Ge 60/70%, FR 전 구간 완료**
- 최종 실용 FR 설계창: **약 15~20 nm**

최종 제출 보고서는 `competition/docs/reports/경진대회_보고서.docx`를 기준으로 한다.

---

## 최종 기준 조건

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

정확한 파이프라인 입력값은 [`baseline/params.yaml`](baseline/params.yaml)을 단일 기준으로 사용한다.

---

## STE 정의

`STE = |stress_GPa| / (180 × 0.042 × x)`

- `x = Ge_percent / 100`
- `stress_GPa = SlFin_MPa / 1000`
- `SlFin`: ChFin 영역의 채널 길이 방향 체적평균 응력
- `180 GPa`: 본 연구에서 사용한 이축탄성계수
- `0.042`: Vegard 계수

초기에는 체적평균과 게이트 계면 인접 단일점 응력을 병행 수집했지만, 최종 데이터에서 체적평균 응력이 다섯 Ge 조건 모두 `gmSat`과 +0.95 이상의 상관을 보인 반면 계면 단일점 방식은 평균 약 -0.207의 상관을 보여 최종 STE는 체적평균으로 확정했다.

`analysis/build.py`가 이 정의로 STE를 자동 계산한다. 사람마다 별도로 손계산한 STE를 합치지 않는다.

---

## 최종 핵심 결과

### 절대 응력

- Ge 조성 주효과: `t = -61.78`
- FR 주효과: `t = -7.97`
- Ge×FR 교호작용: `t = -1.57` → 유의하지 않음
- `R² = 0.9947`

**절대 응력의 양은 Ge 조성이 지배한다.**

### STE

- Ge 조성: `t = 0.32` → 유의하지 않음
- FR: `t = 8.41` → 지배적
- Ge×FR: `t = -0.82` → 유의하지 않음

**투입 응력의 전달 효율은 FR이 지배한다.**

### 실용 설계창

Ge=50%에서 FR=15/22 nm를 추가 검증한 결과:

- FR 15→20: 이득/대가 비율 2.91
- FR 20→22: 0.38
- FR=20 nm를 경계로 약 7.6배 급락
- gmSat도 FR=20 nm에서 최대 후 감소
- FR=22 nm에서 Ioff가 1e-9을 넘어감

따라서 최종 실용 설계창은 **FR 약 15~20 nm**다.

### 깊은 리세스의 비용

Strain_Impact를 꺼도 FR 증가에 따른 SSlin·DIBL·Ioff 열화가 크게 남았다. 따라서 깊은 리세스의 전기적 열화는 **응력 자체보다 형상 변화가 1차 원인**이며, 응력/밴드구조 변화가 누설을 추가 증폭한다.

### Fin-width 민감도

fin 폭을 15→7.5 nm로 줄이면 얕은 FR에서는 SSlin·DIBL·STE가 개선되지만, 깊은 FR에서는 관계가 역전된다. **소자가 미세화될수록 FR 상한은 더 엄격해진다.**

---

## 저장소 구조

| 경로 | 역할 |
|---|---|
| `baseline/params.yaml` | 최종 baseline·DoE·STE 정의의 단일 기준 |
| `baseline/verification_*.csv/xlsx` | 사전/추가 검증 원본 |
| `runs/*.csv` | 본 DoE의 팀원별 Sentaurus/SVisual export |
| `analysis/config.yaml` | 지표 정의와 SWB 컬럼 매핑 |
| `analysis/build.py` | SWB 결과 병합, 단위 변환, STE·DIBL 계산, `grid.csv/status.json` 생성 |
| `analysis/contour.py` | 2차원 지도와 2FI 회귀 분석 |
| `analysis/grid.csv` | 병합된 격자 데이터 — 자동 생성물 |
| `analysis/status.json` | 대시보드용 상태 — 자동 생성물 |
| `analysis/figures/` | 분석 그림 — 자동 생성물 |
| `docs/technical-notes.md` | 최종 기술 결정·검증 기록 |
| `docs/ROLES.md` | 실제 분담과 완료 상태 |

---

## 데이터 처리 원칙

1. **원본 결과는 `runs/` 또는 `baseline/verification_*`에 보존한다.**
2. **STE는 `build.py`가 공통 공식으로 계산한다.**
3. **정전제어는 SSlin, 누설은 Ioff, 숏채널 효과는 DIBL로 분리한다.**
4. `analysis/grid.csv`, `status.json`, `figures/`는 직접 손으로 맞추지 않고 파이프라인으로 재생성한다.
5. 추가 검증점 FR=15/22 nm는 본 5×5 회귀 격자에 섞지 않고 별도 verification 데이터로 유지한다.

---

## 분석 실행

필요 패키지 설치 후:

`python analysis/build.py`

`python analysis/contour.py --metric ste`

또는 전체 그림을 생성하려면:

`python analysis/contour.py --all-figures`

GitHub Actions가 `analysis/**` 또는 `baseline/params.yaml` 변경을 감지하면 대시보드 산출물을 다시 생성하도록 구성되어 있다.

---

## 결과를 읽을 때 주의할 점

- 결과 범위는 **Ge 30~70%, FR 0~35 nm**다. 범위 밖으로 수치를 외삽하지 않는다.
- Ge 효과는 70%에서도 포화하지 않았으므로 `Ge=70%가 최적`이라는 결론은 아니다.
- STE 절대값은 본 연구에서 사용한 `M=180 GPa`에 의존한다.
- baseline fin 폭 15 nm의 정전제어 절대 수준은 구조 치수 영향을 받는다. 7.5 nm 민감도 검증으로 상대적인 경향을 확인했다.
- FinFET 결과를 GAA 수치로 직접 외삽하지 않는다.

---

## 저장소 역할 구분

### `Share`

**팀 결과 공유·재현·분석 실행용**이다. 현재 유효한 baseline과 최종 데이터가 무엇인지 빠르게 확인할 수 있어야 한다.

### `competition`

**프로젝트의 의사결정·검증·전환 기록용**이다. 주제가 어떻게 바뀌었고 어떤 가설을 왜 폐기했는지는 이쪽에서 확인한다.

이 두 역할을 분리해, `Share`의 과거 TODO나 폐기된 방법론이 현재 실행 기준으로 오해되지 않도록 유지한다.
