#!/usr/bin/env bash
# 이 PC에서 자료가 들어올 수 있는 길을 있는 그대로 찍는다. 판단은 안 한다 — 읽는 건 사람과 Claude 몫.
# 0건과 "안 돌았다"를 구분하기 위해 각 검사는 실행 여부를 함께 찍는다.
# test-report/scripts/collect_env.sh 도 이 파일을 불러 쓴다 — 연결 상태는 여기 한 곳에만 적는다.
set -u
echo "## claude mcp list"
if command -v claude >/dev/null 2>&1; then
  TO=""; command -v timeout >/dev/null 2>&1 && TO="timeout 90"
  out=$($TO claude mcp list 2>&1); rc=$?
  printf '%s\n' "$out"
  [ $rc -eq 124 ] && echo "(90초 안에 끝나지 않아 끊었다 — 어느 서버가 응답이 없는지 위 출력까지로 본다)"
  [ $rc -ne 0 ] && [ $rc -ne 124 ] && echo "(주의) claude mcp list 종료 코드 $rc — 위 출력은 실패 메시지일 수 있다"
  if ! printf '%s' "$out" | grep -qE ' - '; then echo "(연결된 MCP 서버 0개 — 목록이 비었는지 명령이 실패했는지 위 출력으로 확인)"; fi
else
  echo "(claude 명령 없음 — Claude Code가 PATH에 없다. 이 검사는 돌지 않았다)"
fi
echo
echo "## CLI 도구"
for t in gws clasp gh glab jq curl git python3 node npm npx; do
  if p=$(command -v "$t" 2>/dev/null); then v=$("$t" --version 2>&1 | head -1); echo "- $t: 있음 ($p · $v)"; else echo "- $t: 없음"; fi
done
echo
echo "## gws 인증 (구글 시트·드라이브·메일)"
if command -v gws >/dev/null 2>&1; then
  gws auth status 2>&1 | grep -E "auth_method|token_valid|expires|email|error|Error|not (logged|auth)" \
    || echo "(gws auth status 출력에 인증 상태 줄이 없다 — 원문 앞 3줄: $(gws auth status 2>&1 | head -3 | tr '\n' ' '))"
else
  echo "(gws 없음 — 이 검사는 돌지 않았다)"
fi
echo
echo "## 프로젝트 .mcp.json"
if [ -f .mcp.json ]; then sed 's/^/    /' .mcp.json; else echo "(없음)"; fi
