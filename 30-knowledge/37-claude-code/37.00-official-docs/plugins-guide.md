# Claude Code Plugins - Source of Truth

> **Source**: claude-plugins-official marketplace (plugin-dev, plugins-reference), 실제 설치/운용 경험
> **Updated**: 2026-08-21 (v2.1.238) - 마켓플레이스 `headersHelper`(HTTP 헤더 발급 명령)·GitLab 마켓플레이스 지원·`archive`(HTTPS zip + SHA-256 pinning) 소스·`command` 소스와 `mode: "link"`·`additionalMarketplaces`/`allowedMarketplaces` 별칭·owner 와일드카드(`owner/*`)·bare `.claude/skills` 검증 반영
> **Purpose**: Plugin 개발/설치/관리 시 유일한 참조 문서. 이 파일이 source of truth.

---

## 1. Plugin 개요

**Plugin**은 Skills, Commands, Agents, Hooks, MCP Servers를 하나의 배포 가능한 패키지로 묶은 단위. 개인이 만든 자동화를 팀/조직에 배포하거나, 마켓플레이스에서 다른 사람이 만든 Plugin을 설치하여 사용할 수 있다.

### 핵심 특성

- `.claude-plugin/plugin.json` manifest 파일이 Plugin의 정체성을 정의
- 설치 한 줄로 Skills + Commands + Agents + Hooks + MCP를 일괄 적용
- 네임스페이스로 다른 Plugin/개인 스킬과 충돌 방지
- user / project / local 3가지 설치 스코프 지원
- Anthropic 공식 마켓플레이스 + 커뮤니티 마켓플레이스 지원

### Skills/Commands와의 관계

```
개인 Skill:   ~/.claude/skills/my-skill/SKILL.md        -> /my-skill
프로젝트 Skill: .claude/skills/my-skill/SKILL.md          -> /my-skill
Plugin Skill:  <plugin>/skills/my-skill/SKILL.md          -> /plugin-name:my-skill
```

Plugin은 기존 Skills/Commands의 상위 배포 레이어. 개별 파일들은 동일한 문법을 따르고, Plugin이 이를 패키징하여 네임스페이스와 배포 기능을 추가한다.

---

## 2. 디렉토리 구조

### 최소 구조 (Plugin으로 인식되기 위한 최소 요건)

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # 필수: manifest
└── (아무 컴포넌트 1개 이상)
```

### 표준 구조

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # 필수: manifest
├── commands/              # 슬래시 커맨드 (자동 발견)
│   ├── analyze.md         # -> /plugin-name:analyze
│   └── report/            # 하위 디렉토리 = 네임스페이스
│       └── weekly.md      # -> /plugin-name:weekly (plugin:plugin-name:report)
├── skills/                # 도메인 지식 (자동 로드)
│   └── my-domain/
│       ├── SKILL.md
│       ├── references/
│       └── examples/
├── agents/                # 자율 실행 에이전트
│   └── validator.md
├── hooks/                 # 이벤트 기반 자동화
│   └── hooks.json
├── servers/               # MCP 서버
│   └── .mcp.json
├── lib/                   # 공유 라이브러리/스크립트
│   └── utils.js
└── README.md
```

### 자동 발견 규칙

| 컴포넌트 | 위치 | 발견 시점 |
|----------|------|----------|
| Commands | `commands/*.md` | Plugin 로드 시 자동 등록 |
| Skills | `skills/*/SKILL.md` 또는 **루트 `SKILL.md` (v2.1.142+)** | Plugin 로드 시 자동 로드 |
| Agents | `agents/*.md` | Plugin 로드 시 자동 등록 |
| Hooks | `hooks/hooks.json` | Plugin 로드 시 자동 적용 |
| MCP | `servers/.mcp.json` | Plugin 로드 시 자동 연결 |

수동 등록 불필요. 정해진 디렉토리에 파일을 배치하면 Claude Code가 자동 인식한다. **v2.1.142부터** plugin의 루트 디렉토리에 `SKILL.md`만 두어도 스킬로 surfacing — 단일 스킬 전용 플러그인은 `skills/<name>/` 구조 없이 배포 가능.

