# FinFET + Embedded SiGe Source/Drain 응력공학

차세대반도체 경진대회 (소자/공정 부문) · 2인(유용성 · 남다연) · Synopsys Sentaurus TCAD

**📊 [진행 현황 대시보드](https://ryu980920.github.io/Share.github.io/)**

---

## 무엇을 하는 연구인가

기존 FinFET 구조에 **Embedded SiGe Source/Drain**(선택적 에피택시로 S/D 를 SiGe 로 대체, in-situ 도핑) 공정을 추가해 PMOS 채널에 압축 응력을 유도한다.
스윕 축은 **Ge 조성(%) × 리세스 깊이(nm)**. Sentaurus 로 이 2차원 전 구간의 응력·이동도를 완전정합(pseudomorphic) 가정 하에 계산하고, 그 위에 **문헌 기반 임계두께 경계선**(People-Bean / Luryi-Suhir)을 겹쳐서 "어느 조합부터 전위결함(소성 완화)으로 응력 이득이 무효화되는지"를 판정한다.

**"~ 최적화"가 아니라 "기존 FinFET 구조 + 새 공정(SiGe eS/D) → 개선"** 흐름을 따른다 — 심사 기준상 필수. 단순 응력 최댓값을 찾는 게 아니라, **결함 발생 경계(trade-off boundary) 지도**를 그리는 것이 목표다.

> **베이스라인은 논문 재현이 아니다.** Synopsys Sentaurus Applications Library 의 `FinFET_14nm` / `FinFET_22nm` 예제를 구조 출발점으로 쓴다.
> ※ 이 예제가 Intel 22nm Tri-Gate / PTM 14nm 에 대응한다는 것은 **파일명 기반 추측이며 미검증**이다. 절대 확정된 사실처럼 인용하지 말 것 — Phase 0 에서 예제 파일을 직접 열어 치수 스펙으로 대조 확인해야 한다 ([docs/ROLES.md](docs/ROLES.md) #1 과제).

핵심 방법론과 검증 이력은 [docs/technical-notes.md](docs/technical-notes.md) 에 정리되어 있다 — 선행연구 목록, 자체 감사로 찾아낸 위험 항목, People-Bean/Luryi-Suhir 공식 출처, 남은 확인 필요 항목 전부 포함.

---

## 결과 공유는 이렇게 한다 — 3단계

숫자 데이터와 첨부물(사진·커브·메모)은 올리는 위치가 다르다. 자세한 설명은 [runs/README.md](runs/README.md), 첨부물 폴더 예시는 `runs/attachments/_예시`.

```
# 1. 수치 데이터 — 자기 이름의 누적 CSV 에 한 줄 추가 (wide 형식)
#    컬럼: run_id,stress_GPa,mobility_gain_pct
echo "G30_R50,1.62,18.4" >> runs/유용성_Ge낮은열.csv     # 예시 — 실제로는 Sentaurus 출력값을 넣을 것

# 2. 첨부물 — 소자 사진·커브·메모는 run_id 별 폴더에
mkdir -p runs/attachments/G30_R50
cp structure.png runs/attachments/G30_R50/
cp idvg_curve.png runs/attachments/G30_R50/
echo "리세스 rate 0.02 로 변경, Ge% 는 baseline 그대로" > runs/attachments/G30_R50/notes.md

# 3. 지표를 정리한다 (★ 손으로 계산하지 않는다)
python analysis/build.py

# 4. 올린다
git add runs/유용성_Ge낮은열.csv runs/attachments/G30_R50 && git commit -m "G30_R50 완료" && git push
```

push 하면 **GitHub Actions 가 알아서** 전체를 다시 병합하고 대시보드를 갱신한다.
> **대용량 파일(`.tdr` `.plt` `.dat`)은 올리지 않는다.** `.gitignore` 가 막고 있다.
> 연구실 서버나 드라이브에 두고 `run.yaml` 의 `notes` 에 위치만 적는다.

---

## 딱 두 가지만 지키면 된다

### 1. `baseline/` 은 직접 고치지 않는다

2명의 결과가 하나의 등고선으로 합쳐지려면 구조·물리모델·바이어스가 **완전히 동일**해야 한다.
누군가 조용히 메쉬나 모델을 바꾸면 그 사람의 격자점만 다른 값이 나오고, **그 거짓말은 발표 전날까지 아무도 눈치채지 못한다.**

고쳐야 하면 PR 을 올리고 나머지 1명이 승인한다.

### 2. 지표는 `build.py` 로만 뽑는다

응력을 "피크값"으로 잡는 사람과 "채널 중심 평균값"으로 잡는 사람이 섞이면,
등고선의 굴곡이 물리가 아니라 정의 차이 때문에 생긴다. **그림만 봐서는 절대 발견되지 않는다.**

지표 정의는 `analysis/config.yaml` 한 곳에만 있다.

---

## Run ID 명명 규칙

```
G{Ge조성%}_R{리세스깊이_nm}
```

| 예시 | 의미 |
|---|---|
| `G30_R50` | Ge 조성 30%, 리세스 깊이 50nm |
| 공칭(baseline) 격자점 | ⚠ TODO — Ge%·리세스 깊이 스윕 값이 아직 미확정 (아래 "확정 필요 항목" 참고). 확정되면 여기 채울 것 |

`data.csv` 의 컬럼명은 정확히 `run_id, stress_GPa, mobility_gain_pct` (대소문자 구분). 틀리면 병합이 깨진다. 정확한 컬럼 구성은 `analysis/config.yaml`·`analysis/build.py` 확정 후 갱신 예정.

---

## ⚠ 확정 필요 항목 (Phase 0 최우선)

기술노트에서 "미확인"으로 표시된 항목 중, 프로젝트 진행 자체를 막는 것들:

1. **Ge% / 리세스 깊이 스윕 값** — `baseline/params.yaml` 의 `doe.x_levels` / `doe.y_levels` 는 지금 예시 placeholder 다. FinFET_14nm/22nm 예제의 실제 구조(핀 폭·핀 높이)를 열어본 뒤, 그 구조에서 기하학적으로 말이 되는 범위로 재확정해야 한다.
2. **FinFET_14nm/22nm 예제 ≟ Intel 22nm Tri-Gate / PTM 14nm** — 파일명 추측일 뿐 미검증. 예제 안 문서를 열어 실제 치수와 대조.
3. **예제가 SProcess 실공정 흐름인지 공정 에뮬레이션인지** — 미확인.
4. **Sentaurus Stress 섹션에 소성 완화(전위결함) 모델 탑재 여부** — 미확인, 현재는 "탑재 안 됨"으로 가정하고 하이브리드 방법론(경계선 별도 오버레이) 설계.
5. **Luryi-Suhir 보정에 쓸 fin 폭 W** — 확정될 baseline 예제 스펙에서 가져와야 함(1번과 연동).

상세 근거는 [docs/technical-notes.md](docs/technical-notes.md) 4절 참고.

---

## 폴더

```
index.html      대시보드 (GitHub Pages 루트)
tasks.js        과제 정의 — 대시보드에서 클릭하면 상세가 뜬다
baseline/       공통 기준. PR 로만 수정
  params.yaml     모든 수치의 유일한 출처 (Ge%/리세스 깊이 스윕 값 TODO)
  bcat_sde.scm    SDE 구조 스크립트 ★골격 — FinFET_14nm/22nm 예제 복사 후 리세스+에피 추가 지점만 TODO 표시
  bcat_sdevice.cmd SDevice 커맨드 ★골격 — 응력/이동도 추출 지점 TODO 표시
analysis/       공용 스크립트. 지표 정의가 여기 한 곳에만 있다
runs/           각자의 결과. 자기 폴더만 건드린다
docs/ROLES.md   역할 분담 · 격자 분할(2인) · 일정
docs/technical-notes.md  검증 기록 (선행연구·자체감사·공식·미확인 항목)
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
버튼에서 본인 Personal Access Token 을 등록하면, 체크박스 클릭과 격자 칸 클릭(사진/커브/메모 업로드)이
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

배포되면 `https://ryu980920.github.io/Share.github.io/` 로 대시보드가 열린다. `index.html` 이 같은 저장소의 `analysis/status.json` 을 읽으므로 별도 설정이 없다.
> 이 저장소는 **public** 이다. 대회 요강에 사전 공개 관련 조항이 있는지 한 번 확인할 것.
> 조항이 있으면 저장소를 private 으로 바꾸고 대시보드는 로컬에서 연다
> (`python -m http.server 8000` 후 `localhost:8000`).

---

## 일정 요약

| Phase | 기간 | 내용 |
|---|---|---|
| P0 | W1 · 8/03–8/09 | 전원 공통 — 예제 구조 확인, 스윕 값 확정, baseline 재현, 2인 값 대조 |
| P1 | W2 · 8/10–8/16 | 1차원 단독 스윕 · 체크포인트 |
| P2 | W3 · 8/17–8/23 | 2차원 DoE 실행 |
| P3 | W4 · 8/24–8/31 | 병합 · 등고선 · 경계선 오버레이 · 발표 |

상세는 [docs/ROLES.md](docs/ROLES.md), 과제별 스윕 범위는 대시보드에서 카드를 클릭.

---

## 원칙 (기존 BCAT 프로젝트에서 그대로 승계)

- "~최적화"가 아니라 "기존 구조 + 새 공정 → 개선" 흐름
- 수치를 지어내지 않는다
- 지표를 손으로/AI 가 직접 계산하지 않는다 — `build.py` 로만
- 확실하지 않으면 "미확인"이라고 명시한다 (BCAT 프로젝트에서 구조 코너 위치를 직관으로 잘못 판단해 방향을 크게 틀어야 했던 사건의 재발 방지)
