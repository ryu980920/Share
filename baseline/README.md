# baseline/ — 잠긴 폴더

## 이 폴더의 규칙

> **직접 push 금지. PR + 나머지 2인 승인으로만 변경.**

3명의 결과가 하나의 등고선으로 합쳐지려면, 구조·물리모델·바이어스 조건이 **완전히 동일**해야 한다.
누군가 조용히 메쉬 밀도를 바꾸면 그 사람의 격자점만 다른 값이 나오고, 등고선은 거짓말이 된다.
그 거짓말은 **발표 전날까지 아무도 눈치채지 못한다.**

## 파일

| 파일 | 역할 |
|---|---|
| `params.yaml` | 모든 수치의 유일한 출처. SDE/SDevice/분석 스크립트가 전부 이걸 참조 |
| `bcat_sde.scm` | SDE 3D 구조 생성 스크립트. `@DBCAT@`, `@NMULT@` 두 개만 격자점마다 바뀜 |
| `bcat_sdevice.cmd` | SDevice 커맨드. BTBT 모델·바이어스 스윕 정의 |

## ⚠️ Phase 0에서 반드시 할 일

**`bcat_sde.scm` 과 `bcat_sdevice.cmd` 는 골격(scaffold)이다.**
문법 구조와 파라미터화 방식은 잡혀 있지만, 아래 항목은 **학교 라이선스의 실제 Sentaurus 버전에서 검증하고 채워야 한다.**

- [ ] 좌표계·치수를 논문 Fig.1 단면과 대조 (`bcat_sde.scm` 의 `TODO-GEOM`)
- [ ] 컨택 이름이 SDevice의 `Electrode` 이름과 일치하는지
- [ ] BTBT 모델 문법이 설치된 버전의 SDevice User Guide와 맞는지 (`TODO-MODEL`)
- [ ] `params.yaml` 의 빈 항목(fin_width, junction_depth, channel_conc) 논문에서 확인
- [ ] 겹침부 국소 메쉬가 실제로 조밀해졌는지 SVisual로 눈으로 확인

**검증이 끝나면 `params.yaml` 의 `verified_by` 에 이름을 쓰고 PR을 올린다.** 그 PR이 머지되어야 W2가 시작된다.

## 변경 이력

| 날짜 | 변경 | 이유 | PR |
|---|---|---|---|
| 2026-08-03 | 초기 골격 | — | — |
