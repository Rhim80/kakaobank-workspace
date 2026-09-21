#!/usr/bin/env bash
# Common surface commands: resolve | daily | progress <path> | todo <command>.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/../skills/wiring/scripts/pick_python.sh"
if [ -z "$PY" ] || ! "$PY" -c 'import sys; assert sys.version_info >= (3, 9)' ; then
  echo "오류: Python 3.9 이상이 필요합니다. setup-workspace의 Python 안내를 따르세요." >&2
  exit 1
fi
if [ "${1:-}" = "todo" ]; then
  shift
  exec "$PY" "$here/../skills/todo/scripts/todo_store.py" "$@"
fi
exec "$PY" "$here/surfaces.py" "$@"
