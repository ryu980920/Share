---
name: "스윕 과제"
about: "격자점 실행 / 검증 / 분석 공통"
title: "[담당자] "
labels: []
---

## 담당 / 대상

- 담당자: <!-- 유용성 / 주수빈 / 남다연 / 전원 -->
- 올릴 파일: `runs/<이름>_<스윕이름>.csv` (숫자) + `runs/attachments/<run_id>/` (사진·메모)
- Run ID: <!-- 예: G30_R50 ~ G30_R70 -->

## 고정 조건 (baseline — 건드리지 않는다)

`baseline/params.yaml` 그대로. ⚠ Ge%/리세스 깊이 스윕 값은 아직 TODO — Phase 0(#1~#5 과제) 완료 전에는
이 표를 확정된 값으로 채우지 말 것.

| 항목 | 값 |
|---|---|
| 베이스라인 출처 | Synopsys Applications Library `FinFET_14nm`/`FinFET_22nm` 예제 (대응 관계 미검증) |
| 게이트 길이 등 구조 | `baseline/params.yaml` 참고 (일부 TODO) |
| 결함 모델 가정 | Sentaurus Stress 섹션에 소성완화 모델 없음으로 가정 (검증 전, `docs/model_choice.md` 참고) |

## 이번에 바꾸는 것

| 변수 | 값 | baseline 대비 |
|---|---|---|
| Ge 조성 [%] | ___ % | |
| 리세스 깊이 [nm] | ___ nm | |

> 다른 값을 함께 바꾸면 두 변수의 효과가 섞여 그 격자점은 버려야 한다.
> 수렴 때문에 어쩔 수 없이 바꿨다면 이 Issue 에 전부 적을 것.

## 체크리스트

- [ ] 격자점 전부 실행 완료
- [ ] `python analysis/build.py` 에서 경고 없음
- [ ] `runs/<이름>_<스윕이름>.csv` 에 `run_id,stress_GPa,mobility_gain_pct` 한 줄 추가
- [ ] `runs/attachments/<run_id>/` 에 소자 사진 · notes.md 업로드 (또는 대시보드에서 GitHub 연동 후 직접 업로드)
- [ ] push 후 대시보드에 반영 확인 (1~2분)

## 결과

| Run ID | stress_GPa | mobility_gain_pct |
|---|---|---|
|  |  |  |

한 줄 소견:
