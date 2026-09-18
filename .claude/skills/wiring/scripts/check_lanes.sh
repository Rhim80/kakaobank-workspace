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
echo
echo "## 이 폴더에서는 안 켜지는 MCP (다른 폴더·다른 도구에 등록된 것)"
# claude mcp list 는 '모든 폴더 공통(user)' + '이 폴더' 등록만 보여준다.
# 다른 폴더에서 claude mcp add 로 등록한 것(기본값 local)과 오픈코드 설정의 MCP는 위 목록에 안 나온다.
# 이름과 등록 위치만 찍는다 — 토큰이 들어 있을 수 있는 env·headers 값은 찍지 않는다.
if command -v python3 >/dev/null 2>&1; then
python3 - <<'PY'
import json, os, re
cwd = os.path.realpath(os.getcwd())
home = os.path.expanduser("~")
found = 0
errors = 0
def load(path):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    if path.endswith(".jsonc"):
        t = re.sub(r'(?m)^\s*//.*$', '', t)
    return json.loads(t)
# 1) Claude Code: 다른 폴더에만 등록된 MCP (~/.claude.json 의 projects)
p = os.path.join(home, ".claude.json")
if os.path.isfile(p):
    try:
        d = load(p)
        for proj, v in (d.get("projects") or {}).items():
            names = list(((v or {}).get("mcpServers") or {}).keys())
            if not names:
                continue
            if os.path.realpath(proj) == cwd:
                continue  # 이 폴더 등록분은 claude mcp list 에 이미 나온다
            print(f"- [Claude Code · 다른 폴더] {proj}: {', '.join(names)}")
            found += 1
    except Exception as e:
        errors += 1
        print(f"(~/.claude.json 을 읽지 못했다: {e} — 이 검사는 돌지 않았다)")
else:
    print("(~/.claude.json 없음 — Claude Code 다른 폴더 등록 검사는 대상 없음)")
# 2) 오픈코드 설정
cands = [os.path.join(home, ".config", "opencode", n) for n in ("opencode.json", "opencode.jsonc", "config.json")]
cands += [os.path.join(cwd, n) for n in ("opencode.json", "opencode.jsonc")]
seen = False
for c in cands:
    if not os.path.isfile(c):
        continue
    seen = True
    try:
        names = list((load(c).get("mcp") or {}).keys())
        if names:
            print(f"- [오픈코드] {c}: {', '.join(names)}")
            found += 1
    except Exception as e:
        errors += 1
        print(f"({c} 을 읽지 못했다: {e} — 이 파일은 확인 안 됨)")
if not seen:
    print("(오픈코드 설정 파일 없음)")
if found == 0 and errors:
    print("(읽은 곳에서는 0개 — 위에서 못 읽은 파일이 있어 0개라고 판정할 수 없다)")
elif found == 0:
    print("(다른 폴더·오픈코드에 등록된 MCP 0개)")
else:
    print("→ 위 MCP는 이 워크스페이스 폴더의 Claude Code에서는 안 켜져 있다. 쓰려면 이 폴더에서 다시 등록하거나 '모든 폴더 공통'(claude mcp add -s user)으로 등록한다.")
PY
else
  echo "(python3 없음 — 이 검사는 돌지 않았다)"
fi
