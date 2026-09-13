# CLAUDE.md - Source of Truth

> **Source**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
> **Updated**: 2026-08-21 (v2.1.238) - `ANTHROPIC_DEFAULT_MODEL`·`CLAUDE_CODE_PROJECT_DIR_NAME`·`CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS` 추가·`CLAUDE_CODE_DISABLE_1M_CONTEXT` 적용 범위 확대·내장 "Concise" 출력 스타일·메모리 폴더 삭제 버그 수정·Cowork 외부 @-import 중단·피드백 설문 공유에 CLAUDE.md 포함 명시 반영
> **Purpose**: CLAUDE.md 작성 시 유일한 참조 문서

---

## 1. 개요

CLAUDE.md는 Claude Code가 세션 시작 시 자동 로드하는 설정 파일. 프로젝트 컨텍스트, 작업 규칙, 코드 스타일을 정의.

---

## 2. 전체 계층 구조 (Hierarchy)

Claude Code는 다음 순서로 메모리를 로드 (모두 병합됨):

| 우선순위 | 위치 | 용도 |
|---------|------|------|
| 1 (최상위) | Managed Policy | 조직 전사 강제 규칙 |
| 2 | `~/.claude/CLAUDE.md` | 개인 전역 설정 |
| 3 | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 프로젝트 설정 |
| 4 | `./.claude/rules/*.md` | 프로젝트 규칙 (자동 로드) |
| 5 | `~/.claude/rules/*.md` | 개인 전역 규칙 (자동 로드) |
| 6 | `./CLAUDE.local.md` | 로컬 전용 (gitignore 권장) |
| 7 | Auto Memory | 세션 간 자동 학습 기록 |

### Managed Policy (조직 전사)

조직 IT/DevOps가 관리하는 최상위 규칙. 개인 사용자가 변경 불가.

| OS | 경로 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

MDM, Group Policy, Ansible 등으로 배포.

### 버전 강제 managed settings (v2.1.163)

```json
{
  "requiredMinimumVersion": "2.1.150",
  "requiredMaximumVersion": "2.1.165"
}
```

**(v2.1.163)** Claude Code 버전이 허용 범위를 벗어나면 시작을 거부하고 승인된 버전으로 안내. 조직이 사용 버전을 통제할 때 사용.

### `allowAllClaudeAiMcps` managed setting (v2.1.149)

**(v2.1.149)** 엔터프라이즈용. `managed-mcp.json`과 함께 claude.ai 클라우드 MCP 커넥터를 로드.

---

## 3. Auto Memory (v2.1.32, 신규)

Claude가 세션 작업 중 자동으로 패턴, 명령어, 선호도를 기록하는 시스템.

### 저장 위치

```
~/.claude/projects/<project>/memory/
├── MEMORY.md           # 인덱스 (매 세션 첫 200줄 자동 로드)
├── debugging.md        # 토픽별 상세 노트
└── api-conventions.md  # Claude가 자동 생성
```

- `<project>`는 git 저장소 루트에서 파생
- git worktree는 별도 디렉토리
- git 외부는 작업 디렉토리 기준

### 동작

- **세션 시작**: `MEMORY.md` 첫 200줄만 자동 로드
- **토픽 파일**: startup 미로드, Claude가 필요할 때 on-demand 읽기
- **기록 방식**: Claude가 작업 중 자동 기록 또는 직접 지시 ("remember that we use pnpm")

### 제어

```bash
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1  # 비활성화
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0  # 활성화
```

`/memory` 커맨드로 파일 선택기 열기 가능 (CLAUDE.md + Auto Memory 포함). **(v2.1.216)** `/memory`가 GUI 에디터가 닫힐 때까지 대기하지 않도록 변경됨. GUI 에디터가 열려 있는 동안 터미널에 마우스/포커스 깨진 문자가 출력되던 버그도 수정.

### Worktree 간 공유 (v2.1.63)

프로젝트 설정과 auto memory가 같은 git 저장소의 모든 worktree에서 공유됨.

### 커스텀 메모리 디렉토리 (v2.1.74)

```json
{
  "autoMemoryDirectory": "/path/to/custom/memory"
}
```

`settings.json`에서 auto-memory 저장 위치를 변경 가능.

### 메모리 파일 타임스탬프 (v2.1.75, v2.1.214)

메모리 파일에 last-modified 타임스탬프가 추가되어, Claude가 최신/오래된 메모리를 구분 가능. **(v2.1.214)** 메모리 파일 frontmatter에 **ISO 형식 타임스탬프**가 추가됨. 또한 frontmatter 값이 인라인 `#`에서 잘리던 버그가 수정됨.

### MEMORY.md 크기 제한 (v2.1.83)

`MEMORY.md` 인덱스가 200줄 제한에 더해 **25KB 크기 제한**도 추가됨. 둘 중 먼저 도달하는 기준으로 잘림.