**(v2.1.157)** `.claude/skills` 디렉토리에 있는 플러그인은 **마켓플레이스 없이 자동 로드**됨. `claude plugin init <name>`으로 `.claude/skills`에 새 플러그인 스캐폴드를 생성 가능.

---

## 3. plugin.json Manifest

### 필수 필드

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Plugin이 하는 일을 한 줄로 설명"
}
```

### 전체 필드

```json
{
  "name": "iloom-ax",
  "version": "1.0.0",
  "description": "일룸 AX 컨설팅 업무 자동화",
  "author": {
    "name": "일룸 DX팀",
    "email": "dx@iloom.com"
  },
  "homepage": "https://github.com/iloom/ax-plugin",
  "repository": "https://github.com/iloom/ax-plugin",
  "license": "MIT",
  "keywords": ["iloom", "ax", "automation"]
}
```

### 필드 설명

| 필드 | 필수 | 설명 |
|------|------|------|
| name | O | Plugin 이름 (kebab-case, 영문) |
| version | O | 시맨틱 버전 (major.minor.patch) |
| description | O | 한 줄 설명 |
| author | X | 작성자 정보 (name, email) |
| homepage | X | Plugin 홈페이지 URL |
| repository | X | Git 저장소 URL |
| license | X | 라이선스 종류 |
| keywords | X | 검색용 키워드 배열 |

---

## 4. 네임스페이스

Plugin 설치 후 모든 커맨드에 Plugin 이름이 prefix로 붙는다.

```
개인 스킬:        /analyze-review
Plugin 설치 후:   /iloom-ax:analyze-review
```

### 하위 디렉토리 네임스페이스

```
commands/
├── deploy/
│   ├── staging.md      # /staging (plugin:my-plugin:deploy)
│   └── prod.md         # /prod (plugin:my-plugin:deploy)
└── review/
    └── security.md     # /security (plugin:my-plugin:review)
```

`/help` 출력에서 `(plugin:plugin-name)` 또는 `(plugin:plugin-name:namespace)` 라벨로 표시된다.

### 충돌 방지

- 서로 다른 Plugin에 같은 이름의 커맨드가 있어도 네임스페이스로 구분
- 개인 스킬과 Plugin 스킬이 같은 이름이면, 개인 스킬은 `/name`, Plugin 스킬은 `/plugin-name:name`으로 분리
- **(v2.1.218)** `:`는 플러그인 네임스페이스 예약 문자 — 에이전트 마크다운 파일의 이름에 `:`가 포함되면 거부됨

---

## 5. 설치 스코프

| 스코프 | 명령어 | 영향 범위 | 사용 시점 |
|--------|--------|----------|----------|
| user | `/plugin install --scope user` | 내 모든 프로젝트 | 개인용 유틸리티 |
| project | `/plugin install --scope project` | 이 프로젝트의 모든 사용자 | 팀 표준 도구 |
| local | `/plugin install --scope local` | 내 로컬, 이 프로젝트만 | 테스트/실험 |

- **project 스코프**: `.claude/plugins/` 디렉토리에 설치. git으로 공유되므로 팀원 전원이 자동 적용
- **user 스코프**: `~/.claude/plugins/` 디렉토리에 설치. 개인 환경에만 적용
- **local 스코프**: 로컬에만, git에 포함되지 않음

---

## 6. Plugin 관리 명령어

### 설치/제거/리로드

```bash
# 마켓플레이스에서 설치
/plugin install <plugin-name>

# 특정 마켓플레이스 소스 등록
/plugin marketplace add <marketplace-url-or-org/repo>

# 마켓플레이스에서 설치 (소스 지정)
/plugin install <plugin-name>@marketplace

# 제거
/plugin uninstall <plugin-name>
```

**(v2.1.221)** `/plugin install`이 플러그인을 못 찾으면 바로 실패하지 않고 **낡은 마켓플레이스 카탈로그를 갱신한 뒤 재시도**한다.

**(v2.1.221)** `/plugin`에서 설치한 플러그인은 안전한 경우 **즉시 활성화**된다 (이전에는 항상 `/reload-plugins` 필요).

**(v2.1.232)** `/plugin install plugin@marketplace`가 **마켓플레이스를 먼저 갱신**한 뒤 설치 — 새로 게시된 플러그인을 수동 마켓플레이스 업데이트 없이 설치할 수 있다.

### 조회

```bash
# 설치된 Plugin 목록
/plugin list

