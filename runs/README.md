# runs/ — 결과를 여기에 올린다

격자점 하나를 완료하면 올리는 건 딱 셋: **① CSV(수치) · ② 소자 사진 · ③ 메모**. 저장 위치가 둘로 나뉘니 헷갈리지 말 것 — ①은 `runs/` 바로 아래, ②③은 `runs/attachments/<run_id>/` 안.

> ①(CSV)은 **git 으로만** 올린다 — 대시보드는 사진·메모(②③) 업로드만 지원한다. 숫자는 여전히 `runs/<이름>_<스윕이름>.csv` 에 직접 append 해서 push 할 것.

## ① 수치 데이터 — 자기 이름의 누적 CSV (flat, `runs/` 바로 아래)

| 방식 | 언제 | 만드는 법 |
|---|---|---|
| **SWB 변수표** (권장) | Workbench 로 스윕을 돌릴 때 | SWB 에서 **Export Variables** → 나온 CSV 를 그대로 올림 |
| 직접 작성 | 손으로/엑셀로 정리할 때 | 아래 컬럼 형식 그대로 CSV 로 저장 |

`build.py` 가 **파일을 열어보고 어느 형식인지 자동으로 판단**한다. 신경 쓸 필요 없다.

파일 이름은 `<이름>_<스윕이름>.csv`. **앞부분이 담당자 이름**이라 누가 올린 건지 자동 인식된다.

```
runs/
  유용성_Ge낮은열.csv
  남다연_Ge높은열.csv
  유용성_교차검증.csv
```

격자점을 하나 완료할 때마다 이 파일에 **한 줄씩 추가**한다 (append). 컬럼은 정확히:

```
run_id,stress_GPa,mobility_gain_pct
G20_R30,1.12,9.4
G20_R40,1.20,10.1
```

| 컬럼 | 뜻 |
|---|---|
| `run_id` | 격자점 이름. `G{Ge조성%}_R{리세스깊이_nm}` → `G30_R50` = Ge 30%, 리세스 깊이 50nm |
| `stress_GPa` | 채널 응력 [GPa]. 정확한 추출 정의(피크 vs 채널 중심 평균 등)는 `analysis/config.yaml` 한 곳에서만 정한다 — **손으로 다르게 뽑지 말 것** |
| `mobility_gain_pct` | baseline 대비 정공 이동도 증가율 [%] |

> 컬럼 이름은 **정확히 이대로** (대소문자 구분). 틀리면 `build.py` 가 이유를 알려준다.
> 맨 위에 `#` 으로 시작하는 메모 줄은 넣어도 된다. 무시된다.
> 형식 예시는 [`_예시.csv`](_예시.csv) 참고 — 이름이 `_`로 시작하는 파일은 `build.py`가 무시한다.

### SWB 변수표를 쓸 때 딱 하나만 맞추면 된다

SWB 의 파라미터 이름이 그대로 격자 좌표가 된다. `GePercent = 30`, `Recess_nm = 50` 이면 → `G30_R50` 격자점으로 인식된다.

이름을 바꾸기 어려우면 `analysis/config.yaml` 의 `swb.x_param` / `y_param` 을 실제 이름에 맞추면 된다. `stress_GPa` / `mobility_gain_pct` 에 대응하는 SWB 컬럼 이름도 같은 파일의 `swb.map` 에서 맞춘다 (Phase 0 에서 실제 SWB 출력을 보고 확정 — 지금은 TODO).

### 올리는 법

```bash
python analysis/build.py          # 확인
git add runs/유용성_Ge낮은열.csv
git commit -m "G20 열 완료"
git push
```

push 하면 **GitHub Actions 가 알아서** 전체를 다시 병합하고 대시보드를 갱신한다 (1~2분 소요).

---

## ②③ 첨부물 — `runs/attachments/<run_id>/` (사진 · 메모)

숫자만으로는 안 된다. 격자점 하나를 완료하면 **소자 사진 · 메모**도 같이 올린다.

예시 폴더를 `run_id` 이름으로 복사해서 채운다.

```bash
cp -r runs/attachments/_예시 runs/attachments/G30_R50
```

| 파일 | 내용 | 필수 여부 |
|---|---|---|
| (파일명 자유, 사진 여러 장 가능) | Ge%/리세스를 바꾸며 뭐가 달라졌는지 보여주는 소자 사진 (구조 단면, Id-Vg 커브 등 무엇이든) | 권장 |
| `notes.md` | 이 격자점에서 무엇을 바꿨는지, 뭐가 이상했는지, 다음에 고칠 것 | **필수** |

`notes.md` 를 제외한 모든 파일은 사진으로 집계된다. `analysis/build.py` 는 사진 개수와 `notes.md` 존재 여부만 확인해서 대시보드에 점으로 표시한다 (내용을 읽어서 검증하지는 않는다).

> 직접 `runs/attachments/`에 파일을 두는 대신, [대시보드](https://ryu980920.github.io/Share/)에서 GitHub 연동 후
> 격자 칸을 클릭해 파일+메모를 바로 올려도 된다 — 어떤 자료가 특히 필요한지도 대시보드가 알려준다.

```bash
git add runs/attachments/G30_R50
git commit -m "G30_R50 첨부물"
git push
```

> **공통(joint) 과제는 이 절차가 필요 없다.** 논문 정독, baseline 구조 확정 같은 공동 과제는 파일 제출 없이 체크박스로만 완료를 표시한다 (`analysis/progress.json`).

---

## 자주 하는 실수

| 증상 | 원인 |
|---|---|
| `컬럼 [...] 누락` | 컬럼 이름 오타. `stress_GPa` 를 `Stress_GPa` 나 `stress_gpa` 로 쓴 경우 |
| 격자에 안 올라감 | `run_id` 형식이 다름. `G30R50` ❌ → `G30_R50` ⭕ |
| 대시보드가 안 바뀜 | push 후 Actions 가 끝나기까지 1~2분 걸린다 |
| 첨부물 점이 안 뜸 | 폴더 이름이 `run_id` 와 정확히 일치해야 한다 (`G30_R50`, 대소문자·언더바 포함) |

---

## 올리지 않는 것

`.tdr` `.plt` `.dat` `.log` `.grd` `.bnd` 원본, Workbench 프로젝트 폴더 전체는 **커밋하지 않는다.** `.gitignore` 가 막고 있다.
용량이 커서 저장소가 망가진다. 연구실 서버나 드라이브에 두고 `notes.md` 에 위치만 적는다.
