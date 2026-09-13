# Claude Code Subagents - Source of Truth

> **Source**: [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)
> **Updated**: 2026-08-21 (v2.1.238) - 서브에이전트 fork 기본 활성화(전체 대화·프롬프트 캐시 상속)·인터랙티브 세션의 non-teammate 스폰 기본 백그라운드·세션당 200개 스폰 상한 제거·세션 간 `SendMessage`/`ListAgents`(다른 기계 포함)·`notify_when_idle`·워크플로우 fan-out prefix 시차·teammate 기본 모델 설정 제거(리더 모델 상속)·GitLab MR worktree 지원 반영
> **Purpose**: Subagent 작성 시 유일한 참조 문서

---

## 1. 개요

서브에이전트는 격리된 컨텍스트 윈도우에서 커스텀 시스템 프롬프트, 특정 도구 접근, 독립적 권한으로 작업을 처리하는 특화된 AI 어시스턴트.

### 핵심 특징

- 컨텍스트 보존: 탐색/구현 작업을 메인 대화와 분리
- 제약 강제: 서브에이전트별 도구 접근 제한
- 설정 재사용: 사용자 레벨로 프로젝트 간 공유
- 비용 절감: 빠른/저렴한 모델(Haiku)로 작업 라우팅
- 자동 위임: Description에 따라 Claude가 자동 호출

---

## 2. 기본 제공 서브에이전트

| 에이전트 | 모델 | 도구 | 목적 |
|---------|------|------|------|
| **Explore** | 상속 (Opus 상한) | 읽기 전용 | 빠른 코드베이스 검색 및 분석 |
| **Plan** | 상속 | 읽기 전용 | 계획 모드 중 리서치 |
| **General-purpose** | 상속 | 모든 도구 | 복잡한 다단계 작업 |
| **Bash** | 상속 | 터미널 | 명령어 별도 실행 |
| **statusline-setup** | Sonnet | 설정 도구 | 상태줄 설정 |
| **Claude Code Guide** | Haiku | 읽기 전용 | Claude Code 사용법 안내 |

---

## 3. 파일 구조

### 저장 위치 (우선순위 순)

| 우선순위 | 위치 | 적용 범위 |
|---------|------|----------|
| 1 | `--agents` CLI 플래그 | 현재 세션만 |
| 2 | `.claude/agents/` | 프로젝트 |
| 3 | `~/.claude/agents/` | 모든 프로젝트 |
| 4 | Plugin의 `agents/` | 플러그인 활성화된 곳 |

동일 이름 시 높은 우선순위 버전 적용.

---

## 4. YAML Frontmatter 전체 필드

```yaml
---
name: agent-name
description: When to use this agent and what it does
tools: Tool1, Tool2, Tool3
disallowedTools: Bash, Write
model: sonnet
skills: skill-1, skill-2
permissionMode: acceptEdits
memory: project
background: false
isolation: worktree
mcpServers: server-1, server-2
maxTurns: 50
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check.sh"
---
```

### 필드 상세

| 필드 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `name` | 권장 | 파일명 | 소문자, 하이픈만. 에이전트 고유 식별자. **(v2.1.218)** `:` 포함 이름은 거부됨 (`:`는 플러그인 네임스페이스 예약 문자). |
| `description` | 권장 | - | Claude가 언제 이 에이전트를 사용할지 판단 기준. |
| `tools` | - | 모든 도구 | 허용 목록 (allowlist). 쉼표 구분. |
| `disallowedTools` | - | 없음 | 거부 목록 (denylist). `tools`와 배타적 사용. |
| `model` | - | sonnet | `sonnet`, `opus`, `haiku`, `'inherit'` |
| `skills` | - | 없음 | 프리로드할 Skills. 전체 콘텐츠가 시작 시 주입됨. |
| `permissionMode` | - | default | 권한 동작 방식 (아래 참조). |
| `memory` | - | 없음 | **(신규 v2.1.33)** 세션 간 지속 메모리 스코프. |
| `background` | - | false | **(신규 v2.1.49)** `true`: 항상 백그라운드 실행. |
| `isolation` | - | 없음 | **(신규 v2.1.49)** `worktree`: 임시 git worktree 격리 실행. |
| `mcpServers` | - | 없음 | **(문서화됨)** 사용할 MCP 서버 지정. |
| `maxTurns` | - | 없음 | **(문서화됨)** 최대 에이전틱 턴 수 제한. |
| `hooks` | - | 없음 | 에이전트 라이프사이클 훅. |
| `initialPrompt` | - | 없음 | **(v2.1.83)** 에이전트 시작 시 자동 제출할 첫 턴 프롬프트. |
| `effort` | - | 없음 | **(v2.1.78)** Plugin-shipped 에이전트의 노력 수준. |

### tools vs disallowedTools

| 방식 | 설명 | 사용 시점 |
|------|------|----------|
| `tools` | 허용 목록 (allowlist) | 소수 도구만 허용 |
| `disallowedTools` | 거부 목록 (denylist) | 대부분 허용, 일부 제외 |

두 필드를 동시에 사용하지 않음.

### permissionMode

| 모드 | 설명 |
|------|------|
| `default` | 각 작업에 사용자 확인 |
| `acceptEdits` | 파일 편집 자동 승인 |
| `dontAsk` | 모든 작업 자동 승인 |
| `bypassPermissions` | 모든 권한 우회 |
| `plan` | 계획 모드에서 실행 |

`dontAsk`, `bypassPermissions`는 신뢰할 수 있는 환경에서만 사용.

