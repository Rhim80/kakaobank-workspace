---
name: daily-note
description: 오늘 날짜의 Daily Note 생성 또는 열기. gws (Google Workspace CLI) 인증 시 Google Calendar 오늘 일정 포함. "오늘 daily note", "일일 노트", "daily note", "오늘 작성", "하루 기록" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# daily-note

오늘 날짜의 Daily Note를 생성하거나 여는 스킬.

## 수행 작업

### 1. 오늘 날짜 확인

```bash
TODAY=$(date +%Y-%m-%d)
MONTH=$(date +%Y-%m)
DAY_NUM=$(date +%u)  # 1=월 ~ 7=일

case $DAY_NUM in
  1) WEEKDAY="월요일";;
  2) WEEKDAY="화요일";;
  3) WEEKDAY="수요일";;
  4) WEEKDAY="목요일";;
  5) WEEKDAY="금요일";;
  6) WEEKDAY="토요일";;
  7) WEEKDAY="일요일";;
esac
```

### 2. 파일 경로

```
./40-personal/41-daily/{MONTH}/{TODAY}.md
```

월별 폴더가 없으면 먼저 생성: `mkdir -p ./40-personal/41-daily/{MONTH}`

### 3. 파일이 있으면 → 열기

기존 내용 표시. 업데이트하고 싶은지 물어보기.

### 4. 파일이 없으면 → 템플릿으로 생성

템플릿: `./00-system/01-templates/daily-note-template.md`

변수 치환:
- `YYYY-MM-DD` → `{TODAY}`
- `(요일)` → `{WEEKDAY}`

### 5. (선택) Google Calendar 오늘 일정 추가

**도구**: `gws` (Google Workspace CLI). 설치/인증은 교육 과정에서 `gws auth login`으로 1회 세팅.
JSON 파싱은 Python3 내장 `json` 모듈 사용 (별도 설치 불필요).

```bash
if command -v gws &> /dev/null; then
  # 인증 안 되어 있으면 error 객체 반환 → Python에서 조용히 스킵
  EVENTS_JSON=$(gws calendar +agenda --today --format json 2>/dev/null)

  # JSON은 환경변수로 넘긴다. `echo ... | python3 - <<'PYEOF'` 로 쓰면
  # heredoc이 stdin을 차지해 파이프의 JSON이 파이썬에 도달하지 못한다
  # (json.load(sys.stdin)이 JSONDecodeError로 죽고 아래 except가 삼켜서,
  #  일정이 몇 건이든 항상 빈 섹션이 써진다 — 증상이 안 보이는 고장이었다).
  EVENTS_MD=$(EVENTS_JSON="$EVENTS_JSON" python3 <<'PYEOF' 2>/dev/null
import json, os
try:
    data = json.loads(os.environ.get("EVENTS_JSON") or "{}")
    # gws는 일정 배열을 "events" 키로 준다. "items"로 읽던 자리가 있었는데
    # .get()은 키가 없어도 예외를 안 내므로 조용히 빈 목록이 됐다.
    if "events" in data:
        events = data["events"]
    elif "items" in data:          # 옛 응답 형태 호환
        events = data["items"]
    else:
        print("- (일정을 못 읽었습니다 — gws 응답에 events 키가 없음)")
        events = []
    for ev in events:
        start = ev.get("start", {})
        dt = start.get("dateTime") or start.get("date", "")
        # dateTime("2026-04-24T10:00:00+09:00") → "10:00"
        # date("2026-04-24", 종일 일정) → "종일"
        time_str = dt[11:16] if "T" in dt else "종일"
        summary = ev.get("summary", "(제목 없음)")
        print(f"- **{time_str}** {summary}")
except Exception:
    pass  # 인증 실패/error 응답 구조 → 조용히 스킵
PYEOF
)
fi
```

- `EVENTS_MD`를 daily note의 "오늘 일정" 섹션(템플릿에 없으면 상단에 신설)에 삽입
- `gws` 미설치 / 인증 실패 / Python3 미설치 → 단계 전체 스킵 (에러 메시지 X)
- 참고: `gws calendar +agenda --today`는 오늘 일정만 반환하는 read-only 헬퍼

### 6. 결과 보고

```
✅ Daily Note 생성: ./40-personal/41-daily/2026-04/2026-04-24.md
   요일: 목요일
   일정: 3건 (Google Calendar에서 가져옴)
```

## 팁

- 전날/내일 계산 (Mac/Linux 호환):
  ```bash
  # Mac
  YESTERDAY=$(date -v-1d +%Y-%m-%d)
  TOMORROW=$(date -v+1d +%Y-%m-%d)

  # Linux
  YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
  TOMORROW=$(date -d "tomorrow" +%Y-%m-%d)
  ```
  OS 체크: `[ "$(uname)" = "Darwin" ]`

- 경로는 항상 **상대 경로** (`./40-personal/...`). 워크스페이스 루트에서 실행 전제.

---

Made by Do Better Things
