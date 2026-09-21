---
name: todo
description: 빠르게 Todo를 추가 (우선순위 감지, 프로젝트 태그 지원). "할 일 추가", "todo 추가", "이거 해야해", "기억해둬" 등을 언급하면 자동 실행.
argument-hint: "[우선순위] [프로젝트] 할 일 내용"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# todo

워크스페이스 루트의 `00-system/선언-표면.yaml`이 경로·형식의 원본이다. 아래 래퍼가 실행 가능한 Python 3.9 이상을 확인한다. YAML 모듈은 킷에 동봉되어 있어 패키지 설치는 없다. 선언 오류·실행 실패를 빈 목록으로 숨기지 않는다.

사용자 입력에서 내용·우선순위·프로젝트·기한·근거 원본을 구분한다. `[urgent]`/`[high]`는 high, `[low]`는 low, `[waiting]`는 waiting, 기본은 normal. 다른 대괄호는 프로젝트다. 실제 섹션 이름은 YAML의 `할일.새항목라우팅`과 `할일.섹션`에서 읽는다.

```bash
bash .claude/scripts/surfaces.sh todo validate
bash .claude/scripts/surfaces.sh todo add '할 일 내용' --priority normal
```

필요한 경우 `--project '프로젝트' --source '워크스페이스 상대 원본 경로' --due 'YYYY-MM-DD'`를 더한다. 원본을 찾지 못했으면 경로를 꾸며 넣지 말고 사용자에게 알린다. 사용자 문자열은 셸 인자가 되므로 안전하게 인용한다.

- 배선도에서 받은 자료는 반드시 `--key 'wiring:자료id:항목번호'`를 전달한다. 스크립트가 원본 링크·할 일 id·반영 표식을 함께 저장한다. 재실행과 완료 보관 후 재시도 모두 같은 키로 한다.
- 기존 항목이 반환되면 새로 추가했다고 하지 않는다. 이미 완료된 항목을 다시 열지 않는다. 반복 업무의 새 회차라면 날짜 등을 포함한 별도 `--key`를 쓴다.
- 파일이나 섹션이 없어도 기존 내용을 덮어쓰지 않는다. 추가·중복 판정은 스크립트에 맡긴다.
- 출력의 added/id/section 또는 location/done을 바탕으로 한 줄 보고한다.

로컬 할 일만 관리한다. 글로벌 PKM의 업무별 분류·Google Tasks 동기화는 포함하지 않는다. 완료·조회는 `todos`가 맡는다.
