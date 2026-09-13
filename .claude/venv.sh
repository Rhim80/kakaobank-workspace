# venv.sh — 파이썬 가상환경 활성화 (Mac · Linux · Windows Git Bash 공통)
#
# 쓰는 법 (워크스페이스 루트에서):
#   source .claude/venv.sh                                          # 기본 .venv
#   source .claude/venv.sh .claude/skills/web-bypass/scripts/venv    # 스킬 자체 venv
#
# 활성화 뒤에는 `python3`가 아니라 **`python`**을 쓴다.
# 윈도우 가상환경에는 python3 라는 이름이 없다 (python.exe만 있다).
#
# 가상환경 경로가 OS마다 다른 것(.venv/bin vs .venv/Scripts)을 여기 한 자리에서만 안다.
# 다른 문서·스크립트는 경로를 직접 적지 말고 이 파일을 부른다.

_VENV_TARGET="${1:-.venv}"

# 워크스페이스 루트를 기준으로 해석 — 하위 폴더에서 불러도 같은 곳을 가리키게
if [ -n "${BASH_SOURCE[0]:-}" ]; then
  _VENV_WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  case "$_VENV_TARGET" in
    /* | [A-Za-z]:*) ;;                                # 이미 절대경로
    *) [ -d "$_VENV_WS" ] && _VENV_TARGET="$_VENV_WS/$_VENV_TARGET" ;;
  esac
fi

if [ -f "$_VENV_TARGET/bin/activate" ]; then           # Mac · Linux
  . "$_VENV_TARGET/bin/activate"
elif [ -f "$_VENV_TARGET/Scripts/activate" ]; then     # Windows (Git Bash)
  . "$_VENV_TARGET/Scripts/activate"
else
  echo "ERROR: 가상환경이 없습니다 — $_VENV_TARGET" >&2
  echo "  워크스페이스 기본 환경이면: Claude에게 \"워크스페이스 세팅해줘\" 라고 하세요." >&2
  echo "  스킬 전용 환경이면: 그 스킬 SKILL.md의 설치 안내를 먼저 실행하세요." >&2
  unset _VENV_TARGET _VENV_WS
  return 1 2>/dev/null || exit 1
fi

# 활성화가 실제로 먹었는지 확인.
# 폴더 이름이 바뀐 뒤에도 남아 있는 가상환경은 activate 안에 옛 절대경로를 들고 있어서,
# 켜진 척만 하고 PATH는 없는 폴더를 가리킨다 — 그 뒤 모든 python 호출이 "command not found"로 죽는다.
if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: 가상환경을 켰는데 python이 없습니다 — $VIRTUAL_ENV" >&2
  echo "  이 워크스페이스 폴더가 다른 이름에서 옮겨졌을 때 생깁니다." >&2
  echo "  가상환경을 다시 만드세요 (워크스페이스 루트에서):" >&2
  echo "    rm -rf .venv && python3 -m venv .venv     # 윈도우 Git Bash는 python3 대신 python 또는 py -3" >&2
  echo "    source .claude/venv.sh" >&2
  echo "  그다음 쓰던 스킬의 SKILL.md 설치 안내를 다시 실행하세요." >&2
  unset _VENV_TARGET _VENV_WS
  return 1 2>/dev/null || exit 1
fi

unset _VENV_TARGET _VENV_WS
