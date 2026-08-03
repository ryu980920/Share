# runs/ — 결과를 여기에 올린다

## 방법은 두 가지. 편한 쪽을 쓰면 된다.

| 방식 | 언제 | 만드는 법 |
|---|---|---|
| **① SWB 변수표** (권장) | Workbench 로 스윕을 돌릴 때 | SWB 에서 **Export Variables** → 나온 CSV 를 그대로 올림 |
| ② Id-Vg 원시 곡선 | 곡선 자체가 필요할 때 (모델 비교 등) | `plt2csv.py` 로 변환하거나 엑셀에서 직접 |

`build.py` 가 **파일을 열어보고 어느 형식인지 자동으로 판단**한다. 신경 쓸 필요 없다.

파일 이름은 `<이름>_<스윕이름>.csv`. **앞부분이 담당자 이름**이라 누가 올린 건지 자동 인식된다.

```
runs/
  유용성_D24.csv
  주수빈_D36.csv
  남다연_모델비교.csv
```

---

## ① SWB 변수표 — 새로 만들 게 없다

Workbench 가 이미 만들어주는 표다. 이렇게 생겼다.

```
sprocess,sprocess,...,sdevice,svisual,...
sprocess,sprocess,...,sdevice_IdVgLin,Plot_IdVgLin,...
Init,STI,SFin,...,DBCAT,Nmult,,Vtgm,VtLin,IdSat,Ioff,Igidl,T_RET
1,1,1,...,24,0.30,,0.5231,0.4802,7.20e-05,3.10e-13,1.26e-12,6.40e-02
1,1,1,...,24,1.00,,0.5433,0.5001,7.00e-05,3.10e-13,1.27e-11,6.90e-02
```

- 1행 = 툴 이름, 2행 = 노드 이름, 3행 = 파라미터/변수 이름, 4행부터 = 실험 조건
- `x` / `xx` / 빈칸 = 아직 안 돌아간 셀. **그대로 올려도 된다.** 돌아간 것만 반영된다.

### 딱 두 가지만 맞추면 된다

**(1) 파라미터 이름을 `DBCAT` / `Nmult` 로**

SWB 의 파라미터 이름이 그대로 격자 좌표가 된다.
`DBCAT = 24`, `Nmult = 0.30` 이면 → `D24_N030` 격자점으로 인식된다.

이름을 바꾸기 어려우면 `analysis/config.yaml` 의 `swb.x_param` / `y_param` 을 실제 이름에 맞추면 된다.

**(2) `Igidl` 추출 변수를 추가**

★ **이게 이 프로젝트의 주 지표인데 지금 SWB 에 없다.**
`Ioff` 는 Vg=0 에서의 누설이라 GIDL(Vg 가 음수일 때 겹침부에서 생기는 누설)과 다르다.

SVisual 추출 스크립트에 아래를 추가한다.

```tcl
# Vg = -0.5 V (워드라인 오프 전압) 에서의 드레인 전류
set Igidl [ ... IdVgSat 곡선에서 Vg = -0.5 V 인 지점의 Id ... ]
ext::ExtractValue -out Igidl -name "Igidl"
```

> 정확한 문법은 설치된 버전의 SVisual 매뉴얼 확인. `Vtgm` / `Ioff` 를 뽑는 기존 코드 옆에
> 같은 방식으로 하나 더 추가하면 된다.

### 올리는 법

```bash
# SWB 에서 Export Variables → 나온 파일을 runs/ 에 복사
python analysis/build.py          # 확인
git add runs/유용성_D24.csv
git commit -m "D24 열 완료"
git push
```

---

## ② Id-Vg 원시 곡선 — 곡선 자체가 필요할 때

### CSV 안은 이렇게 생겼다

```csv
run_id,Vg,Id_lin,Id_sat
D24_N030,-1.00,3.124e-13,8.451e-11
D24_N030,-0.95,2.013e-13,5.226e-11
...
D24_N050,-1.00,4.221e-13,1.102e-10
D24_N050,-0.95,...
```

**격자점 여러 개가 한 파일에 세로로 쌓인다.** `run_id` 컬럼이 어느 격자점인지 구분해준다.

| 컬럼 | 뜻 |
|---|---|
| `run_id` | 격자점 이름. `D{DBCAT}_N{도핑배수×100}` → `D24_N030` = DBCAT 24nm, 도핑 ×0.30 |
| `Vg` | 게이트 전압 [V]. -1.0 ~ +2.8, 0.05 간격 |
| `Id_lin` | Vd = 0.1 V 에서의 드레인 전류 [A/µm] |
| `Id_sat` | Vd = 1.0 V 에서의 드레인 전류 [A/µm] |

> 컬럼 이름은 **정확히 이대로** (대소문자 구분). 틀리면 `build.py` 가 이유를 알려준다.
> 맨 위에 `#` 으로 시작하는 메모 줄은 넣어도 된다. 무시된다.

---

### 만드는 법

격자점 하나 돌릴 때마다 한 번씩 실행하면 **같은 파일에 계속 쌓인다.**

```bash
# 첫 번째 격자점 — 파일을 새로 만든다
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       --run-id D24_N030 --out runs/유용성_D24.csv

# 두 번째부터 — --append 를 붙인다
python analysis/plt2csv.py IdVg_lin_des.plt IdVg_sat_des.plt \
       --run-id D24_N050 --out runs/유용성_D24.csv --append
```

실행할 때마다 **파일에 지금 몇 개가 들어 있는지** 알려준다.

```
덧붙임: runs/유용성_D24.csv  (D24_N050 77점 추가 · 파일 전체 2개 격자점 / 154줄)
현재 들어 있는 격자점: D24_N030, D24_N050
```

5개가 다 모이면 확인하고 올린다.

```bash
python analysis/build.py
git add runs/유용성_D24.csv
git commit -m "D24 열 완료"
git push
```

---

### 손으로 만들어도 된다

`.plt` 변환이 안 되면 엑셀에서 만들어도 상관없다. 위 4개 컬럼만 맞으면 된다.
엑셀에서 **다른 이름으로 저장 → CSV UTF-8** 로 저장하면 된다.

---

## 자주 하는 실수

| 증상 | 원인 |
|---|---|
| `컬럼 [...] 누락` | 컬럼 이름 오타. `Vg` 를 `VG` 나 `V_g` 로 쓴 경우 |
| 격자에 안 올라감 | `run_id` 형식이 다름. `D24_N30` (2자리) ❌ → `D24_N030` (3자리) ⭕ |
| `전류가 0.1 A/um 초과` | 폭 정규화를 안 함. `plt2csv.py --width-um` 확인 |
| 대시보드가 안 바뀜 | push 후 Actions 가 끝나기까지 1~2분 걸린다 |

---

## 올리지 않는 것

`.tdr` `.plt` `.dat` `.log` 원본은 **커밋하지 않는다.** `.gitignore` 가 막고 있다.
용량이 커서 저장소가 망가진다. 연구실 서버나 드라이브에 두고 위치만 Issue 에 적는다.
