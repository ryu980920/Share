# FinFET 리세스 깊이 × Ge 조성 프로젝트 — 기술 확인 기록

**주제 확정 이후(FinFET + Embedded SiGe S/D 응력공학, 리세스 깊이 × Ge 조성 2D 트레이드오프 지도)부터 오늘까지 검증한 내용 정리.**
이 문서는 다른 대화방(기술 검증)에서 작성되어 이 레포로 그대로 옮겨진 것. 아래 내용은 전부 실제 검색/검증을 거친 것이며, 확인 안 된 부분은 별도로 "미확인" 표시함.

---

## 0. 확정된 주제

FinFET + Embedded SiGe Source/Drain 응력공학. Selective epitaxial growth로 S/D를 SiGe로 대체(리세스 파고 in-situ 도핑 에피 성장), PMOS 압축 응력 유도. 파라미터 스윕 축은 **Ge 조성(%) × 리세스 깊이**. 결과물은 단일 최적점이 아니라 **2D 트레이드오프 경계 지도**(어느 조합부터 전위결함으로 응력 이득이 무효화되는지).

"~ 최적화"가 아니라 "기존 구조 + 새 공정 → 개선" 흐름을 따라야 한다는 팀 요구사항 반영.

---

## 1. 세 가지 검증 질문에 대한 답

### 1-1. FinFET에 SiGe 응력공학을 적용한 논문이 있는가?

있음. 90년대~2000년대 초 기술은 대부분 평면(planar) 구조 얘기이고, FinFET에 직접 적용한 논문은 2012년부터:

- **Choi, Moroz, Smith, Penzin (Synopsys), "14 nm FinFET Stress Engineering with Epitaxial SiGe Source/Drain," ISTDM 2012** — Synopsys 소속, TCAD 모델링 논문. 우리 방법론과 가장 유사.
- imec, "Strained germanium finFETs," IEDM 2013
- "Investigating the performance of SiGe embedded dual source p-FinFET architecture," *Superlattices and Microstructures*, 2016
- Joshi et al., "Source/drain eSiGe engineering for FinFET technology," *Semiconductor Science and Technology*, 2017
- **Gendron-Hansen, Korablev, Chakarov, Egley, Cho, Benistant (Synopsys), "TCAD analysis of FinFET stress engineering for CMOS technology scaling," SISPAD 2015** (pp. 417-420, DOI: 10.1109/SISPAD.2015.7292349) — eSiGe 캐비티 설계와 FinFET 세대별 응력의 관계를 다룸. **우리 프로젝트와 가장 근접한 선행연구 — 아래 2-3절 참고.**

주의: 예전에 AI 검색 요약이 "2005~2006년 첫 적용"이라고 답한 적 있는데, 이건 Intel 90nm **평면** strained-silicon 연구와 FinFET 특화 연구를 혼동한 잘못된 합성이었음 (검증 후 정정).

### 1-2. 자체 감사 — 교차검증 필요한 항목 (우선순위순, BCAT 코너 사건 재발 방지 목적)

1. **[최고 위험, 미해결]** FinFET_22nm 예제 = Intel 22nm Tri-Gate, FinFET_14nm 예제 = PTM 14nm라는 대응은 **파일명 기반 추측**일 뿐, 예제 안의 실제 문서(치수 스펙)를 열어서 대조한 적 없음. BCAT 코너 사건과 동일한 패턴(직관/이름만 보고 판단). **팀이 학교 라이선스로 파일 직접 열어서 확인 필요.**
2. **[미해결]** FinFET_22nm/14nm 예제가 실제 SProcess 공정 흐름인지, 공정 에뮬레이션(구조만 근사 생성)인지 확인 안 됨.
3. **[부분 확인]** "Ge 40% 이상에서 결함밀도 급증" — 원래는 AI 검색 요약 인용이었으나, 재검증 결과 정확한 물리는 "Ge 40%에서 임계두께(People-Bean) ≈ 50nm"라는 **두께와 결합된 값**임. "40%가 절대 문턱값"이라는 표현은 부정확 — 정정 완료 (아래 3절 공식 참고).
4. **[문제 확인됨, 재분류 필요]** "Ge 30%에서 구동전류 187% 향상" — 출처는 "Design and optimization of stress/strain in GAA nanosheet FETs" (Physica Scripta, 2023)인데, 이건 **GAA 나노시트(NSFET) 논문**이지 FinFET이 아님. 3-stack 나노시트 적층 구조에서 나온 수치라 FinFET 구조에 그대로 적용할 근거 없음. **문서에서 삭제하거나 "나노시트 참고 사례"로 명확히 재분류해야 함.**
5. **[미확인]** Sentaurus SProcess/SDevice의 Stress 섹션에 전위결함(소성 완화) 예측 모델이 기본 탑재돼 있는지 검색으로 확인 안 됨 (공식 매뉴얼이 검색엔진에 안 걸림). 학교 라이선스 매뉴얼 직접 확인 필요. 현재는 "탑재 안 돼 있다"고 가정하고 방법론을 설계함 (2절 참고).
6. Intel 22nm SiGe S/D 관련 — [PMC 논문](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5313396/)으로 Ge 35~40%, 붕소 1-3×10²⁰cm⁻³ 사용 확인됨. 단 이 논문은 **bulk 22nm PMOS** 논문이라 Tri-Gate(FinFET)와 완전히 동일 공정인지는 별도 확인 필요.

