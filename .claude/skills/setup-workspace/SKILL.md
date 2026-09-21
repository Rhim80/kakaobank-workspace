---
name: setup-workspace
description: 워크스페이스를 처음 받은 뒤의 초기 설정. CLAUDE.md 프로필 작성 + Python 확인 + 선택 도구(gws/git) 안내 + 첫 daily note 생성까지 한번에 진행. "워크스페이스 세팅", "초기 설정", "setup", "setup-workspace" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# setup-workspace

워크스페이스를 처음 받은(압축을 푼) 사용자를 위한 초기 설정 스킬.
핵심 단계: **루트 확인 → 프로필 → Python 확인 → 선택 도구 → 저장 위치 확인 → 첫 Daily Note**.

## 수행 작업

### 1. 워크스페이스 루트 + 시드 무결성 확인

이미 개인화한 워크스페이스는 아래 배포 기본값 시드 검사 대신 `00-system/선언-표면.yaml`을 읽고 그 경로의 파일을 검사한다. Python 준비 후 `bash .claude/scripts/surfaces.sh resolve`와 `bash .claude/scripts/surfaces.sh todo validate`를 실행한다. 선언의 위치에 파일이 있는데 기본 위치가 비었다는 이유로 시드를 다시 만들지 않는다.

**1-1. 루트 여부**:

```bash
test -f CLAUDE.md && test -f 00-system/선언-표면.yaml \
  || { echo "ERROR: 워크스페이스 루트에서 실행하세요 (CLAUDE.md·표면 선언 없음)"; exit 1; }
```

루트가 아니면 종료.

**1-2. 시드 파일/폴더 무결성**:

각 스킬이 실제로 참조하는 시드가 살아있는지 일괄 체크. 누락된 건 경고로만 출력하고 자동 복원은 하지 않음 (압축이 덜 풀렸거나 사용자가 실수로 지운 경우 빨리 감지).

```bash
echo "=== 시드 무결성 체크 ==="
missing=()

# 템플릿 (daily-note, weekly-synthesis, ripple이 읽음)
test -f 00-system/01-templates/daily-note-template.md   || missing+=("00-system/01-templates/daily-note-template.md")
test -f 00-system/01-templates/weekly-review-template.md || missing+=("00-system/01-templates/weekly-review-template.md")
test -f 00-system/01-templates/progress-template.md     || missing+=("00-system/01-templates/progress-template.md")

# Personal 디렉토리 (daily/weekly 스킬 등 저장 경로)
test -d 40-personal/41-daily    || missing+=("40-personal/41-daily/")
test -d 40-personal/42-weekly   || missing+=("40-personal/42-weekly/")
test -d 40-personal/43-ideas    || missing+=("40-personal/43-ideas/")
test -d 40-personal/46-todos    || missing+=("40-personal/46-todos/")

# Todo 시드 (todo/todos 스킬 타깃)
test -f 40-personal/46-todos/active-todos.md || missing+=("40-personal/46-todos/active-todos.md")

# CLAUDE.md 프로필 마커 (3단이 이 사이만 교체한다. 절 제목이 아니라 마커로 찾는다)
grep -q "profile:start" CLAUDE.md && grep -q "profile:end" CLAUDE.md \
  || missing+=("CLAUDE.md의 <!-- profile:start -->/<!-- profile:end --> 마커")

# Wiki 시드 (wiki-ingest, wiki-lint가 읽고 씀)
test -f 30-knowledge/00-wiki/SCHEMA.md || missing+=("30-knowledge/00-wiki/SCHEMA.md")
test -f 30-knowledge/00-wiki/index.md  || missing+=("30-knowledge/00-wiki/index.md")
test -f 30-knowledge/00-wiki/log.md    || missing+=("30-knowledge/00-wiki/log.md")

if [ ${#missing[@]} -eq 0 ]; then
  echo "✓ 모든 시드 파일 정상"
else
  echo "⚠️  누락된 시드 (${#missing[@]}개):"
  printf '  - %s\n' "${missing[@]}"
  echo ""
  echo "이 상태로 진행 가능하나, 관련 스킬 실행 시 에러가 날 수 있습니다."
  echo "압축 파일을 다시 풀거나, 빠진 파일을 이림에게 요청하세요."
fi
```