**(v2.1.200)** 인터페이스 표기상 `default` 권한 모드의 이름이 **"Manual"**로 변경됨 (설정 값 `default`는 동일, 표시명만 변경). 또한 `AskUserQuestion` 다이얼로그가 기본적으로 자동 진행(auto-continue)하지 않도록 변경됨.

### memory (v2.1.33, 신규)

세션 간 지속 메모리. 에이전트가 학습한 패턴, 디버깅 인사이트 등을 축적.

```yaml
memory: project    # 프로젝트 스코프
memory: user       # 사용자 전역 스코프
memory: local      # 로컬 스코프
```

### Monitor Tool (v2.1.98)

`Monitor` 도구 추가: 백그라운드 스크립트의 이벤트를 스트리밍으로 수신. 백그라운드 에이전트/태스크의 진행 상황을 실시간으로 추적하는 데 유용.

### MCP `alwaysLoad` 옵션 (v2.1.121)

서브에이전트/메인 세션 모두에 적용되는 MCP 서버 설정:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"],
      "alwaysLoad": true
    }
  }
}
```

`alwaysLoad: true` 설정 시 lazy load가 아닌 즉시 연결. 항상 사용하는 서버에 유용.

### MCP `workspace` 예약명 (v2.1.128)

MCP 서버 이름으로 `workspace`는 더 이상 사용 불가 (예약어). 기존 설정에 `workspace`라는 서버명이 있다면 다른 이름으로 변경 필요.

### Subagent MCP 병렬 재구성 (v2.1.119)

Subagent의 MCP reconfiguration이 직렬에서 **병렬 연결**로 변경되어 시작 시간 단축.

### background (v2.1.49, 신규)

```yaml
background: true   # 항상 백그라운드에서 실행
```

### isolation (v2.1.49, 신규)

```yaml
isolation: worktree  # 임시 git worktree에서 격리 실행
```

- 변경사항 없으면 worktree 자동 정리
- 변경사항 있으면 worktree 경로와 브랜치 반환

### Task(agent_type) 스폰 제한 (v2.1.33, 신규)

에이전트가 스폰할 수 있는 서브에이전트를 화이트리스트로 제한:

```yaml
tools: Task(worker, researcher), Read, Write
```

`claude --agent`로 실행되는 에이전트에만 적용.

---

## 5. Hooks

### 이벤트 유형

| 이벤트 | 매처 | 설명 |
|--------|------|------|
| `PreToolUse` | 도구 이름 | 도구 실행 전 |
| `PostToolUse` | 도구 이름 | 도구 실행 후 |
| `Stop` | 없음 | 에이전트 종료 시 |
| `post-session` | - | **(v2.1.169)** self-hosted runner용. 워크스페이스 삭제 전 작업을 스냅샷할 수 있게 세션 종료 후 실행. |
| `SubagentStart` | 에이전트 이름 | 서브에이전트 시작 시 (프로젝트 레벨) |
| `SubagentStop` | 에이전트 이름 | 서브에이전트 완료 시 (프로젝트 레벨) |
| `TeammateIdle` | - | **(신규 v2.1.33)** Agent Teams용. exit 2로 작업 계속 강제. |
| `TaskCompleted` | - | **(신규 v2.1.33)** 태스크 완료 시. exit 2로 차단 및 피드백. |
| `WorktreeCreate` | - | **(v2.1.50)** isolation worktree 생성 시. |
| `WorktreeRemove` | - | **(v2.1.50)** isolation worktree 삭제 시. |
| `PermissionDenied` | - | **(v2.1.88)** auto mode 권한 거부 후. `{retry: true}` 반환 가능. |
| `TaskCreated` | - | **(v2.1.84)** `TaskCreate`로 태스크 생성 시. |
| `CwdChanged` | - | **(v2.1.83)** 작업 디렉토리 변경 시 (예: direnv 연동). |
| `FileChanged` | - | **(v2.1.83)** 파일 변경 감지 시. |
| `StopFailure` | - | **(v2.1.78)** API 에러(rate limit, auth 실패 등)로 턴 종료 시. |
| `PostCompact` | - | **(v2.1.76)** 컨텍스트 압축 완료 후. |
| `InstructionsLoaded` | - | **(v2.1.69)** CLAUDE.md / rules 로드 시. |
| `Elicitation` | - | **(v2.1.76)** MCP 서버가 구조화된 입력을 요청할 때. |

### Hook 동작

- exit code `0`: 통과
- exit code `2`: 작업 차단 (stderr 메시지 표시)
- 입력은 stdin으로 JSON 형식 전달
- **(v2.1.69)** `agent_id` (서브에이전트) 및 `agent_type` (서브에이전트 + `--agent`) 필드가 훅 이벤트에 포함
- **(v2.1.85)** `if` 필드: 조건부 실행. permission rule 문법 사용 (예: `Bash(git *)`). **(v2.1.89 수정)** compound commands 및 env-var 접두사 매칭 정상화.
- **(v2.1.88)** PreToolUse/PostToolUse에서 Write/Edit/Read의 `file_path`가 절대 경로로 제공
- **(v2.1.85)** `PreToolUse` 훅이 `AskUserQuestion`에 `updatedInput` + `permissionDecision: "allow"` 반환 가능 (headless 연동)
- **(v2.1.89)** `PreToolUse` 훅에서 `permissionDecision: "defer"` 반환 가능. Headless 세션에서 도구 호출 일시 중지 후 `-p --resume`으로 재개.
- **(v2.1.119)** Hook에 `duration_ms` 필드 제공 — 도구 실행에 걸린 시간 (prompt/PreToolUse 처리 시간 제외)
- **(v2.1.121)** PostToolUse hook이 `updatedToolOutput` 필드로 도구 출력을 **재작성/대체** 가능. 사후 가공/필터링 워크플로우에 유용
- **(v2.1.145)** Stop/SubagentStop hook 입력에 `background_tasks` 및 `session_crons` 필드 포함
- **(v2.1.163)** Stop/SubagentStop hook이 `hookSpecificOutput.additionalContext`를 반환하여 Claude에게 피드백을 주고 턴을 계속 진행 가능 (hook 에러로 처리되지 않음)
- **(v2.1.143)** Stop hook이 반복 차단 시 무한 루프 방지: 8회 연속 차단 후 경고와 함께 턴 종료 (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`로 재정의)
- **(v2.1.139)** Hook `args`가 exec form 지원 — 셸 escaping 없이 호출 가능
- **(v2.1.214)** exit code 2 hook의 stdout JSON이 검증에 실패해도 차단(block)이 무시되지 않도록 수정 (이전에는 JSON 파싱 실패 시 차단이 유실됨)
- **(v2.1.214)** SessionStart hook이 fork로 시작된 세션에서 source를 `"fork"`로 올바르게 보고
- **(v2.1.218)** 에이전트 frontmatter의 `hooks`는 **에이전트 파일이 있는 폴더가 워크스페이스 신뢰(trust)를 승인받은 경우에만 실행** — 신뢰되지 않은 폴더의 에이전트 훅 실행 차단