### 1-3. FinFET은 현재도 쓰이는가? (2026년 8월 기준)

쓰임. 단, "다들 GAA로 전환했다"는 아니고 **GAA와 병행 생산 중이며 물량 기준으론 FinFET이 아직 더 큼.**

- TSMC: N2(GAA)가 2025년 4분기 양산 시작, 2026년 1월 고볼륨양산(HVM) 전환. 근데 N3(FinFET) 캐파를 2026~2027년까지 월 18만~25만 장으로 오히려 늘리는 중 — **2026년 현재 최대 물량 노드는 여전히 N3(FinFET)**. N3 기반 제품: Apple M4, A18/A19, AMD MI350·Zen 5.
- 삼성: SF3(2022)부터 GAA 전환 완료.
- 인텔: 18A(2024~2025)부터 GAA(RibbonFET) 전환 완료.

---

## 2. 방법론 이론 검증

### 2-1. "등고선이 결함으로 인한 relaxation을 자동으로 보여줄 것"이라는 가정은 틀릴 수 있음

Sentaurus의 응력 계산은 선형탄성(linear elasticity) 기반이라 기본적으로 **완전 정합(pseudomorphic) 가정** 하에 계산됨. 전위결함 핵생성 자체를 예측하는 소성 완화 모델이 기본 탑재됐는지는 미확인(1-2절 항목 5). 즉 Sentaurus 시뮬레이션 결과만 보면 Ge%·리세스 깊이를 올릴수록 계속 좋아지는 것처럼 나올 수 있음 — 실제로는 결함 때문에 무효화되는 구간이 있어도 시뮬레이터가 그걸 자동으로 반영 안 할 가능성이 큼.

### 2-2. 확정한 하이브리드 방법론

실제 published TCAD 논문들(예: "TCAD Study of the Raised SiGe Source/Drain in 40nm PMOS" — TCAD 결과를 실험 데이터와 별도로 대조 검증; Gendron-Hansen 2015)도 이 방식을 씀: **Sentaurus로 (Ge%, 리세스 깊이) 전 구간 응력/이동도를 탄성 가정 하에 계산 → 그 결과 위에 문헌 기반 임계두께 경계선을 별도로 겹쳐서 유효/무효 영역을 나눈다.**

- 등고선(색 채워진 면) = Sentaurus 시뮬레이션 결과, 결함 미반영, 계속 좋아지는 이상적 곡면
- 경계선 = Sentaurus 밖에서 별도 계산(People-Bean/Luryi-Suhir), "여기부터 결함 발생"을 표시
- 최종 결론 = 경계선 안쪽에서 최대인 지점을 찾는 것 (등고선 전체 최댓값이 아님)

**대안(만약 하이브리드가 여의치 않을 경우):**
- 대안 A(권장, 베이스라인): DoE 스윕 범위 자체를 문헌 임계두께 안쪽으로 제한. 등고선은 "안전 영역 내 성능 지도"가 되고 경계선은 순수 설계 제약으로 취급.
- 대안 B(확장 목표): SDevice에 결함 밀도를 SRH(Shockley-Read-Hall) 트랩으로 수동 주입해서 임계두께 초과 시 Ion 감소·누설 증가가 전기 특성에 실제로 나타나게 함. 구현 난이도 높지만 더 설득력 있음.

### 2-3. 독창성 재확인 — Gendron-Hansen 2015(SISPAD) 논문과의 차별점

이 논문은 우리 프로젝트와 주제가 가장 가까운 선행연구. 냉정하게 봤을 때 "TCAD+FinFET+eSiGe" 조합 자체는 이미 2012~2015년에 다뤄졌으므로 이걸 독창성 근거로 쓰면 안 됨.

