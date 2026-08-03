# BCAT — DBCAT × Elevated S/D 결합 최적화

차세대반도체 경진대회 (소자/공정 부문) · **유용성 · 주수빈 · 남다연** · Synopsys Sentaurus TCAD

**📊 [진행 현황 대시보드](https://ryu980920.github.io/Share/)**

---

## 무엇을 하는 연구인가

DBCAT(질화막 두께)과 Elevated S/D 접합 도핑을 **2차원 격자로 함께 스윕**해,
두 변수가 GIDL 에 대해 독립인지 상호작용하는지를 등고선으로 판정한다.

**결과물의 형태는 "두 개의 1차원 그래프"가 아니라 "하나의 2차원 등고선"이다.**
이게 개별 논문에는 없는 우리만의 결과물이고, 심사 독창성 점수의 실체다.

베이스라인: [Kim et al., Micromachines 2022, 13(9), 1476](https://www.mdpi.com/2072-666X/13/9/1476) (오픈 액세스)

---

## 결과 공유 — 스윕 한 번 = CSV 한 장

폴더를 만들 필요 없다. **자기가 돌린 스윕을 CSV 한 장에 담아 올리면 끝이다.**

Workbench 를 쓴다면 **새로 만들 파일도 없다.** SWB 의 `Export Variables` 로 나온
변수표를 그대로 올리면 `build.py` 가 알아서 읽는다. (자세히 → [runs/README.md](runs/README.md))

```
runs/
  유용성_D24.csv     ← DBCAT 24nm 열 5점이 전부 이 안에
  주수빈_D36.csv
  남다연_D48.csv
```

CSV 안은 이렇게 생겼다. 격자점 여러 개가 세로로 쌓이고, `run_id` 가 구분해준다.

```csv
run_id,Vg,Id_lin,Id_sat
D24_N030,-1.00,3.124e-13,8.451e-11
D24_N030,-0.95,2.013e-13,5.226e-11
...
D24_N050,-1.00,4.221e-13,1.102e-10
```

### 만드는 법

격자점 하나 돌릴 때마다 한 번씩. `--append` 를 붙이면 같은 파일에 계속 쌓인다.

```bash
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       --run-id D24_N030 --out runs/유용성_D24.csv

python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       --run-id D24_N050 --out runs/유용성_D24.csv --append
```

> `.plt` 변환이 안 되면 **엑셀에서 만들어도 된다.** 위 4개 컬럼만 맞으면 된다.

### 올리는 법

```bash
python analysis/build.py          # 확인
git add runs/유용성_D24.csv
git commit -m "D24 열 완료"
git push
```

push 하면 **GitHub Actions 가 알아서** 지표를 다시 뽑고 등고선을 다시 그려 대시보드를 갱신한다.

자세한 형식과 자주 하는 실수는 [runs/README.md](runs/README.md).

> **대용량 파일(`.tdr` `.plt` `.dat`)은 올리지 않는다.** `.gitignore` 가 막고 있다.
> 연구실 서버나 드라이브에 두고 위치만 Issue 에 적는다.

---

## 딱 두 가지만 지키면 된다

### 1. `baseline/` 은 직접 고치지 않는다

3명의 결과가 하나의 등고선으로 합쳐지려면 구조·물리모델·바이어스가 **완전히 동일**해야 한다.
누군가 조용히 메쉬를 바꾸면 그 사람의 격자점만 다른 값이 나오고,
**그 거짓말은 발표 전날까지 아무도 눈치채지 못한다.**

고쳐야 하면 PR 을 올리고 나머지 2명이 승인한다.

### 2. 지표는 `build.py` 로만 뽑는다

Vth 를 "Id = 1e-7 A/µm 지점"으로 잡는 사람과 "선형 외삽"으로 잡는 사람이 섞이면,
등고선의 굴곡이 물리가 아니라 정의 차이 때문에 생긴다. **그림만 봐서는 절대 발견되지 않는다.**

지표 정의는 `analysis/config.yaml` 한 곳에만 있다. 손으로 계산하지 않는다.

---

## Run ID 명명 규칙

```
D{DBCAT_nm}_N{도핑배수×100, 3자리}
```

| 예시 | 의미 |
|---|---|
| `D24_N030` | DBCAT 24 nm, 도핑 = 베이스라인 × 0.30 |
| `D36_N100` | 공칭 조건 = **베이스라인 격자점** |
| `D36_N100_hurkx` | 부가 실험. 접미사가 붙으면 격자에 안 올라간다 |

`N030` 처럼 **세 자리**로 쓴다. `N30` 은 인식이 안 된다.

---

## 담당

| 담당 | 맡은 열 | 격자점 | 추가 과제 |
|---|---|---|---|
| **유용성** | D24, D30 | 10 | 얇은 질화막 극단값에서 구조 생성 확인 |
| **주수빈** | D36, D42 | 10 | 공칭 근방 — 논문 값과 직접 대조 |
| **남다연** | D48 | 5 | BTBT 모델 3종 비교 + 메쉬 수렴성 검증 |

**왜 이렇게 나누는가**: 격자점 25개는 서로 완전히 독립이라, 열 단위로 쪼개면
누가 막혀도 나머지가 안 멈춘다. "구조 담당 / 물리 담당 / 분석 담당" 으로 나누면
앞사람이 늦을 때 전원이 대기하고, 분석 담당은 TCAD 를 한 번도 안 돌려보고 끝난다.

상세는 [docs/ROLES.md](docs/ROLES.md).

---

## 폴더

```
index.html      대시보드 (GitHub Pages)
tasks.js        과제 21개 정의 — 대시보드에서 클릭하면 상세가 뜬다
runs/           결과 CSV. 여기에 올린다
baseline/       공통 기준. PR 로만 수정
  params.yaml     모든 수치의 유일한 출처
  bcat_sde.scm    SDE 구조 스크립트 ★골격. Phase 0 에서 검증 필요
  bcat_sdevice.cmd SDevice 커맨드  ★골격. Phase 0 에서 검증 필요
analysis/
  build.py        runs/*.csv → 지표 → 격자표 → 대시보드 데이터  ★핵심
  contour.py      등고선 + 교호작용 회귀 + 시너지 정량화
  plt2csv.py      Sentaurus .plt → CSV
  config.yaml     지표 정의 (Vth 기준 등)
docs/ROLES.md   역할 · 격자 분할 · 4주 일정
PROMPT.md       AI 에 붙여넣을 프롬프트 (형식 통일용)
```

---

## 처음 시작하는 사람

1. [베이스라인 논문](https://www.mdpi.com/2072-666X/13/9/1476) 정독
2. [대시보드](https://ryu980920.github.io/Share/)에서 **자기 이름이 붙은 과제** 확인 — 클릭하면 스윕 범위가 나온다
3. `pip install -r analysis/requirements.txt`
4. **파이프라인 시험** — Sentaurus 없이 30분이면 전체 흐름이 손에 잡힌다

```bash
python analysis/make_dummy_data.py
python analysis/build.py
python analysis/contour.py --all-figures
python analysis/make_dummy_data.py --clean   # ★ 반드시 삭제
```

`contour.py` 가 **"(b) 시너지"** 로 판정하면 정상이다 (더미에 시너지를 심어뒀다).

5. [PROMPT.md](PROMPT.md) 를 자기 AI 도구에 등록

---

## 일정

| Phase | 기간 | 내용 |
|---|---|---|
| P0 | W1 · 8/03–8/09 | 전원 공통 — 베이스라인 재현, 3인 값 대조 |
| P1 | W2 · 8/10–8/16 | 1차원 단독 스윕 · **8/16 체크포인트** |
| P2 | W3 · 8/17–8/23 | 2차원 DoE 25점 |
| P3 | W4 · 8/24–8/31 | 병합 · 등고선 · 발표 |

---

> 이 저장소는 **public** 이다. 대회 요강에 사전 공개 관련 조항이 있는지 한 번 확인할 것.
> 조항이 있으면 private 으로 바꾸고 대시보드는 로컬에서 연다
> (`python -m http.server 8000` 후 `localhost:8000`).