### HTTP Hooks (v2.1.63)

셸 커맨드 대신 HTTP POST로 훅 실행 가능:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: http
          url: "https://example.com/webhook"
```

### Stop/SubagentStop 훅 (v2.1.47 추가)

`last_assistant_message` 필드: 에이전트 최종 응답 텍스트를 훅에서 직접 접근 가능 (트랜스크립트 파싱 불필요).

### 예시

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup.sh"
```

---

## 6. 실행 모드

### Background (v2.1.198부터 기본)

**(v2.1.198)** 서브에이전트는 이제 **기본으로 백그라운드에서 실행**됨. 완료 시 알림이 오며, 메인 세션은 대기하지 않고 계속 진행 가능. 결과가 나오기 전에 반드시 다음 작업을 이어가야 하는 경우 Task 호출에 `run_in_background: false`를 전달해 동기 실행.

```yaml
background: true  # YAML 설정 — 항상 백그라운드 고정
```

또는:
- Task tool의 `run_in_background: true`/`false`로 개별 제어
- 실행 중 `Ctrl+B`로 백그라운드 전환

**동작**: ESC로 메인 취소 시 백그라운드는 계속 실행. `Ctrl+F`로 강제 종료.

**(v2.1.76)** 백그라운드 에이전트를 kill하면 부분 결과가 대화 컨텍스트에 보존됨. **(v2.1.199)** rate limit으로 중단된 서브에이전트도 조용히 실패하지 않고 부분 결과를 반환하며, API 에러를 성공으로 잘못 보고하던 문제가 수정됨. **(v2.1.216 수정)** 시작 직후(startup window)에 높은 우선순위 메시지가 도착하면 백그라운드 서브에이전트가 취소되던 버그, 재개(resume)된 백그라운드 에이전트 세션이 기본 에이전트로 되돌아가던 버그(이제 에이전트의 프롬프트·도구 제한이 복원됨) 수정.

**(v2.1.232)** 인터랙티브 세션에서 팀원(teammate)이 아닌 에이전트 스폰도 **기본 백그라운드**로 실행됨.

### Foreground (동기 실행)

Task 호출에 `run_in_background: false`를 주면 서브에이전트 완료까지 메인 대화가 대기하고 결과를 즉시 확인.

### `/subtask`·`/fork` (v2.1.212)

**(v2.1.212)** 세션 내 서브에이전트 실행 방식이 `/subtask` 커맨드로 대체됨 (이전 in-session 서브에이전트 런칭을 교체). 별도로 `/fork`는 현재 대화를 **새 백그라운드 세션으로 복제**하면서 메인 세션을 그대로 유지 — 같은 맥락에서 갈라져 병렬 탐색할 때 사용. (bare `/btw` 동작도 함께 조정됨.) **(v2.1.216)** `/fork` 확인 메시지가 한 줄로 정리됨 — 새 세션 이름, `claude attach` id, 체크아웃 공유 여부 표시.

### 서브에이전트 포크 (v2.1.232부터 기본 활성화)

**(v2.1.232)** 서브에이전트 포크가 **기본 활성화**됨. Agent 호출에 `subagent_type: "fork"`를 주면 그 서브에이전트가 **현재 대화 전체와 프롬프트 캐시를 그대로 상속**한다 — 맥락을 다시 설명할 필요가 없고 캐시를 재사용하므로 비용도 낮다. fork는 부모 모델을 그대로 쓰며 `model` 오버라이드는 무시된다.

**(v2.1.223)** 워크플로우 에이전트·포크된 스킬·슬래시 커맨드·재개된 백그라운드 에이전트가 요청한 서브에이전트 모델이 제한되어 **부모 모델로 대신 실행**될 때 경고가 표시됨.

### 서브에이전트 스폰 상한 (v2.1.217~v2.1.224)

**(v2.1.224)** 세션당 서브에이전트 스폰 **200개 상한이 제거**됨 — 장시간 세션이 새 에이전트를 거부하지 않는다 (아래 동시 실행·깊이·예산 상한은 그대로 유지). WebSearch 도구 호출은 세션 전체 기준 기본 200회 상한이 유지됨(튜닝 가능). **(v2.1.212)** 2분을 초과하는 MCP 도구 호출은 세션 사용성을 위해 자동으로 백그라운드로 전환됨.