# 활성/비활성 필터 (v2.1.163)
/plugin list --enabled
/plugin list --disabled

# Plugin 상세 정보
/plugin info <plugin-name>
```

### 로컬 상태 파일 직독 (`/plugin` UI 없이 확인·스크립트용)

- `~/.claude/settings.json` → `enabledPlugins`(활성 여부) · `extraKnownMarketplaces`(등록 소스)
- `~/.claude/plugins/installed_plugins.json` → 설치 경로·버전·스코프(user/project)
- `~/.claude/plugins/known_marketplaces.json` → `lastUpdated` = **카탈로그 신선도의 유일한 출처**
- `~/.claude/plugins/marketplaces/<이름>/.claude-plugin/marketplace.json` → 전체 카탈로그

마켓플레이스 클론에는 자체 `.git`이 없다 — `~/.claude` 저장소 안에 파일로 들어와 있어서 `git -C <마켓플레이스 경로> log`는 ~/.claude의 커밋(스킬 작업 이력)을 돌려준다. 이걸 갱신일로 읽지 말 것.

**(v2.1.163)** `/plugin list` 커맨드 추가 (`--enabled`/`--disabled` 필터). **(v2.1.157)** `/plugin` 인자 자동완성 추가: 서브커맨드, 설치된 플러그인 이름, 알려진 마켓플레이스의 플러그인.

**(v2.1.186)** `/plugin`의 Installed 탭에 "Skills" 섹션 추가 — 설치된 플러그인이 제공하는 스킬을 한눈에 확인. **(v2.1.172)** `/plugin`에서 마켓플레이스 플러그인을 둘러볼 때 검색 바(search bar) 추가.

### MCP 서버 CLI 인증 (v2.1.186, v2.1.181)

**(v2.1.186)** `claude mcp login <name>` / `claude mcp logout <name>` 커맨드 추가 — 인터랙티브 메뉴 없이 CLI에서 MCP 서버 인증/로그아웃 처리. **(v2.1.181)** MCP OAuth 브라우저 페이지를 Claude Code 비주얼 스타일에 맞추고 성공 시 자동 닫힘. **(v2.1.186)** `claude mcp get`/`remove`에 오타 제안 및 긴 서버 목록 truncation 추가.

### 활성화/비활성화

```bash
# 임시 비활성화 (제거하지 않고 끔)
/plugin disable <plugin-name>

# 다시 활성화
/plugin enable <plugin-name>
```

### 업데이트

```bash
# 최신 버전으로 업데이트
/plugin update <plugin-name>

