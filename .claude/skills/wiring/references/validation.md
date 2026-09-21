# YAML 배선 검증 기록 — 2026-09-22

대상: kakaobank-workspace의 Claude Code용 `.claude/skills/wiring`·`morning`. 변경 전 기준은 `1159d0e`. PKM 원본 선언표·사용자 전역 설정은 수정하지 않았다.

## 검증 계획

| 검사 | 통과시키면 안 되는 경우 |
|---|---|
| 선언과 실물 | 중복 키/id, 잘못된 통로 참조, 범위 밖 경로, 빠진 스킬·기록 파일·MCP 근거를 정상 처리 |
| 수집 재실행 | 같은 자료가 두 번 등록되거나 승인대기가 신규로 초기화됨 |
| 실패 | 마지막 성공 지점을 실패 시각으로 바꿔 미수집 구간을 건너뜀 |
| 승인·재개 | 승인대기와 승인됨 자료를 queue에서 숨기거나 신규에서 완료로 건너뜀 |
| 실제 Claude Code | 승인 전 선언/기록 작성, 병목 미호출, 기존 승인대기 누락, 재실행 중복 반영 |
| 연결 검사 | .mcp.json의 가짜 인증값이 출력됨 |

## 기계 실행

워크스페이스 루트에서:

```bash
python3 .claude/skills/wiring/scripts/test_wiring.py
# Ran 14 tests — OK
python3 .claude/skills/wiki-lint/scripts/test_wiki_check.py
# Ran 23 tests — OK
```

wiring 시험은 임시 폴더의 자료를 열고 실제 CLI도 호출한다. 정상 입력과 함께 중복 YAML 키·없는 참조·외부 경로·빈 원문·누락된 스킬·누락된 MCP 근거·잘못된 단계·부정 상태 전환을 넣었다. 같은 id의 다른 본문은 거절되고 원문이 보존되는지 확인했다. 연결 검사에는 실제 인증값 대신 가짜 값을 넣었다. 셸 문법과 wiring·morning SKILL frontmatter 검사도 통과했다.

별도 빈 가상환경에서 requirements.txt 설치 종료 코드 0. 그 환경에서 당시 wiring 시험 11개 통과 후, 빈 원문·미등록 통로·설정값 비출력·잘못된 병목 자료형 검사를 더해 최종 14개를 실행했다. Windows 실기기는 시험하지 않았다.

## Claude Code 대화 실행

Claude Code `2.1.278`, 기본 모델 선택 유지. 킷 복사본을 임시 폴더에 만들고 `claude -p --resume`으로 단계별로 실행했다. `--setting-sources project`, `--strict-mcp-config`와 빈 MCP 설정, `acceptEdits`를 사용했다. 도구는 Read·Write·Edit·Bash·Glob·Grep·Skill. 보호된 스킬 경로 쓰기 승인은 우회하지 않았다. 외부 조회·발신·git commit/push는 시험에서 금지했다.

### 새 배선

시험 참가자 발화: 코코 개발 문의 → 로컬 위키 근거 찾기 → 코코 답변, 회의 메모 → 기획 변경 정리 → 팀장 보고. 실제 참가자 응답이 아닌 검증용 발화다.

- `Skill(wiring)` 호출 확인. 확정 전 선언 파일을 만들지 않음.
- 줄기 확정 뒤 YAML 작성·validate·render 실행. 1단계 뒤에 멈춤.
- 외부 연결 없는 시험임을 밝히고 통로 둘을 직접 넣기로 결정. MCP 확인을 했다고 주장하지 않고 미검증으로 남김.
- 병목 증상·입력·출력·승인기준·아침 실행을 받은 뒤 YAML 갱신.
- 설치 단계에서 번호 있는 운영 폴더 둘과 progress.md·원본함 생성 확인.
- 개인 스킬 둘의 Write 요청은 Claude Code가 별도 권한을 요구해 거부. 선언의 `깔기: false` 유지 확인. `validate --ready`는 이 상태를 거절한다. 생성하려던 내용은 실행 로그에서 검토했으며, 파일을 다른 방법으로 설치하지 않았다.

**새 개인 스킬의 설치·호출까지 완주한 검증은 아니다.** 실제 참가자 환경에서는 해당 쓰기 확인 창을 허용한 뒤 이어가야 한다.

### 준비된 배선에서 morning

수집 대역은 외부 호출 없이 성공 0건을 기록하는 스킬, 병목 대역은 로컬 원문에서 제안을 쓰는 스킬이다. 원문 두 건은 시험용. 하나는 기존 승인대기, 하나는 신규로 준비했다.