현행 상한 3종:
- **동시 실행 상한** (v2.1.217): 동시에 돌 수 있는 서브에이전트 **기본 20개** — `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`로 재정의. 한 메시지가 무한정 백그라운드 에이전트를 fan-out 하는 것을 방지
- **중첩 스폰 깊이 3** (v2.1.219): 서브에이전트가 자신의 서브에이전트를 **기본 3단계까지 스폰 가능**. 중첩을 끄려면 `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`
- **`--max-budget-usd` 적용 강화** (v2.1.217): 예산 상한 도달 시 새 스폰이 거부되고 **실행 중인 백그라운드 에이전트도 중단**됨 (이전에는 백그라운드 에이전트가 계속 실행)

### 세션 설정 상속 (v2.1.198)

**(v2.1.198)** 서브에이전트와 컨텍스트 압축(compaction)이 세션의 **확장 사고(extended thinking) 설정을 상속**함. 내장 **Explore** 에이전트는 더 이상 Haiku 고정이 아니라 메인 세션의 모델을 상속(단 Opus 상한). **(v2.1.198)** 서브에이전트는 자신을 스폰한(launcher) 쪽의 메시지를 일반 작업 지시로 취급.

### 병렬 실행

여러 서브에이전트를 동시에 실행 가능. Task tool을 한 메시지에서 여러 번 호출.

**(v2.1.161)** 병렬 도구 호출 중 하나의 Bash 명령이 실패해도 같은 배치의 나머지 호출은 취소되지 않음 — 각 도구가 독립적으로 결과 반환.

### Dynamic Workflows (v2.1.154, 신규)

**(v2.1.154)** Claude에게 "workflow를 만들어달라"고 요청하면 수십~수백 개의 에이전트에 작업을 백그라운드로 분산 오케스트레이션. 더 크고 복잡한 작업을 한 번에 처리 가능.

- `/workflows`로 실행 중인 workflow 목록 조회
- **(v2.1.160)** 트리거 키워드가 `workflow` → `ultracode`로 변경됨. 일반 문장으로 요청하면 여전히 동작하나, "workflow"라는 단어 자체는 더 이상 트리거하지 않음. 트리거 키워드는 프롬프트 입력에서 보라색으로 강조됨
- **(v2.1.202)** `Dynamic workflow size` 설정으로 workflow가 자동 산정하는 에이전트 수(권고값)를 조정 가능. `workflow.run_id`/`workflow.name`이 OpenTelemetry 속성에 추가됨
- **(v2.1.219)** 기본 크기 권고값이 **medium**(에이전트 15개 미만 목표)로 변경. `/config`의 `Dynamic workflow size`에서 다른 크기나 무제한 선택 가능. 실행 중 workflow 상태 줄에 현재 기본 크기가 표시됨
- **(v2.1.219)** `workflowSizeGuideline` 설정 키 추가 — 어느 settings 파일에서든 이 권고값을 지정 가능. 지정하면 `/config`의 해당 행은 숨겨짐
- **(v2.1.229)** fan-out 시 같은 prefix를 쓰는 형제 에이전트를 **시차를 두고 시작**해, 뒤따르는 에이전트가 캐시된 프롬프트 prefix를 다시 지불하지 않고 재사용하도록 개선. 끄려면 `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS=0`

### 백그라운드 세션으로 셸 실행 (v2.1.154)

```bash
# claude agents 뷰에서: ! <command> 입력 → 백그라운드 세션으로 셸 실행
claude --bg --exec '<command>'   # CLI에서 직접
```

attach/detach 가능한 백그라운드 세션으로 임의 셸 명령 실행.

### 세션 간 메시지 (v2.1.224~v2.1.238)

**(v2.1.224)** `SendMessage`가 **세션 간(cross-session)** 으로 확장됨 — 내 기계들에서 돌고 있는 다른 Claude Code 세션에 메시지를 보낼 수 있고, `ListAgents`로 그 세션들을 찾는다 (macOS·Linux).

- **(v2.1.224)** `crossSessionInbound`·`dialogExpiry` 설정 추가. 권한 우회(bypassed permissions)로 돌고 있는 세션으로 들어오는 메시지는 **승인 대기로 보류**되고, 그 외 세션으로 가는 메시지는 자동 전달됨
- **(v2.1.232)** `/config`에 "Dialog expiry"와 "Messages from your other sessions"(cross-session inbound accept/hold/refuse) 행 추가
- **(v2.1.232)** 살아 있는 세션 하나와 정확히 일치하는 **이름만으로 전달** — ref로 다시 확인하라고 묻지 않음
- **(v2.1.229)** `ListAgents`가 끊긴 Remote Control 세션을 `offline`, 클라우드 세션을 `cloud`로 표시
- **(v2.1.234)** `SendMessage`·`ListAgents`가 계정의 세션 목록이 너무 길어 **전부 확인하지 못했을 때 그 사실을 알림** — 못 본 세션을 없는 것으로 취급하지 않음
- **(v2.1.235)** 전달 한도를 넘는 큰 메시지를 **발송 전에 거부** (조용히 버리지 않음)
- **(v2.1.236)** `notify_when_idle` 옵션 추가 — 같은 기계의 다른 세션에게 "다음에 유휴 상태가 되면 한 번 알려달라"고 요청. opt-in·1회성이며 폴링하지 않음 (macOS·Linux)
- **(v2.1.236)** 빠른 연속 발송이 상대 세션 inbox 수용량을 넘길 상황이면 **미리 거부** — 보냈다고 보고하고 실제로는 버리던 문제 수정
- **(v2.1.228)** 세션 간 메시지의 발신자와 본문이 접힌 한 줄 대신 **인라인으로 표시**됨. 다른 기계의 Remote Control 세션으로 보낸 메시지는 내 Remote Control 세션 이름이 발신자로 표시됨

