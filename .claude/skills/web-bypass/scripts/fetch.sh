#!/usr/bin/env bash
# web-bypass thin wrapper — venv python으로 fetch.py 실행.
#
# 사용법:
#   bash scripts/fetch.sh <URL> [--save-to-pkm PATH] [--no-cache] [--ttl SEC]
#                              [--force] [--device auto|desktop|mobile]
#                              [--no-playwright] [--timeout N] [--max-attempts N]
#
# 종료 코드:
#   0  성공 (engine ok=True)
#   1  실패 (engine ok=False, blocked/페이월/네트워크 오류 등)
#   2  CLI 인자 오류
#   3  --save-to-pkm 경로 충돌 (--force 없이 덮어쓰기 시도)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 가상환경 파이썬 — Mac·Linux는 venv/bin/python, 윈도우는 venv/Scripts/python.exe
VENV_PY="$SKILL_DIR/scripts/venv/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="$SKILL_DIR/scripts/venv/Scripts/python.exe"

if [ ! -x "$VENV_PY" ]; then
  echo "ERROR: venv 미설치. 먼저 'bash $SKILL_DIR/scripts/install.sh' 실행." >&2
  exit 2
fi

exec "$VENV_PY" "$SKILL_DIR/scripts/fetch.py" "$@"