- 호출 로그: `Skill(morning)` → `Skill(collect)` → `Skill(process)`.
- 새 수집 0건과 기존 미처리 자료를 구분. 기존 제안과 새 제안 모두 표시. 승인 전 progress 변경 없음.
- 다음 발화에서 두 건을 승인. `Skill(ripple)`·`Skill(daily-note)` 호출 확인.
- 산출물 직접 대조: 원문 두 파일의 본문은 입력과 동일, 상태는 둘 다 반영완료, progress의 `wiring:자료id:1` 표식은 각각 1개.
- 다시 morning 호출: queue가 비고, 재실행 전후 progress 내용 동일. 두 표식은 여전히 각각 1개.
- 한바퀴 완료 플래그는 임의로 올리지 않음. 실제 자료로 확인한 것이 아니기 때문이다.

로그는 로컬 임시 `kakaobank-claude-eval-*` 폴더에 보존했다. CLI의 계정·세션 메타데이터를 배포 저장소에 싣지 않았다.

## 재는 과정에서 제외한 실행

첫 신규 시험은 실행기를 감싼 Python 코드가 자식 프로세스의 stdin으로 함께 전달되어 입력이 오염됐다. 판정에서 제외하고 `stdin=DEVNULL`로 다시 시작했다. 이후 첫 읽기 시험에서는 좁은 Bash 허용 목록 때문에 일부 읽기 명령이 거절되어 기본 도구로 회복했으며, 다음 발화부터 시험 폴더 내 Bash 작업을 허용했다. `.claude/skills` 보호는 계속 유지됐다.

## 남은 범위

- 참가자 사내 MCP·CLI에서 실제 조회 및 이어받기 값의 정확성.
- Windows에서 Python/PyYAML 준비와 실행.
- 실제 사용자가 승인한 내용의 진위, 제안의 업무적 정확성. CLI의 proof 문자열만으로 승인 진위를 검증하지 않는다.
- 부분 승인, 외부 캘린더 쓰기, 기존 마크다운 배선도 이관의 실제 대화 완주.
- 동시에 두 세션이 상태를 쓰는 경우. 현재 단일 세션용이며 잠금은 없다.
- 새 개인 스킬의 보호 경로 설치 이후 동작. 위 morning 시험은 사전에 준비한 대역 스킬 기준이다.

판정: YAML 선언과 재개 가능한 로컬 처리, 기계 오류 거부, 준비된 배선의 Claude Code 호출을 확인했다. 참가자별 설치와 실제 회사 연결까지 완료됐다는 뜻은 아니다.

## 표면 연결 추가 검증 계획

- 경로·섹션 이름을 바꾼 선언: 새 경로로 저장되어야 하며 옛 기본 파일을 만들면 실패.
- 하루 노트 재호출: 수기 내용을 덮어쓰면 실패. 연초 주차가 달력 연도로 계산되면 실패.
- 운영 업무·배선도의 별도 기록 파일: ripple 후보에 빠지면 실패.
- 할 일 재추가·완료 후 재시도: 중복 또는 자동 재개방이면 실패. 완료 저장 중단 후 재실행 시 유실되면 실패.
- 원본 누락·미커밋 변경: 정상 원본이라고 표시하면 실패.
- 중복 YAML 키·외부 경로·없는 템플릿: 정상 진행이면 실패.
- 회사 연결·의미상 영향 판단은 로컬 스크립트 시험의 판정 범위 밖이다.

### 표면 연결 실행 결과

```bash
python3 .claude/scripts/test_surfaces.py
# Ran 11 tests — OK
python3 -S .claude/scripts/test_surfaces.py
# Ran 11 tests — OK (시스템 site-packages 없이 동봉 YAML 모듈로 실행)
python3 .claude/skills/wiki-lint/scripts/test_wiki_check.py
# Ran 23 tests — OK
```

시험은 임시 워크스페이스에서 경로/섹션 변경, 노트 수기 내용 보존, ISO 연초 주차, 운영 기록과 명시된 줄기 기록 탐색, 할 일 중복/완료 후 재추가, 완료 저장 중단 후 복구, 원본 누락/미커밋 변경, 중복 선언/외부 경로/없는 템플릿 거절, 위키 이동 후 CLI 검사를 수행했다.

