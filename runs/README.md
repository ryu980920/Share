# runs/ — 시뮬레이션 결과

격자점 하나 = 폴더 하나. 폴더 이름이 곧 Run ID다.

```
runs/D36_N100/
  run.yaml      메타데이터        ★필수
  idvg.csv      원시 Id-Vg        ★필수
  metrics.csv   추출 지표         ★필수 (extract.py 가 생성. 손으로 만들지 않는다)
  plot.png      Id-Vg 플롯 (log 스케일)
  README.md     3줄 요약          ★필수
```

## 새 격자점 시작하기

```bash
cp -r runs/_template runs/D36_N100
# run.yaml 을 채운다
# Sentaurus 결과를 idvg.csv 로 변환한다 (analysis/plt2csv.py 참고)
python analysis/extract.py runs/D36_N100
```

## 자기 담당 격자점

`docs/ROLES.md` 의 격자표 참고.

- **A** — D24, D30 열 (10점) + 교차검증 `D36_N100`
- **B** — D36, D42 열 (9점) + 교차검증 `D24_N100`
- **C** — D48 열 (5점) + 모델/메쉬 실험 + 교차검증 `D42_N100`

## 규칙

- 남의 폴더를 건드리지 않는다.
- `.tdr`, `.plt` 원본은 커밋하지 않는다 (`.gitignore` 참고).
- 실패한 실행도 지우지 말고 `run.yaml` 의 `status: failed` 와 실패 이유를 남긴다.
  **실패 기록이 나중에 가장 유용하다.** 같은 벽에 두 번 부딪히지 않게 해준다.
