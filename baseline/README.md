# baseline/ — 잠긴 폴더

## 이 폴더의 규칙

> **직접 push 금지. PR + 다른 팀원 2인 승인으로만 변경.**

3명의 결과가 하나의 등고선으로 합쳐지려면, 구조·물리모델·바이어스 조건이 **완전히 동일**해야 한다.
누군가 조용히 메쉬 밀도나 모델을 바꾸면 그 사람의 격자점만 다른 값이 나오고, 등고선은 거짓말이 된다.
그 거짓말은 **발표 전날까지 아무도 눈치채지 못한다.**

## 파일

| 파일 | 역할 |
|---|---|
| `params.yaml` | 모든 수치의 유일한 출처. SDE/SProcess/SDevice/분석 스크립트가 전부 이걸 참조. geometry/materials/doping 은 실제 확인된 값으로 채워짐. Ge%/FR 스윕 값(`doe.x_levels`/`y_levels`)은 **확정됨**(`values_confirmed: true`, [30,40,50,60,70]×[0,10,20,30,35]) — STE 정규화 방법은 잠정(provisional) 상태, 25격자점 스윕 데이터를 모은 뒤 체적평균/계면 단일점 중 최종 결정 예정 |
| `finfet_sprocess.scm` | 구조 생성 스크립트(SProcess). ⚠ **git에는 없음 — 로컬 전용, `.gitignore` 처리됨 (2026-08-06)**. Synopsys Sentaurus 라이선스 예제(Munkang Choi, 2013) 원본을 기반으로 한 실제 스크립트라 재배포 조항 확인 전까지 public repo에 올리지 않기로 함. 각자 자기 로컬/Sentaurus 환경에 직접 준비할 것 — 내용은 이 README와 devlog.md에 요약돼 있음 |
| `finfet_sdevice.cmd` | SDevice 커맨드. ⚠ **git에는 없음 — 로컬 전용, `.gitignore` 처리됨.** 사유는 위와 동일 |
| `finfet_svisual_stress.tcl` | ChFin 영역 체적평균 응력(SlFin/SwFin/ShFin, MPa) 추출 — STE 정규화 방법의 실제 구현체. ⚠ **git에는 없음 — 로컬 전용, `.gitignore` 처리됨** |
| `finfet_svisual_extract.tcl` | IdVg 곡선에서 VtiSat/IdSat_norm/SSSat/gmSat 등 전기적 지표 추출. ⚠ **git에는 없음 — 로컬 전용, `.gitignore` 처리됨** |
| `verification_strain_impact_G50F0.csv` | Strain_Impact=1/0 비교 증빙 원본 CSV |

> ⚠️ **2026-08-06: 위 스크립트 4개는 더 이상 이 저장소(public)에 커밋하지 않는다.** Synopsys Sentaurus 라이선스 예제(Munkang Choi, 2013)를 기반으로 한 실제 코드라 재배포 조항을 확인하기 전까지 위험을 감수하지 않기로 함(팀 판단). 각자 Sentaurus 설치본의 Applications Library에서 같은 예제(FinFET_14nm)를 직접 열면 원본을 볼 수 있고, 팀이 무엇을 바꿨는지는 이 README·`params.yaml`·`competition/docs/devlog.md`에 전부 텍스트로 기록돼 있다 — 코드 자체가 없어도 "무엇을 어떻게 바꿨는지"는 재현 가능하다.

## ⚠️ Phase 0에서 반드시 할 일