# 세션 재시작 없이 변경사항 적용 (v2.1.69)
/reload-plugins
```

### `claude plugin init` (v2.1.157)

```bash
claude plugin init <name>   # .claude/skills에 새 플러그인 스캐폴드 생성
```

### `defaultEnabled: false` (v2.1.154)

```json
{
  "name": "my-plugin",
  "defaultEnabled": false
}
```

**(v2.1.154)** `plugin.json` 또는 마켓플레이스 항목에서 `defaultEnabled: false` 선언 가능. `/plugin` 또는 `claude plugin enable`로 활성화. 활성화된 플러그인의 dependency는 여전히 자동 활성화됨.

### `--scope` for marketplace remove (v2.1.153)

```bash
claude plugin marketplace remove <name> --scope user|project|local
```

**(v2.1.153)** `marketplace remove`가 `--scope`를 받도록 확장 (`marketplace add`, `install`, `uninstall`과 대칭).

### `skipLfs` 마켓플레이스 소스 옵션 (v2.1.153)

**(v2.1.153)** `github`/`git` 플러그인 마켓플레이스 소스에 `skipLfs` 옵션 추가 — clone/update 시 Git LFS 다운로드 건너뜀.

### `archive` 플러그인 소스 (v2.1.224)

**(v2.1.224)** `archive` 플러그인 소스 추가 — git이나 npm 없이 **HTTPS로 받은 zip**에서 플러그인을 설치한다. 선택적으로 **SHA-256 핀 고정** 가능.

### `command` 마켓플레이스 소스 (v2.1.229)

**(v2.1.229)** 마켓플레이스 `command` 소스 추가 — 로컬 명령(예: IDE)이 플러그인 디렉토리를 출력하면 **세션마다 다시 해석**되고 재시작 없이 반영된다. `mode: "link"`를 쓰면 복사하지 않고 그 자리에서 사용.

### GitLab 마켓플레이스 (v2.1.232)

**(v2.1.232)** 플러그인 마켓플레이스가 GitLab을 지원 — bare `gitlab.com` 저장소 URL(중첩 subgroup 포함)이 `github.com` URL처럼 clone된다. clone 인증 실패 힌트도 **실제 git 호스트 이름**을 말하도록 수정.

### `headersHelper` 인증 헤더 (v2.1.238)

**(v2.1.238)** url 마켓플레이스 또는 카탈로그 엔트리에 `headersHelper`를 두면, 그 명령이 카탈로그와 **동일 오리진 아카이브** fetch에 쓸 HTTP 헤더(예: 짧은 수명 토큰)를 발급한다.

- 카탈로그 엔트리의 `headersHelper`는 **그 플러그인을 설치·업데이트할 때만** 실행되고, 실행 전 명령이 화면에 표시됨
- `claude plugin install`·`claude plugin update`가 `[y/N]`로 확인 (`-y`로 생략)

### 마켓플레이스 설정 별칭·owner 와일드카드 (v2.1.223, v2.1.232)

- **(v2.1.223)** managed 설정 `strictKnownMarketplaces`·`blockedMarketplaces`에 **owner 와일드카드**(`"owner/*"`) 지원 — GitHub 조직 아래 모든 마켓플레이스 저장소를 한 번에 허용·차단
- **(v2.1.232)** `additionalMarketplaces`·`allowedMarketplaces`가 각각 `extraKnownMarketplaces`·`strictKnownMarketplaces`의 별칭으로 허용됨

### `claude plugin validate` 검사 확대 (v2.1.233)

**(v2.1.233)** `claude plugin validate`가 `.claude/skills` 디렉토리만 있는 경우도 검사해, frontmatter 파싱에 실패하는 `SKILL.md`를 보고한다.

### Context-aware 플러그인 추천 (v2.1.154, v2.1.152)

- **(v2.1.154)** `/plugin` Discover 탭이 현재 디렉토리의 relevance 신호와 일치하는 플러그인을 "suggested for this directory" 어노테이션으로 핀 고정
- **(v2.1.152)** `pluginSuggestionMarketplaces` managed setting: 관리자가 context-aware tip으로 추천 가능한 조직 마켓플레이스를 allowlist
- **(v2.1.187)** `/plugin`이 거의 쓰지 않는(underused) 설치 플러그인을 표면화해 정리(cleanup)를 유도
- **(v2.1.217)** frontend-design 플러그인 추천 팁이 평생 3회 노출로 제한 (이전에는 무한 반복)

### `--plugin-url` Direct Install (v2.1.129)

```bash
claude --plugin-url https://example.com/my-plugin.zip
```

마켓플레이스 등록 없이 `.zip` archive URL 직접 설치. 내부 배포/테스트 시 유용.

### `--plugin-dir` Zip Archive (v2.1.128)

```bash
claude --plugin-dir /path/to/my-plugin.zip
```

`--plugin-dir`이 디렉토리뿐 아니라 `.zip` 파일도 받도록 확장.

### `claude plugin prune` (v2.1.121)

```bash
claude plugin prune
```

다른 plugin의 dependency였으나 더 이상 참조되지 않는 orphaned plugins 제거.

### `claude plugin tag` (v2.1.118)

```bash
claude plugin tag
```

릴리스 git tag 생성 + version 검증. plugin 배포 워크플로우 자동화.

---

## 7. `${CLAUDE_PLUGIN_ROOT}` 환경 변수

Plugin 내부에서 파일 경로를 참조할 때 사용하는 특수 환경 변수. Plugin이 어디에 설치되든 올바른 경로로 확장된다.

### 사용법

```markdown
---
description: Plugin 스크립트 실행
allowed-tools: Bash(node:*)
---

분석 실행: !`node ${CLAUDE_PLUGIN_ROOT}/scripts/analyze.js`

템플릿 참조: @${CLAUDE_PLUGIN_ROOT}/templates/report.md