### MEMORY.md 인덱스 압축 알림·초과 에러 (v2.1.186, v2.1.210, v2.1.211)

**(v2.1.186)** `MEMORY.md` 인덱스가 크기 제한에 가까워지면 에이전트가 인덱스를 압축(compact)하도록 알림을 받음. **(v2.1.211)** 인덱스가 상한을 넘어설 때의 경고가 개선됨. **(v2.1.210)** 제한을 초과하는 메모리 쓰기는 **명시적 에러**를 발생시킴 (이전에는 조용히 실패).

### 팀 메모리 스토어 (v2.1.172)

**(v2.1.172)** 원격(remote) 세션에서 마운트된 팀 메모리 스토어를 메모리 recall이 찾지 못하던 버그 수정.

### 유휴 백그라운드 셸 메모리 압박 회수 (v2.1.193)

**(v2.1.193)** 메모리 압박 시 유휴(idle) 백그라운드 셸을 자동으로 회수(reaping). 장시간 세션에서 백그라운드 셸이 쌓여 메모리를 점유하는 것을 방지.

### 메모리 폴더 보호·외부 import (v2.1.228~v2.1.234)

- **(v2.1.228)** 세션 정리(cleanup)가 프로젝트의 memory 폴더 **내부 파일까지 지우던 버그** 수정
- **(v2.1.232)** Cowork 세션은 user 스코프 메모리 파일의 **외부 @-import를 더 이상 인라인하지 않음**
- **(v2.1.234)** 보안: 원격 파일 읽기·세션 복원·**CLAUDE.md include**·워크플로우 스크립트·파일 업로드가 Windows NT 네임스페이스(`\??\`) 경로를 거부 (NTLM 자격증명 유출 경로 차단)

---

## 4. @import 문법

외부 파일을 참조하여 CLAUDE.md를 모듈화:

```markdown
@30-knowledge/37-claude-code/skills-guide.md
@./docs/coding-standards.md
@~/.claude/my-project-instructions.md
```

### 규칙

- 상대 경로 또는 절대 경로 사용 가능
- 참조된 파일은 컨텍스트에 자동 포함
- Code span/code block 내 `@`는 import 처리 안 됨
- **Recursive import 최대 깊이: 5 hops**
- 외부 import 포함 프로젝트 첫 실행 시 **승인 다이얼로그** 표시
- 바이너리 파일(이미지, PDF)은 자동 제외

### HTML 주석 처리 (v2.1.72)

CLAUDE.md 내 HTML 주석(`<!-- ... -->`)은 자동 주입 시 Claude에게 숨겨짐. Read 도구로 직접 읽을 때는 보임. 내부 메모를 Claude에게 노출하지 않으면서 유지 가능.

### Worktree 환경 권장 패턴

```markdown
# CLAUDE.local.md에서 home directory import로 공유
@~/.claude/my-project-instructions.md
```

worktree마다 `CLAUDE.local.md`가 별도 존재하므로 home directory import 활용.

---

## 5. .claude/rules/ 자동 로드

`.claude/rules/` 내 모든 `.md` 파일 자동 로드. 서브디렉토리 재귀 탐색 지원.

```
.claude/
├── CLAUDE.md
├── rules/
│   ├── git.md
│   ├── security.md
│   ├── frontend/
│   │   └── react.md
│   └── backend/
│       └── api.md
└── settings.json
```

조건부 규칙은 [[rules-guide]] 참조.

---

## 6. --add-dir + CLAUDE.md 로딩 (v2.1.20)

`--add-dir`로 추가된 디렉토리의 CLAUDE.md와 rules도 로드 가능:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

로드 대상: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`

기본값은 비활성화. 환경변수 설정 필요.

### `/cd` 커맨드 (v2.1.169)

**(v2.1.169)** `/cd` 커맨드로 세션의 작업 디렉토리를 프롬프트 캐시를 깨뜨리지 않고 새 경로로 이동. 디렉토리 변경 시 해당 위치의 CLAUDE.md 인식과 함께 사용.

### `DirectoryAdded` 훅 (v2.1.219)

**(v2.1.219)** `/add-dir` 또는 SDK `register_repo_root` 컨트롤 요청으로 **세션 도중 새 작업 디렉토리가 등록된 뒤** 발화하는 `DirectoryAdded` 훅 추가. 디렉토리 추가에 맞춰 해당 위치의 CLAUDE.md·rules 로딩 후처리를 걸 때 사용.

---

## 7. 권장 포함 내용

### 필수

1. **프로젝트 개요**: 목적, 기술 스택
2. **폴더 구조**: 주요 디렉토리 설명
3. **코딩 규칙**: 스타일 가이드, 네이밍 컨벤션
4. **작업 규칙**: 파일 작업, Git, 보안 규칙

### 선택

- 사용자 프로필 / 작업 스타일
- 도구 설정 (MCP, 외부 도구)
- 자주 쓰는 명령어

---

## 8. settings.json과의 관계

| 항목 | CLAUDE.md | settings.json |
|------|-----------|---------------|
| 프로젝트 지침 | O | X |
| 코딩 스타일 | O | X |
| 도구 권한 | X | O |
| 모델 설정 | X | O |
| 환경 변수 | X | O |

**원칙**: 지침은 CLAUDE.md, 설정은 settings.json

### `/config` 영구 저장 (v2.1.119)

`/config`로 변경한 설정이 `~/.claude/settings.json`에 영구 저장됨. 우선순위는 project > local > policy 순으로 override. 이전에는 세션 한정이었으나 이제 재시작 후에도 유지.

### `claude project purge` (v2.1.126)

```bash
claude project purge [path]
```

해당 프로젝트의 모든 Claude Code state(세션, auto memory, 캐시)를 삭제. 프로젝트 정리 또는 fresh start에 유용.

### `CLAUDE_CODE_HIDE_CWD` (v2.1.119)

```bash
export CLAUDE_CODE_HIDE_CWD=1
```

시작 로고에서 작업 디렉토리를 숨김. 데모/녹화 시 경로 노출 방지.

### 세션 기본값 환경변수 (v2.1.223~v2.1.236)

- **(v2.1.236)** `ANTHROPIC_DEFAULT_MODEL` — 새 세션이 시작할 모델을 지정. `/model`로 고른 값이 이를 덮어쓰고 재시작 후에도 유지됨 (`ANTHROPIC_MODEL`과 다른 점)
- **(v2.1.234)** `CLAUDE_CODE_PROJECT_DIR_NAME` — 세션마다 자기 설정 디렉토리를 주는 호스트가 프로젝트별 트랜스크립트 디렉토리에 짧은 이름을 지정
- **(v2.1.233)** `CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS` — WebFetch 세션 URL 캐시 TTL 조정 (기본 15분은 그대로)
- **(v2.1.233)** `CLAUDE_CODE_TOOL_MEMORY_LIMIT` — Linux에서 Bash 도구 명령에 memory cgroup 적용(opt-in). 폭주하는 빌드가 세션을 멈추지 못하게 함
- **(v2.1.223)** `CLAUDE_CODE_DISABLE_1M_CONTEXT`가 **1M 네이티브 윈도우를 가진 모든 Claude 모델**을 auto-compaction으로 200K에 묶도록 확대(고정 목록이 아님). auto-compaction이 200K를 유지하지 못하면 시작 시 경고
- **(v2.1.223)** 인식되지 않는 모델 ID의 세션도 가정된 컨텍스트 윈도우 안에서 auto-compact됨. 이전 동작으로 되돌리려면 `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1`

### Prompt Cache TTL 제어 (v2.1.108~2.1.129)

- `ENABLE_PROMPT_CACHING_1H=1` (v2.1.108): API key/Bedrock/Vertex/Foundry에서 1시간 prompt cache TTL 활성화 (기존 `ENABLE_PROMPT_CACHING_1H_BEDROCK` deprecated)
- `FORCE_PROMPT_CACHING_5M=1`: 5분 TTL 강제
- `DISABLE_PROMPT_CACHING*` 설정 시 시작 경고 (v2.1.108)
- **(v2.1.129 수정)** 1시간 prompt cache TTL이 5분으로 다운그레이드되던 버그 수정
- **(v2.1.132 수정)** Bedrock/Vertex 400 errors with `ENABLE_PROMPT_CACHING_1H` 수정

---

## 9. 작성 팁

### 간결하게 유지

- 목표: 150줄 이하
- 상세 내용은 @import 또는 rules/ 활용
- 반복 방지: 한 곳에만 정의

### 명확한 규칙

```markdown
# Good
- **커밋 전**: `npm test` 실행 필수

# Bad
- 커밋 전에 테스트를 실행하면 좋을 것 같아요
```

### 주의사항

1. 민감정보 제외 (API 키, 비밀번호 절대 금지)
2. 경로 일관성 (팀 공유 시 상대 경로 권장)
3. CLAUDE.local.md는 .gitignore에 추가
4. 정기적으로 프로젝트 변화에 맞춰 갱신
5. **(v2.1.224)** 피드백 설문의 트랜스크립트 공유에 동의하면 마지막 요청의 모델 설정 — **CLAUDE.md 지침이 들어간 시스템 프롬프트**, 도구 정의, 모델 파라미터 — 도 함께 업로드됨. 비밀정보는 기존대로 redact되고, 공유가 너무 크면 이 필드들이 먼저 버려짐

### 시스템 프롬프트 / 모델 기본값 (v2.1.154, v2.1.197)

- **(v2.1.237)** 내장 **"Concise" 출력 스타일** 추가 — 서두와 진행 설명을 빼고 결과부터 말하되 작업 자체는 동일하게 수행. `/config`의 Output style에서 선택
- **(v2.1.238 수정)** 커스텀·프로젝트·플러그인 출력 스타일이 세션 도중 기본 목소리로 되돌아가던 버그 수정
- **(v2.1.219)** **Claude Opus 5**(`claude-opus-5`)가 기본 Opus 모델로 도입됨 — **1M 토큰 컨텍스트**, fast 모드 $10/$50 per Mtok. `/model` 피커의 병합된 Opus 행이 "Opus (1M context)"로 표시됨
- **(v2.1.197)** **Claude Sonnet 5**가 기본 모델로 도입됨 — **1M 토큰 컨텍스트**. 긴 CLAUDE.md/메모리/대화를 담을 여유가 커짐
- **(v2.1.196)** 조직 기본 모델(organization default models) 지원 — 관리자가 조직 전체의 기본 모델을 설정 가능. 함께 세션에 읽기 쉬운 기본 이름(readable default session names)이 부여됨
- **(v2.1.154)** Opus 4.8 출시. 기본 high effort, 가장 어려운 작업은 `/effort xhigh`
- **(v2.1.154)** **lean 시스템 프롬프트**가 Haiku/Sonnet/Opus 4.7 이전 모델을 제외한 모든 모델에서 기본값. 시스템 컨텍스트가 가벼워져 CLAUDE.md 등 사용자 지침의 상대 비중이 커짐
- **(v2.1.154)** Claude가 스스로 판단 가능한 경우 multiple-choice 질문을 자제하고 바로 진행 — 충분한 컨텍스트가 있으면 묻지 않음
- **(v2.1.149)** 마크다운 출력이 GFM task list 체크박스(`- [ ] todo` / `- [x] done`)를 일반 불릿이 아닌 체크박스로 렌더링. CLAUDE.md/메모리의 체크리스트 표시에 영향

### 알려진 수정

- **(v2.1.221)** 백그라운드 세션이 작업 보존을 위해 커밋·push할 때 **CLAUDE.md에 적힌 git 지침을 따름** (커밋 메시지 규약·브랜치 정책 등이 백그라운드 세션에도 적용). 필요한 작업일 때만 draft PR을 열고, 마지막에 작업물 위치를 항상 보고
- **(v2.1.222)** Remote Control 자동 시작을 **repo-local settings(`.claude/settings.json`·`.claude/settings.local.json`)에서 켤 수 없게 변경** — 끄는 것만 가능. 켜려면 `/config`에서 사용자 스코프로 설정
- **(v2.1.217)** `CLAUDE.md`(또는 `SKILL.md`)의 `paths` frontmatter에 brace 그룹(`{a,b}`)이 많으면 CLI가 시작 시 OOM/멈춤 발생하던 버그 수정 — brace 확장이 예산 제한(budget-bounded)됨
- **(v2.1.217)** 트랜스크립트 쓰기 실패(디스크 풀 등)나 상속된 환경변수로 세션 저장이 꺼진 경우 조용히 유실하는 대신 **경고 표시**
- **(v2.1.216)** 파일을 수정하는 훅 이후 `@`-mention이 아무것도 첨부하지 않던 버그 수정
- **(v2.1.101)** 인식되지 않는 hook 이벤트 이름에 대한 settings 내구성 개선 (설정 파일에 미래 hook 이벤트가 있어도 크래시하지 않음)
- **(v2.1.94)** `forceRemoteSettingsRefresh` 정책과 함께 기본 effort 수준이 medium에서 high로 변경 (API-key, Bedrock/Vertex/Foundry, Team, Enterprise)
- **(v2.1.90)** 도구 호출 중 CLAUDE.md 자동 로드 시 축소된 search/read 요약 배지가 fullscreen 스크롤백에서 여러 번 표시되던 버그 수정
- **(v2.1.88)** 긴 세션에서 중첩 CLAUDE.md 파일이 수십 번 재주입되는 버그 수정
- **(v2.1.86)** Read 도구가 compact line-number 포맷 사용 + 변경 없는 재읽기 중복 제거 (토큰 절약)

---

## Sources

- [Manage Claude's memory](https://code.claude.com/docs/en/memory)
- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## Related

- [[rules-guide]] - .claude/rules/ 상세 가이드
- [[skills-guide]] - Skills 시스템 가이드
- [[subagents-guide]] - Subagent 가이드

---

> **전체 변경 이력**: `~/.claude/cache/changelog.md` (버전별 CHANGELOG 원본)에서 관리. 이 문서는 현재 동작 상태(SoT)만 담으며 버전별 이력을 누적하지 않는다. 동기화 버전은 상단 `Updated` 표기 참조.
