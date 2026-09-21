---
name: wiki-lint
description: |
  00-wiki 토픽 페이지 헬스체크. 모순, 고아 페이지, 오래된 정보, 누락된 교차 참조 점검.
  "wiki-lint", "위키 점검", "위키 헬스체크", "wiki health", "토픽 점검" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Edit
  - AskUserQuestion
---
먼저 `00-system/선언-표면.yaml`을 Read하고 `위키.위치`를 워크스페이스 상대 경로 `WIKI_PATH`로 사용한다. 선언이 없거나 경로가 범위 밖이면 중단한다. 옛 기본 경로로 대신 실행하지 않는다. 아래 셸 예시는 그 값을 안전하게 인용해 WIKI_PATH에 지정한 뒤 실행한다. 위키를 옮겼다면 SCHEMA·index·log와 기존 출처/링크도 함께 대조한다.


# Wiki Lint

`선언의 위키 위치` 토픽 페이지의 헬스체크.

## 기계 검사 실행

먼저 대상 워크스페이스의 `CLAUDE.md`와 `위키.위치/SCHEMA.md`를 읽는다. 대상 루트에서 다음을 실행한다(Mac·Linux·Windows Git Bash). 추가 패키지나 venv는 필요 없다.

```bash
WIKI_PY=""
for c in python3 python py; do
  if "$c" -c 'import sys; assert sys.version_info >= (3, 9)' 2>/dev/null; then WIKI_PY="$c"; break; fi
done
if [ -z "$WIKI_PY" ]; then
  echo "Python 3.9 이상이 필요합니다. setup-workspace의 Python 설치 안내를 따르세요."
else
  "$WIKI_PY" .claude/skills/wiki-lint/scripts/wiki_check.py --root "$PWD" --wiki-dir "$WIKI_PATH" --json
fi
```

변경분은 같은 명령에 `--files 토픽A.md 토픽B.md`를 추가한다. 다른 폴더/글로벌에 설치한 스킬에서 실행할 때는 검사기의 실제 경로와 `--root "대상 워크스페이스 절대경로"`를 함께 지정한다. 루트를 생략하면 스크립트가 설치된 워크스페이스를 검사하며 홈이나 다른 PKM을 찾지 않는다.

종료 코드 0은 구조 오류 없음(경고는 남을 수 있음), 1은 구조 오류, 2는 실행 실패다. Python이 없거나 실행이 실패했으면 통과로 보고하지 않는다. `--index`는 index 수정 후보 출력만 하며 원본 파일로 직접 리다이렉트하지 않는다.

## 동작 방식

### Step 1: 전체 기계 검사 후 토픽 페이지 수집

위 명령으로 전체 검사를 실행하고 출력의 root·scope·files_read와 오류/경고를 기록한다. 아래 A~M 중 기계로 잡히는 항목은 출력에서 가져오고, 의미·역방향 링크·허브·log는 원문을 읽어 별도로 판단한다.

```
WIKI_PATH = 00-system/선언-표면.yaml의 위키.위치
```

- Glob: `$WIKI_PATH/*.md` (SCHEMA.md, README.md, index.md, log.md 제외)
- 각 파일의 제목, Related 섹션, Last enriched 날짜 수집

### Step 2: 점검 실행 (A~M)

#### A. 고아 페이지 (Orphan Pages)
- index.md에 등재되지 않은 토픽 페이지
- 다른 토픽의 Related에서 한 번도 참조되지 않는 페이지
- **조치**: index.md에 추가 제안

#### B. 죽은 링크 (Dead Links)
- Related 섹션에서 참조하는 `[[토픽]]`이 실제 파일로 없음
- **조치**: 링크 제거 또는 새 토픽 생성 제안

#### C. 오래된 페이지 (Stale Pages)
- **기한은 페이지 유형마다 다르다**: concept 180일 / entity 60일 / synthesis 120일. 유형은 `index.md`의 유형 칸에서 읽는다
- 일괄 90일로 재면 **안 바뀌어도 정상인 페이지가 경고를 채운다** — 가치·개념은 반년을 묵어도 정상이고 조직·도구는 두 달이면 낡는다. 경고에 볼 필요 없는 것이 섞이면 목록 자체를 안 보게 된다
- **이 검사가 통과시키면 안 되는 경우**: index에서 유형을 못 읽은 페이지를 조용히 건너뛰는 것. 유형 미표기는 따로 세어 보고한다
- **조치**: "이 토픽은 여전히 유효한가?" 플래그

