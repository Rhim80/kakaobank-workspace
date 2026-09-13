#!/usr/bin/env bash
# 이 PC에서 자료가 들어올 수 있는 길을 있는 그대로 찍는다. 판단은 안 한다 — 읽는 건 사람과 Claude 몫.
# 0건과 "안 돌았다"를 구분하기 위해 각 검사는 실행 여부를 함께 찍는다.
set -u
echo "## claude mcp list"
if command -v claude >/dev/null 2>&1; then
  out=$(claude mcp list 2>&1); rc=$?
  printf '%s\n' "$out"
  [ $rc -ne 0 ] && echo "(주의) claude mcp list 종료 코드 $rc — 위 출력은 실패 메시지일 수 있다"
  if ! printf '%s' "$out" | grep -qE ' - '; then echo "(연결된 MCP 서버 0개 — 목록이 비었는지 명령이 실패했는지 위 출력으로 확인)"; fi
else
  echo "(claude 명령 없음 — Claude Code가 PATH에 없다. 이 검사는 돌지 않았다)"
fi
echo
echo "## CLI 도구"
for t in gws clasp gh glab jq python3 curl git; do
  if p=$(command -v "$t" 2>/dev/null); then echo "- $t: 있음 ($p)"; else echo "- $t: 없음"; fi
done
echo
echo "## gws 인증 (구글 시트·드라이브·메일)"
if command -v gws >/dev/null 2>&1; then
  gws auth status 2>&1 | head -5 || echo "(gws auth status 실패)"
else
  echo "(gws 없음 — 이 검사는 돌지 않았다)"
fi
echo
echo "## 프로젝트 .mcp.json"
if [ -f .mcp.json ]; then cat .mcp.json; else echo "(없음)"; fi
