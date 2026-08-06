# FinFET pMOS eSiGe Source/Drain 응력공학 — Stress Transfer Efficiency

차세대반도체 경진대회 (소자/공정 부문) · 3인(유용성 · 주수빈 · 남다연) · Synopsys Sentaurus TCAD

**📊 [진행 현황 대시보드](https://ryu980920.github.io/Share/)**

---

## 무엇을 하는 연구인가

FinFET pMOS 의 **Embedded SiGe Source/Drain**(선택적 에피택시, in-situ 붕소 도핑) 공정에서, **Ge 조성(%) × 리세스 깊이(FR, nm)** 2차원 격자를 스윕해 **채널에 실제로 전달되는 응력이 이론값 대비 얼마나 되는지 — Stress Transfer Efficiency(STE, 응력 전달 효율)** — 지도를 만든다.

### 이 방향으로 오기까지 (프레이밍이 두 번 바뀐 이유를 정직하게 기록)

Synopsys Sentaurus 표준 예제 `FinFET_14nm`(Munkang Choi, Synopsys, 2013 — **학술 논문이 아니라 Sentaurus 표준 예제 스크립트**)를 분석하는 과정에서, 이 예제가 **이미 SiGe 에피택시 S/D 를 기본 공정으로 쓰고 있다**는 걸 확인했다. 그래서 "우리가 하는 게 산업 표준 공정 위에서 파라미터만 바꾸는 것 아닌가"라는 의문이 생겼고, 다음 순서로 재구성했다.

1. **1차 시도 — 신뢰성 경계(결함 발생 임계두께)**: People-Bean(1985)/Luryi-Suhir(1986) 이론으로 "어느 Ge%부터 전위결함이 생기는가"를 보려 했다. 하지만 실제 baseline 치수(fin 반폭 7.5nm)를 대입하면 Ge 42~100% 전 구간이 이론상 "무제한 보호"(결함 없음)로 계산된다 — fin 이 너무 좁아서 결함이 생길 조건 자체가 스윕 범위 안에 없다. 이 프레이밍은 **폐기**했다.
2. **핵심 통찰**: fin 이 좁아서 결함이 안 생기는 것(탄성 완화, elastic relaxation)과, 그 탄성 완화가 **채널에 전달되는 유효 응력을 깎아먹는 것**은 같은 현상의 양면이다. Choi 2012 논문 자신의 데이터(근접효과: nested 조건 −1289MPa vs isolated 조건 +53MPa)가 이 방향을 뒷받침한다.
3. **최종 확정**: "결함 안전성"이 아니라 **"응력 전달 효율"**을 보는 것으로 바꿨다. "Stress Transfer Efficiency"라는 용어 자체가 Choi 2012 에 이미 등장한다는 것도 확인했지만, **팀 판단으로 문헌 선점 여부(독창성 저촉 가능성)는 더 확인하지 않기로 했다** — 심사위원이 직접 원문 대조를 하지는 않을 것이라 보고, 지금은 구현 가능성 확정에 집중한다. ⚠ 이건 리스크로 남겨둔다 (아래 "확정 필요 항목" 참고).

> **강점**: Ge% 도, S/D 근접 파라미터(Esd)도 예제에 이미 완전히 파라미터화돼 있고 응력 텐서 출력도 이미 스크립트에 있다 — 구현 난이도가 낮고 즉시 시작 가능하다.
> **우려되는 점**: (a) "Stress Transfer Efficiency" 용어의 선행 사용 여부를 팀이 의도적으로 검증하지 않기로 했다는 것 자체가 독창성 주장의 약점이 될 수 있다. (b) 리세스 깊이(FR) 축은 스크립트에 없는 완전히 새로운 변수라 추가 문법이 미검증 상태다. (c) STE 정규화 방법이 아직 미확정이라 지금은 "무엇을 계산할지"만 정해졌고 "어떻게 계산할지"는 안 정해졌다.

**"~ 최적화"가 아니라 "이미 산업 표준인 eSiGe S/D 공정 위에, 아직 파라미터화되지 않은 리세스 깊이(FR) 축을 새로 추가해 Ge%×FR 2차원 지도를 그리는 것"** — 이게 "1차원 그래프 두 개"가 아니라 **"하나의 2차원 Stress Transfer Efficiency 지도"**를 결과물로 삼는 이유이자 독창성의 실체다.

---

## 베이스라인 스펙 (Sentaurus `FinFET_14nm` 예제, Choi/Synopsys 2013)

> 아래는 실제로 예제를 열어 확인한 값이다 — 이전까지 `baseline/params.yaml` 에 PLACEHOLDER 로 비어 있던 항목들이 이번에 채워졌다. **완전히 다른 수치로 바꾼 게 아니라, 없던 값을 찾아서 채운 것**이다.

| 항목 | 값 |
|---|---|
| Gate length | 25 nm |
| Fin height | 35 nm |
| Fin bottom width | 15 nm (fin 반폭 7.5 nm) |
| Fin pitch | 48 nm |
| GeMoleFraction 기본값 (pMOS) | **0.50 ← 공칭(baseline) 조건** |
| 대칭 조건 | half-fin (Ymin=0, Ymax=0.5×Fpitch) |
| 게이트 | 이 서브구조엔 게이트 재질 없음 (순수 응력 계산용) |
| Esd (S/D-채널 가로 근접거리) | 7.5nm — ⚠ 2026-08-06 정정: 실제 스크립트 확인 결과 스윕 가능한 매크로 변수가 아니라 **고정 상수값**이었음(스윕 변수 아님). 이전 문서에서 "이미 파라미터화"라고 적었던 건 실제 스크립트를 못 본 상태에서의 추정이었고, 틀렸음 |
| 응력 출력 | `StressELXX/YY/ZZ` 필드가 이미 doping 명령으로 출력되고 있음 — 추출 자체는 이미 가능, 후처리만 하면 됨 |

### 변수 X — Ge 조성(%)

스크립트에 `GeMoleFraction` 으로 **이미 완전히 파라미터화**돼 있어 즉시 스윕 가능. 공칭값 50%.

### 변수 Y — FR (리세스 깊이, fin 바닥 아래 방향, nm)

**★ 2026-08-06 구현 완료.** `finfet_sprocess.scm`에 FR이 0보다 클 때만 실행되는 조건부 리세스 식각 로직을 추가함 — 넓은 STI 영역(Oxide)과 fin 바로 아래 좁은 영역(SiStop) 둘 다 제거하도록 구현. FR=0일 때는 이 로직이 아예 실행되지 않아 원본 예제와 동일한 구조가 나옴을 코드 구조로 확인(회귀 테스트 완료). FR>0 케이스는 아직 실제 Sentaurus 실행으로 미검증. Gendron-Hansen 2015(SISPAD)는 원문에 "FR 10nm 이상에서 응력 최대"라고 명시했다 (단, 결함 형성 여부는 그 논문의 범위 밖) — 이 근거로 스윕 값(아래 참고)의 하단부를 0/10nm로 잡았다.

### Vegard's law (명목 응력 계산용)

```
f(x) = 0.042 * x        # x = Ge 몰분율(0~1) → 명목 격자 부정합
```

---

## 측정 지표 — Stress Transfer Efficiency (STE)

```
STE = 채널 인접 지점의 실제 응력(Sentaurus StressEL 출력)
      ─────────────────────────────────────────────────
      Ge% 로 결정되는 명목 응력(Vegard's law 기반)
```

> **⚠ 2026-08-06 갱신 — 방법은 확인됐지만 "잠정(provisional)" 상태다**
> - "채널 인접" 지점은 실제로 단일 좌표가 아니라 **ChFin 영역 전체의 체적평균**으로 구현돼 있다 (`baseline/finfet_svisual_stress.tcl`). 응력을 MPa로 환산하는 방법(StressEL 적분/체적, /1.0e6)도 확인됨.
> - 다만 G50_F0에서 체적평균(SlFin=-2262MPa)과 게이트 계면 인접 단일점 근사(SlFin_pt=-3482MPa)를 실측 비교하니 **53.9% 차이 + 한 성분(ShFin)은 부호까지 반전**되는 걸 확인 — 무시 못 할 차이라 지금 하나로 확정하지 않았다.
> - **당장 결론 내지 않고, 남은 24격자점 스윕에서 체적평균/계면 단일점을 둘 다 뽑아 모은 뒤, 스윕이 끝나면 최종 STE 정의를 결정**하기로 함 (`baseline/params.yaml`의 `stress_transfer_efficiency.normalization` 참고). 그때까지 STE 수치는 "참고용"이지 "결론"이 아니다.

핵심 방법론과 검증 이력은 [docs/technical-notes.md](docs/technical-notes.md) 에 정리할 예정 — 선행연구 목록, 자체 감사로 찾아낸 위험 항목, 남은 확인 필요 항목 전부 포함.

---

## 결과 공유는 이렇게 한다 — 딱 세 가지

격자점 하나를 완료하면 올리는 건 이 셋뿐이다: **① CSV(수치) ② 소자 사진(뭐가 달라졌는지 보여주는 것) ③ 대시보드가 알려주는 추천 자료**.

**가장 쉬운 방법 — [대시보드](https://ryu980920.github.io/Share/)에서 바로 올리기.** "GitHub 연동" 후 격자 칸(또는 Run ID 입력)을 클릭하면 사진 업로드 + 메모 작성이 그 자리에서 끝나고, 자동으로 커밋된다. 아래 git 명령을 몰라도 된다.

<details>
<summary>git 으로 직접 올리고 싶다면 (선택)</summary>

```bash
# 1. 수치 데이터 — 자기 이름의 누적 CSV 에 한 줄 추가
echo "G50_F10,1.62" >> runs/주수빈_Ge낮은열.csv     # 컬럼: run_id,stress_GPa (ste 는 정규화 방법 확정 전까지 선택)

# 2. 사진·메모 — run_id 폴더에 (파일명 자유, 여러 장 가능)
mkdir -p runs/attachments/G50_F10
cp 아무사진.png runs/attachments/G50_F10/
echo "FR 10nm 로 변경, Ge% 는 baseline 그대로" > runs/attachments/G50_F10/notes.md

# 3. 지표 정리 (★ 손으로 계산하지 않는다) + 올리기
python analysis/build.py
git add runs/주수빈_Ge낮은열.csv runs/attachments/G50_F10 && git commit -m "G50_F10 완료" && git push
```

push 하면 **GitHub Actions 가 알아서** 전체를 다시 병합하고 대시보드를 갱신한다.
</details>

자세한 설명은 [runs/README.md](runs/README.md).
> **대용량 파일(`.tdr` `.plt` `.dat`)은 올리지 않는다.** `.gitignore` 가 막고 있다.
> 연구실 서버나 드라이브에 두고 `notes.md` 에 위치만 적는다.

---

## 딱 두 가지만 지키면 된다

### 1. `baseline/` 은 직접 고치지 않는다

3명의 결과가 하나의 등고선으로 합쳐지려면 구조·물리모델·바이어스가 **완전히 동일**해야 한다.
누군가 조용히 메쉬나 모델을 바꾸면 그 사람의 격자점만 다른 값이 나오고, **그 거짓말은 발표 전날까지 아무도 눈치채지 못한다.**

고쳐야 하면 PR 을 올리고 나머지 2명이 승인한다.

### 2. 지표는 `build.py` 로만 뽑는다

STE 를 사람마다 다른 지점/다른 환산 방식으로 계산하면, 지도의 굴곡이 물리가 아니라 정의 차이 때문에 생긴다. **그림만 봐서는 절대 발견되지 않는다.**

지표 정의는 `analysis/config.yaml` 한 곳에만 있다 (STE 정규화 방법 확정 전까지는 TODO 상태로 둔다).

---

## Run ID 명명 규칙

```
G{Ge조성%}_F{FR_nm}
```

| 예시 | 의미 |
|---|---|
| `G50_F10` | Ge 조성 50%(공칭), FR(리세스 깊이) 10nm |
| 공칭(baseline) 격자점 | `G50_F0` — FR=0이 예제 원본과 동일 구조임을 코드 구조(리세스 로직이 FR=0에서는 실행 안 됨)로 확인함(2026-08-06) |

> ★ 이 표기는 실제로 정착된 컨벤션이다 (대시보드·스크립트·CSV 전부 이 형식 사용 중). 옛 `G{Ge%}_R{리세스깊이}` 표기(R)는 FR 도입 전 잔재였고 지금은 F로 통일됨 — 대시보드 입력창의 예시 placeholder도 `G00_F00`으로 정정해뒀다(2026-08-06).

`data.csv` 의 필수 컬럼명은 정확히 `run_id, stress_GPa` (대소문자 구분). `ste` 컬럼은 STE 정규화 방법이 provisional 상태라 여전히 선택 사항이다 — 있으면 `build.py` 가 통과시키기만 하고 계산하지는 않는다. 틀리면 병합이 깨진다.

---

## ⚠ 확정 필요 항목 (팀 논의 우선순위)

1. ~~FR(리세스 깊이) 변수를 SDE 스크립트에 추가하는 정확한 문법~~ — **2026-08-06 구현 완료** (`baseline/finfet_sprocess.scm`에 조건부 리세스 식각 로직 추가). FR=0 회귀 테스트 통과, FR>0은 아직 실제 Sentaurus 실행 미검증(tasks.js #1).
2. **STE 정규화 방법 — provisional** — 체적평균(현재 구현) vs 계면 인접 단일점, G50_F0 실측 비교로 53.9% 차이 확인됨. 25격자점 스윕 데이터로 최종 결정 예정(`baseline/params.yaml` `stress_transfer_efficiency.normalization` 참고).
3. ~~Ge%×FR 스윕 격자 값~~ — **2026-08-06 확정**: Ge% [30,40,50,60,70](50% 중심), FR [0,10,20,30,35](35nm = fin 전체 높이와 일치). `baseline/params.yaml` `doe.values_confirmed: true`.
4. **"Stress Transfer Efficiency" 용어의 선행 사용(Choi 2012) 문제를 발표자료에서 어떻게 언급할지** — 팀은 검증하지 않기로 했지만, Q&A 대응 문장은 미리 준비가 필요할 수 있다.

상세 근거는 [docs/technical-notes.md](docs/technical-notes.md) 참고 (재작성 예정).

---

## 폴더

```
index.html      대시보드 (GitHub Pages 루트)
tasks.js        과제 정의 — 대시보드에서 클릭하면 상세가 뜬다
baseline/       공통 기준. PR 로만 수정
  params.yaml     모든 수치의 유일한 출처 (Ge%×FR 스윕 값 확정됨, STE 정규화는 provisional)
  finfet_sprocess.scm  SDE/SProcess 구조 스크립트 — 실제 원본 내용(2026-08-06). ⚠ 라이선스 문제로 git엔 없음(.gitignore), 로컬 전용
  finfet_sdevice.cmd   SDevice 커맨드 — 실제 원본 내용(2026-08-06). ⚠ 위와 동일, git엔 없음
  finfet_svisual_stress.tcl / finfet_svisual_extract.tcl  응력/전기 지표 추출 SVisual 스크립트(2026-08-06 신규). ⚠ 마찬가지로 git엔 없음 — 스윕 담당자끼리 팀 채널로 직접 파일 공유해서 동일 버전 쓸 것
analysis/       공용 스크립트. 지표 정의가 여기 한 곳에만 있다 (STE 최종 계산식은 스윕 데이터 확보 후 provisional → 확정)
runs/           각자의 결과. 자기 폴더만 건드린다
docs/ROLES.md   역할 분담 · 격자 분할(3인) · 일정
docs/technical-notes.md  검증 기록 (재작성 예정)
PROMPT.md       AI 에 붙여넣을 프롬프트 (형식 통일용)
```

---

## 처음 들어온 팀원

1. [docs/technical-notes.md](docs/technical-notes.md) 정독 — 지금까지 검증된 것과 안 된 것을 구분해서 기억할 것
2. [docs/ROLES.md](docs/ROLES.md) 에서 **자기 담당 격자점** 확인
3. `pip install -r analysis/requirements.txt`
4. **파이프라인 시험** — Sentaurus 없이 더미 데이터로 전체 흐름 확인 (`analysis/make_dummy_data.py`)
5. [PROMPT.md](PROMPT.md) 를 자기 AI 도구에 등록
6. 대시보드에서 체크박스·첨부물 업로드를 쓰려면 **GitHub 연동** — 아래 참고

---

## 대시보드에서 체크·업로드가 실제로 저장되게 하기

대시보드([index.html](index.html))는 정적 페이지라 기본은 읽기 전용이다. 우측 상단 **"GitHub 연동"**
버튼에서 본인 Personal Access Token 을 등록하면, 체크박스 클릭과 격자 칸 클릭(사진/메모 업로드)이
GitHub API 로 직접 `analysis/progress.json`·`runs/attachments/` 에 커밋된다.

1. [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) 에서
   Fine-grained token 발급 — Repository access 를 `ryu980920/Share` 하나로 지정, Permissions →
   **Contents: Read and write**
2. 대시보드의 "GitHub 연동" 버튼에 붙여넣고 저장

토큰은 **이 브라우저(localStorage)에만** 저장되고 서버로 전송되지 않는다. 공용 컴퓨터에서 썼다면
쓰고 나서 "연동 해제"로 지울 것. 두 사람이 거의 동시에 체크하면 저장이 한 번 실패할 수 있는데,
자동으로 최신본을 다시 받아 재시도하니 다시 눌러보면 된다.

> 연동 안 해도 대시보드는 그냥 보는 용도로는 문제없다 — `progress.json`을 직접 편집해서
> commit+push 하는 예전 방식도 여전히 된다.

---

## GitHub Pages 켜기 (저장소 주인, 2분)

**Settings → Pages → Source: `Deploy from a branch` → `main` / `/ (root)`**

배포되면 `https://ryu980920.github.io/Share/` 로 대시보드가 열린다. `index.html` 이 같은 저장소의 `analysis/status.json` 을 읽으므로 별도 설정이 없다.
> 이 저장소는 **public** 이다. 대회 요강에 사전 공개 관련 조항이 있는지 한 번 확인할 것.
> 조항이 있으면 저장소를 private 으로 바꾸고 대시보드는 로컬에서 연다
> (`python -m http.server 8000` 후 `localhost:8000`).

---

## 일정 요약

> 2026-08-06 기준 재확인 — 기존 4주 일정(W1 8/03~W4 8/31) 틀 유지, W1 마감까지 3일 남음. 상세는 [docs/ROLES.md](docs/ROLES.md) 에서 조정.

| Phase | 기간 | 내용 |
|---|---|---|
| P0 | W1 · 8/03–8/09 | 전원 공통 — FR 변수(구현 완료, 실행 검증 중), 스윕 값(확정됨), STE 정규화(provisional), baseline 재현·3인 값 대조(진행 중) |
| P1 | W2 · 8/10–8/16 | 1차원 단독 스윕 · 체크포인트 |
| P2 | W3 · 8/17–8/23 | 2차원 DoE 실행 |
| P3 | W4 · 8/24–8/31 | 병합 · STE 지도 · 발표 |

상세는 [docs/ROLES.md](docs/ROLES.md), 과제별 스윕 범위는 대시보드에서 카드를 클릭.

---

## 원칙 (기존 BCAT 프로젝트에서 그대로 승계)

- "~최적화"가 아니라 "기존 구조 + 새 공정 → 개선" 흐름
- 수치를 지어내지 않는다
- 지표를 손으로/AI 가 직접 계산하지 않는다 — `build.py` 로만
- 확실하지 않으면 "미확인"이라고 명시한다 (BCAT 프로젝트에서 구조 코너 위치를 직관으로 잘못 판단해 방향을 크게 틀어야 했던 사건, 그리고 이번 프로젝트에서 결함 경계 프레이밍을 한 번 폐기한 사건 — 둘 다 같은 교훈: 실제 수치로 먼저 검증하고 프레이밍을 정하라)
