# BCAT DBCAT × Elevated S/D 결합 최적화 — TCAD 공동연구

> 차세대반도체 경진대회 (소자/공정 부문) · 3인 팀 · Synopsys Sentaurus TCAD
> **이 저장소는 private입니다. 외부 공유 금지.**

## 한 줄 목표

DBCAT(질화막 두께)과 Elevated S/D 접합 도핑을 **2차원 격자로 함께 스윕**해,
두 변수가 GIDL에 대해 독립인지 상호작용하는지를 등고선으로 판정한다.

**결과물의 형태는 "두 개의 1차원 그래프"가 아니라 "하나의 2차원 등고선"이다.**

---

## 이 저장소의 작동 원리 (3줄 요약)

1. `baseline/` 에 **모두가 공유하는 단 하나의 구조·커맨드 파일**이 있다. 아무도 직접 못 고친다.
2. 각자 자기 담당 격자점만 돌려서 `runs/<RUN_ID>/` 에 **정해진 이름의 CSV**를 올린다.
3. `analysis/` 스크립트가 그 CSV들을 자동으로 합쳐 등고선을 그린다. → 3명의 결과가 저절로 하나가 된다.

이 구조 때문에 **파일 이름과 컬럼 이름을 틀리면 병합이 깨진다.** 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있다.

---

## 폴더 구조

```
baseline/       공통 기준. 수정은 PR + 2인 승인 필수 (직접 push 금지)
  params.yaml     ← 베이스라인 수치의 유일한 출처 (Single Source of Truth)
  bcat_sde.scm    ← SDE 구조 생성 스크립트
  bcat_sdevice.cmd← SDevice 커맨드 파일
runs/           각자의 시뮬레이션 결과. 자기 폴더만 건드린다
  D36_N100/       ← 격자점 하나 = 폴더 하나
    run.yaml        메타데이터 (담당자, 변경한 값, 실행 시간)
    idvg.csv        원시 Id-Vg 데이터  ★필수
    metrics.csv     추출된 지표        ★필수 (extract.py가 생성)
    plot.png        Id-Vg 플롯
    README.md       3줄 요약
analysis/       공용 스크립트. 지표 정의가 여기 한 곳에만 있다
  config.yaml     지표 추출 기준 (Vth 정의, GIDL 측정점 등)
  extract.py      idvg.csv → metrics.csv
  merge.py        runs/**/metrics.csv → grid.csv
  contour.py      grid.csv → 등고선 + 교호작용 회귀
docs/           일정, 역할, 과제 초안, 개발 로그
  SETUP_GITHUB.md 저장소 세팅 순서 (private 전환, Projects 보드)
  ROLES.md        역할 분담 · 격자 분할 · 4주 일정
  ISSUES.md       과제 초안 21개
  devlog.md       결정과 그 이유
prompts/        AI에게 넣을 프롬프트 (형식 통일용) ★팀원 필독
CLAUDE.md       Claude Code 자동 로드용 규칙 (prompts/00 과 같은 내용)
```

## AI 를 쓸 때

3명이 각자 다른 AI 로 결과를 정리하면 형식이 제각각이 되어 자동 병합이 깨진다.
**대화 시작할 때 `prompts/00_공통컨텍스트.md` 를 붙여넣는다.** 자세한 건 [prompts/README.md](prompts/README.md).

---

## 처음 들어온 팀원이 할 일 (순서대로)

0. (저장소 주인만) [docs/SETUP_GITHUB.md](docs/SETUP_GITHUB.md) 대로 private 전환 + Projects 보드 생성
1. [MDPI 2022 베이스라인 논문](https://www.mdpi.com/2072-666X/13/9/1476) 정독 — 오픈 액세스
2. 「DRAM 기초 학습자료」 완독
3. [docs/ROLES.md](docs/ROLES.md) 에서 **자기 담당 격자점** 확인
4. [CONTRIBUTING.md](CONTRIBUTING.md) 의 명명 규칙 숙지
5. [prompts/00_공통컨텍스트.md](prompts/00_공통컨텍스트.md) 를 자기 AI 도구에 등록
6. 자기에게 배정된 Issue를 열어 작업 시작

---

## 진행 현황

Projects 보드에서 확인: `Projects` 탭 → `BCAT DoE`

| Phase | 기간 | 상태 |
|---|---|---|
| P0 공통 — 베이스라인 재현 | W1 (8/03–8/09) | ⬜ |
| P1 1차원 단독 스윕 | W2 (8/10–8/16) | ⬜ |
| P2 2차원 DoE 실행 | W3 (8/17–8/23) | ⬜ |
| P3 병합·분석·발표 | W4 (8/24–8/31) | ⬜ |

**체크포인트 (8/16)**: DBCAT 단독 스윕에서 GIDL 주효과가 미미하면 → 2차원 격자 확장 전에 스윕 범위 재검토. (기획서 5-4절 시나리오 B)