누락이 있으면 사용자에게 "이대로 진행할까요? (y/N)" 확인. N이면 종료.

**단 프로필 마커 누락은 예외 — 진행하지 않고 멈춘다.** 다른 시드는 없으면 나중에 그 스킬이 에러를 내지만, 마커가 없으면 3단이 **조용히 프로필 섹션을 하나 더 만들어** CLAUDE.md에 같은 절이 둘 생긴다. 사용자는 알아채지 못하고 Claude는 어느 쪽을 읽을지 모른다.

```
CLAUDE.md에 프로필 마커(<!-- profile:start --> / <!-- profile:end -->)가 없습니다.
"## 내 프로필" 절의 항목들을 이 두 줄로 감싼 뒤 다시 실행해 주세요.
```

### 2. 대화형 프로필 질문

순서대로 하나씩 물어본다. 한 번에 하나씩 (일괄 질문 금지).

먼저 **마커 사이가 이미 채워져 있는지** 확인 (절 제목이 아니라 마커로 찾는다):
- 비어있으면 → 아래 질문 진행
- 이미 채워져 있으면 → "프로필이 이미 있어요. 다시 채울까요? (y/N)" → N이면 이 단계 스킵

질문 목록:
1. **이름 또는 호칭** — "어떻게 불러드릴까요?"
2. **하는 일** — "현재 어떤 일을 하고 계세요? (ex: 카페 사장, 마케터, 프리랜서 디자이너)"
3. **요즘 걸려 있는 일** — "요즘 걸려 있는 일 2~3개만 알려주세요. 잘 안 풀리는 것이나 계속 신경 쓰이는 것으로요"
4. **이 워크스페이스 용도** — "이 워크스페이스를 어떻게 쓰고 싶으세요? (ex: 일일 기록, 프로젝트 관리, 학습 정리)"

답변은 변수로 저장 (`USER_NAME`, `USER_WORK`, `USER_ONGOING`, `USER_PURPOSE`).

**3번을 "관심사"로 묻지 않는다.** 관심사로 물으면 취미가 나오고, 취미는 Claude의 답을 바꾸지 않는다. **걸려 있는 일은 "일을 시작하기 전 관련 파일을 먼저 찾는다"의 검색 대상이 되므로 실제로 쓰인다.** 프로필 항목은 쓰이는 곳이 있을 때만 묻는다.

### 3. CLAUDE.md 업데이트

**`<!-- profile:start -->`와 `<!-- profile:end -->` 사이만** `Edit` 도구로 교체한다. 마커 두 줄은 남긴다. 파일 전체 덮어쓰기 금지.

**절 제목("## 내 프로필")으로 찾지 않는다.** 제목은 바뀔 수 있고, 바뀌면 이 단계가 섹션을 못 찾아 새로 만들어 버린다(실제로 그렇게 깨진 적이 있다). 마커는 바뀌지 않는다.

마커 사이를 이렇게 채운다:
```markdown
**이름**: {USER_NAME}
**하는 일**: {USER_WORK}
**요즘 걸려 있는 일**: {USER_ONGOING}
**이 워크스페이스 용도**: {USER_PURPOSE}
**판단 성향**: <!-- 물어보지 않은 항목. 비워둔 채로 남긴다 -->

_작성일: YYYY-MM-DD_
```

**필드 이름은 CLAUDE.md에 있는 것과 글자까지 같아야 한다.** 한쪽만 바꾸면 다음 세션이 빈 값으로 읽는다.

**"판단 성향" 줄은 지우지 않는다.** 세팅에서 묻지 않는 항목이지만 `do-better-drive`가 이 줄을 읽는다. 섹션을 통째로 바꾸면서 이 줄을 빠뜨리면, 나중에 사용자가 채워 넣을 자리 자체가 사라진다.

### 4. Python 확인

