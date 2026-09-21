---
name: daily-note
description: 선언된 위치에 오늘 Daily Note 생성·열기·기록. "오늘 노트", "daily note", "하루 기록" 요청에 사용.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# daily-note

워크스페이스 루트의 `00-system/선언-표면.yaml`이 경로·형식의 원본이다. 아래 래퍼가 실행 가능한 Python 3.9 이상을 확인한다. YAML 모듈은 킷에 동봉되어 있어 패키지 설치는 없다. 선언 오류·실행 실패를 빈 목록으로 숨기지 않는다.

```bash
bash .claude/scripts/surfaces.sh resolve
bash .claude/scripts/surfaces.sh daily
```

`daily`는 선언의 템플릿으로 오늘 노트를 만들고 created/path를 반환한다. 기존 파일은 그대로 보존한다. 반환된 경로를 Read한다. 생성/열기 요청만이면 여기서 끝낸다. 기록 내용까지 요청받았으면 기존 내용을 읽고 해당 섹션에 최소한으로 덧붙인다. 재실행 시 같은 사실을 중복 기록하지 않는다.

`morning` 호출이면 실제 수집·반영·남은 승인대기·실패 결과를 남긴다. `ripple`과 공유하는 완료 섹션은 `하루.완료섹션`이다. 할 일의 정본은 `할일.위치`이므로 노트에는 참조/요약만 남기고 별도 활성 할 일 저장소로 쓰지 않는다.

## 선택: 오늘 일정 읽기

기본 `하루.캘린더조회: false`이면 외부 조회하지 않는다. 사용자가 켜기로 결정하고 도구/인증을 준비한 뒤 true로 바꾼다.

true일 때 설치된 gws의 도움말로 명령 지원을 확인하고 `gws calendar +agenda --today --format json`을 실행한다. 종료 코드·JSON 오류·인증 오류는 **조회 실패**로 알린다. 성공한 events 배열(옛 응답은 items)만 오늘 일정 섹션에 반영한다. 빈 배열일 때만 0건이라고 한다. 기존 일정 섹션은 갱신하고 중복 추가하지 않는다. 캘린더 쓰기는 이 스킬의 작업이 아니다.
