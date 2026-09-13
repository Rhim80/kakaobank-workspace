# GEO 모니터링 — 검증 루프 (geo_monitor)

ko-geo의 4번째 오퍼레이션. 변환한 콘텐츠가 **실제로** 생성형 엔진 답변에 인용/언급되는지
측정해, 변환→측정→재변환 루프를 닫는다.

## 원리

특별한 백도어가 아니라 **"AI한테 반복해서 묻고, 답변에 내 브랜드/도메인이 나오는지 센다"** 이다.

1. **타깃 질문 라이브러리** — 실제 사용자가 물어볼 법한 질문을 정의
2. **반복 질의** — 각 엔진(Perplexity·Gemini·ChatGPT)에 N번씩 질문
3. **응답 파싱** — 답변 본문/출처에 브랜드명(언급)·도메인(인용)이 나오는지 판정
4. **비율 집계** — 답변이 비결정적이라 1회가 아니라 **표본 N건 중 몇 건**으로 인용률·언급률 산출

## 측정하는 3층위

- **인용(cited)**: 내 도메인이 답변 출처/본문에 직접 등장 — 가장 강한 신호
- **언급(mention)**: 링크 없이 브랜드명만 등장
- **경쟁사 점유**: 같은 질문에서 경쟁사가 몇 번 언급됐나 (상대 위치)

## 두 가지 모드

### manual (키 0개, 비용 0원 — 기본 권장)
키가 없어도 당장 된다. 엔진 채팅창(이미 구독 중인 ChatGPT·Perplexity·Gemini)에 질문을
붙여넣고, 받은 답변을 응답 파일에 모아 파싱한다.

```bash
PY=.claude/skills/ko-geo/scripts/geo_monitor.py
python $PY init geo.json                    # 설정 뼈대 → brand/queries/competitors 채우기
python $PY template geo.json resp.md        # 응답 파일 뼈대 생성
# (각 엔진 채팅창에 질문 붙여넣고, 답변을 resp.md 블록에 채움)
python $PY manual geo.json resp.md --label baseline
```

### run (키 있을 때 자동)
Perplexity sonar(실시간 웹 RAG, GEO의 핵심)·Gemini(google_search grounding) 자동 질의.
`scripts/.env`에 키 설정 후:

```bash
python $PY run geo.json --label after --engine perplexity,gemini
```

- Gemini: Google AI Studio 무료 티어로 시작 가능
- Perplexity: 사용량 과금이나 질의가 짧아 월 수천 원 수준
- ChatGPT(OpenAI)·Claude는 현재 자동 미지원 → manual 모드로 커버

## 검증 루프 사용법

```
1. baseline 측정   python $PY manual geo.json resp.md --label baseline
2. ko-geo 변환     (geo_transform) → 콘텐츠 발행
3. 대기            발행분이 각 엔진에 크롤링·색인될 때까지 (며칠~몇 주)
4. after 측정      python $PY manual geo.json resp2.md --label after
5. 비교            python $PY compare geo.json --before baseline --after after
```

## 한계 (반드시 인지)

1. **시차** — 발행 직후엔 안 오른다. 색인된 뒤에야 인용 가능. 즉시 A/B가 아닌 며칠~몇 주 루프.
2. **비결정성** — 같은 질문도 답이 매번 다르다. 표본 1건은 무의미, 비율로만 본다(samples≥5 권장).
3. **영향 가능한 엔진 한정** — 실시간 웹을 끌어오는 Perplexity·구글 AI Overviews·ChatGPT 검색모드는
   ko-geo 변환이 먹힌다. 학습 기억만으로 답하는 모드는 단기간엔 안 움직인다 → 측정 타깃을 웹검색형으로.

## config 예시

```json
{
  "brand": { "names": ["두베터", "Do Better Things"], "domains": ["dbt.imiwork.com"] },
  "competitors": ["경쟁사A", "경쟁사B"],
  "queries": ["비개발자 AI 교육 추천", "Claude Code 컨설팅 어디가 좋아"],
  "engines": ["perplexity", "gemini"],
  "samples": 5,
  "log_path": "geo-monitor-log.md"
}
```