- **Gendron-Hansen 2015가 하는 것**: 캐비티(리세스) 형상을 여러 FinFET 세대(기술 노드 스케일링)에 걸쳐 어떻게 설계해야 fin 전체 높이에 응력이 고르게 전달되는지. 축 = 기술 노드 세대. 목표 = 응력 최대화.
- **우리가 하는 것**: 축 = Ge% × 리세스 깊이. 목표 = 이 조합이 언제 결함으로 무효화되는지 경계선을 찾는 것 (응력 최대화가 아니라 신뢰성 경계 매핑).
- **미확인 사항**: 이 논문과 2012년 Choi 등 논문 둘 다 IEEE 페이월이라 원문 전체를 못 읽음 — 초록/2차 요약만 확인. 팀이 학교 IEEE Xplore 계정으로 원문 직접 확인 필요 (독창성 주장의 최종 확인 단계).

### 2-4. Ge 조성과 리세스 깊이가 각각 응력에 미치는 영향 (물리적 메커니즘)

- **Ge 조성**: Vegard's law에 따라 Ge%가 높을수록 SiGe의 자연 격자 상수가 커짐. Si 기판 위에 정합 성장하면서 억지로 눌린 상태(압축 변형)가 됨 → 이 변형이 옆의 채널 실리콘까지 기계적으로 전달돼 정공 이동도 향상. Ge%가 높을수록 변형 에너지가 커지지만, 그만큼 버틸 수 있는 두께(임계두께)는 줄어듦(People-Bean, 3-1절).
- **리세스 깊이**: 격자 차이 크기와 무관한 순수 기하학적 요인. 깊을수록 SiGe 부피·채널 근접성이 늘어 응력 전달이 세지지만, 무한정 좋아지진 않음 — "적당한 SiGe 오버필이 최대 응력"이라는 결과가 40nm PMOS TCAD 논문에서 확인됨(비단조적, 자체 기하학적 최적점 존재).
- **"Orthogonal(독립)"과 "트레이드오프"는 모순 아님**: 문헌에서 "Ge%와 리세스 깊이가 orthogonal한 설계 손잡이"라는 표현은 *성능 설계 관점*(각자 다른 성능 지표를 담당, 독립적으로 조작 가능)에서 하는 말이고, *신뢰성/결함 발생 관점*에서는 두 값이 함께 결정에 저장되는 변형 에너지 총량을 정하므로 트레이드오프가 맞음. (자동차 속도 페달과 핸들 각도는 독립 조작이지만 전복 한계선은 둘의 조합으로 정해지는 것과 같은 논리.)

### 2-5. FinFET 구속 효과 — 평면 기준 공식보다 실제로 더 넓은 안전 영역

FinFET은 fin이라는 좁은 구조라 SiGe가 옆면까지 둘러싸여 자람(공간적 구속). [US9245980 특허](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9245980)에서 이런 구속 구조가 평면(blanket) 기준 임계두께보다 더 두껍게/높은 Ge%로도 결함 없이 버틸 수 있음을 확인. 이 효과를 반영하는 공식이 Luryi-Suhir (3-2절).

---

## 3. 사용할 공식 (등고선에 경계선 그릴 때 둘 다 적용)

### 3-1. People-Bean (1985) — 평면(blanket) 기준 임계두께, 보수적 하한

**R. People, J. C. Bean, "Calculation of critical layer thickness versus lattice mismatch for GeₓSi₁₋ₓ/Si strained-layer heterostructures," Applied Physics Letters, 47(3), 322–324 (1985).** (1986년 Erratum 있음, 같이 인용)

에너지 균형(변형 에너지 vs 결함 생성 에너지) 기반 모델. 실무 근사식:

**Tc ≈ 1.23 × x⁻³·⁰⁸ (nm, x = Ge 몰분율)**

예: x=0.3(Ge 30%) → Tc ≈ 52nm. (다른 문헌의 "Ge 40%→Tc≈50nm"와 대략 정합)

#### 원 논문 그래프 직접 대조 — 못 함 (페이월)

People & Bean(1985) 원 논문은 페이월에 막혀 있고, 논문의 Fig.(임계두께 vs Ge 조성 그래프)에서 값을 읽어 재구성한 2차 자료도 검색으로는 찾지 못함. **원 논문을 실제로 본 적 없이 숫자를 지어내는 것을 피하기 위해, 이 그래프 대조 자체는 "팀이 원 논문 PDF를 구해서 직접 읽어야 하는 미확인 항목"으로 남겨둔다** (4절 5번).

#### 근사식 자체의 신뢰도 — 대신 찾은 더 중요한 사실

**A. Hartmann et al., "Critical thickness for plastic relaxation of SiGe on Si(001) revisited," Journal of Applied Physics, 110, 083529 (2011).** Ge 12/22/32/42/52%에서 실제로 SiGe를 성장시키고 XRD로 실측 임계두께(결함 발생 시점)를 측정한 논문.

**Ge 22% 이상 구간에서는 실측 임계두께가 People-Bean 예측치보다 약 2배 더 높게 나옴.** 즉 근사식(Tc≈1.23x⁻³·⁰⁸)의 오차는 "몇 % 수준"이 아니라, **실제보다 최대 ~2배 더 보수적으로(더 얇게) 예측하는 경향**이 2011년에 이미 실측으로 검증돼 있음.