설정 로드: @${CLAUDE_PLUGIN_ROOT}/config/settings.json
```

### 확장 결과

```
${CLAUDE_PLUGIN_ROOT}/scripts/analyze.js
-> /home/user/.claude/plugins/my-plugin/scripts/analyze.js
```

### 필수 사용 규칙

```markdown
# 올바른 사용 (항상 CLAUDE_PLUGIN_ROOT 사용)
@${CLAUDE_PLUGIN_ROOT}/templates/foo.md

# 잘못된 사용 (상대 경로는 현재 디렉토리 기준이 됨)
@./templates/foo.md
```

Plugin 내부 파일을 참조할 때는 반드시 `${CLAUDE_PLUGIN_ROOT}`를 사용해야 한다. 상대 경로는 사용자의 현재 작업 디렉토리 기준으로 해석되어 오동작한다.

### `${CLAUDE_PLUGIN_DATA}` (v2.1.78)

Plugin 업데이트 후에도 유지되는 영구 상태 저장 경로:

```markdown
설정 저장: @${CLAUDE_PLUGIN_DATA}/user-config.json
```

- `/plugin uninstall` 시 삭제 여부 확인 프롬프트 표시
- Plugin 업데이트 시 데이터 보존

### Plugin-shipped Agent 확장 frontmatter (v2.1.78)

Plugin의 `agents/` 디렉토리에 포함된 에이전트에 추가 frontmatter 지원:

```yaml
---
name: my-agent
effort: medium
maxTurns: 50
disallowedTools: Bash, Write
---
```

### Plugin 사용자 설정 (v2.1.83)

Plugin manifest에 `userConfig` 옵션 지원. Plugin 활성화 시 사용자에게 설정 입력 요청:

```json
{
  "userConfig": {
    "api_key": {
      "description": "API key for the service",
      "sensitive": true
    }
  }
}
```

- `sensitive: true`: macOS keychain 또는 보호된 credentials 파일에 저장
- Plugin 활성화 시 설정 입력 프롬프트 표시

### `source: 'settings'` Plugin (v2.1.80)

settings.json에 Plugin 항목을 인라인으로 선언 가능:

```json
{
  "plugins": {
    "my-plugin": {
      "source": "settings",
      "path": "/path/to/plugin"
    }
  }
}
```

### `CLAUDE_CODE_PLUGIN_SEED_DIR` 다중 경로 (v2.1.79)

플랫폼 경로 구분자(Unix `:`, Windows `;`)로 여러 seed 디렉토리 지정 가능:

```bash
export CLAUDE_CODE_PLUGIN_SEED_DIR="/path/one:/path/two"
```

---

## 8. 공식 마켓플레이스 Plugin 목록

> 아래는 **발췌**다 — `anthropics/claude-plugins-official` 카탈로그는 278개(2026-08-05 기준: development 116 · productivity 49 · database 36 · monitoring 20 · security 17 …). 전체는 `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`.

### Development & Code Quality

| Plugin | 용도 | 주요 기능 |
|--------|------|----------|
| plugin-dev | Plugin 개발 | Skills/Commands/Agents/Hooks 생성 가이드 |
| claude-md-management | CLAUDE.md 정비 | `claude-md-improver` 스킬 = 코드베이스와 대조 감사 / `/revise-claude-md` 커맨드 = 세션 학습 회수 (둘은 용도가 다름) |
| code-review | 코드 리뷰 | 멀티 에이전트 리뷰 + 신뢰도 점수 |
| code-simplifier | 코드 리팩토링 | 기능 유지하며 코드 단순화 |
| feature-dev | 기능 개발 | E2E 기능 개발 워크플로우 |

### Git & Workflow

| Plugin | 용도 | 주요 기능 |
|--------|------|----------|
| commit-commands | Git 워크플로우 | /commit, /commit-push-pr |
| hookify | 자동화 규칙 | 대화 패턴에서 Hook 자동 생성 |

### Frontend & Design

| Plugin | 용도 | 주요 기능 |
|--------|------|----------|
| frontend-design | UI 개발 | 프로덕션급 UI, 제네릭 디자인 방지 |
| playground | 시각화 | 데이터 탐색, 디자인 플레이그라운드 |

### Learning & Guidance

| Plugin | 용도 | 주요 기능 |
|--------|------|----------|
| explanatory-output-style | 학습 | 코드 선택 이유를 교육적으로 설명 |
| learning-output-style | 인터랙티브 학습 | 의사결정 지점에서 사용자 참여 유도 |
| security-guidance | 보안 | 코드 편집 시 보안 이슈 경고 |

### Language Servers (LSP)

| Plugin | 언어 |
|--------|------|
| typescript-lsp | TypeScript/JavaScript |
| pyright-lsp | Python |
| gopls-lsp | Go |
| rust-analyzer-lsp | Rust |
| clangd-lsp | C/C++ |
| jdtls-lsp | Java |
| kotlin-lsp | Kotlin |
| swift-lsp | Swift |
| csharp-lsp | C# |
| php-lsp | PHP |
| lua-lsp | Lua |

### External Plugins (외부 서비스 연동)

| Plugin | 서비스 |
|--------|--------|
| supabase | Supabase DB/Auth |
| slack | Slack 메시지 |
| github | GitHub API |
| firebase | Firebase |
| stripe | Stripe 결제 |
| greptile | 코드베이스 검색 |

---

## 9. Plugin 만들기: Claude Code에게 요청

Plugin을 직접 손으로 만들 필요 없다. Claude Code에게 자연어로 요청하면 된다.

### 기본 요청

```
"내가 만든 VOC 분석 스킬이랑 리포트 커맨드를 iloom-ax라는 Plugin으로 만들어줘"
```

Claude Code가 처리하는 작업:
1. 디렉토리 구조 생성
2. plugin.json manifest 작성
3. 기존 스킬/커맨드 파일 복사 및 배치
4. README.md 생성

### plugin-dev Plugin 활용

공식 마켓플레이스의 `plugin-dev` Plugin을 설치하면 `/create-plugin` 커맨드를 사용할 수 있다.

```bash
/plugin install plugin-dev
/create-plugin "일룸 AX 업무 자동화 플러그인"
```

8단계 가이드 워크플로우로 진행:

| 단계 | 내용 |
|------|------|
| Phase 1 | Discovery: 요구사항 파악 |
| Phase 2 | Component Planning: 컴포넌트 구성 결정 |
| Phase 3 | Detailed Design: 상세 설계 + 질문 |
| Phase 4 | Structure Creation: 디렉토리 + manifest 생성 |
| Phase 5 | Implementation: 각 컴포넌트 구현 |
| Phase 6 | Validation: 품질 검증 |
| Phase 7 | Testing: 테스트 + 검증 |
| Phase 8 | Documentation: 문서화 + 배포 준비 |

### 조직 정책 관리

**(v2.1.83)** `managed-settings.d/` drop-in 디렉토리 지원. `managed-settings.json`과 함께 별도 팀이 독립적 정책 조각을 배포 가능 (알파벳 순 병합).

**(v2.1.84)** `allowedChannelPlugins` managed setting으로 팀/기업 관리자가 channel plugin allowlist 정의.

**(v2.1.85)** 조직 정책(`managed-settings.json`)으로 차단된 Plugin은 설치/활성화 불가, 마켓플레이스에서 숨김.

### Plugin bin/ 실행 파일 (v2.1.91)

Plugin이 `bin/` 디렉토리에 실행 파일을 포함할 수 있으며, Bash 도구에서 bare command로 직접 호출 가능:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── bin/
│   └── my-tool          # Bash에서 `my-tool` 로 직접 실행 가능
└── skills/
```

