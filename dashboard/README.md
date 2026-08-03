# dashboard/ — Run Sheet 대시보드

`index.html` 하나로 세 가지 환경에서 동작한다. **어느 방식이든 같은 화면이다.**

| 방식 | 데이터가 어디서 오나 | 외부에 뭐가 보이나 | 준비 |
|---|---|---|---|
| ① 로컬 서버 | 내 PC 의 `analysis/status.json` | **아무것도** | 명령어 1줄 |
| ② 파일 직접 열기 | 버튼으로 고른 `status.json` | **아무것도** | 없음 |
| ③ GitHub Pages | private 저장소 → GitHub API | 사이트 껍데기만 (데이터 0) | Pages 배포 + 토큰 |

---

## ① 로컬 서버 — 기본 권장

저장소 루트에서:

```bash
python analysis/merge.py          # status.json 생성
python -m http.server 8000
```

브라우저에서 `http://localhost:8000/dashboard/` 를 연다. 끝이다.

`git pull` 만 하면 팀원들의 최신 결과가 반영된다. **배포가 없으니 유출도 없다.**

## ② 파일 직접 열기 — 서버 띄우기 귀찮을 때

`index.html` 을 더블클릭 → 상단 **"status.json 직접 열기"** 버튼 → `analysis/status.json` 선택.

> `file://` 에서는 브라우저 보안 정책상 자동 로딩이 막혀서 이 버튼이 필요하다.

## ③ GitHub Pages — 링크로 공유하고 싶을 때

**전제**: GitHub **Pro 또는 Team** 플랜. (Free 는 private 저장소에서 Pages 를 못 쓴다.
학생이면 [Student Developer Pack](https://education.github.com/pack) 으로 Pro 를 무료로 받을 수 있다.)

### 이 방식이 안전한 이유

- 저장소는 **private** 이다. 소스·데이터·결과 전부 비공개.
- Pages 사이트에는 **데이터가 한 글자도 들어가지 않는다.** 껍데기(HTML/JS)만 공개된다.
- 방문자가 자기 토큰을 넣으면, 그 토큰으로 **GitHub API 가 private 저장소를 읽어와** 화면에 그린다.
- 협업자가 아니면 토큰을 만들어도 404 가 난다. → **조원 3명만 실제 데이터를 본다.**

### 설정

1. **Settings → Pages** → Source: `Deploy from a branch` → `main` / `/ (root)`
2. 배포되면 `https://<계정>.github.io/<저장소>/dashboard/` 로 접속
3. 각자 fine-grained PAT 발급:
   - GitHub → Settings → Developer settings → **Personal access tokens → Fine-grained tokens**
   - **Repository access**: `Only select repositories` → 이 저장소 **하나만**
   - **Permissions**: `Contents` → **Read-only** 만
   - 만료: 대회 종료일(9/1)로 설정
4. 사이트에서 저장소 경로와 토큰을 입력 → 불러오기

토큰은 브라우저 메모리에만 있고 어디에도 저장·전송되지 않는다. 새로고침하면 다시 입력해야 한다.

### 그래도 남는 노출

- **저장소 이름과 사이트 URL 은 공개된다.** `BCAT-...` 같은 이름이면 주제가 드러난다.
- 사이트의 과제 목록(`tasks.js`)도 공개된다. **여기에 스윕 범위가 들어 있다.**

이게 걸리면 두 가지 대응이 있다.

- **대응 1**: Pages 로 배포할 브랜치를 따로 파고, 거기서는 `tasks.js` 를 비워둔다.
  → 과제 상세도 API 로 가져오게 만들면 완전히 껍데기만 남는다.
- **대응 2**: 그냥 ①번을 쓴다. 3명이 어차피 저장소를 clone 하므로 실질적 불편이 없다.

> **판단 기준**: 대회 요강에 사전 공개 관련 조항이 있는지 먼저 확인할 것.
> 조항이 있으면 ③번은 쓰지 않는다. 없더라도, 얻는 것(링크 공유의 편의)에 비해
> 잃을 수 있는 것(독창성 주장의 근거)이 크다.

---

## 화면 구성

- **상단 통계** — 전체/완료 격자점, 진행률, 교차검증 상태
- **DoE 격자** — 25칸. 테두리 색 = 담당자, 배경 밝기 = GIDL 크기(어두울수록 낮음=좋음)
- **과제 카드 21개** — 클릭하면 고정 조건 / **스윕 범위(베이스라인 대비 상대값)** / 할 일 / 완료 판정 기준 / 산출물

## 과제 내용을 고칠 때

`dashboard/tasks.js` 와 `docs/ISSUES.md` **둘 다** 고친다. 같은 내용의 두 표현이다.
