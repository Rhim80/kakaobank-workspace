#!/usr/bin/env bash
# web-bypass 의존성 설치 (사용자 수동 실행)
#
# 사용법:
#   bash scripts/install.sh                    # venv + curl_cffi/bs4/pyyaml만
#   bash scripts/install.sh --with-playwright  # 위 + Playwright Chromium (~300MB)
#   bash scripts/install.sh --with-cloak       # 위 + CloakBrowser 스텔스 Chromium (~200MB)
#
# 멱등성: 기존 venv가 있으면 재생성하지 않고 pip install --upgrade만 수행.
#
# 라이선스 주의 (CloakBrowser):
#   wrapper 코드는 MIT, 상업적 사용 무료. 단 패치된 Chromium 바이너리는
#   재배포 금지(BINARY-LICENSE). 이 스크립트는 vendoring 하지 않고 pip
#   공식 채널에서 런타임 다운로드만 한다 — 라이선스상 "재배포 아님"으로 허용.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$SKILL_DIR/scripts"
VENV_DIR="$SCRIPTS_DIR/venv"
REQ_FILE="$SCRIPTS_DIR/requirements.txt"

WITH_PLAYWRIGHT=0
WITH_CLOAK=0
for arg in "$@"; do
  case "$arg" in
    --with-playwright) WITH_PLAYWRIGHT=1 ;;
    --with-cloak) WITH_CLOAK=1 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $arg" >&2
      exit 2
      ;;
  esac
done

# 라이선스 가드 (vendoring 표기 누락 방지)
if [ ! -f "$SKILL_DIR/LICENSE" ]; then
  echo "ERROR: $SKILL_DIR/LICENSE 누락. vendoring 출처 확인 필요." >&2
  exit 1
fi

# venv 생성 (없을 때만)
if [ ! -d "$VENV_DIR" ]; then
  # 파이썬을 부르는 이름은 OS마다 다르다 (윈도우 Git Bash엔 python3 가 없을 수 있다).
  # 이름만 보지 않고 실제로 실행해 "Python 3."이 나오는 것을 고른다 —
  # 윈도우에는 Microsoft Store를 여는 가짜 python3 스텁이 기본으로 깔려 있다.
  PYBOOT=""
  for c in python3 python py; do
    v=$("$c" --version 2>&1) || continue
    case "$v" in Python\ 3.*) PYBOOT="$c"; break ;; esac
  done
  if [ -z "$PYBOOT" ]; then
    echo "ERROR: 파이썬 3을 찾지 못했습니다." >&2
    echo "  Mac: brew install python / Ubuntu: sudo apt install python3 python3-venv" >&2
    echo "  윈도우: https://www.python.org/downloads/ — 설치 시 'Add python.exe to PATH' 체크" >&2
    exit 1
  fi
  echo "==> venv 생성: $VENV_DIR ($PYBOOT)"
  "$PYBOOT" -m venv "$VENV_DIR"
else
  echo "==> 기존 venv 사용: $VENV_DIR"
fi

# 가상환경 안 실행파일 폴더 — Mac·Linux는 bin, 윈도우는 Scripts.
# 이 스크립트에서 경로를 아는 자리는 여기 한 곳뿐이다.
VENV_BIN="$VENV_DIR/bin"
[ -d "$VENV_BIN" ] || VENV_BIN="$VENV_DIR/Scripts"
if [ ! -d "$VENV_BIN" ]; then
  echo "ERROR: venv 안에 실행파일 폴더가 없습니다 ($VENV_DIR/{bin,Scripts})." >&2
  exit 1
fi
# python3 가 아니라 python 을 쓴다 — 윈도우 venv에는 python3 라는 이름이 없다.

# pip 업그레이드
"$VENV_BIN/pip" install --quiet --upgrade pip wheel

# wheel 우선 설치 (curl_cffi 빌드 실패 회피)
echo "==> 의존성 설치 (wheel 우선)"
if ! "$VENV_BIN/pip" install --only-binary=:all: -r "$REQ_FILE"; then
  echo "WARN: wheel 전용 설치 실패. 소스 빌드로 재시도." >&2
  "$VENV_BIN/pip" install -r "$REQ_FILE"
fi

# 임포트 검증
echo "==> 의존성 임포트 검증"
"$VENV_BIN/python" -c "import curl_cffi, bs4, yaml; print('OK:', curl_cffi.__version__, bs4.__version__, yaml.__version__)"

# 옵션: Playwright Chromium
if [ "$WITH_PLAYWRIGHT" = "1" ]; then
  echo "==> Playwright Chromium 설치 (~300MB)"
  "$VENV_BIN/pip" install --quiet playwright
  "$VENV_BIN/playwright" install chromium
fi

# 옵션: CloakBrowser 스텔스 Chromium (Cloudflare/Turnstile/DataDome 챌린지 통과)
# pip 공식 채널 다운로드만 수행 — 바이너리 vendoring 안 함 (BINARY-LICENSE 준수).
if [ "$WITH_CLOAK" = "1" ]; then
  echo "==> CloakBrowser 설치 (pip cloakbrowser + 스텔스 Chromium 다운로드, ~200MB)"
  "$VENV_BIN/pip" install --quiet cloakbrowser
  # 바이너리 사전 다운로드 (공식 채널). 실패해도 첫 fetch 때 자동 다운로드되므로 비치명적.
  "$VENV_BIN/python" -c "from cloakbrowser import ensure_binary; ensure_binary()" \
    || echo "WARN: 바이너리 사전 다운로드 실패 — 첫 실행 시 자동 다운로드됩니다." >&2
  "$VENV_BIN/python" -c "import cloakbrowser; print('OK: cloakbrowser', cloakbrowser.__version__)"
fi

# 캐시 디렉토리
mkdir -p "$HOME/.cache/web-bypass"

echo ""
echo "설치 완료."
echo "  venv:   $VENV_DIR"
echo "  cache:  $HOME/.cache/web-bypass"
echo ""
echo "다음 단계:"
echo "  bash $SCRIPTS_DIR/fetch.sh \"https://news.ycombinator.com/item?id=1\""