위키 점검은 `.claude/skills/wiki-lint/SKILL.md`의 실행 절차로 확인한다. Python 3.9 이상·표준 라이브러리만 필요하며 위키만 쓸 때 패키지를 설치하지 않는다.

**왜 필요한가**: `kakao-read`(윈도우)와 `wiring`의 검사 스크립트가 파이썬을 부른다. 둘 다 **패키지 설치 없이** 돈다 — 카톡·연결 검사는 표준 라이브러리, YAML 배선은 스킬 안에 동봉한 순수 파이썬 PyYAML을 쓴다(Python 3.9 이상). 가상환경(venv)이나 pip 설치는 하지 않는다.

**4-1. Python 설치 확인**:

파이썬을 부르는 이름이 OS마다 다르다 — Mac·Linux는 `python3`, 윈도우는 보통 `python` 또는 `py`뿐이다. 그래서 **이름을 고정하지 않고 실제로 실행해 보고 되는 것을 고른다.**

```bash
PYBOOT=""
for c in python3 python py; do
  v=$("$c" --version 2>&1) || continue
  case "$v" in Python\ 3.*) PYBOOT="$c"; echo "Python: $v ($c)"; break ;; esac
done
[ -z "$PYBOOT" ] && echo "ERROR: 파이썬 3이 없습니다 (아래 설치 안내 참고)"
```

`command -v`로 있는지만 보지 않는 이유: **윈도우에는 `python3`라는 이름이 있는 척하는 가짜가 기본으로 깔려 있다.** 치면 Microsoft Store 창이 열리고 파이썬은 실행되지 않는다. 실제로 `--version`을 시켜 "Python 3."이 나오는 것만 고르면 이 가짜가 걸러진다.

없으면 **OS에 맞는 설치 안내**를 보여주고 이 단계를 건너뛴다:

```markdown
**Mac**: `brew install python`  (Homebrew가 없으면 https://brew.sh 먼저)
**Ubuntu·WSL**: `sudo apt install python3 python3-venv`
**윈도우**: https://www.python.org/downloads/ 에서 설치 파일 받기
  - 설치 첫 화면의 **"Add python.exe to PATH" 체크박스를 반드시 켠다.**
    이걸 놓치면 설치는 되는데 Git Bash에서 파이썬을 못 찾는다 (가장 흔한 걸림돌).
  - 설치 후 **Git Bash 창을 닫았다 새로 연다.** 열려 있던 창은 옛 PATH를 그대로 쓴다.
```

설치 뒤 다시 4-1을 돌려 `PYBOOT`가 잡히는지 확인하고 진행한다.

### 5. 선택 도구 안내 (설치 강제 X)

**어떤 도구가 어떤 스킬을 풀어주는지** 한번에 체크하고 보여준다:

```bash
echo "=== 선택 도구 상태 ==="
command -v git &>/dev/null && echo "✓ git: $(git --version)" || echo "✗ git: 미설치 (daily-review, weekly-synthesis 동작 제한)"
command -v gws &>/dev/null && echo "✓ gws: $(gws --version 2>&1 | head -1)" || echo "✗ gws: 미설치 (daily-note의 Google Calendar 연동 스킵)"
case "$(uname -s)" in
  Darwin)
    command -v sqlcipher &>/dev/null && echo "✓ sqlcipher: $(sqlcipher --version 2>&1 | head -1)" \
      || echo "✗ sqlcipher: 미설치 (kakao-read 카톡 읽기 비활성 — brew install sqlcipher)" ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "ℹ️  kakao-read: 윈도우는 sqlcipher가 필요 없습니다 (실행 중인 카톡 메모리를 읽는 방식)" ;;
  *)
    if [ -d /mnt/c ]; then
      echo "ℹ️  kakao-read: WSL — 윈도우 방식으로 동작합니다 (sqlcipher 불필요)"
    else
      echo "ℹ️  kakao-read: 이 OS($(uname -s))에선 비활성 — Mac·윈도우 전용 (다른 스킬엔 영향 없음)"
    fi ;;
esac
```

