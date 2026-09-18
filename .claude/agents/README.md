# Agents

이 폴더는 이 워크스페이스 전용 서브에이전트를 담습니다.

## Agents란?

Agents는 **독립된 컨텍스트에서 복잡한 작업을 수행**하는 Claude의 하위 인스턴스입니다.

- 메인 세션의 컨텍스트 오염 방지 (큰 리서치, 병렬 작업 등)
- 명시적 위임: `research-worker로 조사해줘`
- 암묵적 위임: description에 맞는 작업을 Claude가 자동으로 위임

## 파일 구조

```
.claude/agents/
├── README.md             # 이 파일
└── [agent-name].md       # 각 에이전트 1파일 (YAML frontmatter + 시스템 프롬프트)
```

## 에이전트 파일 구조

```yaml
---
name: agent-name
description: 이 에이전트를 언제 쓰는지. 메인이 위임 판단할 때 이 설명을 봄.
tools: Read, Write, Bash, ...  # 허용 도구
---

# 에이전트 시스템 프롬프트

역할, 절차, 출력 형식 등
```

## 포함된 에이전트

| 에이전트 | 역할 | 호출 예시 |
|---------|------|----------|
| `research-worker` | 외부 웹 다중 소스 교차검증 리서치 | "3개 소스로 검증한 시장 조사" |
| `analysis-worker` | 데이터에서 패턴 발견 → 의미 해석 → 행동 연결 (집계·비율은 python으로 직접 계산) | "이 데이터에서 패턴 찾아줘" |
| `content-worker` | 글 작성, 문서 생성, 콘텐츠 구조화 | "이 분석으로 블로그 글 작성" |
| `verify-worker` | 요청한 일이 요청대로 됐는지 독립된 눈으로 판정 (고치지 않음) | "제대로 했는지 확인해줘" |

`verify-worker`가 있는 이유 — **일한 세션이 자기 일을 채점하면 놓친다.** 방금 판단을
내린 쪽은 그 판단을 다시 의심하지 못한다. 그래서 물려받은 것이 없는 다른 눈이 필요하다.

## 체인 패턴

전형적인 워커 체인:

```
1. research-worker  → 외부 정보 수집
2. analysis-worker  → 수집 데이터 분석
3. content-worker   → 분석 결과로 문서 작성
```

`verify-worker`는 체인 밖이다 — 일이 끝난 뒤 "시킨 것이 됐나"를 따로 본다.

## 호출 방법

메인 세션에서 자연어로 호출:
- "research-worker로 ~ 조사해줘"
- "이 데이터 analysis-worker로 분석"
- 또는 description에 맞는 작업이면 Claude가 자동 위임

복잡한 파이프라인은 여러 워커를 순차 또는 병렬로 연결.

---

Made by Do Better Things
