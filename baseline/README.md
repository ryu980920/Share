# baseline/ — 잠긴 폴더

## 이 폴더의 규칙

> **직접 push 금지. PR + 다른 팀원 2인 승인으로만 변경.**

3명의 결과가 하나의 등고선으로 합쳐지려면, 구조·물리모델·바이어스 조건이 **완전히 동일**해야 한다.
누군가 조용히 메쉬 밀도나 모델을 바꾸면 그 사람의 격자점만 다른 값이 나오고, 등고선은 거짓말이 된다.
그 거짓말은 **발표 전날까지 아무도 눈치채지 못한다.**

## 파일

| 파일 | 역할 |
|---|---|
| `params.yaml` | 모든 수치의 유일한 출처. SDE/SProcess/SDevice/분석 스크립트가 전부 이걸 참조. geometry/materials 는 실제 확인된 값(Gate 25nm 등)으로 채워짐. Ge%/FR 스윕 값·STE 정규화 방법은 현재 TODO placeholder (`doe.values_confirmed: false`) |
| `finfet_sprocess.scm` | 구조 생성 스크립트. **골격뿐이다.** Sentaurus FinFET_14nm 예제(Choi/Synopsys 2013)를 그대로 복사한 뒤, FR(리세스 깊이) 변수를 신규로 추가하는 지점이 `TODO-FR`로 표시돼 있다 — GeMoleFraction/Esd 는 예제에 이미 있어 손댈 필요 없음 |
| `finfet_sdevice.cmd` | SDevice 커맨드. 응력(StressELXX/YY/ZZ) 추출 정의 — 예제에 이미 출력되고 있어 `TODO-STRESS-EXTRACT` 는 확인만 하면 된다 |

## ⚠️ Phase 0에서 반드시 할 일

**`finfet_sprocess.scm` 과 `finfet_sdevice.cmd` 는 골격(scaffold)이지, 실제 Sentaurus 문법으로 검증된 스크립트가 아니다.**
AI가 실제 Scheme/커맨드 문법을 처음부터 지어내지 않은 이유도 이것 — 설치된 버전의 Applications Library 예제를 열어서 직접 채워야 한다.

- [ ] **FR(리세스 깊이) 변수를 Esd 파라미터화 방식을 참고해 신규로 추가** — 문법 미확인, 최우선 게이트 (tasks.js #1)
- [ ] 예제가 SProcess 실공정 흐름인지 공정 에뮬레이션인지 확인
- [ ] 위 결과로 `params.yaml` 의 `doe.x_levels`(Ge%) / `doe.y_levels`(FR) 확정 → `values_confirmed: true` 로 변경
- [ ] **STE 정규화 방법**(채널 인접 지점, GPa 환산) 확정 → `stress_transfer_efficiency.normalization` 채우기
- [ ] 컨택 이름이 SDevice 의 `Electrode` 이름과 일치하는지
- [ ] StressELXX/YY/ZZ 가 실제로 Plot 블록에 포함돼 있는지, 단위가 무엇인지 확인
- [ ] SiGe/Si 계면 국소 메쉬가 실제로 조밀해졌는지 SVisual 로 눈으로 확인

**검증이 끝나면 PR을 올리고 다른 팀원이 승인한다.** 그 PR이 머지되어야 W2가 시작된다.

## 변경 이력

| 날짜 | 변경 | 이유 | PR |
|---|---|---|---|
| 2026-08-03 | 초기 골격 (BCAT DRAM) | — | — |
| 2026-08-04 | FinFET + Embedded SiGe S/D 주제로 전환 | 팀 주제 변경 (3인→2인, DBCAT×doping → Ge%×리세스 깊이) | — |
| 2026-08-04 | 2인→3인 복귀 (주수빈 재합류), 열 분할 2등분→3등분 | 인원 변경 | — |
| 2026-08-04 | `bcat_sde.scm`/`bcat_sdevice.cmd` → `finfet_sde.scm`/`finfet_sdevice.cmd` 로 파일명 변경 | 예전 BCAT DRAM 프로젝트 파일명이 그대로 남아있어 현재 주제(FinFET)와 안 맞고 혼동을 유발함 — 내용은 이미 FinFET 용으로 재작성돼 있었으나 이름만 안 바뀌어 있었다 | — |
| 2026-08-05 | 결함 경계(People-Bean/Luryi-Suhir) 프레이밍 폐기 → Stress Transfer Efficiency(STE) 프레이밍 전환. `finfet_sde.scm` → `finfet_sprocess.scm` 로 재개명, FR(리세스 깊이) 변수 신규 도입, params.yaml geometry/materials 실제 값 확정(Gate 25nm, Fin height 35nm 등) | baseline 치수(fin 반폭 7.5nm)에서 결함 경계 프레이밍이 판별력을 잃어(Ge 42~100% 전 구간 "무제한 보호") 프레이밍 전환. 자세한 경위는 README.md | — |
