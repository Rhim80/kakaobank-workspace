---
name: ko-geo
description: >
  한국어 콘텐츠를 생성형 AI(ChatGPT, Perplexity, Gemini, Claude 등)의 응답에
  더 잘 인용되도록 GEO(Generative Engine Optimization) 최적화 변환·진단을 수행하는 스킬.
  Princeton/IIT KDD 2024 GEO 논문(arXiv:2311.09735)의 방법론과 실험 결과를 그대로 반영한다.

  다음과 같은 요청이 들어오면 반드시 이 스킬을 사용한다:
  - "GEO 최적화", "GEO 변환", "GEO 진단", "GEO 점수"
  - "AI 검색에 잘 나오게", "생성형 AI에 인용되게", "AI가 내 글 인용하게"
  - "퍼플렉시티/ChatGPT/Gemini에 잘 나오게 / 인용되게"
  - "내 블로그/상세페이지/랜딩페이지/콘텐츠 GEO 변환"
  - "통계 보강", "인용구 추가", "출처 표기", "유창성 다듬기" (콘텐츠 맥락에서)
  - "AI Visibility", "AI 검색 최적화", "Answer Engine Optimization"

  또한 변환 결과의 검증(모니터링)도 이 스킬이 담당한다:
  - "GEO 모니터링", "GEO 측정", "인용 측정", "인용률 측정"
  - "AI가 내 글 인용하는지 확인/추적", "퍼플렉시티/ChatGPT에 내 브랜드 나오는지"
  - "GEO 검증", "변환 효과 측정", "before/after 인용률 비교"
---

# KoGEO — Korean Generative Engine Optimization

Princeton/IIT KDD 2024 "GEO: Generative Engine Optimization" 논문 기반 한국어 콘텐츠 자동 최적화 스킬.

논문은 9가지 GEO 전략을 GEO-bench(10K 쿼리)로 검증해, 콘텐츠 가시성을 최대 +40% 끌어올릴 수 있음을 보였다. 이 스킬은 그중 효과가 검증된 방법을 한국어 콘텐츠에 적용 가능한 형태로 모듈화한다.

---

## 워크플로우

요청을 받으면 아래 3단계 중 적합한 것을 수행한다.

```
[1] geo_analyze   → 취약점 진단 (모듈별 점수 + 우선순위)
[2] geo_transform → 모듈 순차 변환
[3] geo_report    → 변환 전후 비교 + 적용된 모듈 요약
[4] geo_monitor   → 변환 콘텐츠가 실제 AI 답변에 인용되는지 측정 (검증 루프)
```

기본 동작: 요청이 모호하면 **진단 → 변환 → 보고** 순으로 실행한다.
사용자가 특정 모듈만 지정하면 해당 모듈만 적용한다.
"측정·모니터링·인용 확인" 의도면 [4] geo_monitor 로 분기한다.

상세 모듈 정의는 → [references/modules.md](references/modules.md)
도메인별 전략 매핑은 → [references/domain-strategy.md](references/domain-strategy.md)
조합 시너지/순서 설계는 → [references/combinations.md](references/combinations.md)
가시성 지표(PAWC, Subjective Impression) 정의는 → [references/methodology.md](references/methodology.md)
인용 측정/검증 루프는 → [references/monitoring.md](references/monitoring.md)

---

## [1] GEO 취약점 진단 (geo_analyze)

콘텐츠를 받으면 10개 모듈을 0~10점으로 평가한다.
점수가 낮을수록 개선 여지가 크다. 우선순위는 (낮은 점수) × (논문에서 검증된 개선 효과)로 산정한다.

**출력 형식:**

```
## GEO 취약점 진단 결과

전체 점수: XX / 100
SERP 추정 순위대: (1~2위 / 3~5위 / 미진입) — 적용 전략에 영향

| 모듈 | 점수 | 문제점 | 우선순위 |
|------|------|--------|----------|
| M1 통계 보강 (Statistics)        | X/10 | ... | 🔴/🟡/🟢 |
| M2 인용구 삽입 (Quotation)       | X/10 | ... | ... |
| M3 출처 표기 (Cite Sources)      | X/10 | ... | ... |
| M4 유창성 향상 (Fluency)         | X/10 | ... | ... |
| M5 두괄식 배치 (Position)        | X/10 | ... | ... |
| M6 전문 용어 (Technical Terms)   | X/10 | ... | ... |
| M7 쉬운 표현 (Easy-to-Understand)| X/10 | ... | ... |
| M8 권위적 어조 (Authoritative)   | X/10 | ... | ... |
| M9 키워드 과밀 회피 (Anti-Stuffing)| X/10 | ... | ... |
| M10 FAQ 블록 (Query Matching)    | X/10 | ... | ... |

**즉시 적용 Top 3**: M?, M?, M?
**예상 인용률 향상(PAWC 기준)**: +XX ~ +XX%
**도메인 추정**: (예: 뷰티/IT/맛집/법·정부…)
```

