# .claude/rules/ - Source of Truth

> **Source**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
> **Updated**: 2026-08-21 (v2.1.238) - sandbox credential 마스킹 옵션 확장(`extract`·JWT·SigV4)·macOS 와일드카드 read-deny 우선 적용·sandbox 바이너리 override 승인 필요·GitLab 토큰 redaction·권한 다이얼로그 표기 일치·턴 중 `/permissions` 변경·Write 도구 read-before-write 완화·auto mode 분류기 기본값 통일 반영
> **Purpose**: .claude/rules/ 시스템 유일한 참조 문서

---

## 1. 개요

`.claude/rules/` 디렉토리는 CLAUDE.md를 여러 파일로 모듈화하여 관리. 모든 `.md` 파일이 자동 로드됨. 서브디렉토리도 재귀 탐색.

---

## 2. 기본 구조

```
your-project/
├── .claude/
│   ├── CLAUDE.md
│   └── rules/
│       ├── code-style.md
│       ├── testing.md
│       ├── security.md
│       ├── frontend/
│       │   └── react.md
│       └── backend/
│           └── api.md
```

---

## 3. 저장 위치 및 우선순위

| 위치 | 경로 | 적용 범위 |
|------|------|----------|
| 프로젝트 | `./.claude/rules/*.md` | 해당 프로젝트 |
| 사용자 | `~/.claude/rules/*.md` | 모든 프로젝트 |

**우선순위** (높음 -> 낮음):
1. Enterprise policy
2. 프로젝트 CLAUDE.md
3. 프로젝트 rules
4. 사용자 CLAUDE.md
5. 사용자 rules
6. CLAUDE.local.md

`paths` 필드가 없는 규칙은 모든 파일에 무조건 적용.

---

## 4. 조건부 규칙 (Path-Specific Rules)

YAML frontmatter로 특정 파일에만 규칙 적용 가능.

### 작동하는 형식

```markdown
---
globs: **/*.ts, src/**/*.tsx
---

# API 개발 규칙
- 모든 API 엔드포인트에 입력 검증 필수
```

### paths 필드 개선 (v2.1.84)

**(v2.1.84)** Rules와 Skills의 `paths:` frontmatter가 **YAML 리스트 형식**을 정식 지원:

```yaml
# v2.1.84부터 작동 - YAML 리스트
paths:
  - "src/**/*.ts"
  - "lib/**/*.tsx"

# 기존 방식도 계속 작동
globs: **/*.ts, src/**/*.tsx
```

