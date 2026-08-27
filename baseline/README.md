# baseline/ — 최종 공통 조건 및 검증 데이터

이 폴더는 팀원이 동일한 구조·물리조건·지표 정의를 사용하도록 맞추는 **공통 기준 폴더**다.

경진대회 본 프로젝트는 완료됐으며, 과거의 `provisional`, `Phase 0 미완료`, `스윕 시작 전` 상태는 현재 기준이 아니다. 변경 과정은 Git 이력과 `competition` 저장소에서 확인한다.

---

## 파일 역할

| 파일 | 역할 |
|---|---|
| `params.yaml` | 최종 baseline, DoE, STE 정의의 단일 수치 기준 |
| `verification_strain_impact_G50F0.csv` | Strain_Impact 1/0 결합 검증 |
| `verification_strain_impact_G50_FRsweep.csv` | FR 축에서 응력 전기효과 ON/OFF 비교 |
| `verification_FR_refine_G50.csv` | Ge=50%, FR=15/22 nm 설계창 경계 보강 |
| `verification_finwidth_half_G60_G70.xlsx` | Fin width 15→7.5 nm 민감도 검증 |

Synopsys Applications Library 예제를 기반으로 한 실제 SProcess/SDevice/SVisual 스크립트 원문은 라이선스 재배포 위험을 피하기 위해 이 public 저장소에 포함하지 않는다.

---

## 최종 baseline

| 항목 | 값 |
|---|---:|
| Gate length | 25 nm |
| Fin height | 35 nm |
| Fin width (top / bottom) | 15 nm |
| Esd | 7.5 nm |
| S/D concentration | 2 × 10²⁰ cm⁻³ Boron |
| Channel concentration | 2 × 10¹⁸ cm⁻³ |
| Vdd | 0.8 V |
| Gate workfunction | 4.623 eV |
| Channel / substrate orientation | ⟨110⟩ / (100) |

정확한 기계 판독 값은 `params.yaml`을 사용한다.

---

## 본 DoE

- Ge: 30 / 40 / 50 / 60 / 70 %
- FR: 0 / 10 / 20 / 30 / 35 nm
- 총 25점
- 상태: **25/25 완료**

추가 FR=15/22 nm 점은 25점 회귀 격자에 포함하지 않고 `verification_FR_refine_G50.csv`로 별도 유지한다.

---

## 최종 STE 정의

`STE = |stress_GPa| / (180 × 0.042 × x)`

- `x = Ge_percent / 100`
- `stress_GPa = SlFin_MPa / 1000`
- `SlFin`: ChFin 영역의 채널 길이 방향 체적평균 응력

### 체적평균 채택 근거

본 스윕에서 체적평균 `SlFin`과 계면 인접 단일점 `SlFin_pt`를 함께 수집했다.

최종 비교 결과:

- `SlFin`은 다섯 Ge 조건 모두 `gmSat`과 +0.95 이상의 상관
- 계면 단일점 방식은 평균 약 -0.207의 상관

따라서 STE 분자는 **체적평균 `SlFin`으로 확정**했다.

`analysis/build.py`가 이 공식을 자동 적용하므로 팀원이 별도로 계산한 STE를 병합하지 않는다.

---

## 검증 완료 항목

### 응력–전기 결합

G50_F0에서 `Strain_Impact=1/0` 비교:

- IdSat_norm 약 +227% 차이
- 결론: 응력–전기 결합 정상 작동

### FR 구조 반영

FR=15 nm 실제 실행 후 좌표축 단면에서 의도한 추가 식각 확인.

### 재현성

동일 조건 격자점 4쌍 독립 재실행 결과 편차 0.0%.

### FR 설계창 경계

Ge=50%에서 FR=15/22 nm 추가 검증:

- FR 15→20 이득/대가 비율: 2.91
- FR 20→22: 0.38
- 약 7.6배 감소
- 실용 설계창: **FR 약 15~20 nm**

### 깊은 FR의 열화 원인

Strain_Impact OFF에서도 SSlin·DIBL·Ioff 열화가 크게 남아, **형상 변화가 1차 원인**임을 확인했다.

### Fin width 민감도

15→7.5 nm 검증에서 얕은 FR은 정전제어와 STE가 개선됐지만 깊은 FR에서는 전기적 특성이 크게 악화됐다.

→ **소자가 미세화될수록 FR 상한은 더 엄격해진다.**

---

## 현재 운영 원칙

1. 최종 공통 조건은 `params.yaml`에서만 관리한다.
2. 본 DoE 원본 결과는 `runs/`에 보존한다.
3. 추가 검증은 `baseline/verification_*`에 분리한다.
4. `analysis/grid.csv`, `status.json`, `figures/`는 직접 손으로 수정하지 않고 분석 파이프라인으로 재생성한다.
5. 과거의 TODO·초기 계획을 확인하려면 Git 이력 또는 `competition` 저장소를 사용한다.

---

## 최종 보고서와의 관계

- 최종 제출 보고서: `ryu980920/competition/docs/reports/경진대회_보고서.docx`
- 최신 프로젝트 요약: `ryu980920/competition/docs/reports/project-summary.md`

최종 수치나 해석이 충돌할 경우 **최종 제출 보고서를 우선**한다.
