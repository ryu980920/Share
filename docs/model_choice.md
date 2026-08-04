# 방법론 선택 근거 — Sentaurus 소성완화 모델 유무

> [tasks.js #7 — 유용성] 담당. Sentaurus Stress 섹션에 전위결함(소성 완화) 예측 모델이
> 있는지 여부가 이 프로젝트 방법론(하이브리드 vs 단일 시뮬레이션) 전체를 결정한다.
> 발표 Q&A "결함을 왜 시뮬레이터가 아니라 별도 공식으로 처리하나요?" 의 답이 여기 있어야 한다.

---

## 1. Sentaurus Stress 섹션 소성완화(전위결함 핵생성) 모델 탑재 여부

**결론:** ⚠ TODO — 아래 중 하나를 선택하고 근거를 채울 것

- [ ] **있음** — 모델명, 버전, 활성화 방법을 아래에 기록
- [ ] **없음** — 이 경우 하이브리드 방법론(등고선 + People-Bean/Luryi-Suhir 경계선 별도 오버레이)이
      유일한 선택지임을 아래에 문서화한다. `analysis/contour.py` 는 이 가정(없음)을 전제로 이미 짜여 있다 —
      "있음"으로 결론 나면 `contour.py`/`README.md`/`docs/technical-notes.md` 를 다시 검토해야 한다.
- [ ] **확인 불가** — 설치된 라이선스/버전에서 판단이 안 되는 경우. 사유와 확인 시도한 항목을 기록

**근거 (Device User Guide 등 문서 인용 또는 화면 캡처 위치):**

TODO

**결론이 "없음"일 경우 — 하이브리드 방법론이 유일한 선택지인 이유:**

TODO (예: Sentaurus 는 응력장을 연속체 역학으로 풀 뿐 임계두께 이후의 misfit dislocation
핵생성·전파는 별도 모델이 없어 시뮬레이션 결과가 임계두께를 넘어서도 비현실적으로 계속
응력이 증가하는 것으로 나온다 — 그래서 문헌 기반 경계선을 별도로 겹쳐 판정한다, 등)

---

## 2. People-Bean(1985) 근사식 오차 검증

`baseline/params.yaml` 의 `critical_thickness.people_bean_1985.formula`:
`Tc_nm = 1.23 * x^(-3.08)` (x = Ge 몰분율, 0~1) — R. People, J. C. Bean,
Appl. Phys. Lett. 47(3), 322–324 (1985); 1986 Erratum.

원 논문의 Fig.(임계두께 vs Ge 조성 그래프)와 위 근사식을 직접 대조한다.

**오차 비교 표 (TODO — 원 논문 그래프에서 최소 3~4개 지점을 읽어서 채울 것):**

| Ge 몰분율 x | 원 논문 Tc [nm] | 근사식 Tc = 1.23·x⁻³·⁰⁸ [nm] | 오차 [%] |
|---|---|---|---|
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

**종합 오차 범위:** TODO (예: "±_%, x=0.2~0.4 구간에서는 ±_% 이내")

> 오차가 크게 나오는 구간이 있으면 `contour.py` 의 `people_bean_tc_nm()` 주석에도
> 그 구간에서는 근사식 신뢰도가 낮다는 점을 남길 것.

---

## 3. 결론 요약 (발표용 한 문장)

TODO — 예: "Sentaurus Stress 섹션에는 소성완화 모델이 없음을 확인 (Device User Guide vXXXX,
X장 참고). 따라서 이 프로젝트는 People-Bean/Luryi-Suhir 문헌 경계선을 등고선에 별도로
오버레이하는 하이브리드 방법론을 택했다. People-Bean 근사식은 Ge 몰분율 0.2~0.4 구간에서
원 논문 대비 오차 ±_% 이내로 확인됨."

---

작성자: 유용성 · 작성일: TODO