출력 후 설명:

```markdown
**git**: 현재 워크스페이스가 git repo면 daily-review / weekly-synthesis가 변경사항을 분석해줍니다.
  - 세팅: `git init` 후 첫 커밋

**gws (Google Workspace CLI)**: `하루.캘린더조회`를 사용자가 true로 켰을 때 daily-note가 오늘의 Google Calendar 일정을 가져옵니다.
  - 설치: `npm install -g gws-cli` (교육 과정에서 별도 안내)
  - 인증: `gws auth login` (브라우저 OAuth)
  - 기본값은 조회 꺼짐. 켠 뒤 인증·조회에 실패하면 실패로 알리고, 0건으로 처리하지 않음

**kakao-read (Mac·윈도우 둘 다 됩니다 — 읽는 방식이 다릅니다)**

- **Mac**: 카톡의 암호화된 로컬 DB를 직접 읽습니다.
  - 설치: `brew install sqlcipher`
  - 최초 1회: `python3 .claude/skills/kakao-read/scripts/kakao_read.py setup` (본인 userId 캐시)
  - 카카오톡 데스크톱 앱에 한 번 이상 로그인돼 있어야 함
- **윈도우·WSL**: 실행 중인 카톡의 메모리를 읽습니다. sqlcipher도 키도 필요 없습니다.
  - 파이썬만 있으면 됩니다(4단에서 세팅). 읽는 순간 **카톡이 켜져 있어야** 합니다.
  - 자세한 절차는 `kakao-read` 스킬을 부르면 안내합니다.
- 그 외 OS(순수 리눅스)에선 자동 비활성 — 다른 스킬엔 영향 없음
```

설치까지 자동으로 하지 않음. 사용자가 필요성 판단 후 진행.

### 5-1. 저장 위치 확인 — 내 대화가 어디로 올라가는지 (중요)

이 워크스페이스에는 앞으로 카톡 요약·회신 초안·업무 기록 같은 **민감한 내용**이 쌓인다(예: kakao-read로 읽은 본인 카톡). git 원격(GitHub 등)에 올리는 순간 그 내용이 내 컴퓨터 밖의 서버로 복사되고, 저장소가 **공개(public)** 상태면 인터넷의 누구나 볼 수 있다. 그래서 세팅 때 딱 한 번, 기계가 검사한다:

```bash
echo "=== 저장 위치 확인 ==="
if git remote get-url origin &>/dev/null; then
  echo "원격 저장소: $(git remote get-url origin)"
  if command -v gh &>/dev/null; then
    vis=$(gh repo view --json visibility -q .visibility 2>/dev/null)
    case "$vis" in
      PRIVATE) echo "✓ 비공개(private) — 남이 볼 수 없습니다" ;;
      PUBLIC)  echo "공개(public) 원격입니다 — 배포 원본인지 업무 백업 원격인지 아래에서 구분합니다" ;;
      *)       echo "⚠️ 공개 여부를 확인하지 못했습니다 (gh 로그인 필요) — 수동 확인으로" ;;
    esac
  else
    echo "ℹ️ gh 미설치 — 수동 확인: 브라우저로 저장소 페이지를 열어 이름 옆의 Public/Private 표시를 보세요"
  fi
else
  echo "ℹ️ 원격 저장소 없음 — 모든 것이 이 컴퓨터에만 저장됩니다"
fi
```

결과에 따라:

- **공개(public)면 origin의 용도를 확인한다.** `Rhim80/kakaobank-workspace`에서 배포 킷을 복제한 경우, 참가자의 업무 백업 저장소가 아니다. 공개 킷은 그대로 두고 로컬 세팅을 이어가며 이 원격으로 업무 자료를 push하지 않는다. 개인 백업이 필요하면 회사가 허용한 저장 위치를 본인이 정한다. 그 밖에 본인의 업무 자료를 올리는 공개 원격이면 외부 업로드를 멈추고 저장 위치를 확인한다. clone만으로 로컬 변경이 원격에 자동 업로드되는 것은 아니다.
- **비공개면** 한 문장 알려주고 넘어간다: "비공개라 남이 볼 수는 없지만, 내 GitHub 계정이 뚫리면 여기 쌓인 대화도 함께 노출됩니다. 계정에 2단계 인증을 켜두세요."
- **원격이 없으면** 사본이 한 벌뿐임을 알려준다: "이 컴퓨터가 고장 나면 되찾을 수 없습니다. 백업(비공개 원격 또는 주기적 외장 복사)을 권합니다."