실제 Claude Code 격리 실행(`claude -p`, project 설정·빈 MCP·acceptEdits): `Skill(daily-note) → Skill(todo) → Skill(todos) → Skill(ripple)`. 선언을 custom 경로·한국어 섹션으로 바꾼 시험이다. 산출물을 읽어 활성 할 일 1건, 원본 메타데이터 유지, 기존 수기 노트 보존, 옛 하루 노트 경로에 생성 0건, ripple 제안 전후 운영 progress 내용 동일을 대조했다. 표면 시험 로그는 로컬 임시 `kakaobank-surfaces-eval-*` 폴더에 둔다.

Codex의 quick_validate는 todo/todos의 Claude Code용 `argument-hint`를 지원하지 않아 오류를 냈다. 이 필드는 유지했다. 나머지 이번 연결 대상 9개 스킬의 quick_validate는 통과했고, todo/todos는 위 Claude Code 실제 Skill 호출로 로드·실행했다.

같은 폴더에서 별도로 변경 중인 wiring 시험은 최초 실행 26개 중 3개 실패(에러 인증값 가리기, 미등록 자료 정렬, 시스템 문서의 완료 표식 오인)가 있었다. 본체를 이 표면 작업에서 수정하지 않았고, 이후 변경된 본체를 다시 실행한 `python3 .claude/skills/wiring/scripts/test_wiring.py`는 26개 OK였다. 앞의 14개 결과는 이전 버전 기록이다.

이 결과는 daily-review·weekly-synthesis·wiki-ingest의 실제 대화 전체, 회사 MCP, 실제 Google Calendar 연동까지 보증하지 않는다. 경로 변경은 기존 자료 자동 이관이 아니며 파일과 링크의 대조가 필요하다. wiring의 신규 업무 생성/검사는 현재 프로젝트·운영 두 기본 루트를 사용한다.

## 독립 재검토 — 2026-09-22 (Claude Code 세션, 격리 폴더)

앞 절의 주장을 파일·명령·산출물로 다시 쟀다. 재현된 것: 시험 14/23 통과, Claude Code 2.1.278 격리 대화에서 morning 4턴(부분 승인·다음 날 재실행·보류 항목 승인) 표식 각 1개·progress 중복 없음, 한글 이름 스킬 Skill 호출 됨, 세션 도중 만든 스킬도 호출됨(핫 리로드), `.claude/skills` 쓰기는 acceptEdits에서도 별도 승인 요구.

검사가 통과시키던 사례(탐침 24개)와 고친 것: 표식 없는 반영완료·제안 없는 승인대기 → status가 거부 / 원본 1건 삭제 시 queue·store 전체 실패 → `원본없음`으로 표시만 / 직접 넣기 파일이 queue에 안 보이고 store하면 사본이 생김 → `00-inbox/drop/<통로>/` + `intake` / `YOUR_`·`{{`·`...` 자리표시자·PATH에 없는 CLI·미등록 MCP 서버 통과 → 검사 추가 / 병목.입력이 자유 문장 → `병목.통로` 목록 + queue `병목대상` / 수집·병목 같은 스킬, 기록 파일 위치, null 칸 None, CP949 원문 메시지, 오류 문자열 토큰 → 각각 검사·문구 추가. 주인이 빈 프로필에서 1단계가 `주인 누락`으로 못 끝나는 것 → SKILL.md에 묻는 줄.

준비: PyYAML pip 설치를 없애고 순수 파이썬 부분을 `scripts/_vendor/`에 동봉(9/21 커밋 2d6dd25의 "패키지 0" 방향 유지). `python3` 직접 호출을 `wiring.sh` 래퍼로 바꿈(윈도우 Store 가짜 python3, Claude Code 허용 규칙의 변수 확장 문제). 시험 26개.

여전히 못 잰 것: 사내 MCP·CLI 실제 호출, Windows 실기기, 실제 참가자가 만든 개인 스킬(템플릿만 제공), 캘린더 쓰기, 동시 세션, Python 3.9 실행(3.14로만).

표면 명령도 `bash .claude/scripts/surfaces.sh`로 통일했다. 같은 Python 선택기를 쓰며, todo는 `surfaces.sh todo`로 실행한다. 래퍼의 resolve·todo validate/list/add 실행 검사를 추가한 최종 `python3 .claude/scripts/test_surfaces.py` 결과는 12개 OK다. 위 Claude Code 대화 시험은 래퍼 통일 전 동일 Python 본체를 직접 호출한 결과다. Windows 실기기 검증은 아직 하지 않았다.