### Plugin Skills 이름 기반 호출 (v2.1.94)

Plugin manifest에서 `"skills": ["./"]`로 선언된 스킬이 frontmatter의 `name` 필드를 기반으로 호출됨. 디렉토리명이 아닌 명시적 이름으로 정확한 매칭. **(v2.1.216 수정)** `name` frontmatter 필드가 있는 plugin 스킬이 슬래시 커맨드 자동완성에서 plugin prefix를 잃던 버그 수정.

### Frontmatter 불리언 표기 (v2.1.218)

**(v2.1.218)** 스킬·플러그인 frontmatter의 불리언 필드에 `true`/`false` 외에 `yes`/`no`/`on`/`off`/`1`/`0` (대소문자 무관)도 허용됨.

### Plugin Hooks 개선 (v2.1.94~2.1.101)

- **(v2.1.94)** Plugin skill hooks가 YAML frontmatter에서 정의해도 무시되던 버그 수정
- **(v2.1.94)** `CLAUDE_PLUGIN_ROOT` 없이 plugin hooks가 "No such file or directory" 에러 발생하던 버그 수정
- **(v2.1.94)** `${CLAUDE_PLUGIN_ROOT}`가 local-marketplace plugin에서 잘못된 디렉토리로 확장되던 버그 수정
- **(v2.1.101)** `allowManagedHooksOnly` 설정에서도 plugin hooks가 정상 실행되도록 개선
- **(v2.1.101)** `/plugin` 및 `claude plugin update`에 마켓플레이스 새로고침 경고 추가