### 6. 첫 Daily Note 생성 제안

"오늘의 첫 Daily Note를 만들까요? (Y/n)"
Yes면 `daily-note` 스킬 호출.

### 7. 다음 단계 안내

```
워크스페이스 세팅 완료!

다음에 해볼 것 (이름을 외울 필요 없이 그냥 말하면 됩니다):
1. "오늘 daily note 만들어줘" → 매일의 기록 시작
2. "할 일 추가해줘: XXX" → 첫 할 일
3. "배선도 그려줘" → 사전 업무파악 응답으로 내 업무 배선을 만들고, "아침 시작하자"로 이어갑니다
4. "새 프로젝트 시작" → 목적에서 완료까지 7단계로 밀어줍니다

CLAUDE.md에 Claude가 지킬 규칙이 적혀 있습니다. 그중 "항상 이렇게 해줘" 절은
비어 있는데, 여기가 이 워크스페이스가 당신 것이 되는 자리입니다 —
쓰다가 "아니 그렇게 말고" 하는 순간이 오면 Claude가 규칙으로 남길지 물어봅니다.

자세한 건 README.md 참고!
```

폴더 구조와 저장 위치는 `CLAUDE.md`의 "어디에 저장하나"에 있으므로 여기서 반복하지 않는다. Python 안내도 4단에서 이미 했다 — **같은 말을 두 번 하면 참가자는 둘 다 안 읽는다.**

## 원칙

- **일괄 질문 금지**. 하나씩 물어야 인지 부담 낮음.
- **답변은 짧게 유도**. 긴 자기소개 요구하지 말 것.
- **CLAUDE.md 덮어쓰기 금지**. `profile:start`~`profile:end` 마커 사이만 `Edit`로 바꾼다. **절 제목으로 찾지 않는다** — 제목이 바뀌면 못 찾고 새로 만들어 중복시킨다.
- **이미 채워져 있으면** 덮어쓰기 전 사용자에게 확인.
- **프로필은 쓰이는 곳이 있는 항목만 묻는다.** 답이 Claude의 행동을 안 바꾸는 항목(취미·관심사류)은 세팅을 길게 만들 뿐이다.
- **Python은 확인만**. 없으면 설치 안내만 하고 넘어간다 — 카톡 읽기(윈도우)를 안 쓸 사람도 있음.
- **선택 도구(git/gws)는 상태만 체크**. 자동 설치·인증은 안 함 (교육 과정에서 별도 안내되는 영역).
- **저장 위치는 숨기지 않는다**. 배포 원본과 업무 백업 원격을 구분한다(5-1). 저장소 공개 여부를 자동 변경하거나 업무 자료를 승인 없이 push하지 않는다.
- **재실행 안전**. 이미 세팅된 항목은 스킵.

## CLAUDE.md와의 대응

이 스킬이 `CLAUDE.md`의 어디를 건드리는지. **절을 더하거나 이름을 바꾸면 이 표와 `CLAUDE.md` 쪽 같은 표를 함께 고친다.**

| CLAUDE.md 절 | 이 스킬 |
|---|---|
| 내 프로필 | 2·3단이 마커 사이를 채운다 |
| 일하는 방식 | 채우지 않는다 (고정) |
| 항상 이렇게 해줘 | 비워둔다. 7단이 존재만 알린다 |
| 어디에 저장하나 | 1단 시드 체크가 이 경로들을 검사 |
| 지식은 위키에 | 1단 시드 체크 (SCHEMA·index·log) |
| 스킬 | 4·5단 (Python 확인·선택 도구) |

---

Made by Do Better Things