우선순위 산정:
- 🔴 (낮은 점수 + 해당 도메인 고효과 모듈) → 즉시 적용
- 🟡 (낮은 점수 + 중간 효과)
- 🟢 (이미 양호하거나 효과 작음)

---

## [2] GEO 변환 (geo_transform)

상세 프롬프트는 → [references/modules.md](references/modules.md)

**기본 적용 순서 (안전한 디폴트):**

```
M5 (두괄식 배치)        → 구조 정리부터
 → M1 (통계 보강)
 → M2 (인용구 삽입)
 → M3 (출처 표기)
 → M6 (전문 용어) / M7 (쉬운 표현) — 도메인에 따라 택1
 → M8 (권위적 어조)     — 토론·역사·논쟁성 도메인일 때만
 → M10 (FAQ 블록)       — B2C/롱테일 쿼리 노리는 콘텐츠일 때
 → M4 (유창성 향상)     — 다른 모듈 추가 후 마지막 다듬기
 → M9 (키워드 과밀 회피)— 최종 정제
```

**도메인별 최우선 모듈 (논문 Table 3 기반):**

| 도메인 | 1순위 | 2순위 | 근거 (논문) |
|--------|-------|-------|-------------|
| 법·정부·공공 | M1 통계 | M3 출처 | Statistics가 Law&Gov.에서 1위 |
| 토론·논쟁성 (정책/사회) | M8 권위적 | M1 통계 | Authoritative가 Debate 1위 |
| 역사·인물 | M2 인용구 | M8 권위적 | Quotation이 History에서 1위 |
| 사실 기반 (스펙/제품) | M3 출처 | M1 통계 | Cite Sources가 Statement/Facts 1위 |
| 사회·인물 | M2 인용구 | M4 유창성 | Quotation이 People & Society 1위 |
| 비즈니스·과학·헬스 | M4 유창성 | M1 통계 | Fluency가 Business/Science/Health 1위 |
| 의견·오피니언 | M1 통계 | M2 인용구 | Statistics가 Opinion 1위 |
| 맛집·카페 (B2C 체험) | M2 인용구 | M10 FAQ | 체험·신뢰·검색 변형 매칭 |
| 뷰티·화장품 | M1 통계 | M6 전문 용어 | 성분·효능 정량화 |
| IT·기술 블로그 | M6 전문 용어 | M1 통계 | 전문성 신호 |

**SERP 순위대별 전략 (논문 Table 2):**

| 추정 순위 | 효과 큰 전략 | 비고 |
|-----------|-------------|------|
| Rank 5+ (저순위·신규) | M3 출처 (Cite Sources +115.1%) | 가장 큰 폭 향상. **GEO의 핵심 기회** |
| Rank 4-5 | M2 인용구 + M1 통계 | 70~99% 향상 가능 |
| Rank 1-2 (이미 상위) | M4 유창성 중심 | 단독 통계·인용은 오히려 비교 우위 약화 |

**변환 원칙 (반드시 준수):**

1. **사실 불변**: 원본의 사실·의미·메시지를 절대 바꾸지 않는다. 재배치·보강만 한다.
2. **날조 금지**: 없는 통계·인용을 만들어내지 않는다. 합리적 범위 내 추정치는 반드시 "(추정)" 표기.
3. **출처 형식**: `(기관명, 연도)` 또는 `[출처명, 연도]`. URL 전체보다는 기관명+연도.
4. **자연스러운 한국어**: 직역체·번역체·문어체 과잉을 피한다.
5. **연쇄 적용**: 각 모듈의 출력을 다음 모듈의 입력으로 전달한다.
6. **Keyword Stuffing 절대 금지**: 동일 키워드 3회 이상 반복은 -8~-10% 역효과 (논문 검증).

---

## [3] 변환 보고서 (geo_report)

변환 완료 후 반드시 아래 형식으로 요약을 제공한다.

