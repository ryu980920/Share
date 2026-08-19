## 무엇을 바꿨나
- 2026-08-19: `stress_ZZ_field.png` 추가 — SVisual StressZZ 단면 캡처. Ge% 비교용 5장 세트(G30/40/50/60/70_F0) 중 하나, 전부 동일 컬러 스케일(0 ~ -3.6e9 Pa) 사용. 이 점의 stress_GPa = -2.262 GPa (grid.csv 기준). 컬러바 단위가 Pa로 표시되는 건 알려진 사항 — 발표 때 구두 설명 예정
- 새로 바꾼 건 없음 — baseline(G50_F0, Ge=0.50/FR=0) 신뢰성 검증 단계. SVisual(`n1_e_fps`)로 구조를 직접 열어서 재질/도핑/형상을 눈으로 확인
- `01_전체구조_overview.png` — 구조 전체를 처음 열어본 컷. 축(X=높이, Y=핀 폭, Z=채널 길이) 확인용
- `02_SiGe_SD_형상_단독.png` — SiGe(S/D 에피)만 Materials 탭에서 단독으로 켠 형상. {111} facet 다이아몬드 모양 확인
- `03_ChFin_채널_단독_경계확인.png` — Regions 탭에서 채널(ChFin)만 단독으로 분리해서 켠 컷. 대부분 n형(Nch 수준, 빨강)이고 SiGe와 맞닿는 가장자리에만 얇은 청록 띠(붕소 확산 꼬리)가 있음 — **STE 정규화의 "채널 인접 지점" 좌표를 잡을 때 이 경계선을 참고할 것**
- `04_SD_채널_SD_단면.png` — `transform reflect back` 적용 후 소스-채널-드레인이 한 번에 보이는 단면. 색은 NetActive: 양끝 빨강(S/D, 고농도) → 중앙 파랑(채널, 배경 도핑)으로 자연스럽게 이어짐

## 이상했던 점 / 경고
- 처음엔 "채널이 SiGe 아니냐"는 오해가 있었음 → Materials 탭(재질)과 Regions 탭(세부 영역) 혼동이 원인. ChFin만 Regions 탭에서 분리하니 정상적인 n형 Silicon으로 확인됨(오해였음)
- S/D 도핑도 "표면만 고농도, 몸통은 배경 수준"으로 잘못 봤었는데, 이것도 ChFin이 같이 섞인 화면 때문 — SDepi만 분리하면 BTotal·BActive 둘 다 부피 전체 균일(~2e20)
- SSSat 절대값(183~550 mV/dec)이 이상적 60mV/dec 대비 매우 높음 — 이 서브구조는 게이트 재질이 없는(`gate_material_present:false`) 순수 응력/도핑 계산용이라서 그런 것으로 추정. 완전한 게이트 스택에서 재확인 필요
- Esd(언더컷)는 "채널 아래로" 파고드는 게 아니라 "핀 전체 높이에 걸쳐 균일하게 옆으로(채널 길이 방향)" 7.5nm만 파고드는 것 — 게이트 밑 25nm 채널 자체는 0.5nm 여유를 두고 안 건드림 (Esd=7.5nm < Lsp0=8nm)

## 다음에 수정할 것
- [ ] STE 정규화 방법(채널 인접 지점 좌표, GPa 환산 방식) 팀 확정 — `03_ChFin_채널_단독_경계확인.png`의 경계선 참고
- [ ] SSSat 비정상적으로 높은 값 원인 확인 (완전한 게이트 스택 구조에서 재검증)
- [ ] Strain_Impact=1/0 SWB 비교(`baseline/verification_strain_impact_G50F0.csv`)로 응력-이동도 결합 정상 작동 확인 완료 — 상세는 `baseline/README.md`, `baseline/params.yaml`의 `verification.strain_impact_coupling` 참고
