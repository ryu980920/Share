# baseline/ — 잠긴 폴더

## 이 폴더의 규칙

> **직접 push 금지. PR + 다른 팀원 1인 승인으로만 변경.**

2명의 결과가 하나의 등고선으로 합쳐지려면, 구조·물리모델·바이어스 조건이 **완전히 동일**해야 한다.
누군가 조용히 메쉬 밀도나 모델을 바꾸면 그 사람의 격자점만 다른 값이 나오고, 등고선은 거짓말이 된다.
그 거짓말은 **발표 전날까지 아무도 눈치채지 못한다.**

## 파일

| 파일 | 역할 |
|---|---|
| `params.yaml` | 모든 수치의 유일한 출처. SDE/SDevice/분석 스크립트가 전부 이걸 참조. Ge%·리세스 깊이 스윕 값은 현재 TODO placeholder (`doe.values_confirmed: false`) |
| `bcat_sde.scm` | SDE 3D 구조 생성 스크립트. **골격뿐이다.** Synopsys Applications Library `FinFET_14nm`/`FinFET_22nm` 예제를 그대로 복사한 뒤, 리세스 식각 + SiGe 에피택시 단계만 추가하는 지점이 `TODO-RECESS`/`TODO-EPI`로 표시돼 있다 |
| `bcat_sdevice.cmd` | SDevice 커맨드. 응력/이동도 추출 정의. 소성 완화(전위결함) 모델 탑재 여부를 먼저 확인해야 하는 지점이 `TODO-STRESS-PHYSICS`로 표시돼 있다 |

파일명(`bcat_*`)은 예전 BCAT 프로젝트에서 그대로 넘어온 것으로, 내용은 FinFET/SiGe 용으로 새로 썼다.

## ⚠️ Phase 0에서 반드시 할 일

**`bcat_sde.scm` 과 `bcat_sdevice.cmd` 는 골격(scaffold)이지, 실제 Sentaurus 문법으로 검증된 스크립트가 아니다.**
AI가 실제 Scheme/커맨드 문법을 처음부터 지어내지 않은 이유도 이것 — 설치된 버전의 Applications Library 예제를 열어서 직접 채워야 한다.

- [ ] `FinFET_14nm`/`FinFET_22nm` 예제를 열어 실제 구조(핀 폭·핀 높이·게이트 길이)를 확인하고, Intel 22nm Tri-Gate / PTM 14nm 대응 여부를 대조 (현재는 **파일명 기반 추측, 미검증**)
- [ ] 예제가 SProcess 실공정 흐름인지 공정 에뮬레이션인지 확인
- [ ] 위 결과로 `params.yaml` 의 `doe.x_levels`(Ge%) / `doe.y_levels`(리세스 깊이) 확정 → `values_confirmed: true` 로 변경
- [ ] Sentaurus Stress 섹션에 소성 완화(전위결함) 모델이 있는지 확인 — 없으면 하이브리드 방법론(People-Bean/Luryi-Suhir 경계선 오버레이)이 유일한 선택지임을 문서화
- [ ] 컨택 이름이 SDevice 의 `Electrode` 이름과 일치하는지
- [ ] `params.yaml` 의 빈 항목(`fin_width_nm` 등) 예제 구조에서 확인 — Luryi-Suhir 보정에 필요
- [ ] 리세스+에피 계면 국소 메쉬가 실제로 조밀해졌는지 SVisual 로 눈으로 확인

**검증이 끝나면 PR을 올리고 다른 팀원이 승인한다.** 그 PR이 머지되어야 W2가 시작된다.

## 변경 이력

| 날짜 | 변경 | 이유 | PR |
|---|---|---|---|
| 2026-08-03 | 초기 골격 (BCAT DRAM) | — | — |
| 2026-08-04 | FinFET + Embedded SiGe S/D 주제로 전환 | 팀 주제 변경 (3인→2인, DBCAT×doping → Ge%×리세스 깊이) | — |
