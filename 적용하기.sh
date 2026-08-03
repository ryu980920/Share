#!/usr/bin/env bash
# =====================================================================
#  업데이트 적용 스크립트
#  압축을 푼 뒤 Git Bash 에서:   bash 적용하기.sh
#  (지울 것 정리 → 커밋 → push 까지 한 번에)
# =====================================================================
set -u

cd "$(dirname "$0")" || exit 1

if [ ! -d .git ]; then
  echo "[중단] 여기는 git 저장소가 아니다."
  echo "       압축을 '레포 폴더 안'에 풀었는지 확인할 것."
  echo "       현재 위치: $(pwd)"
  exit 1
fi

if [ ! -f analysis/build.py ]; then
  echo "[중단] analysis/build.py 가 없다. 압축이 제대로 안 풀렸다."
  exit 1
fi

echo "== 1. 안 쓰는 파일 정리 =="
for p in analysis/extract.py analysis/merge.py runs/_template; do
  if [ -e "$p" ]; then
    git rm -r -q --cached "$p" 2>/dev/null
    rm -rf "$p"
    echo "   삭제: $p"
  fi
done
rm -rf analysis/__pycache__ analysis/figures analysis/grid.csv analysis/status.json 2>/dev/null

echo
echo "== 2. 변경 내용 =="
git add -A
git status --short
if git diff --staged --quiet; then
  echo "   바뀐 게 없다. 이미 적용된 상태."
  exit 0
fi

echo
echo "== 3. 커밋 & push =="
git commit -q -m "결과 공유 방식 변경: 스윕 CSV 한 장 + SWB 변수표 지원 + 담당자 이름 반영"
if git push; then
  echo
  echo "완료. 1~2분 뒤 대시보드 확인:"
  echo "   https://ryu980920.github.io/Share/"
else
  echo
  echo "[실패] push 가 안 됐다. 위 메시지를 확인할 것."
  echo "  - 인증 창이 떴다면 승인하고 'git push' 를 다시 실행"
  echo "  - 'rejected' 라면 'git pull --rebase' 후 'git push'"
  exit 1
fi