### Plugin MCP 서버 재동기화/재연결 수정 (v2.1.210, v2.1.211)

- **(v2.1.210)** re-sync 도중 plugin이 제공하는 MCP 서버가 강제 종료(torn down)되던 버그 수정. plugin 캐시 쓰기가 실패 시 임시 파일을 남기던 문제도 수정
- **(v2.1.211)** 유휴 웹 세션이 깨어난 뒤 plugin MCP 서버가 재연결되지 않던 버그, `--settings` 플래그로 활성화한 plugin이 로드되지 않던 버그 수정

### 번들 플러그인 커맨드 동작 변경 (v2.1.202~v2.1.222)

- **(v2.1.222)** **ultraplan 기능 제거**
- **(v2.1.221)** `/ultrareview` 에러 메시지 개선: 베이스와 히스토리를 공유하지 않는 저장소에서, 브랜치가 없는 체크아웃은 앞단에서 거부하고 브랜치 생성을 안내. 이미 완전한(complete) 클론에는 `git fetch --unshallow`를 더 이상 제안하지 않음
- **(v2.1.221)** 플러그인·조직 배포 스킬이 터미널 전용 빌트인(`/help`·`/feedback` 등)과 같은 이름이면 비대화형 세션에서 호출 불가하던 버그 수정. "Plugins changed" 알림이 리로드 후에도 남던 버그 수정
- **(v2.1.218)** `/code-review`가 **백그라운드 서브에이전트로 실행** — 리뷰 작업이 대화 컨텍스트를 채우지 않음. `/code-review ultra`가 non-interactive 세션에서 조용히 로컬 리뷰로 대체되던 버그 수정 — 이제 클라우드 리뷰를 실행
- **(v2.1.216~218)** `/ultrareview` 개선: "review my auth changes" 같은 서술형 인자 지원(현재 브랜치 리뷰 + 텍스트를 노트로 적용), 잘못된 인자에 대한 에러 피드백 개선, diff-too-large 에러가 설정된 한도·측정된 diff 크기·가장 큰 기여 파일을 표시
- **(v2.1.206)** `commit-commands`의 `/commit-push-pr`이 설정된 push remote로의 `git push`를 자동 허용
- **(v2.1.202)** `code-review`의 `/review <pr>`가 다시 **단일 패스(fast single-pass) 리뷰**로 복귀 (멀티 패스 아님). 상세 멀티 에이전트 리뷰는 `/code-review` 사용

### 백그라운드 모니터 (v2.1.105)

Plugin manifest에 최상위 `monitors` 키 지원. 세션 시작 또는 스킬 호출 시 자동으로 arm 되는 백그라운드 모니터를 정의할 수 있음.

### `experimental` Manifest 섹션 (v2.1.129)