**이전 버그 참고** (Issue #17204): v2.1.83 이전에는 YAML 배열 형식이 작동하지 않았음. v2.1.84에서 수정됨.

**현재 권장**: `paths:` YAML 리스트 또는 `globs:` CSV 형식 모두 사용 가능.

### 알려진 제한사항

1. **user-level paths 미작동**: `~/.claude/rules/`에서 `paths:` / `globs:` 조건부 로딩이 완전히 비작동 (Issue #21858, 미해결)
2. **세션 내 해제 안 됨**: 한 번 로드된 조건부 규칙은 다른 디렉토리로 이동해도 세션 내에서 계속 활성 (Issue #16299, 미해결)
3. **Git worktree 무시**: Worktree 내에서 paths/globs 필터링이 무시됨 (Issue #23569)
4. **(v2.1.69 수정)** print 모드(`claude -p`)에서 조건부 rules와 중첩 CLAUDE.md가 로드되지 않던 버그 수정됨
5. **(v2.1.198 수정)** 심링크 경로를 통한 `.claude/rules/` 조건부 규칙이 로드되지 않던 버그 수정됨. rules 디렉토리를 심링크로 공유하는 구성에서 조건부 규칙이 정상 적용.
6. **(v2.1.211 수정)** 중첩 `.claude/rules/*.md` 파일이 부적절하게 로드되던 버그 수정.

### Glob 패턴

| 패턴 | 매칭 대상 |
|------|-----------|
| `**/*.ts` | 모든 디렉토리의 TypeScript 파일 |
| `src/**/*` | src/ 하위 모든 파일 |
| `*.md` | 프로젝트 루트의 마크다운 파일 |
| `**/*.{ts,tsx}` | ts와 tsx 파일 모두 |
| `{src,lib}/**/*.ts` | src와 lib 디렉토리 |

---

## 5. --add-dir 디렉토리 rules 로딩 (v2.1.20)

추가 디렉토리의 rules도 로드 가능:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

공유 규칙 저장소를 여러 프로젝트에서 참조할 때 유용.

---

## 6. @import 활용

rules 파일에서 외부 문서 참조 가능:

```markdown
# Subagent 작성 규칙

@/path/to/official-docs/subagents-guide.md

## 추가 규칙
- 프로젝트 특화 규칙...
```

Recursive import 최대 깊이: 5 hops.

---

## 7. Symlink 활용

여러 프로젝트에서 공통 규칙 공유:

```bash
# 공유 rules 디렉토리 심링크
ln -s ~/shared-claude-rules .claude/rules/shared

# 개별 규칙 파일 심링크
ln -s ~/company-standards/security.md .claude/rules/security.md
```

순환 심링크는 자동 감지되어 안전하게 처리.

**(v2.1.89)** `Edit(//path/**)` 및 `Read(//path/**)` allow 규칙이 이제 심링크의 **해결된 대상 경로**(resolved symlink target)를 확인. 이전에는 요청 경로만 확인했으나, 이제 실제 파일 위치 기준으로 권한 매칭.

### Bash Permission 강화 (v2.1.97~2.1.101)

- **(v2.1.98)** 백슬래시 이스케이프된 플래그(`\-flag`)로 Bash 도구 권한 우회 방지
- **(v2.1.98)** 복합 Bash 명령어(`cmd1 && cmd2`)가 강제 권한 프롬프트를 우회하던 버그 수정
- **(v2.1.98)** 읽기 전용 명령어에 env-var 접두사가 있으면 안전한 것으로 알려진 경우에만 프롬프트 생략
- **(v2.1.98)** `/dev/tcp/...` 또는 `/dev/udp/...`로의 리다이렉트 시 프롬프트 표시
- **(v2.1.101)** `permissions.deny` 규칙이 PreToolUse 훅의 `permissionDecision: "ask"` 결정을 올바르게 오버라이드

### WSL 정책 상속 (v2.1.118)

`wslInheritsWindowsSettings` 정책 추가. WSL 환경에서 Windows side의 managed settings(보안 정책 포함)를 자동 상속.

```json
{
  "wslInheritsWindowsSettings": true
}
```

### Auto Mode 기본 리스트 확장 (v2.1.118)

`allow`/`soft_deny`/`environment` 리스트에 `"$defaults"` 토큰 사용 시 빌트인 기본 리스트를 그대로 유지하면서 사용자 항목 추가:

```json
{
  "permissions": {
    "allow": ["$defaults", "Bash(my-tool:*)"]
  }
}
```

### `blockedMarketplaces` 패턴 강제 (v2.1.119)

`blockedMarketplaces`의 `hostPattern`과 `pathPattern`이 정확히 enforce 되도록 수정. 이전에는 일부 패턴이 적용 안 되던 보안 버그 해결.

### `allowManagedDomainsOnly` (v2.1.126)

이 설정이 정확히 enforce 되도록 수정 — 관리되는 도메인 외에는 모든 외부 호출이 거부됨.

### In-project Path Allow Rules (v2.1.129)

`Edit(.claude/**)`, `Read(./src/**)` 등 프로젝트 내부 경로에 대한 allow rule이 honor 되도록 수정. 이전에는 일부 in-project 패턴이 무시되던 버그.

### `deniedMcpServers` Wildcard Scheme (v2.1.129)

```json
{
  "deniedMcpServers": ["http://*", "ws://*"]
}
```

스키마 wildcard로 차단 가능. URL prefix 패턴이 정확히 매칭되도록 수정.

### Server-managed Settings Policy (v2.1.129)

엔터프라이즈 사용자에게 server-managed settings policy가 정확히 적용되도록 수정. 이전에는 일부 케이스에서 적용 안 되던 버그.

### 병렬 Shell Tool 거부 처리 (v2.1.128)

병렬 shell tool calls에서 read-only 명령 하나가 실패하면 형제(sibling) 명령들도 자동 cancel. 이전에는 형제들이 계속 실행되던 동작.

### PowerShell Tool 권한 (v2.1.119, v2.1.126)

- **(v2.1.119)** PowerShell 명령이 permission mode에서 Bash와 동일하게 auto-approvable
- **(v2.1.126)** Windows에서 PowerShell이 primary shell로 인식 (Git Bash 부재 시)
- **(v2.1.126)** PowerShell tool에서 bare `--`가 stop-parsing flag로 mis-flag 되던 버그 수정

### 셸 Startup 파일 / 빌드 설정 쓰기 프롬프트 (v2.1.160)

- **(v2.1.160)** 셸 startup 파일(`.zshenv`, `.zlogin`, `.bash_login`)과 `~/.config/git/`에 쓰기 전 프롬프트 표시 — 의도치 않은 명령 실행 방지
- **(v2.1.160)** `acceptEdits` 모드에서도 코드 실행을 부여하는 빌드 도구 설정 파일에 쓰기 전 프롬프트: `.npmrc`, `.yarnrc*`, `bunfig.toml`, `.bazelrc`, `.pre-commit-config.yaml`, `.devcontainer/` 등

### Read-before-edit grep 완화 (v2.1.160, v2.1.144)

- **(v2.1.160)** `grep`/`egrep`/`fgrep` 단일 파일 명령이 read-before-edit 체크를 만족 — `grep`으로 파일을 본 후 별도 `Read` 없이 Edit 가능
- **(v2.1.144)** `head`/`tail` 파일 보기도 read-before-edit 체크를 만족. `egrep`/`fgrep`/`git grep`/`git diff`의 "no matches"(exit code 1)가 더 이상 명령 실패로 보고되지 않음

### WebFetch 권한 규칙 우선순위 (v2.1.162)

**(v2.1.162)** WebFetch 권한 규칙이 빌트인 preapproved 도메인에도 적용되도록 수정. 명시적 `WebFetch(domain:...)` deny/ask/allow 규칙이 preapproved-host 자동 허용보다 우선.

### `Tool(param:value)` 권한 문법 (v2.1.178)

**(v2.1.178)** 권한 규칙에서 도구 입력 파라미터를 매칭하는 `Tool(param:value)` 문법 추가. 도구의 특정 인자 값을 기준으로 allow/deny/ask 규칙 작성 가능.

### `Agent(type)` deny 규칙 (v2.1.186)

**(v2.1.186)** `Agent(type)` deny 규칙과 `Agent(x,y)` 제한이 named 서브에이전트 스폰에도 적용되도록 수정 (이전에는 named 서브에이전트 스폰 시 미적용).

### 와일드카드 매칭 수정 (v2.1.172)

- **(v2.1.172)** `WebFetch(domain:*.example.com)` 와일드카드가 서브도메인을 매칭하지 않던 버그 수정
- **(v2.1.172)** `Read(secrets-*/config.json)`처럼 패턴 중간에 와일드카드가 있는 규칙이 거부되던 버그 수정

### `$HOME` 경로 deny 규칙 (v2.1.163)

**(v2.1.163)** home 디렉토리 경로에 대한 deny 규칙(예: `Read(~/Desktop/**)`)이 `$HOME`을 통해 경로를 참조하는 Bash 명령도 차단하도록 수정.

### Deny 규칙 도구 이름 glob (v2.1.166)

**(v2.1.166)** deny 규칙의 도구 이름에 glob 패턴 사용 가능. 예: `mcp__*` 같은 패턴으로 여러 MCP 도구를 한 규칙으로 차단.

### `fallbackModel` 설정 (v2.1.166)

**(v2.1.166)** `settings.json`에 `fallbackModel` 설정 추가. 기본 모델을 사용할 수 없을 때 전환할 fallback 모델을 최대 3개까지 지정. 기존 단일 `--fallback-model` 플래그를 설정 파일에서 다중 지정으로 확장.

### thinking 비활성화 옵션 (v2.1.166)

**(v2.1.166)** 환경변수와 모델별 토글로 thinking을 비활성화하는 옵션 추가.

### hook `if` `$()`/`$VAR` 매칭 (v2.1.163)

**(v2.1.163)** hook `if: "Bash(...)"` 조건이 `$()`나 `$VAR`를 포함한 모든 Bash 명령에 잘못 발화하던 버그 수정 — 이제 subshell과 backtick 내부 명령에도 정확히 매칭.

### Windows 권한 규칙 / Read deny (v2.1.162)

- **(v2.1.162)** 백슬래시 표기(`~\`, `\\server\share`)나 대소문자 변형 경로로 작성된 Windows 권한 규칙이 매칭 안 되던 버그 수정
- **(v2.1.162)** Read deny 규칙이 Glob/Grep 결과에서 파일을 숨기도록 수정

### 데이터 유출 탐지 / 위험 경로 (v2.1.154)

- **(v2.1.154)** auto-mode classifier의 데이터 유출(특히 저장소 내용 대량 전송) 탐지 개선
- **(v2.1.154)** `HOME`에 trailing slash가 있을 때 `rm -rf $HOME`이 위험 경로로 차단 안 되던 버그 수정

### PowerShell `cd` 권한 우회 (v2.1.149)

- **(v2.1.149)** PowerShell 빌트인 `cd` 함수(`cd..`, `cd\`, `cd~`, `X:`)가 작업 디렉토리를 감지 없이 변경해 이후 명령이 워크스페이스 밖을 읽던 권한 우회 버그 수정
- **(v2.1.149)** git worktree에서 sandbox 쓰기 allowlist가 공유 `.git`만이 아닌 main 저장소 루트 전체를 덮던 버그 수정 (`hooks/`, `config`는 denied)
- **(v2.1.149)** PowerShell prefix/wildcard allow 규칙(예: `PowerShell(dotnet.exe build *)`)이 네이티브 실행 파일/스크립트를 사전 승인 안 하던 버그 수정
- **(v2.1.145)** 비-allowlist 환경변수에 대한 bare 변수 할당이 자동 승인되던 권한 프롬프트 우회 버그 수정

### Find Tool Allow Rule (v2.1.114) 재정의 — 보충

`Bash(find:*)` allow rule 하에서도 `find -exec`/`find -delete`는 자동 승인되지 않음. 필요 시 명시적 권한 부여. **(v2.1.120 보강)** `find` 명령이 file descriptor를 소진해 host가 죽던 버그가 수정됨 (macOS/Linux).

### `sandbox.credentials` — credential 파일 읽기 차단 (v2.1.187)

**(v2.1.187)** `sandbox.credentials` 설정 추가. 샌드박스 명령이 credential 파일(자격증명 파일)을 읽는 것을 차단한다. 민감한 인증 정보가 도구를 통해 유출되는 경로를 막는 용도.

### single-segment `dir/**` 규칙 정밀화 (v2.1.214)

- **(v2.1.214)** single-segment `dir/**` **allow 규칙**이 트리 어디든 중첩된 `dir` 디렉토리 쓰기를 자동 승인하던 버그 수정 — 이제 `<cwd>/dir`에서만 매칭
- **(v2.1.214)** single-segment `dir/**` **hook 조건**도 `<cwd>/dir`에만 매칭하도록 변경

### 추가 Bash/도구 권한 프롬프트 (v2.1.214~v2.1.238)

- **(v2.1.214)** `file` 명령에 `-m`/`-f` 플래그가 있으면 권한 요청 (안전하지 않은 옵션 실행 방지). 자동 승인되던 일부 `help`/`man` 명령의 안전하지 않은 옵션도 프롬프트 대상으로 조정
- **(v2.1.214)** 데몬 리다이렉트 플래그를 가진 `docker` 명령에 권한 프롬프트 추가
- **(v2.1.214)** Bash 권한 체크 정밀화: 파일 디스크립터 리다이렉트 형태 분석, 10,000자 초과 명령 판정, `[[ ]]` 내 zsh 변수 subscript 처리, Windows PowerShell 5.1 세션의 권한 우회 수정
- **(v2.1.216)** `&&` 리스트나 부정(negation) 안에 리다이렉트를 포함한 복합문의 Bash 권한 체크 수정
- **(v2.1.216)** Bash 명령의 non-ASCII 문자 파싱이 실제 셸 단어 경계와 일치하도록 수정
- **(v2.1.216)** 보이지 않는 유니코드 문자를 포함한 PowerShell 명령의 권한 검증 수정
- **(v2.1.216)** Windows에서 읽기 전용 명령이 네트워크 경로에 권한 프롬프트 없이 접근하던 버그 수정
- **(v2.1.221)** zsh가 `[[ ]]` 정규식 조건절 안에서 숨은 명령을 실행할 수 있던 **Bash 권한 체크 우회 수정** — 해당 명령은 이제 권한 프롬프트를 띄움
- **(v2.1.221)** Windows에서 따옴표 문자가 포함된 경로를 PowerShell 권한 체크가 잘못 처리하던 버그 수정 — 그런 경로는 이제 승인을 요구함
- **(v2.1.222)** 백그라운드 에이전트 작업(요약·compaction·이름 변경)에서 **PreToolUse 자동 허용 훅이 도구 제한을 우회**하던 버그 수정
- **(v2.1.228)** Write 도구가 **이번 세션에 읽지 않은 기존 파일도 최신 모델은 덮어쓸 수 있게** 변경 (Edit 도구 규칙과 동일). 구형 모델은 여전히 먼저 읽어야 함
- **(v2.1.229)** `/commit-push-pr`에서 위험 플래그(`--force`·`--amend`·`--no-verify` 등)를 쓰는 git·gh 명령이 **더는 자동 승인되지 않음**
- **(v2.1.234)** `/permissions`를 **Claude가 작업하는 도중에도 열 수 있음** — 규칙 변경이 현재 턴의 남은 부분부터 적용됨
- **(v2.1.235)** 권한 다이얼로그의 표시 문구와 "don't ask again" 옵션이 **실제 허용 범위와 항상 일치**하도록 수정. 내용을 전부 표시할 수 없으면 "don't ask again"을 제공하지 않음
- **(v2.1.238)** 셸 조건절의 zsh 고유 문법에 대한 Bash 도구 권한 체크 개선

### `sandbox.filesystem.disabled` 설정 (v2.1.216)

**(v2.1.216)** `sandbox.filesystem.disabled` 설정 추가 — 파일시스템 격리는 건너뛰되 네트워크 egress 제어는 유지.

### `sandbox.network.strictAllowlist` 설정 (v2.1.219)

**(v2.1.219)** `sandbox.network.strictAllowlist` 설정 추가 — 샌드박스 명령이 allowlist에 없는 호스트에 접근하면 **프롬프트 없이 거부**.

### credential 파일 마스킹 `mode: "mask"` (v2.1.221)

**(v2.1.221)** Linux·WSL의 샌드박스 credential 파일에 `mode: "mask"` 추가. 샌드박스 명령은 **센티널(가짜) 사본**을 읽고 — 파일 전체 또는 `extract` 정규식이 잡은 구간만 — 실제 값은 샌드박스 프록시가 egress 시점에 치환한다. macOS에서는 파일 마스킹이 `deny`로 폴백.

### sandbox credential 마스킹 옵션 확장 (v2.1.224)

**(v2.1.224)** credential 마스킹 옵션이 추가됨:

- `extract`·`onExtractNoMatch` — 구조화된 환경변수 값에서 마스킹할 구간을 정규식으로 지정하고, 매치가 없을 때의 처리를 정함
- `decode: "jwt"` + `maskClaims` — JWT를 해독해 지정한 claim만 마스킹
- `awsPairs`·`sigv4` — AWS SigV4 재서명

셋 다 `network.tlsTerminate`가 필요하며, **user·managed·`--settings`에서만** 반영된다 (프로젝트 설정으로 지정 불가).

### macOS 와일드카드 read-deny 우선 적용 (v2.1.236)

**(v2.1.236)** macOS에서 와일드카드 read-deny 규칙(`**/.env` 등)이 **허용된 읽기 영역 안에서도 우선**하고, 매치된 디렉토리의 내용까지 덮으며, **거부된 파일의 이름을 바꿔 우회할 수 없게** 됨.

### sandbox 바이너리 override·IPv6 표기 (v2.1.229, v2.1.232)

- **(v2.1.229)** 네트워크 도메인 목록의 IPv6 리터럴은 브래킷 표기(`[::1]:443`)를 쓰고, 모호한 표기는 **fail-closed**로 강제되며 `/doctor`가 표시함
- **(v2.1.232)** 서버 관리 설정이 sandbox 바이너리를 덮어쓰는 경우(`sandbox.bwrapPath`·`sandbox.socatPath`·`sandbox.ripgrep`) **승인을 요구**함. managed settings 승인 다이얼로그는 엔드포인트 URL을 표시하고, 텔레메트리 전용 변경은 문구를 명확히 하며, 통상 OpenTelemetry 옵션은 건너뜀
- **(v2.1.232)** `sandbox.ripgrep`은 **user·managed·`--settings`에서만** 반영 — 프로젝트 설정이 sandbox의 ripgrep 바이너리를 덮어쓸 수 없음

### GitLab 토큰 redaction·`glab` 보호 (v2.1.232)

**(v2.1.232)** GitLab 토큰 계열(`glrt-`·`gloas-`·`glptt-`·`glagent-`·`glimt-`·`glsoat-`·`glcbt-`·`glft-`·`glffct-`)에 대한 비밀 redaction 추가. 라우팅 가능한 `glpat-`·`gldt-` 토큰은 전체 redact. `glab` CLI 설정 저장소도 `gh`와 동일한 샌드박스·credential 경로 보호를 받음.

### 심링크 경유 쓰기/복원 차단 (v2.1.216)

- **(v2.1.216)** workflow 저장·scheduled-task 쓰기가 `.claude` 위치의 심링크를 따라가 프로젝트 밖으로 쓰이던 버그 수정
- **(v2.1.216)** `/rewind`가 추적 경로의 심링크·하드링크를 통해 파일을 복원/삭제하지 않으며, 건너뛴 경로 수를 보고

### Auto Mode 확장 (v2.1.193~v2.1.236)

- **(v2.1.236)** `Monitor` allow 규칙이 auto 모드가 켜진 동안에는 보류되어, Monitor 명령도 Bash 명령과 **같은 방식으로 심사**됨
- **(v2.1.236)** Bedrock·Vertex AI·Foundry에서, 그리고 텔레메트리를 껐을 때도 분류기가 **Claude API와 동일한 기본값**(severity 점수 기반 분류 포함)을 사용
- **(v2.1.236)** git status 체크가 저장소의 `status.showUntrackedFiles=no` 설정에 속아 "깨끗함"으로 보고하지 못하도록 수정
- **(v2.1.222)** 다른 에이전트 세션으로 보내는 `SendMessage` 메시지가 **발송 전 권한 분류기의 평가**를 받도록 변경
- **(v2.1.221)** 병렬 도구 호출의 권한 체크가 캐시 효율적으로 동작하고, 체크 대기 중 모드를 바꾸면 낡은 결과를 적용하지 않고 다시 프롬프트함. 캐시된 대화 prefix를 판정 간 재사용해 auto-mode 권한 체크의 prompt-cache 비용 절감
- **(v2.1.221)** 승인 프롬프트에서 "Permission mode changed while the auto-mode classifier call was queued" 반복 안내 제거
- **(v2.1.218)** 위험 `rm`·백그라운드 `&`·의심스러운 Windows 경로 체크가 **권한 다이얼로그를 열지 않고 auto-mode 분류기가 판정**하도록 변경
- **(v2.1.218)** plan 모드 + auto에서 정적 분석기가 read-only임을 증명 못 하는 Bash 명령도 프롬프트 대신 **auto-mode 분류기가 판정**
- **(v2.1.218)** 신뢰(trust) 다이얼로그가 승인 범위가 되는 **저장소 루트를 명시**하도록 개선. 서버 관리 설정의 무해한 기능/비용 토글은 설정 승인 프롬프트를 트리거하지 않음
- **(v2.1.216)** OAuth 토큰이 세션 중 만료/회전된 후 auto mode가 "HTTP 401" 분류기 에러로 명령을 거부하던 버그 수정
- **(v2.1.207)** Bedrock/Vertex/Foundry에서 **opt-in 없이** auto mode 사용 가능
- **(v2.1.210)** auto mode 권한 분류기(permission classifier)가 기본 **Sonnet 5**를 사용
- **(v2.1.210)** 지나치게 광범위한(overly broad) 권한 규칙에 대해 시작 시 경고 표시
- **(v2.1.211)** "always allow" 규칙을 저장소 루트에 저장하도록 변경
- **(v2.1.205)** auto mode에 트랜스크립트 파일 변조(tampering)를 차단하는 규칙 추가. 미해결 변수를 포함한 `rm -rf` 실행 전에 확인하도록 개선
- **(v2.1.193)** `autoMode.classifyAllShell` 설정 추가. auto-mode 거부 사유가 트랜스크립트와 `/permissions`에 기록됨

---

## 8. Best Practice

### DO

- 주제별 분리: 각 파일은 하나의 주제만 (testing.md, api-design.md)
- 명확한 파일명: 파일명만으로 내용 파악 가능
- 조건부 규칙은 `globs:` CSV 형식 사용
- 정기적 검토: 프로젝트 변화에 맞춰 갱신

### DON'T

- 모든 규칙을 조건부로 만들기
- 너무 세분화된 파일 구조
- 중복되는 규칙
- user-level rules에서 조건부 규칙 의존 (현재 미작동)

---

## 9. 일반적인 규칙 구성

| 파일 | 용도 |
|------|------|
| `code-style.md` | 코드 스타일, 포맷팅 |
| `testing.md` | 테스트 작성 컨벤션 |
| `security.md` | 보안 요구사항 |
| `git.md` | Git 워크플로우 |
| `api-design.md` | API 설계 원칙 |

---

## Sources

- [Manage Claude's memory](https://code.claude.com/docs/en/memory)
- [Issue #17204 - globs vs paths](https://github.com/anthropics/claude-code/issues/17204)
- [Issue #16299 - paths scope bug](https://github.com/anthropics/claude-code/issues/16299)
- [Issue #21858 - user-level paths](https://github.com/anthropics/claude-code/issues/21858)

## Related

- [[claude-md-guide]] - CLAUDE.md 가이드
- [[skills-guide]] - Skills 시스템 가이드

---

> **전체 변경 이력**: `~/.claude/cache/changelog.md` (버전별 CHANGELOG 원본)에서 관리. 이 문서는 현재 동작 상태(SoT)만 담으며 버전별 이력을 누적하지 않는다. 동기화 버전은 상단 `Updated` 표기 참조.