```
## KoGEO 변환 완료

**적용 모듈**: M?, M?, M? (총 N개)
**예상 인용률 향상 (PAWC 기준)**: +XX ~ +XX%
**예상 Subjective Impression 향상**: +XX ~ +XX%

### 주요 변경 사항
- M1 통계 보강: "많은 고객이" → "월 방문객 약 2,400명 (네이버 플레이스, 2024)"
- M2 인용구 삽입: 피부과 전문의 ◯◯◯ 인용 1건 추가
- M3 출처 표기: 식약처 고시 (2023) 출처 2건 추가
- M5 두괄식 배치: 결론 1문단을 최상단으로 이동
- M10 FAQ 블록: 4개 항목 추가
...

### GEO 최적화 콘텐츠
[전체 변환 결과 — 마크다운 또는 원본과 동일한 포맷으로]

### 다음 단계 권장
- (예) Perplexity·ChatGPT에서 타깃 쿼리 3개로 인용 여부 모니터링
- (예) 1~2주 후 재진단(geo_analyze)으로 효과 측정
```

---

## [4] GEO 모니터링 (geo_monitor)

변환한 콘텐츠가 실제로 AI 답변에 인용되는지 측정해 검증 루프를 닫는다. 상세는 → [references/monitoring.md](references/monitoring.md)

원리: 타깃 질문을 엔진에 N번씩 던져 답변에 내 브랜드명(언급)·도메인(인용)이 나오는 **비율**을 집계한다. 답변이 비결정적이라 1회가 아니라 표본으로 본다.

```bash
source .claude/venv.sh                    # 가상환경 활성화 (Mac·윈도우 공통)
python -m pip install python-dotenv requests        # 최초 1회

PY=.claude/skills/ko-geo/scripts/geo_monitor.py
python $PY init geo.json                  # 설정 뼈대 → brand/queries/competitors 채우기
python $PY template geo.json resp.md      # manual 응답 파일 뼈대
python $PY manual geo.json resp.md --label baseline   # 붙여넣은 답변 파싱·집계 (키 0개)
python $PY run    geo.json --label after  # 키 있으면 자동 질의(Perplexity·Gemini)
python $PY compare geo.json --before baseline --after after   # 전후 인용률 비교
```

- **manual 모드**: API 키 불필요·비용 0원. 채팅창에 질문 붙여넣고 답변을 모아 파싱. (기본 권장)
- **run 모드**: `scripts/.env`에 키 설정 시 자동. Gemini 무료 티어로 시작 가능.
- **검증 루프**: baseline 측정 → geo_transform 변환·발행 → (색인 대기, 며칠~몇 주) → after 측정 → compare.
- **한계**: ① 발행 직후엔 안 오름(색인 시차) ② 비결정적이라 비율로만(표본≥5) ③ 실시간 웹검색형 엔진에서만 변환 효과가 잡힘.

---

## 주의사항

- **Keyword Stuffing 절대 금지**: 논문 실험에서 -8% (PAWC), Subjective Impression 사실상 무변화. SEO 시대 관행을 GEO에 적용하지 말 것.
- **Authoritative 단독은 효과 약함**: 어조만 권위적으로 바꿔도 가시성은 거의 안 오른다. 토론·역사·논쟁성 도메인 외에는 다른 모듈과 조합으로만 사용.
- **Unique Words는 효과 미미**: "독특한 단어 추가"는 논문에서 baseline 수준. 이 스킬에서는 모듈로 채택하지 않음.
- **사실 날조 금지**: 없는 통계·인용·출처를 지어내지 않는다. 추정은 반드시 "(추정)" 명시.
- **도메인 정합성**: 맛집 글에 IT 전문 용어, 기술 글에 감성적 인용구 같은 부적합한 모듈은 적용하지 않는다.
- **길이 통제**: 원본 대비 +30% 초과 시 핵심 정보만 남기고 정리한다. 길이 자체는 PAWC 향상 요인이 아니다.
- **블랙박스 한계**: 논문도 명시했듯 생성형 엔진은 빠르게 진화한다. 이 스킬의 권장치는 2024년 8월 KDD 논문 시점 기준이며, 정기 재검증을 권장한다.
- **한국어 특수성**: 논문은 영어 기준이다. 한국어에서는 출처 표기 관습(괄호 vs 각주), 존칭, 인용구 따옴표 스타일을 자연스럽게 맞춘다.

---

Made by Do Better Things
