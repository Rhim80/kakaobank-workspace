---
name: weekly-synthesis
description: 한 주간의 작업과 사고를 종합하여 Weekly Synthesis 생성. "주간 정리", "이번 주 회고", "weekly review", "일주일 요약", "주간 리뷰" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
---

# weekly-synthesis

이번 주 작업과 사고를 종합해 선언의 주간 파일에 저장한다.

워크스페이스 루트의 `00-system/선언-표면.yaml`이 경로·형식의 원본이다. 아래 래퍼가 실행 가능한 Python 3.9 이상을 확인한다. YAML 모듈은 킷에 동봉되어 있어 패키지 설치는 없다. 선언 오류·실행 실패를 빈 목록으로 숨기지 않는다.

## 분석 프로세스

### 1. 날짜와 경로

```bash
bash .claude/scripts/surfaces.sh resolve
```

반환된 주간시작~주간끝과 주간파일을 사용한다. ISO 주차 연도를 쓰므로 연말·연초에도 파일명이 맞는다.

### 2. 활동 수집

선언의 하루 위치에서 해당 주의 노트를 읽고, git 저장소면 그 기간 log와 미커밋 status/diff를 함께 본다. 선언의 진행 루트와 배선도 줄기 기록에서 프로젝트·반복 운영 업무를 함께 읽는다. 원문에 없는 사고·감정·성과는 추정해서 채우지 않는다.

### 3. 패턴 식별

- 반복되는 테마
- 공통 도전 과제
- 돌파 순간
- 에너지 패턴 (무엇이 에너지를 줬고, 무엇이 소진시켰나)

### 4. 학습 종합

- 발견된 핵심 인사이트
- 사고가 어떻게 진화했나
- 발견한 연결점
- 답한 질문 / 제기된 질문

### 5. 진척도 평가

- 진전된 프로젝트
- 유지된 영역
- 추가된 자료
- 아카이브된 항목

## 출력 형식

```markdown
---
week: YYYY-WXX
period: YYYY-MM-DD ~ YYYY-MM-DD
tags: [weekly]
---

# Weekly Synthesis — Week of {YYYY-MM-DD}

## Week at a Glance
- 작성한 Daily Notes: N개
- 활성 프로젝트: [목록]
- 주요 성취: [목록]

## Key Themes

### Theme 1: [이름]
- 어디서 나타났나: [컨텍스트]
- 왜 중요한가: [의미]
- 다음 행동: [할 것]

### Theme 2: [이름]
...

## Major Insights

1. [인사이트 + 맥락]
2. [인사이트 + 맥락]

## Progress by Project

### [프로젝트명]
- 진전: ...
- 막힌 것: ...
- 다음 주 초점: ...

## Questions Emerged
- [질문 1 — 왜 중요한가]
- [질문 2 — 왜 중요한가]

## Energy Audit
- 에너지 준 것: ...
- 에너지 뺏은 것: ...
- 조정할 것: ...

## Connections Made
- [노트 A] ↔ [노트 B]: [의미]

## Next Week's Intentions
1. [주 초점]
2. [부 초점]
3. [탐색할 것]

## To Process
- Inbox 항목: N개
- 고립된 노트: [목록]
- 누락된 연결: [식별된 것]
```

## 저장 경로

resolve가 반환한 `주간파일`. 기존 파일은 읽고 변경분만 반영한다.

## 후속 행동

분석 후 사용자에게 제안:
- 완료된 프로젝트가 있으면 → "90-archive로 이동할까요?"
- Inbox 항목 많으면 → "00-inbox 폴더를 지금 함께 정리할까요?" (일반 자료만 대상으로 하며 배선도에 등록된 원본함 자료는 이동·수정하지 않는다)
- 00-wiki에 승격할 인사이트가 있으면 → "wiki-ingest로 저장할까요?"

## 원칙

- **숫자보다 패턴에 집중** — "몇 개 했다"보다 "무엇이 반복되고 있나"
- **에너지 관찰** — 지속가능성의 핵심 지표
- **다음 주 intentions은 3개 이하** — 너무 많으면 지킬 수 없음

---

Made by Do Better Things