> **종합 판정**: Ge 22% 이상에서는 People-Bean 예측치가 실측 대비 최대 ~2배 과소평가한다(즉 실제로는 더 두껍게 키워도 안전할 수 있다) — Hartmann et al., JAP 110, 083529 (2011) 참고. **이 근사식은 「보수적 하한」으로만 쓰고, 정밀치로 신뢰하지 않는다.** 등고선 경계선 해석에도 이 판정을 그대로 반영한다(아래 "적용 계획" 참고).

### 3-2. Luryi-Suhir (1986) — fin 구속 보정, 실제 안전 영역

**S. Luryi, E. Suhir, "New approach to the high quality epitaxial growth of lattice-mismatched materials," Applied Physics Letters, 49(3), 140–142 (1986).**

좁은 메사(mesa/fin) 구조에서는 변형이 전위결함이 아니라 옆면(자유 표면)을 통해 탄성적으로 완화될 수 있음. **경험식: 메사(fin) 폭 W가 People-Bean 임계두께 Tc의 약 15배 이하(W < 15×Tc)면, 결함 없이 탄성 완화만으로 버틸 수 있음.**

### 적용 계획

등고선 위에 **두 개의 경계선**을 겹쳐 그림:
1. People-Bean 기준선 (보수적, 평면 가정 — 게다가 3-1절 Hartmann(2011) 결과에 따르면 Ge 22% 이상에서는 이마저도 실측보다 최대 ~2배 더 보수적)
2. Luryi-Suhir 보정선 (fin 구속 반영, 실무 경험식: fin 폭 W < 15×Tc(People-Bean 평면값)이면 결함 없이 버틸 수 있음. fin 폭은 baseline 예제의 문서 스펙에서 확정)

두 선 사이의 영역은 "평면 기준으론 위험해 보이지만 실제 fin 구조에서는 안전한 영역"이고, 여기에 Hartmann(2011) 결과를 더하면 **"이중으로 보수적으로 잡아도 안전한 영역"**이라는 더 강한 주장이 된다 — People-Bean 자체가 이미 실측보다 보수적인데, 거기에 Luryi-Suhir로 fin 구속까지 반영하면 실제 안전 마진은 두 선이 시사하는 것보다 더 크다는 뜻. 발표에서는 이걸 "우리가 그리는 경계선은 안전 방향으로 이중 보정된 것"이라고 명시적으로 프레이밍할 것 — 이게 우리 프로젝트만의 정량적 주장으로 활용 가능 (2-3절 독창성 근거와 연결).

---

## 4. 남은 확인 필요 항목 (우선순위순)

1. FinFET_22nm/14nm 예제의 실제 문서 스펙을 열어서 Intel 22nm / PTM 14nm 수치와 대조 확인 (최우선)
2. FinFET_22nm/14nm 예제가 SProcess 실제 공정 흐름인지 공정 에뮬레이션인지 확인
3. Sentaurus Stress 섹션에 소성 완화(전위결함) 모델이 있는지 학교 라이선스 매뉴얼에서 확인
4. Gendron-Hansen(2015)·Choi 등(2012) 논문 원문을 IEEE Xplore에서 직접 열어서 독창성 차별점 최종 확인
5. People-Bean 근사식(Tc≈1.23x⁻³·⁰⁸)을 **원 논문 그래프와 직접** 대조해 오차 확인 — 페이월 때문에 검색으로는 못 함, 팀이 원 논문 PDF(학교 도서관/저널 구독) 구해서 직접 대조 필요. (대신 Hartmann et al. 2011 실측 논문으로 "Ge≥22%에서 최대 ~2배 과소평가 경향"까지는 이미 확인됨 — 3-1절)
6. Intel 22nm SiGe S/D가 bulk와 Tri-Gate에서 동일 공정인지 확인
7. **(레포 편입 시 추가)** Ge%/리세스 깊이 스윕의 구체적 격자 값(레벨 개수·범위) — 위 1번이 끝나야 확정 가능
8. **(레포 편입 시 추가)** Luryi-Suhir 보정에 쓸 fin 폭 W의 실제 값 — 위 1번과 연동

## 5. 다음 단계

- 팀이 baseline 예제 파일(FinFET_14nm/22nm)을 직접 열어서 위 1~2번 확인
- 확인 결과를 바탕으로 `baseline/params.yaml` 의 Ge%/리세스 깊이 스윕 값 확정
- Sentaurus로 (Ge%, 리세스 깊이) 그리드 시뮬레이션 실행, 데이터 확보
- 확보된 데이터에 People-Bean + Luryi-Suhir 경계선 오버레이해서 최종 등고선 완성
