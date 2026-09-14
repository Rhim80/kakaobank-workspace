#!/usr/bin/env bash
# 이 PC의 상태를 있는 그대로 찍는다. 판단은 안 한다.
# 각 검사는 "안 됨"과 "안 돌았음"을 구분해 찍는다 — 0건은 성공처럼 보이기 때문.
set -u
echo "## 환경"
echo "- 날짜: $(date '+%Y-%m-%d %H:%M')"
echo "- OS: $(uname -s) $(uname -r) ($(uname -m))"
echo "- 셸: ${SHELL:-?}"
if command -v claude >/dev/null 2>&1; then echo "- Claude Code: $(claude --version 2>&1 | head -1)"; else echo "- Claude Code: 명령 없음(PATH에 claude 없음)"; fi
for t in node npm npx python3 git gws clasp gh; do
  if p=$(command -v "$t" 2>/dev/null); then v=$("$t" --version 2>&1 | head -1); echo "- $t: 있음 ($v)"; else echo "- $t: 없음"; fi
done
echo
echo "## claude mcp list (원문)"
if command -v claude >/dev/null 2>&1; then
  out=$(claude mcp list 2>&1); rc=$?
  printf '%s\n' "$out"
  echo "(종료 코드 $rc$( [ $rc -ne 0 ] && echo ' — 실패 메시지일 수 있음'))"
  printf '%s' "$out" | grep -qE ' - ' || echo "(서버 줄 0개 — 연결된 MCP가 없는 것인지 명령이 실패한 것인지 위 출력과 종료 코드로 본다)"
else
  echo "(claude 없음 — 이 검사는 돌지 않았다)"
fi
echo
echo "## 바깥 접근 (사내 망에서 나가는 길 — 각 5초 제한)"
echo "(응답 코드가 무엇이든 숫자가 나오면 연결은 된 것. '실패'만 막힌 것)"
for u in https://api.anthropic.com https://registry.npmjs.org https://pypi.org https://github.com; do
  code=$(curl -sS -o /dev/null -m 5 -w '%{http_code}' -I "$u" 2>&1) && echo "- $u: 응답 $code" || echo "- $u: 실패 ($code)"
done
echo
echo "## 워크스페이스"
echo "- 위치: $(pwd)"
echo "- 스킬 수: $(ls -d .claude/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "- 스킬 목록: $(ls -d .claude/skills/*/ 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"
if [ -f .mcp.json ]; then echo "- .mcp.json:"; sed 's/^/    /' .mcp.json; fi
echo "- 배선도 파일: $( [ -f 00-system/wiring/배선도.md ] && sed -n 's/^진행: //p' 00-system/wiring/배선도.md || echo '없음(배선도 그리기 전)')"