- [x] **FR(리세스 깊이) 변수 추가** — `finfet_sprocess.scm`에 조건부 리세스 식각 로직(FR>0일 때만 실행)으로 구현 완료. FR=0 회귀 테스트 통과(원본과 동일 구조). **FR=15nm 실제 Sentaurus 실행으로 검증 완료(2026-08-07, 유용성)** — SVisual 좌표축 단면(cutline) 비교로 TRECH 영역이 baseline 대비 정확히 ~15nm 더 깎인 것을 확인, 전기적 지표도 물리적으로 타당한 방향(IdSat_norm↑, SSSat↓)으로 변함 (tasks.js #1, 나머지 2인 확인은 아직)
- [ ] 예제가 SProcess 실공정 흐름인지 공정 에뮬레이션인지 확인
- [x] **`doe.x_levels`(Ge%) / `doe.y_levels`(FR) 스윕 값 확정** (2026-08-06) — Ge% [30,40,50,60,70](50% 중심), FR [0,10,20,30,35](35nm=fin 전체 높이와 일치). `values_confirmed: true`. 25격자점(5×5) 본 스윕 시작 가능 → tasks.js #10~17
- [ ] **STE 정규화 방법 — 잠정(provisional) 상태, 최종 채택 보류** (2026-08-06 수정) — G50_F0에서 체적평균(SlFin=-2262MPa) vs 계면 인접 근사(SlFin_pt=-3482MPa)를 실측 비교한 결과 53.9% 차이 + ShFin은 부호까지 반전됨. 무시할 수 없는 차이라 지금 하나로 확정하지 않고, **남은 24격자점 스윕에서 SlFin/SlFin_pt를 둘 다 뽑아 모은 뒤 마지막에 결정**하기로 함 (`stress_transfer_efficiency.normalization` 참고). ⚠ 스윕 담당자 전원이 `finfet_svisual_stress.tcl`의 2026-08-06 버전(SlFin_pt 등 포함)을 동일하게 써야 함 — 이 파일은 라이선스 문제로 git에 없으므로(`.gitignore` 참고) 팀 채널로 직접 파일을 공유해서 싱크 맞출 것
- [x] 컨택 이름 일치 확인 — `finfet_sprocess.scm`에서 지정한 게이트/소스/드레인 컨택 이름이 `finfet_sdevice.cmd`의 전극 이름과 일치함 (2026-08-06)
- [x] StressELXX/YY/ZZ 확인 — Plot 블록엔 없지만(SDevice), `finfet_svisual_stress.tcl`에서 응력 성분 세 개를 직접 적분해서 추출. 단위는 MPa (SlFin 등, /1.0e6 환산)
- [ ] SiGe/Si 계면 국소 메쉬가 실제로 조밀해졌는지 SVisual 로 눈으로 확인 — 1차 육안 확인(NetActive 메쉬)은 양호해 보이나, 정량적 수렴성 검사는 tasks.js #8(남다연) 결과로 확정 필요
- [x] **Strain_Impact=1/0 비교로 응력→전기 결합이 실제로 작동하는지 확인** (2026-08-06, G50_F0 기준. IdSat_norm +227% 등, 방향성 문헌과 일치. 상세는 `params.yaml`의 `verification.strain_impact_coupling` 참고). `finfet_sdevice.cmd`에서 이 매크로가 켜지면 응력-이동도 결합 물리모델(피에조저항 모델)이 활성화되는 구조로 돼 있음이 실제 메커니즘

**검증이 끝나면 PR을 올리고 다른 팀원이 승인한다.** 그 PR이 머지되어야 W2가 시작된다.

> ⚠️ 2026-08-06 항목은 팀 판단으로 PR 절차를 생략하고 main에 직접 반영함 (사용자 확정, devlog 참고).

## 변경 이력

| 날짜 | 변경 | 이유 | PR |
|---|---|---|---|
| 2026-08-03 | 초기 골격 (BCAT DRAM) | — | — |
| 2026-08-04 | FinFET + Embedded SiGe S/D 주제로 전환 | 팀 주제 변경 (3인→2인, DBCAT×doping → Ge%×리세스 깊이) | — |
| 2026-08-04 | 2인→3인 복귀 (주수빈 재합류), 열 분할 2등분→3등분 | 인원 변경 | — |
| 2026-08-04 | `bcat_sde.scm`/`bcat_sdevice.cmd` → `finfet_sde.scm`/`finfet_sdevice.cmd` 로 파일명 변경 | 예전 BCAT DRAM 프로젝트 파일명이 그대로 남아있어 현재 주제(FinFET)와 안 맞고 혼동을 유발함 — 내용은 이미 FinFET 용으로 재작성돼 있었으나 이름만 안 바뀌어 있었다 | — |
| 2026-08-05 | 결함 경계(People-Bean/Luryi-Suhir) 프레이밍 폐기 → Stress Transfer Efficiency(STE) 프레이밍 전환. `finfet_sde.scm` → `finfet_sprocess.scm` 로 재개명, FR(리세스 깊이) 변수 신규 도입, params.yaml geometry/materials 실제 값 확정(Gate 25nm, Fin height 35nm 등) | baseline 치수(fin 반폭 7.5nm)에서 결함 경계 프레이밍이 판별력을 잃어(Ge 42~100% 전 구간 "무제한 보호") 프레이밍 전환. 자세한 경위는 README.md | — |
| 2026-08-06 | Strain_Impact=1/0 SWB 비교로 응력-이동도 결합 검증 완료 (G50_F0). SVisual로 ChFin/SDepi 재질·도핑(BActive/BTotal)·Esd 언더컷 형상도 별도 확인 | Phase 0 baseline 신뢰성 확보 — 스윕 본격 시작 전에 물리 결합이 실제로 작동하는지 확인 필요했음 | — (PR 생략, 직접 반영) |
| 2026-08-06 | `finfet_sprocess.scm`/`finfet_sdevice.cmd`를 TODO 골격에서 실제 원본 스크립트로 교체, `finfet_svisual_stress.tcl`/`finfet_svisual_extract.tcl` 신규 추가. `params.yaml`의 `doping`(Nsd=2.0e20 등), `stress_transfer_efficiency.normalization`(체적평균 방식 확인), `meta.verified_by` 채움 | 지금까지 실제 스크립트 내용이 채팅에서만 공유되고 repo엔 TODO 골격만 있어 팀원이 GitHub만 봐서는 실제 구현을 확인할 수 없었음 — 팀 가시성 확보 | — (PR 생략, 직접 반영) |
| 2026-08-06 | 라이선스 문제로 스크립트 4개 `.gitignore` 처리. `doe.x_levels`/`y_levels` 확정(`values_confirmed: true`). STE 정규화는 G50_F0 실측 비교(체적평균 vs 계면 단일점, 53.9% 차이 + 부호 반전 1개 성분)로 provisional 상태로 정정 — 25격자점 스윕 데이터로 최종 결정 예정. `analysis/progress.json`의 담당자 키 오류 수정(#1/#3/#4/#16 누락된 주수빈 키 추가, #9/#10/#11/#12/#13/#17 tasks.js와 어긋난 키 수정) + #4(baseline 구조 재현) 유용성 체크 — 실제 G50_F0 실행 결과(verification CSV)가 있어 구조 스크립트가 end-to-end로 동작함이 확인됨 | 스윕 시작 전 마지막 P0 정리 — 스윕 값 확정으로 #10~17 착수 가능해졌고, 대시보드 데이터 정합성도 바로잡음 | — (PR 생략, 직접 반영) |
| 2026-08-07 | **FR>0 실제 Sentaurus 실행 검증 완료(G50_F15, 유용성)** — SVisual에서 baseline(FR=0)과 FR=15nm 구조를 좌표축 있는 단면(cutline)으로 나란히 비교, TRECH 영역 세로 치수가 baseline 대비 약 0.015(15nm)만큼 더 깎인 것을 좌표로 확인. 전기적 지표도 예상 방향대로 변화(IdSat_norm +12.9%, IdLin_norm +11.3%, SSSat -32.9%, \|VtiSat\| -4.2%). `analysis/progress.json` #1 유용성 체크 | tasks.js #1의 마지막 미검증 항목(FR>0 실행)이 해소됨 — 나머지 2인 확인만 남음 | — (PR 생략, 직접 반영) |
| 2026-08-10 | **#14(Ge=50% 중간열) 첫 스윕 실행, FR=10nm까지 결과 확인** — `analysis/config.yaml`의 SWB 파라미터명이 실제 SVisual export(`Ge`/`FR`/`SlFin`/`SlFin_pt`/`VtiSat` 등)와 안 맞고 검증 전 추측값(`GeMoleFraction`/`FR_nm`/`Stress`/`Vth`)으로 남아있던 걸 발견·수정, `build.py`에 단위 변환(Ge 몰분율→%, FR um→nm) 추가 — 업로드된 실제 CSV로 파싱 재검증 완료. FR=0→10nm 구간 전기적 지표가 8/7 FR=15nm 검증과 같은 방향으로 변화(IdSat_norm +9.4%, SSSat -25.8%, \|VtiSat\| 소폭 감소) 확인. STE 정규화는 기존 결정대로 SlFin(체적평균)/SlFin_pt(계면 단일점) 두 방식을 `map`에 둘 다 걸어 매 실행마다 병행 수집하도록 파이프라인에 반영 — 25격자점 다 모이면 비교해 최종 결정 | config.yaml이 실측 데이터 없이 추측으로 작성돼 있어 #14 첫 실행 CSV를 build.py가 인식 못 함 — 원인 규명·수정 필요했음. FR=20/30/35nm 세 점은 전기적 지표 미추출(x) 상태라 #14는 아직 미완료(구조/응력 데이터만 완비) | — (PR 생략, 직접 반영) |
| 2026-08-13 | **#10(주수빈, Ge% 낮은 열 단독 스윕)·#12/#14(유용성, FR 단독 스윕=Ge% 중간열)** 격자점 CSV 반영 — `runs/유용성_G중간열.csv`(G50_F0~F35 5점 전부, 전기적 지표 완비), `runs/주수빈_Ge스윕.csv`(G30_F0, G40_F0). `build.py`가 헤더 1줄 + `[n12]: 0.4` 노드 태그 export 형식(팀원마다 Export Variables 옵션이 달라 생긴 세 번째 형식)도 인식하도록 `looks_like_swb`/`read_swb`에 파서 보강. `analysis/progress.json` #10/#12/#14 체크. 전체 격자 진행률 7/25(28%) | FR 축은 5점 다 채워져 트렌드 판정 가능해졌고(문헌 방향과 일치하되 FR=30~35에서 SS/Ioff 트레이드오프 관찰), Ge% 축도 30/40/50 세 점으로 1차 트렌드 확인 가능해짐 — 나머지 격자점(Ge=60/70, Ge=30/40의 FR=10~35)은 계속 진행 중 | — (PR 생략, 직접 반영) |
| 2026-08-13 (2) | **#11(남다연, Ge% 높은 열 단독 스윕)** 격자점 CSV 반영 — `runs/남다연_Ge스윕.csv`(G60_F0, G70_F0). `analysis/progress.json` #11 체크 — 이로써 Ge% 축(30/40/50/60/70%, FR=0 고정) 5점 전부 완료. 전체 격자 진행률 9/25(36%) | Ge% 축 트렌드가 30~70% 전 구간에서 확인됨: 응력(SlFin) -1346→-3210MPa, IdSat_norm 4.72e-4→6.32e-4, gmSat도 9.58e-5→1.14e-4 로 전부 반전 없이 단조 증가 — FR 축과 달리 이 구간에선 gmSat도 같이 계속 올라서(포화 없음) "이동도 개선"과 "IdSat_norm 증가"가 분리되지 않고 같은 방향으로 감. 다만 SSSat(105→316)·Ioff_norm(1.07e-10→6.01e-10)도 같이 계속 나빠지는 트레이드오프는 동일하게 존재 | — (PR 생략, 직접 반영) |
| 2026-08-15 | **#15(남다연, Ge% 높은 열 전체 격자)** 완료 — `runs/남다연_G높은열.csv`(G60/G70 × FR=0/10/20/30/35, 8개 신규 격자점). SWB "Open view in a spreadsheet"가 팀원 서버에 스프레드시트 프로그램이 없어 실행 불가했던 문제를, 결과 셀만 선택해 복사 → 원격 세션 내 `gedit`에 붙여넣기 → 파일로 저장 → 다운로드하는 방식으로 우회해 확보. `analysis/progress.json` #15 체크. 전체 격자 진행률 17/25(68%) — 남은 건 Ge=30/40의 FR=10~35(#13, 주수빈)뿐 | G60_F0/G70_F0는 기존 `남다연_Ge스윕.csv`와 교차검증 결과 편차 0.0%로 일치(같은 데이터 다른 경로로 재확인된 셈). gmSat이 FR=20 근처에서 포화되는 패턴이 Ge=60%·70%에서도 동일하게 재현됨(1.19e-4, 1.24e-4에서 각각 피크 후 정체) — 8/13(2)에 Ge=50%에서만 확인했던 "gm 포화 vs IdSat_norm 지속 상승" 디커플링이 Ge% 축 전체에서 일반적인 현상임을 확인. SSSat도 세 Ge% 모두 FR=20 부근에서 최저, FR=30~35에서 급격히 재악화되는 동일한 U자형 패턴 재현 — FR=30/35 트레이드오프가 Ge%와 무관한 리세스 깊이(전기적/구조적) 자체의 효과로 보임 | — (PR 생략, 직접 반영) |
| 2026-08-15 (2) | **#13(주수빈, Ge% 낮은 열 전체 격자)** 완료 — `runs/주수빈_G낮은열.csv`(G30/G40 × FR=0/10/20/30/35, 8개 신규 격자점). `analysis/progress.json` #13 체크. **이로써 DoE 격자 25/25(100%) 완주.** `contour.py --all-figures` 첫 전체 실행 — 교호작용 회귀 R²=0.9947, Ge%×FR 교호작용 계수 -0.034(\|t\|=1.57<2, 유의하지 않음) → "(a) 상호작용 없음·독립" 판정. `analysis/figures/contour_stress_GPa.png` 최초로 빈 곳 없이 생성 | 격자 완주로 #17(2D STE 지도)·#18(교호작용 정량화)을 실제 데이터로 시작할 수 있게 됨. `contour.py`의 "시너지 정량화" 섹션이 "최댓값 지점: G30_F0"를 출력하는데, 이는 stress_GPa가 음수(압축응력)라 대수적으로 가장 큰(0에 가장 가까운) 값을 고른 것일 뿐 — 실제 응력 크기가 가장 큰 지점은 G70_F30(-3.560GPa)이다. 발표 자료에 이 스크립트 출력을 그대로 인용하면 안 되고 반드시 부호 설명을 붙여야 함. gm 포화(FR=20 근처) vs SSSat 재악화(FR=30~35) 패턴이 Ge=30/40%에서도 동일 재현 — 5개 Ge% 전 구간에서 일반적인 FR축 현상으로 확정 | — (PR 생략, 직접 반영) |
| 2026-08-19 | **Strain_Impact=0 FR 스윕 검증** — `baseline/verification_strain_impact_G50_FRsweep.csv`(Ge=50%, FR 0/10/20/30/35 × Strain_Impact 1/0, 10행). `analysis/figures/verify_strain_impact_FRsweep.png` 신규. `docs/reports/project-summary.md` 4-3절·8-3절 반영 | FR축 열화(SSlin·DIBL·Ioff 악화)가 응력을 꺼도 재현됨을 확인 — ChStop 제거(형상 변화)가 주원인이라는 8/15 결론의 직접 검증. 응력을 켜면 열화 폭이 더 큼(Ioff는 10배 이상 차이) — 밴드갭 축소가 관통 경로 누설을 추가로 증폭시키는 2차 효과로 해석. 후속으로 FR=15/22nm 2점(Ge=50 고정) 추가 스윕 제안 | — (PR 생략, 직접 반영) |
| 2026-08-19 (2) | **응력 비교 사진 5장 재확보** — `runs/attachments/G{30,40,50,60,70}_F0/stress_ZZ_field.png`, 동일 Ge%(FR=0) 5점 전부 같은 컬러 스케일(0~-3.6e9 Pa)로 재촬영·게이트/S-D 영역으로 확대. G30/40/60/70_F0 `notes.md` 신규 작성 + G50_F0 갱신 | 8/15 이전부터 밀려있던 사진 재작업·notes.md 누락을 동시에 해소. 컬러바 단위(Pa)는 아직 미해결 — 발표에서 구두 설명 | — (PR 생략, 직접 반영) |
| 2026-08-23 | **FR=15/22nm 실측 추가 → 실용 설계창 상한 22→20nm 정정** — `baseline/verification_FR_refine_G50.csv`(Ge=50%, FR 0/10/15/20/22/30/35 × Strain_Impact 1/0). `analysis/figures_presentation.py` 의 `draw_overlay()` 흰 띠를 15~20 으로 수정 + 근거 캡션 추가, `pres_tradeoff_overlay.png` 재생성 | 두 점 다 이웃 사이에 매끄럽게 들어가 기존 보간은 타당했으나, **이득/대가 비율(nm당 STE 이득 ÷ nm당 SSlin 손실)이 FR 15→20 구간 2.91 에서 20→22 구간 0.38 로 7.6배 급락** — 22nm 는 이미 무릎을 지난 지점. gmSat 도 FR=20 최댓값 후 22nm 에서 감소하고, Ioff 가 1e-9 를 처음 넘는 것도 22nm(1.93e-9). 정정 후 주장이 더 강해짐(STE 98.5~99.6%, SSlin 82.2~84.7, Ioff<1e-9). ⚠ `runs/` 가 아닌 `baseline/` 에 둔 이유: `runs/` 에 넣으면 Ge=50 열만 7점인 비직사각 격자가 되어 등고선 pivot 에 NaN 이 생기고 25점 회귀가 깨진다 | — (PR 생략, 직접 반영) |