---

## 7. 모델 선택 가이드

| 모델 | 용도 | 속도 | 비용 |
|------|------|------|------|
| `haiku` | 파일 검색, 간단한 포맷팅 | 매우 빠름 | 저렴 |
| `sonnet` | 대부분의 작업 (기본값) | 빠름 | 보통 |
| `opus` | 복잡한 아키텍처, 정교한 분석 | 느림 | 비쌈 |
| `'inherit'` | 메인 대화 모델 상속 | 가변 | 가변 |

**(v2.1.219)** `opus` 별칭이 가리키는 기본 Opus 모델이 **Claude Opus 5 (`claude-opus-5`)**로 변경 — 1M 컨텍스트, fast 모드 $10/$50 per Mtok. `/fast`는 Opus 5와 Opus 4.8에 적용되고 Opus 4.7은 fast 모드에서 제외됨.

**(v2.1.222 수정)** 조직이 특정 모델을 제한한 환경에서 `model: opus` 같은 **패밀리 별칭**이 부모 모델로 떨어지던 버그 수정 — 이제 같은 패밀리 안에서 조직이 허용한 가장 최신 모델로 단계적으로 내려감(서브에이전트·팀원 모두).

---

## 8. Skills 연동

### 서브에이전트에 Skills 프리로드

```yaml
skills: seo-optimizer, ghost-validator
```

- 지정된 Skills 전체 콘텐츠가 시작 시 주입
- 서브에이전트는 부모 스킬을 **상속받지 않음** (명시적 지정 필수)
- 내장 에이전트 (Explore, Plan, general-purpose)는 Skills 접근 불가

---

## 9. CLI 사용법

