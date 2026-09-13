#!/usr/bin/env bash
# 업스트림 fivetaku/insane-search 동기화
#
# vendored 영역(engine/, references/, LICENSE)만 갱신.
# scripts/, SKILL.md, README.md, NOTICE는 우리 자산이라 보존.
# CLI 시그니처가 바뀌면 fetch.py wrapper가 깨질 수 있으니 --help diff로 감지.

set -euo pipefail

SKILL=.claude/skills/web-bypass
HELP_OLD="$SKILL/.engine-help.txt"
HELP_NEW=$(mktemp)

if [ ! -d "$SKILL" ]; then
  echo "ERROR: $SKILL 미존재. 먼저 install 필요." >&2
  exit 1
fi

TMP=$(mktemp -d)
trap "rm -rf '$TMP' '$HELP_NEW'" EXIT

echo "==> upstream clone"
git clone --depth 1 https://github.com/fivetaku/insane-search "$TMP" 2>&1 | tail -3

NEW_SHA=$(cd "$TMP" && git rev-parse HEAD)
NEW_VER=$(grep '"version"' "$TMP/.claude-plugin/plugin.json" | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')

echo "==> rsync engine/ + references/ + LICENSE"
rsync -a --delete "$TMP/skills/insane-search/engine/" "$SKILL/engine/"
rsync -a --delete "$TMP/skills/insane-search/references/" "$SKILL/references/"
cp "$TMP/LICENSE" "$SKILL/LICENSE"

# rsync가 engine/을 pristine으로 덮어쓰므로, 로컬 개선분을 패치로 다시
# 덧입힌다: cloakbrowser 통합(executor.py + waf_profiles.yaml) +
# validators.py 오탐 수정(본문에 벤더명 있는 정상 페이지 challenge 오판 방지).
# 조용한 실패 금지: dry-run으로 검사 후 실패하면 명확히 경고하고 중단 신호.
PATCH_FILE="$SKILL/scripts/cloakbrowser.patch"
if [ -f "$PATCH_FILE" ]; then
  echo "==> cloakbrowser 패치 재적용"
  if ( cd "$SKILL/engine" && patch -p1 --forward --dry-run < "$PATCH_FILE" >/dev/null 2>&1 ); then
    ( cd "$SKILL/engine" && patch -p1 --forward < "$PATCH_FILE" >/dev/null )
    echo "    cloakbrowser 패치 적용 완료"
  else
    echo "" >&2
    echo "WARN: cloakbrowser.patch 적용 실패 — upstream이 executor.py/waf_profiles.yaml" >&2
    echo "      구조를 바꿨을 수 있습니다. cloakbrowser 챌린지 폴백이 사라진 상태입니다." >&2
    echo "      scripts/cloakbrowser.patch를 보고 수동 재적용 후 패치를 갱신하세요." >&2
  fi
else
  echo "INFO: cloakbrowser.patch 없음 — cloakbrowser 통합 재적용 생략"
fi

echo "fivetaku/insane-search@${NEW_SHA} v${NEW_VER} $(date +%Y-%m-%d) (renamed: web-bypass)" > "$SKILL/upstream.txt"

# CLI 시그니처 변경 감지 (fetch.py wrapper 영향)
SYNC_VENV_PY="$SKILL/scripts/venv/bin/python"
[ -x "$SYNC_VENV_PY" ] || SYNC_VENV_PY="$SKILL/scripts/venv/Scripts/python.exe"
if [ -x "$SYNC_VENV_PY" ]; then
  ( cd "$SKILL" && "$SYNC_VENV_PY" -m engine --help ) > "$HELP_NEW" 2>&1 || true
  if [ -f "$HELP_OLD" ]; then
    if ! diff -q "$HELP_OLD" "$HELP_NEW" > /dev/null 2>&1; then
      echo ""
      echo "WARN: engine CLI signature 변경 감지. fetch.py wrapper 검토 필요."
      echo "diff:"
      diff "$HELP_OLD" "$HELP_NEW" || true
    else
      echo "==> engine CLI signature 변화 없음"
    fi
  else
    echo "==> 첫 sync, baseline 저장"
  fi
  cp "$HELP_NEW" "$HELP_OLD"
else
  echo "INFO: venv 미설치, CLI signature 검사 생략"
fi

echo ""
echo "Sync 완료. upstream.txt:"
cat "$SKILL/upstream.txt"
