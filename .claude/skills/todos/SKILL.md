---
name: todos
description: 저장된 Todo 조회 및 관리. 전체/오늘/프로젝트별/오래된 것/통계 뷰 지원. "할 일 보기", "todos", "오늘 할 일", "오버듀", "할 일 통계" 등을 언급하면 자동 실행.
argument-hint: "[today|project|overdue|stats|] (없으면 전체)"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# todos

워크스페이스 루트의 `00-system/선언-표면.yaml`이 경로·형식의 원본이다. 아래 래퍼가 실행 가능한 Python 3.9 이상을 확인한다. YAML 모듈은 킷에 동봉되어 있어 패키지 설치는 없다. 선언 오류·실행 실패를 빈 목록으로 숨기지 않는다.

```bash
bash .claude/scripts/surfaces.sh todo list --mode all
```

모드: `all` 전체, `today` 선언의 오늘 섹션, `project` 프로젝트별, `overdue` 재검토 후보, `stats` 섹션별 개수. 조회는 파일을 바꾸지 않는다. 완료된 체크박스와 빈 시드 체크박스는 활성 개수에서 제외한다.

`overdue`는 원본 누락·변경·검증 불가 또는 선언된 기간 이상 갱신되지 않은 항목이다. 기한 초과 확정 판정이 아니다. `source_status`가 missing/review/unverified면 원본을 먼저 열어 아직 할 일인지 판단한다. 추가 날짜만 보고 독촉하지 않는다. source_status=current도 원본 의미상 유효함까지 보증하지 않는다.

완료 요청은 먼저 목록의 내용·id를 대조한 뒤 실행한다:

```bash
bash .claude/scripts/surfaces.sh todo done '목록의 id'
```

사용자가 이미 체크한 항목을 보관하라고 요청하면 `cleanup`을 실행한다. 완료 파일에 먼저 보관한 뒤 활성 파일에서 지운다. 중간 실패 시 같은 명령을 재실행할 수 있다. 단일 작성 세션 기준이다.

결과는 실제 항목과 개수로 요약한다. 원본 자체의 상태나 외부 서비스는 이 스킬이 변경하지 않는다.
