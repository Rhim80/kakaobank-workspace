#!/usr/bin/env bash
# wiring.py를 "실제로 도는 파이썬"으로 실행한다. 쓰는 법: bash .claude/skills/wiring/scripts/wiring.sh <명령> [인자…]
# 파이썬 이름은 OS마다 다르고(윈도우 python3는 Store 가짜) $PY 같은 변수 명령은 Claude Code 허용 규칙에 안 걸린다.
# 그래서 고정 문자열 한 줄로 부른다 — 파이썬 판정은 pick_python.sh 한 곳.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/pick_python.sh"
if [ -z "$PY" ]; then
  echo "오류: 실행되는 파이썬 3이 없습니다(python3·python·py 모두 안 돈다). setup-workspace 4단계의 설치 안내를 따르세요" >&2
  exit 1
fi
exec "$PY" "$here/wiring.py" "$@"