`themes`와 `monitors`가 plugin manifest의 `"experimental"` 섹션 아래로 이동:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "experimental": {
    "themes": [...],
    "monitors": [...]
  }
}
```

이전 최상위 선언은 점진적으로 deprecated. 신규 plugin은 `experimental` 사용.

### Plugin Version Constraints Auto-update (v2.1.118)

Pinned plugin이 version constraint(예: `"^1.2.0"`) 만족하는 가장 높은 git tag로 자동 업데이트. `git pull`처럼 작동하되 SemVer 범위 내에서.

### Plugin 의존성 충돌 보고 (v2.1.111, v2.1.114)

- **(v2.1.111)** `plugin install`이 conflicting/invalid/overly complex version requirement를 구분해서 보고
- **(v2.1.114)** 이미 설치된 plugin과 dependency 버전 충돌 시 `range-conflict`로 정확히 보고 (이전에는 잘못 성공)

### PreCompact Hook 차단 (v2.1.105)

Plugin hooks의 `PreCompact` 이벤트에서 exit code 2 또는 `{"decision":"block"}` 반환으로 컨텍스트 압축 자체를 차단 가능.

### Package.json 의존성 자동 설치 (v2.1.105)

`package.json`과 lockfile을 포함한 마켓플레이스 플러그인 설치/업데이트 시 의존성이 자동 설치됨 (이전 버전 버그 수정).

### Policy-managed Plugin 자동 업데이트 (v2.1.108)

Policy로 관리되는 플러그인이 처음 설치된 프로젝트가 아닌 다른 프로젝트에서 실행되어도 자동 업데이트 되도록 수정.

### MCP Tool Result Size Override (v2.1.91)

MCP 도구 결과에 `_meta["anthropic/maxResultSizeChars"]` 어노테이션으로 최대 500K까지 결과 크기를 늘릴 수 있음. DB 스키마 등 대형 결과가 잘리지 않고 전달됨.

### 오프라인 마켓플레이스 캐시 보존 (v2.1.90)

`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` 환경변수: `git pull` 실패 시 기존 마켓플레이스 캐시를 유지. 오프라인 환경에서 유용.

### 유효성 검사 (v2.1.77)

```bash
claude plugin validate
```

Skill, Agent, Command frontmatter와 `hooks/hooks.json`을 검사하여 YAML 파싱 오류 및 스키마 위반을 감지.

**(v2.1.221)** 마켓플레이스명·플러그인명이 **Claude Desktop의 managed marketplace 동기화에서 거부될 이름**이면 경고를 표시. Desktop 배포 전에 이름을 고칠 수 있게 하는 용도.

**(v2.1.221)** `skills` 경로로 `"."`(플러그인 루트) 사용 가능. 루트에 `SKILL.md`를 둔 경우 나오던 검증 에러가 이제 플러그인 루트를 쓰라고 안내한다.

### 테스트

```bash
# 로컬에서 Plugin 테스트
cc --plugin-dir /path/to/my-plugin

# 또는 프로젝트의 .claude-plugin/ 디렉토리에 복사하여 테스트
```

---

## 10. 팀 배포 흐름

### 만드는 사람 (1회)

```
1. Claude Code에게 Plugin 생성 요청
2. 결과 확인 (폴더 구조, plugin.json)
3. GitHub 저장소에 push
```

### 사용하는 사람 (팀원)

```bash
# 1) 마켓플레이스 소스 등록
/plugin marketplace add org/repo

# 2) Plugin 설치
/plugin install plugin-name@marketplace
```

### 업데이트 배포

```
만드는 사람: 변경 후 GitHub push + version 올리기
사용하는 사람: /plugin update plugin-name
```

---

## 11. 코드베이스 -> Plugin 추천 매핑

| 상황 | 추천 Plugin |
|------|-------------|
| Plugin 개발하려는 경우 | plugin-dev |
| PR 기반 워크플로우 | commit-commands |
| 코드 리뷰 자동화 | code-review |
| React/Vue/Angular 프론트엔드 | frontend-design |
| 자동화 규칙 만들기 | hookify |
| TypeScript 프로젝트 | typescript-lsp |
| Python 프로젝트 | pyright-lsp |
| 보안 민감 코드 | security-guidance |
| 학습/온보딩 | explanatory-output-style |

---

## Related

- [[skills-guide]] - Skills 시스템 (Plugin의 하위 컴포넌트)
- [[subagents-guide]] - Subagent 가이드 (Plugin의 agents/ 컴포넌트)
- [[rules-guide]] - Rules 가이드 (Plugin의 hooks와 관련)
- [[claude-md-guide]] - CLAUDE.md 가이드
- [[claude-mem-plugin]] - 실제 설치·운용 중인 플러그인 사례 (메모리 플러그인)

---

> **전체 변경 이력**: `~/.claude/cache/changelog.md` (버전별 CHANGELOG 원본)에서 관리. 이 문서는 현재 동작 상태(SoT)만 담으며 버전별 이력을 누적하지 않는다. 동기화 버전은 상단 `Updated` 표기 참조.
