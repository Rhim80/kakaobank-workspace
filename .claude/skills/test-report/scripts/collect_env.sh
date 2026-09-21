#!/usr/bin/env bash
# 이 PC의 상태를 있는 그대로 찍는다. 판단은 안 한다.
# 각 검사는 "안 됨"과 "안 돌았음"을 구분해 찍는다 — 0건은 성공처럼 보이기 때문.
# 연결 상태(mcp list·CLI·gws 인증·.mcp.json)는 wiring/scripts/check_lanes.sh 가 원본 — 여기 다시 적지 않는다.
set -u
echo "## 환경"
echo "- 날짜: $(date '+%Y-%m-%d %H:%M')"
echo "- OS: $(uname -s) $(uname -r) ($(uname -m))"
echo "- 셸: ${SHELL:-?}"
if command -v claude >/dev/null 2>&1; then echo "- Claude Code: $(claude --version 2>&1 | head -1)"; else echo "- Claude Code: 명령 없음(PATH에 claude 없음)"; fi
echo
LANES=.claude/skills/wiring/scripts/check_lanes.sh
if [ -f "$LANES" ]; then bash "$LANES"; else echo "## 연결 상태"; echo "(check_lanes.sh 없음 — wiring 스킬이 빠진 워크스페이스. 이 절은 돌지 않았다)"; fi
echo
echo "## 파이썬 가상환경 만들 수 있나 (데이터 스킬용)"
PYPICK=.claude/skills/wiring/scripts/pick_python.sh   # 파이썬 판정 원본
if [ ! -f "$PYPICK" ]; then echo "(pick_python.sh 없음 — 이 검사는 돌지 않았다)"
else
  . "$PYPICK"
  if [ -n "$PY" ]; then echo "- 파이썬: $PY ($PY_VER)"; "$PY" -c "import venv, ensurepip; print('- venv·ensurepip: 있음')" 2>&1 || echo "- venv·ensurepip: 없음(위 에러 참고 — setup-workspace의 .venv 단계가 막힌다)"
  else echo "- 실행되는 파이썬 없음 (python3·python·py 모두 안 돈다 — setup-workspace의 .venv 단계가 막힌다)"; fi
fi
echo
echo "## 바깥 접근 (사내 망에서 나가는 길 — 각 5초 제한)"
echo "(응답 코드가 무엇이든 숫자가 나오면 연결은 된 것. '실패'만 막힌 것. 막힌 호스트를 쓰는 스킬은 사내에서 안 돈다)"
# 윈도우 curl(Schannel)은 인증서 폐기 확인을 못 하면 CRYPT_E_NO_REVOCATION_CHECK로 실패한다 (2026-09-18 카뱅 윈도우 PC에서 대부분의 호스트가 이 에러).
# 폐기 확인만 끈다 — 연결 자체가 막힌 것은 그대로 실패로 나온다.
NOREVOKE=""; curl -V | head -1 | grep -qi schannel && NOREVOKE="--ssl-no-revoke"
probe() { code=$(curl $NOREVOKE -sS -o /dev/null -m 5 -w '%{http_code}' -I "https://$1" 2>&1 | tr '\n' ' '); case "$code" in [1-5][0-9][0-9]) echo "응답 $code";; *) echo "실패 (${code% 000})";; esac; }
echo "### 공통 (Claude Code · 구글 로그인 · 패키지 · 저장소)"
ANTH=""
for h in api.anthropic.com accounts.google.com oauth2.googleapis.com registry.npmjs.org pypi.org github.com; do r=$(probe $h); echo "- $h: $r"; [ "$h" = api.anthropic.com ] && ANTH="$r"; done
# 이 스크립트는 Claude Code 세션 안에서 돈다 — Claude Code는 지금 api.anthropic.com에 닿고 있다.
# 그런데 curl이 실패라고 하면 이 PC에서는 curl 검사 자체가 틀린 것이다. 아래 '실패'들을 막힘의 근거로 쓰지 않게 표시한다.
case "$ANTH" in 실패*) echo "(주의) api.anthropic.com이 실패로 나왔지만 Claude Code는 이 PC에서 돌고 있다 — 이 PC에서는 curl 검사를 믿을 수 없다. 아래 스킬별 '실패'는 막혔다는 근거가 아니다. curl: $(curl -V | head -1)";; esac
echo "### 스킬별 — 각 스킬의 scripts/ 안 코드가 실제로 부르는 호스트 (문서의 예시 주소 example.com 류는 뺌)"
SKIP='^(example\.com|spa-site\.com|protected-site\.com|infinite-scroll\.com|\.\.\.|www\.idpf\.org)$'
CACHE=$(mktemp)   # macOS 기본 bash(3.2)엔 연관배열이 없어 파일로 캐시 — 같은 호스트는 한 번만 찍는다
for d in .claude/skills/*/; do
  n=$(basename "$d"); [ "$n" = "test-report" ] && continue
  hosts=$(grep -rhoE 'https?://[A-Za-z0-9.-]+' "$d/scripts" 2>/dev/null | sed -E 's#^https?://##' | sort -u | grep -vE "$SKIP" || true)
  [ -z "$hosts" ] && continue
  line="- $n:"
  for h in $hosts; do
    r=$(grep -m1 "^$h	" "$CACHE" | cut -f2- || true)
    if [ -z "$r" ]; then r=$(probe "$h"); printf '%s\t%s\n' "$h" "$r" >> "$CACHE"; fi
    line="$line $h → $r ·"
  done
  echo "${line% ·}"
done
rm -f "$CACHE"
echo
echo "## 워크스페이스"
echo "- 위치: $(pwd)"
echo "- 스킬 수: $(ls -d .claude/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "- 스킬 목록: $(ls -d .claude/skills/*/ 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"
if [ -f "00-system/01-templates/kakaobank/일일-금리-마감실적-체크.md" ]; then echo "- 한글 파일명: 정상 (압축이 깨지지 않고 풀렸다)"; else echo "- 한글 파일명: 깨짐 또는 없음 — 00-system/01-templates/kakaobank/ 안 파일 이름을 아래에 붙인다"; ls 00-system/01-templates/kakaobank/ 2>&1 | sed 's/^/    /'; fi
echo "- 배선도 파일: $( [ -f 00-system/wiring/배선도.md ] && sed -n 's/^진행: //p' 00-system/wiring/배선도.md || echo '없음(배선도 그리기 전)')"
