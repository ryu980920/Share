# GitHub 저장소 세팅 — 30분 안에 끝난다

> 이 순서대로 하면 된다. 1~2번은 저장소 주인(유용성)만, 6번부터는 팀원 각자.

---

## 1. 기존 저장소 정리 (5분)

현재 `VCAT-1T1C-DRAM-TCAD-Research` 는 두 가지 문제가 있다.

- **이름이 틀렸다** — 주제는 VCAT 이 아니라 BCAT 이다
- **공개돼 있다** — GitHub Pages 는 무료/Pro/Team 플랜에서 무조건 공개다

**Settings → General** 에서:

1. `Repository name` → `BCAT-DBCAT-ESD-TCAD` 로 변경
2. 맨 아래 `Danger Zone` → **Change repository visibility** → **Private**
   - 이 순간 GitHub Pages 사이트는 자동으로 내려간다. 정상이다.
3. `Settings → Pages` → Source 를 **None** 으로

> **왜 사이트를 버리는가**: private 저장소에서 Pages 를 쓰려면 GitHub Enterprise Cloud 가 필요하다.
> 그리고 Pages 로 서빙되는 HTML/JS 는 소스가 그대로 보이므로, 로그인 버튼을 달아도 데이터는 노출된다.
> 경진대회 전에 주제·파라미터·결과가 공개되는 위험을 감수할 이유가 없다.
> 대시보드 기능은 아래 4번의 Projects 가 그대로 대체한다.

---

## 2. 팀원 초대 (2분)

**Settings → Collaborators → Add people**

- 팀원 2명의 GitHub 아이디 또는 이메일 입력
- 권한: **Write** (Admin 은 주지 않는다 — 실수로 저장소 설정을 바꾸는 것을 막는다)

---

## 3. baseline 보호 (5분) ★ 이게 핵심

**Settings → Rules → Rulesets → New branch ruleset**

| 설정 | 값 |
|---|---|
| Ruleset Name | `protect-main` |
| Enforcement status | Active |
| Target branches | `main` |
| Require a pull request before merging | ✅ |
| Required approvals | **1** |
| Block force pushes | ✅ |

> `baseline/` 만 2명 승인으로 두는 세밀한 설정은 무료 플랜에서 제한이 있을 수 있다.
> 안 되면 **규칙으로 정하고 PR 템플릿 체크리스트로 관리**한다 —
> `.github/pull_request_template.md` 에 이미 항목이 들어 있다.

---

## 4. Projects 보드 생성 (5분) — 대시보드 대체

저장소 상단 **Projects → New project → Board**

컬럼 4개를 만든다: `대기` / `진행` / `검토` / `완료`

그리고 **Settings → Custom fields** 로 아래를 추가하면 필터링이 된다.

| 필드 | 타입 | 값 |
|---|---|---|
| 담당 | Single select | A / B / C |
| Phase | Single select | P0 / P1 / P2 / P3 |
| DBCAT | Number | 24 / 30 / 36 / 42 / 48 |

이렇게 하면 "A 담당의 P2 과제만 보기" 같은 뷰가 만들어진다.
**원래 만들려던 웹 대시보드가 하려던 일을 GitHub 이 그냥 해준다.**

---

## 5. 파일 올리기 (5분)

이 저장소 파일 일체를 로컬에 풀고:

```bash
cd BCAT-DBCAT-ESD-TCAD
git init
git add .
git commit -m "협업 구조 초기 세팅: baseline, 분석 파이프라인, Issue 템플릿, 프롬프트"
git branch -M main
git remote add origin https://github.com/<계정>/BCAT-DBCAT-ESD-TCAD.git
git push -u origin main
```

---

## 6. Issue 발행 (10분)

`docs/ISSUES.md` 를 보고 **Phase 0 의 5개(#1~#5)를 먼저** 만든다.
나머지는 각 Phase 시작 시점에 발행한다. 한꺼번에 21개를 만들면 보드가 안 보인다.

Issue 를 만들 때 **New issue → 템플릿 선택** 화면이 뜨는지 확인한다.
안 뜨면 `.github/ISSUE_TEMPLATE/` 가 제대로 푸시되지 않은 것이다.

라벨도 미리 만들어 두면 편하다: `sweep` `setup` `analysis` `verification` `presentation` `phase-0`~`phase-3` `A` `B` `C`

---

## 7. 팀원 각자 (10분)

- [ ] 초대 수락
- [ ] 저장소 clone
- [ ] `pip install -r analysis/requirements.txt`
- [ ] `README.md` → `CONTRIBUTING.md` → `docs/ROLES.md` 순서로 읽기
- [ ] `prompts/00_공통컨텍스트.md` 를 자기 AI 도구에 등록
  - ChatGPT → Custom Instructions 또는 Project 지식
  - Claude → Project 의 Knowledge
  - Claude Code → 아무것도 안 해도 됨 (`CLAUDE.md` 자동 로드)
- [ ] Issue `#5` (파이프라인 시험)를 실제로 해보기 — 30분이면 끝나고, 전체 흐름이 손에 잡힌다

---

## 확인 체크리스트

- [ ] 저장소가 private 이다 (로그아웃 상태에서 URL 을 열어 404 가 나오는지 확인)
- [ ] Pages 사이트가 내려갔다
- [ ] 팀원 2명이 Write 권한으로 들어와 있다
- [ ] main 에 직접 push 가 막힌다 (시험 삼아 해보기)
- [ ] New issue 에서 템플릿 3종이 보인다
- [ ] Projects 보드에 Phase 0 Issue 5개가 올라가 있다
