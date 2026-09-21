---
name: daily-review
description: 어제/오늘 git 변경사항을 분석하고, daily note + todos 기반으로 오늘 우선순위를 제안. "일일 리뷰", "오늘 뭐 했지", "어제 작업 정리", "daily review" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
---

# daily-review

워크스페이스 루트의 `00-system/선언-표면.yaml`이 경로·형식의 원본이다. 아래 래퍼가 실행 가능한 Python 3.9 이상을 확인한다. YAML 모듈은 킷에 동봉되어 있어 패키지 설치는 없다. 선언 오류·실행 실패를 빈 목록으로 숨기지 않는다.

```bash
bash .claude/scripts/surfaces.sh resolve
bash .claude/scripts/surfaces.sh todo list --mode all
```

resolve의 오늘 노트를 읽는다. 없으면 생성했다고 하지 말고 기존 기록·할 일 기준으로 리뷰하며 daily-note를 안내한다. git 저장소면 어제~오늘 git log에 status/diff의 미커밋 변경도 합쳐 실제 변경 파일을 읽는다. 저장소가 아니면 노트와 할 일만 분석한다.

우선순위는 선언의 오늘/이번주 섹션, 기한, 업무 원본을 대조해 최대 3개 제안한다. 원본이 missing/review/unverified인 할 일은 먼저 실제 근거를 확인하며 오래됐다는 이유만으로 올리지 않는다. 진행은 선언의 `진행.루트`와 배선도 줄기 기록을 함께 본다.

변경 요약·우선순위와 근거·이어갈 일을 짧게 보고한다. 이 스킬은 읽기 전용이다. 파일 생성·완료 이동·외부 변경을 하지 않는다.
