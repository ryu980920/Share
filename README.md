# BCAT — DBCAT × Elevated S/D 결합 최적화

차세대반도체 경진대회 (소자/공정 부문) · 3인 · Synopsys Sentaurus TCAD

**📊 [진행 현황 대시보드](https://jujushmaterial.github.io/BCAT-DBCAT-ESD-TCAD/)** ← Pages 배포 후 주소 수정할 것

---

## 무엇을 하는 연구인가

DBCAT(질화막 두께)과 Elevated S/D 접합 도핑을 **2차원 격자로 함께 스윕**해,
두 변수가 GIDL 에 대해 독립인지 상호작용하는지를 등고선으로 판정한다.

**결과물의 형태는 "두 개의 1차원 그래프"가 아니라 "하나의 2차원 등고선"이다.**
이게 개별 논문에는 없는 우리만의 결과물이고, 심사 독창성 점수의 실체다.

베이스라인: [Kim et al., Micromachines 2022, 13(9), 1476](https://www.mdpi.com/2072-666X/13/9/1476) (오픈 액세스)

---

## 결과 공유는 이렇게 한다 — 3단계

```bash
# 1. 자기 격자점 폴더를 만들고 결과를 넣는다
cp -r runs/_template runs/D24_N070
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt -o runs/D24_N070/idvg.csv
# run.yaml, README.md 를 채운다

# 2. 지표를 뽑는다 (★ 손으로 계산하지 않는다)
python analysis/extract.py runs/D24_N070

# 3. 올린다
git add runs/D24_N070 && git commit -m "D24_N070 완료" && git push
```

push 하면 **GitHub Actions 가 알아서** 전체를 다시 병합하고 대시보드를 갱신한다.
`merge.py` 를 아무도 기억할 필요가 없다.

> **대용량 파일(`.tdr` `.plt` `.dat`)은 올리지 않는다.** `.gitignore` 가 막고 있다.
> 연구실 서버나 드라이브에 두고 `run.yaml` 의 `notes` 에 위치만 적는다.

---

## 딱 두 가지만 지키면 된다

### 1. `baseline/` 은 직접 고치지 않는다

3명의 결과가 하나의 등고선으로 합쳐지려면 구조·물리모델·바이어스가 **완전히 동일**해야 한다.
누군가 조용히 메쉬를 바꾸면 그 사람의 격자점만 다른 값이 나오고, **그 거짓말은 발표 전날까지 아무도 눈치채지 못한다.**

고쳐야 하면 PR 을 올리고 나머지 2명이 승인한다.

### 2. 지표는 `extract.py` 로만 뽑는다

Vth 를 "Id = 1e-7 A/µm 지점"으로 잡는 사람과 "선형 외삽"으로 잡는 사람이 섞이면,
등고선의 굴곡이 물리가 아니라 정의 차이 때문에 생긴다. **그림만 봐서는 절대 발견되지 않는다.**

지표 정의는 `analysis/config.yaml` 한 곳에만 있다.

---

## Run ID 명명 규칙

```
D{DBCAT_nm}_N{도핑배수×100, 3자리}
```

| 예시 | 의미 |
|---|---|
| `D24_N030` | DBCAT 24 nm, 도핑 = 베이스라인 × 0.30 |
| `D36_N100` | 공칭 조건 = **베이스라인 격자점** |

`idvg.csv` 의 컬럼명은 정확히 `Vg, Id_lin, Id_sat` (대소문자 구분). 틀리면 병합이 깨진다.

---

## 폴더

```
index.html      대시보드 (GitHub Pages 루트)
tasks.js        과제 21개 정의 — 대시보드에서 클릭하면 상세가 뜬다
baseline/       공통 기준. PR 로만 수정
  params.yaml     모든 수치의 유일한 출처
  bcat_sde.scm    SDE 구조 스크립트 ★골격. Phase 0 에서 검증 필요
  bcat_sdevice.cmd SDevice 커맨드  ★골격. Phase 0 에서 검증 필요
analysis/       공용 스크립트. 지표 정의가 여기 한 곳에만 있다
runs/           각자의 결과. 자기 폴더만 건드린다
docs/ROLES.md   역할 분담 · 격자 분할 · 4주 일정
PROMPT.md       AI 에 붙여넣을 프롬프트 (형식 통일용)
```

---

## 처음 들어온 팀원

1. [베이스라인 논문](https://www.mdpi.com/2072-666X/13/9/1476) 정독
2. [docs/ROLES.md](docs/ROLES.md) 에서 **자기 담당 격자점** 확인
3. `pip install -r analysis/requirements.txt`
4. **파이프라인 시험** — Sentaurus 없이 30분이면 전체 흐름이 손에 잡힌다

```bash
python analysis/make_dummy_data.py
python analysis/extract.py --all
python analysis/merge.py
python analysis/contour.py --all-figures
python analysis/make_dummy_data.py --clean   # ★ 반드시 삭제
```

`contour.py` 가 **"(b) 시너지"** 로 판정하면 정상이다 (더미에 시너지를 심어뒀다).

5. [PROMPT.md](PROMPT.md) 를 자기 AI 도구에 등록

---

## GitHub Pages 켜기 (저장소 주인, 2분)

**Settings → Pages → Source: `Deploy from a branch` → `main` / `/ (root)`**

배포되면 `https://<계정>.github.io/<저장소>/` 로 대시보드가 열린다.
`index.html` 이 같은 저장소의 `analysis/status.json` 을 읽으므로 별도 설정이 없다.

> 이 저장소는 **public** 이다. 대회 요강에 사전 공개 관련 조항이 있는지 한 번 확인할 것.
> 조항이 있으면 저장소를 private 으로 바꾸고 대시보드는 로컬에서 연다
> (`python -m http.server 8000` 후 `localhost:8000`).

---

## 일정 요약

| Phase | 기간 | 내용 |
|---|---|---|
| P0 | W1 · 8/03–8/09 | 전원 공통 — 베이스라인 재현, 3인 값 대조 |
| P1 | W2 · 8/10–8/16 | 1차원 단독 스윕 · **8/16 체크포인트** |
| P2 | W3 · 8/17–8/23 | 2차원 DoE 25점 |
| P3 | W4 · 8/24–8/31 | 병합 · 등고선 · 발표 |

상세는 [docs/ROLES.md](docs/ROLES.md), 과제별 스윕 범위는 대시보드에서 카드를 클릭.
