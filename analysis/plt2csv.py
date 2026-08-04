#!/usr/bin/env python3
"""
plt2csv.py — ⚠ TODO: BCAT 프로젝트용 스크립트였고 지금은 안 맞는다.

BCAT 프로젝트는 SDevice 의 Id-Vg 곡선(.plt, "datasets = [...]" 형식)에서
매 Vg 지점의 전류를 읽어 long-format CSV 를 만드는 게 목적이었다.

이번 FinFET 프로젝트의 데이터는 그런 curve 가 아니라 격자점 하나당
stress_GPa / mobility_gain_pct 값 하나씩(wide format, analysis/build.py 참고)이라
이 스크립트를 그대로 쓸 수 없다.

★ Phase 0 에서 다음을 확인한 뒤 이 스크립트를 다시 써야 한다:
  1. Sentaurus Device 가 응력/이동도 값을 정확히 어떤 파일·형식으로
     출력하는지 (.plt 안의 특정 데이터셋인지, 로그 파일의 요약값인지,
     TDR 안의 필드 값을 SVisual 로 따로 뽑아야 하는지 등 — 미확인).
  2. 그 출력에서 analysis/config.yaml 의 stress.extraction_point /
     mobility.extraction_note 에 정의된 대표값을 어떻게 계산할지.

그 전까지는 build.py 의 wide-format CSV(run_id,stress_GPa,mobility_gain_pct)에
Sentaurus Workbench "Export Variables" 기능으로 직접 값을 뽑아 채우거나,
수동으로 로그 파일을 열어 값을 확인해서 넣는 방식으로 진행할 것
(★ 절대 값을 지어내지 말 것 — PROMPT.md 절대 규칙 1).
"""

import sys

if __name__ == "__main__":
    print(__doc__, file=sys.stderr)
    sys.exit(1)
