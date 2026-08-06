#!/usr/bin/env python3
"""
check_tasks.py — analysis/task_rules.yaml 규칙에 따라 파일 존재 여부를 확인하고
analysis/progress.json 의 체크박스를 자동으로 true 로 올린다.

★ false -> true 로만 움직인다. 이미 true 인 값(수동 체크 포함)은 절대 안 건드린다.
★ PR 승인·3인 교차대조가 필요한 P0 게이트 과제(#1,#3,#4,#5)는 task_rules.yaml에
  규칙이 없다 — 파일 하나 올렸다고 자동으로 "팀이 확인했다"고 처리하면 안 되기
  때문. 이 과제들은 대시보드에서 직접 체크할 것.

GitHub Actions(update-dashboard.yml)가 push 때마다 자동으로 실행한다.
직접 돌리려면:  python analysis/check_tasks.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "analysis" / "task_rules.yaml"
PROGRESS = ROOT / "analysis" / "progress.json"


def csv_has_rows(rel_path):
    """CSV가 존재하고 헤더 말고 데이터가 최소 1행 이상 있는지."""
    p = ROOT / rel_path
    if not p.exists():
        return False
    try:
        df = pd.read_csv(p, comment="#")
        return len(df) > 0
    except Exception:
        return False


def any_exists(paths):
    return any((ROOT / p).exists() for p in paths)


def main():
    if not RULES.exists():
        print("analysis/task_rules.yaml 없음 — 건너뜀")
        return 0
    if not PROGRESS.exists():
        print("analysis/progress.json 없음 — 건너뜀")
        return 0

    rules = (yaml.safe_load(open(RULES, encoding="utf-8")) or {}).get("rules", [])
    progress = json.load(open(PROGRESS, encoding="utf-8"))

    changed = []
    for r in rules:
        if r.get("enabled") is False or not r.get("owner"):
            continue
        n, owner = str(r["n"]), r["owner"]

        ok = False
        if "csv_has_rows" in r:
            ok = any(csv_has_rows(p) for p in r["csv_has_rows"])
        elif "any_exists" in r:
            ok = any_exists(r["any_exists"])

        if not ok:
            continue

        entry = progress.setdefault(n, {})
        if entry.get(owner) is not True:
            entry[owner] = True
            changed.append(f"#{n} {owner}")

    if changed:
        with open(PROGRESS, "w", encoding="utf-8", newline="\n") as f:
            json.dump(progress, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("자동 체크됨: " + ", ".join(changed))
    else:
        print("자동으로 새로 체크할 항목 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