### JSON 플래그로 정의

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  }
}'
```

### 에이전트 목록 확인 (v2.1.50)

```bash
claude agents  # 인터랙티브 세션 없이 에이전트 목록
```

**(v2.1.98)** `/agents` 커맨드가 탭 레이아웃으로 변경: **Running** 탭(실행 중인 에이전트)과 **Library** 탭(사용 가능한 에이전트)으로 분리.

**(v2.1.97)** `/agents`에 `N running` 인디케이터가 표시되어 현재 실행 중인 서브에이전트 수를 즉시 확인 가능.

**(v2.1.198)** `/agents` **위저드(대화형 생성 마법사)가 제거**됨. 에이전트 정의는 `.claude/agents/*.md` 파일을 직접 만들어 관리. **(v2.1.198)** `claude agents` 뷰에서 시작한 백그라운드 에이전트가 작업 완료 시 커밋·푸시하고 draft PR을 여는 기능 추가.

**(v2.1.139)** `claude agents` 명령이 모든 background/foreground 에이전트 세션을 한 화면에서 보여줌. 메인 인터페이스를 떠나지 않고도 progress 확인.

**(v2.1.142)** `claude agents`에서 백그라운드 세션을 직접 구성하는 플래그가 추가됨:

```bash
claude agents <agent-name> \
  --add-dir <path> \
  --settings <path> \
  --mcp-config <path> \
  --plugin-dir <path> \
  --permission-mode acceptEdits \
  --model sonnet \
  --effort high \
  --dangerously-skip-permissions
```

부모 세션의 환경을 그대로 상속하지 않고 백그라운드 에이전트만의 컨텍스트/권한/모델/에포트를 명시 가능.

**(v2.1.142)** Fast mode 기본 모델이 **Opus 4.7**로 승격 (이전: 4.6). `Explore`/`fast-task` 같은 빠른 분기 작업의 응답 품질이 자동 상승.

**(v2.1.154)** Opus 4.8 출시. fast mode가 Opus 4.8에서 기존 대비 낮은 비용으로 제공 (표준 요금 2배에 2.5배 속도). Haiku/Sonnet/Opus 4.7 이전 모델을 제외한 모든 모델에서 lean 시스템 프롬프트가 기본값.

### `claude agents --json` (v2.1.145)

```bash
claude agents --json   # 실행 중인 Claude 세션을 JSON으로 나열 (스크립팅용)
```

tmux-resurrect, 상태바, 세션 피커 등에 활용. **(v2.1.162)** `waitingFor` 필드로 대기 중 세션이 무엇에 막혀 있는지 표시 (예: 권한 프롬프트). **(v2.1.145)** `agent_id`/`parent_agent_id` OTEL span 속성 추가 — 백그라운드 서브에이전트 span이 디스패치한 Agent 도구 span 아래에 중첩.

### `agent` 필드 honor (v2.1.157)

```bash
# settings.json의 agent 필드가 디스패치된 세션에 적용됨
claude agents --agent <name>   # override
```

**(v2.1.157)** `settings.json`의 `agent` 필드가 `claude agents`로 디스패치된 세션에 적용됨. `--agent <name>`으로 override.

### `--resume` 백그라운드 세션 (v2.1.144)

**(v2.1.144)** `claude --bg`나 agent 뷰로 시작한 백그라운드 세션이 `/resume`에서 인터랙티브 세션과 함께 표시됨 (`bg` 마킹). 완료된 백그라운드 서브에이전트 알림에 경과 시간 포함 (예: "Agent completed · 3h 2m 5s").

### `worktree.bgIsolation: "none"` (v2.1.143)

```json
{
  "worktree": { "bgIsolation": "none" }
}
```

**(v2.1.143)** 백그라운드 세션이 `EnterWorktree` 없이 작업 복사본을 직접 편집하도록 허용. worktree가 실용적이지 않은 저장소용.

### Named Subagents in @ Mention (v2.1.88)

**(v2.1.88)** 커스텀 에이전트가 `@` mention typeahead 자동완성에 표시됨. `@agent-name`으로 직접 참조 가능.

### --print 모드 agent 처리 (v2.1.119)

`--print`(`-p`) 모드가 agent의 frontmatter `tools:`/`disallowedTools:`/`permissionMode`를 honor:

```bash
claude -p --agent my-agent "summarize the codebase"
```

- Agent의 `tools:` allowlist와 `disallowedTools:` denylist 적용
- Built-in agents의 `permissionMode` 자동 적용
- Headless 자동화에서 agent 권한 설정이 정확히 반영됨

### --dangerously-skip-permissions 보호 경로 우회 (v2.1.121, v2.1.126)

`--dangerously-skip-permissions` 플래그가 보호 경로(`.claude/`, `.git/`, 시스템 디렉토리) 프롬프트도 우회. 신뢰된 자동화 환경에서만 사용.

### Forked Subagent 외부 빌드 지원 (v2.1.117)

```bash
CLAUDE_CODE_FORK_SUBAGENT=1 claude ...
```

외부 빌드(non-Anthropic-managed)에서도 fork subagent 활성화. **(v2.1.121)** SDK의 non-interactive 세션에서도 작동.

### Agent frontmatter mcpServers (`--agent` 메인 세션)  (v2.1.117)

`--agent` 플래그로 메인 세션을 실행할 때, agent frontmatter의 `mcpServers:` 필드가 로드되어 해당 MCP 서버에 연결됨.

### --bare 플래그 (v2.1.81)

스크립트용 `-p` 호출에서 hooks, LSP, plugin sync, skill walks를 건너뛰는 경량 모드:

```bash
claude --bare -p "prompt"  # ANTHROPIC_API_KEY 또는 apiKeyHelper 필요
```

- OAuth/keychain 인증 비활성화
- Auto-memory 완전 비활성화
- ~14% 빠른 API 요청 (v2.1.83)

### Worktree 모드 실행 (v2.1.49)

```bash
claude --worktree  # 또는 -w
```

### EnterWorktree `path` 파라미터 (v2.1.105)

`EnterWorktree` 도구에 `path` 파라미터 추가. 현재 저장소의 **기존** worktree로 전환할 때 사용. 새로 생성하지 않고 기존 worktree를 재사용.

### Stale Worktree 자동 정리 (v2.1.105)

Squash-merge된 PR의 worktree가 무기한 남아있던 동작이 수정됨. PR이 squash merge되면 해당 에이전트 worktree도 정리 대상으로 포함.

### EnterWorktree 로컬 HEAD 브랜치 (v2.1.128)

`EnterWorktree`가 새 worktree를 만들 때 **로컬 HEAD에서 브랜치를 분기**. 이전에는 origin 기준이었으나 로컬 미커밋/미푸시 변경사항을 활용 가능하도록 동작 변경.

### EnterWorktree 세션 중 전환 (v2.1.157)

**(v2.1.157)** `EnterWorktree`가 세션 도중에 Claude-managed worktree 간 전환 가능. 또한 에이전트 작업 종료 시 Claude가 관리하던 worktree를 **unlock 상태로 남김** — `git worktree remove`/`prune`으로 정리 가능.

### EnterWorktree 외부 경로 확인 (v2.1.206)

**(v2.1.206)** `EnterWorktree`가 `.claude/worktrees/` **밖**의 worktree로 진입할 때 확인 프롬프트를 표시. 의도치 않게 관리 범위 밖 worktree로 들어가는 것을 방지.

### `--forward-subagent-text` (v2.1.211)

**(v2.1.211)** stream-json 출력에서 서브에이전트의 텍스트를 상위로 전달하는 `--forward-subagent-text` 플래그(및 동명 환경변수) 추가. 백그라운드 서브에이전트 진행 텍스트를 스크립트 파이프라인에서 받아볼 때 사용.

**(v2.1.219)** 중첩 전달 지원 — depth 2 이상에서 스폰된 서브에이전트도 `--forward-subagent-text`를 켜면 스트림에 나타나며, 자신을 스폰한 Agent `tool_use` id를 키로 구분됨.

### 백그라운드 에이전트 자동 업그레이드 (v2.1.206)

**(v2.1.206)** Claude Code 업데이트 후 백그라운드 에이전트가 자동으로 업그레이드됨 (이전에는 구 바이너리에 남아있던 문제 해결).

### 특정 에이전트 비활성화

```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(my-custom-agent)"]
  }
}
```

---

## 10. 컨텍스트 관리

### Resume (재개)

서브에이전트는 전체 히스토리를 유지하며 재개 가능.

**(v2.1.77 Breaking)**: Agent tool의 `resume` 파라미터 제거됨. 대신 `SendMessage({to: agentId})`로 이전 에이전트를 계속. `SendMessage`는 중지된 에이전트를 백그라운드에서 자동 재개.

### Auto-Compaction

컨텍스트 윈도우 임계치 도달 시 자동 요약. 중요 정보 보존.

### Transcript 저장

```
~/.claude/projects/[project-hash]/sessions/[session-id].jsonl
```

`cleanupPeriodDays` 후 자동 정리 (기본 30일).

---

## 11. 제한사항

1. **중첩 스폰 깊이 3** (v2.1.219): 서브에이전트가 자신의 서브에이전트를 **기본 3단계까지** 스폰 가능. 중첩을 끄려면 `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` (v2.1.217에서 기본 차단이었다가 v2.1.219에서 깊이 3으로 다시 열림). auto 모드에서는 서브에이전트 스폰을 분류기가 사전 평가 (v2.1.178)
2. **Agent tool `model` 파라미터 복원** (v2.1.72): 호출별 모델 오버라이드 가능
3. **스킬 상속 불가**: 부모 대화 스킬을 상속받지 않음. `skills` 필드로 명시 필요.
4. **트랜스크립트 격리**: 각 호출은 새로운 컨텍스트 (재개하지 않는 한)
5. **`TaskOutput` 도구 Deprecated** (v2.1.83): `Read`로 백그라운드 태스크 출력 파일 경로를 직접 읽는 방식으로 대체
6. **WorktreeCreate HTTP hook** (v2.1.84): `type: "http"` 지원. `hookSpecificOutput.worktreePath`로 생성된 worktree 경로 반환
7. **(v2.1.92 수정)** tmux 윈도우가 삭제/재번호화된 후 서브에이전트 스폰이 영구 실패하던 버그 수정 ("Could not determine pane count")
8. **(v2.1.90 수정)** `--resume` 시 deferred tools, MCP 서버, 커스텀 에이전트가 있는 사용자에게 프롬프트 캐시 전체 미스 발생하던 회귀 버그 수정 (v2.1.69 이후)
9. **(v2.1.98 수정)** 서브에이전트가 동적 주입된 MCP 서버의 도구를 상속받지 못하던 버그 수정
10. **(v2.1.98 수정)** 격리된 worktree의 서브에이전트가 자체 worktree에 대한 Read/Edit 접근이 거부되던 버그 수정
11. **(v2.1.101 수정)** `--resume`/`--continue` 시 대형 세션에서 컨텍스트 유실되던 버그 수정
12. **(v2.1.101 수정)** `--resume` 체인 복구 시 관련 없는 서브에이전트 대화로 잘못 연결되던 버그 수정
13. **(v2.1.152)** 기본 모델을 찾을 수 없으면 세션 나머지 동안 `--fallback-model`로 전환 (매 요청 실패 대신)
14. **(v2.1.147)** Pinned 백그라운드 세션(`Ctrl+T`)이 idle 상태에서 유지되고, 업데이트 적용 시 in-place 재시작되며, 메모리 압박 시 non-pinned 세션 이후에만 shed됨
15. **(v2.1.145)** Agent Teams 팀원의 non-ASCII 이름이 잘못된 헤더 인코딩으로 모든 API 호출 실패하던 버그 수정
16. **(v2.1.145)** `CLAUDE_CODE_SUBAGENT_MODEL`이 Agent Teams 팀원 프로세스에 적용 안 되던 버그 수정
17. **`TeamCreate`/`TeamDelete` 도구 제거** (v2.1.178): 모든 세션이 하나의 암묵적(implicit) 팀을 갖게 되어 명시적 팀 생성/삭제 도구가 사라짐
18. **백그라운드 서브에이전트 권한 프롬프트** (v2.1.186): 이전에는 자동 거부였으나, 메인 세션에 권한 프롬프트를 표시하도록 변경
19. **`--effort` 상속** (v2.1.186): tmux/pane 백엔드로 띄운 Agent Teams 팀원이 리더의 `--effort` 레벨을 상속
20. **Task tool `mode` 파라미터 Deprecated** (v2.1.212): `mode` 파라미터가 폐기됨 (세션 내 서브에이전트는 `/subtask`로 실행)
21. **`isolation: 'worktree'` git 변경 격리 강화** (v2.1.210, v2.1.216): worktree 격리 서브에이전트가 git을 변경하는 명령을 메인 저장소가 아닌 자기 worktree에서 실행하도록 수정. **(v2.1.216)** `git -C`·`--git-dir`·`GIT_DIR`/`GIT_WORK_TREE`로 공유 체크아웃에 git을 리다이렉트하는 우회도 차단. worktree 세션이 작업 디렉토리와 프로젝트가 불일치할 때 다른 프로젝트의 잔여 worktree에 들어가던 버그, git 저장소 없는 worktree의 백그라운드 세션이 삭제 불가하던 버그 수정
22. **Agent 도구 프롬프트 인젝션 방어** (v2.1.210): Agent 도구가 간접(indirect) 프롬프트 인젝션에 대해 강화됨
23. **서브에이전트 상태 페이로드에 reasoning effort 포함** (v2.1.214): `claude agents --json` 등 상태 조회에 서브에이전트의 노력 수준(reasoning effort)이 추가됨
24. **`Agent` 도구 빈 도구 실행 버그 수정** (v2.1.208): Agent 도구가 도구 없이 실행되던 버그 수정
25. **백그라운드 세션 격리 심링크 정규화** (v2.1.217): 심링크된 작업 디렉토리를 정규화(canonicalize)하지 않아 세션이 워크스페이스 폴더를 벗어날 수 있던 버그 수정
26. **fork 세션 계보(lineage) 보존** (v2.1.218): headless·SDK 세션에서 compaction 후 fork-session 계보가 유실되던 버그 수정
27. **worktree 격리가 파일 편집·Bash 전체에 적용** (v2.1.222): worktree 격리 세션과 그 서브에이전트가 메인 체크아웃에 파괴적 git 명령을 실행할 수 있던 문제 수정. 격리가 이제 **모든 세션 유형의 파일 편집과 Bash에 적용**됨
28. **PreToolUse 자동 허용 훅의 도구 제한 우회 차단** (v2.1.222): 백그라운드 에이전트 작업(요약·compaction·이름 변경)에서 PreToolUse auto-allow 훅이 도구 제한을 우회하던 버그 수정
29. **`SendMessage` 권한 분류기 통과** (v2.1.222): auto 모드에서 다른 에이전트 세션으로 보내는 `SendMessage` 메시지가 발송 전 권한 분류기의 평가를 받음. 또한 긴 요약을 거부하던 문제가 **잘라내기(truncate)로 변경**되어 글자 수 제한으로 발송이 실패하지 않음
30. **서브에이전트 effort 라벨 표시 수정** (v2.1.222): 서브에이전트 트랜스크립트 뷰의 스피너가 세션의 effort 레벨이 아니라 **서브에이전트 자신의 `effort:` 설정**을 표시하도록 수정
31. **`/fork` 자체 worktree 생성** (v2.1.221): `/fork`로 분기한 세션이 원본 세션의 체크아웃에서 작업하지 않고 **자기 worktree를 새로 만듦**
32. **백그라운드 세션의 작업 보존 방식 변경** (v2.1.221): 백그라운드 세션이 작업 보존을 위해 커밋·push하고, 필요한 작업일 때만 draft PR을 열며, **CLAUDE.md의 git 지침을 따르고**, 마지막에 작업물이 어디 있는지 항상 보고함
33. **`/status` 세션 종류 표시** (v2.1.221): `interactive` / 백그라운드 잡의 `attached`·`unattended` 구분 표시
34. **에이전트 파일 이름 `:` 금지 유지 + 스킬 이름 충돌 수정** (v2.1.218, v2.1.221): 에이전트 이름의 `:`는 플러그인 네임스페이싱 예약. 플러그인·조직 배포 스킬이 터미널 전용 빌트인(`/help`·`/feedback` 등)과 같은 이름이면 비대화형 세션에서 호출 불가하던 버그 수정
35. **세션당 스폰 200개 상한 제거** (v2.1.224): 장시간 세션이 새 에이전트를 거부하지 않음 (동시 실행 20개·중첩 깊이 3·예산 상한은 유지)
36. **teammate 기본 모델 설정 제거** (v2.1.234): `/config`의 "Default teammate model" 행이 사라지고, agent-team 팀원은 **스폰이 모델을 지정하지 않으면 리더의 모델**을 사용
37. **커스텀 서브에이전트 생성 권유 제거** (v2.1.232): 시작 팁과 `/powerup` 투어에 있던 "커스텀 서브에이전트를 만들어보라"는 안내가 제거됨
38. **`claude agents` 워크스페이스 신뢰 프롬프트** (v2.1.225): 신뢰되지 않은 디렉토리에서 `claude agents`를 열면 `claude`와 동일하게 신뢰 여부를 물음
39. **GitLab MR 지원** (v2.1.233, v2.1.234): `--worktree` 플래그와 `claude agents` 뷰가 GitLab merge request URL을 지원하며 MR은 `!N`으로 표시됨. GitLab 리모트 + 인증된 `glab` CLI가 있으면 푸터·스테이터스라인에 MR 배지 표시
40. **`selection:clear` 키바인딩** (v2.1.234): 인앱 텍스트 선택을 해제하는 동작에 키를 바인딩 가능 — agents 뷰에서도 동작
41. **긴 세션 메모리 증가 수정** (v2.1.238): 서브에이전트 도구 결과가 최근 표시 범위를 벗어나면 해제되도록 수정 — 장시간 인터랙티브 세션의 무한 메모리 증가 해소
42. **`/code-review` 백그라운드 실행 확대** (v2.1.232): high·xhigh·max 레벨도 다른 레벨과 동일하게 백그라운드 에이전트로 실행

### EndConversation 도구 (v2.1.214)

**(v2.1.214)** 극도로 남용적(abusive)이거나 jailbreak를 시도하는 사용자에 대응하기 위한 `EndConversation` 도구 추가. 세션을 안전하게 종료하는 용도.

---

## 12. Best Practice

### DO

- 단일 책임 원칙: 하나의 명확한 역할
- 상세한 프롬프트: 예제와 제약사항 포함
- 최소 권한: `tools` 또는 `disallowedTools`로 제한
- Description에 트리거 키워드 포함 ("use proactively", "when user mentions X")
- Claude와 협업하여 초안 생성 후 반복 개선
- 프로젝트 에이전트는 Git 커밋

### DON'T

- 모호한 description ("Help with code")
- 불필요하게 `opus` 모델 사용
- 모든 도구 허용 (필요 없는 경우)
- 민감한 작업에 `bypassPermissions` 사용

---

## Sources

- [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## Related

- [[skills-guide]] - Skills 시스템 가이드
- [[claude-md-guide]] - CLAUDE.md 가이드
- [[worker-agents]] - 본 가이드의 실구현 사례 (5개 워커 에이전트)
- [[worker-agents-creation-log]] - 워커 에이전트 생성·강화 과정 기록

---

> **전체 변경 이력**: `~/.claude/cache/changelog.md` (버전별 CHANGELOG 원본)에서 관리. 이 문서는 현재 동작 상태(SoT)만 담으며 버전별 이력을 누적하지 않는다. 동기화 버전은 상단 `Updated` 표기 참조.