#### D. 모순 탐지 (Contradictions)
- 서로 다른 토픽 페이지에서 동일 주제에 대해 상충하는 주장
- Grep으로 공통 키워드 가진 페이지 쌍을 찾고 내용 비교
- **조치**: `[!contradiction YYYY-MM-DD]` 플래그(**날짜를 플래그 안에** 넣는다 — 밖에 쓰면 D-2가 나이를 못 센다) + 최신 여부 표시

#### D-2. 닫히지 않은 모순 (Open Contradictions)
- 다는 규칙만 있고 **떼는 규칙이 없으면 열린 채 쌓인다.** 열린 지 30일 넘은 플래그를 모아 보여준다
- 닫는 법: 판정되면 지우지 않고 `[!superseded YYYY-MM-DD → 이긴 근거 한 줄]`로 바꾼다. 진 쪽 본문은 그대로 남긴다 — 왜 그렇게 정했는지가 남아야 같은 논쟁이 다시 열리지 않는다
- **lint가 닫지 않는다** — 어느 쪽이 맞는지는 사용자가 정한다
- **이 검사가 통과시키면 안 되는 경우**: SCHEMA·가이드처럼 **형식을 설명하는 문장** 속 플래그를 실제 모순으로 세는 것, footer 요약에서 그 플래그를 가리키는 참조를 세는 것
- **조치**: 목록만 제시

#### E. 누락된 교차 참조 (Missing Cross-References)
- 본문에서 다른 토픽명이 언급되지만 Related에 링크 없음
- **조치**: Related에 추가 제안

#### F. 누락된 토픽 (Missing Pages)
- 여러 페이지에서 참조되지만 전용 페이지 없음
- **조치**: 새 토픽 페이지 생성 제안

#### G. 비대한 페이지 (Oversized Pages)
- SCHEMA 「기계 검사 기준」의 근거 크기 경고를 확인하고 분리 필요성은 내용으로 판단
- **조치**: 독립 토픽으로 분리 제안

#### H. 데이터 갭 (Data Gaps)
- 주장은 있지만 source 인용 없음
- 반복 언급되지만 자체 근거 부족한 개념
- **조치**: 웹 검색으로 보강 가능한 갭 식별 → 리서치 제안

#### I. 활동 분석 (log.md 기반)
- 한 번도 enriched 안 된 시드 페이지
- 최근 30일간 ingest 없는 카테고리
- **조치**: ingest 필요성 제안

#### J. Infobox 누락/훼손
- H1 바로 아래 `> **관련**:` 줄 없음
- 관련 링크 6개 초과 (덤프)
- Infobox wikilink가 실제 파일로 없음
- **조치**: 누락 시 `## Related`에서 상위 6개 추출, 초과 시 indegree 약한 것 제거

#### K. index 한 줄 설명 품질
- 키워드 콤마 덤프 탐지 (쉼표 3개+ 또는 토큰 8개+)
- 70자 초과
- 문장이 아닌 명사구
- **조치**: `## 핵심` 첫 문장 기반 재작성 제안

#### L. Facets 비대/중복
- Infobox Facets가 SCHEMA 권장 상한 초과
- Facets 키워드가 `## 근거`에서 더 이상 언급 안 됨
- **조치**: 약한 키워드 제거 제안

#### M. 허브 블록 표류
- index.md 상단 `> **허브 토픽**` 5개가 실제 indegree 상위 5개와 불일치
- indegree = 각 페이지 Infobox 관련 줄에 자기 토픽이 등장하는 횟수
- **조치**: 상위 5개로 재정렬 제안

### Step 3: 헬스 리포트

```markdown
# Wiki Health Report — YYYY-MM-DD

## 요약
- 총 토픽: N개
- 건강: X개 | 주의: Y개 | 조치 필요: Z개

## 상세

### 고아 페이지 (N개)
| 페이지 | 상태 | 제안 |
|--------|------|------|

### 죽은 링크 (N개)
...

(등)
```

### Step 4: 사용자 승인 후 수정

- AskUserQuestion으로 수정할 항목 확인
- 승인된 항목만 Edit (index.md, Related 등)
- 수정 뒤 같은 범위의 기계 검사를 다시 실행한다. 지식 보강이 없는 정리는 Last enriched를 올리지 않는다.
- 수정 내용과 검사 결과를 SCHEMA log 규약에 따라 기록:
  ```
  ## [YYYY-MM-DD] lint | Wiki Health Check
  - 고아 페이지 N개 → index.md에 추가
  - 누락된 교차 참조 N개 → Related에 추가
  ```

## 핵심 원칙

- **리포트 먼저, 수정은 승인 후**: 자동으로 고치지 않음
- **모순은 플래그만**: 판단은 사용자
- **과잉 제안 금지**: 확실한 문제만 리포트

---

Made by Do Better Things
