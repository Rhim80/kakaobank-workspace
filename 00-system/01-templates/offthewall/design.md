# 오프더월 · 풀노리 — 디자인 가이드

> 한 건물 두 층. 1층 오프더월(디저트 카페), 2층 풀노리(기프트샵·편집샵).
> 이 파일은 보고서·대시보드·안내물 어떤 산출물이든 참조하면 두 사업장의 톤이 그대로 적용되는 단일 출처다.

---

## Overview

오프더월의 브랜드 캔버스는 **종이 상자의 색**이다. 테이크아웃이 중심인 가게라 손님이 브랜드를 만나는 실물은 매장 벽이 아니라 **들고 나가는 박스와 컵**이고, 그래서 시스템의 바닥은 화면처럼 흰 백색이 아니라 크래프트 종이 쪽으로 반 걸음 물러난 `{colors.canvas}`다. 그 위에 굽는 것의 색이 얹힌다 — 타르트 크러스트의 `{colors.crust}`, 강릉 옥수수의 `{colors.corn}`. 색을 따로 고르지 않았다. **파는 것에서 가져왔다.**

이 방향은 유도가 아니라 **두 브랜드가 스스로 쓰는 말과 맞는다.** 오프더월은 태그라인이 `sweet from the earth`이고 매장 외관에 `natural & simple`이 적혀 있다. 풀노리는 사이트에 "자연의 모습을 통하여 우리의 소중한 마음을 전하는 곳", "우리의 기억이 기록이 되는 곳"이라고 쓴다. 세 문구가 전부 **자연·심플·기록** 한 방향이다.

브랜드의 전압은 장식이 아니라 **품목명 자체**에서 나온다. "강릉 옥수수 에그타르트", "강릉 감자&잠봉 에그타르트" — 지역명이 메뉴 이름 안에 들어가 있는 가게다. 그래서 이 시스템은 지역 정체성을 배경 사진이나 일러스트로 설명하지 않는다. **글자로 말하고 만다.** 디스플레이 타입은 크고 담백하게, 꾸밈 없이.

운영의 성격이 레이아웃을 정한다. 하루 다섯 시간 반 열고, 이틀 쉬고, 다 팔리면 닫는다. 만든 만큼만 파는 가게의 리듬이라 **화면도 빽빽하지 않다** — 여백이 넉넉하고, 한 화면에 밀어 넣지 않고, 다 담으려 하지 않는다. 2층 풀노리는 같은 뼈대를 쓰되 `{colors.pungnori}` 하나로 갈린다. 두 층은 다른 브랜드가 아니라 **같은 건물의 두 층**이므로, 시스템을 나누지 않고 색 하나로만 구분한다.

**Key Characteristics:**
- 캔버스는 크래프트 종이 쪽 오프화이트(`{colors.canvas}`). 순백(#fff)은 카드 표면에만 쓰고 페이지 바닥으로는 쓰지 않는다.
- 색은 전부 파는 것에서 왔다 — 크러스트(`{colors.crust}`), 옥수수(`{colors.corn}`), 구운 표면(`{colors.bake}`).
- 강조색은 **하나씩만** 쓴다. 1층은 `{colors.corn}`, 2층은 `{colors.pungnori}`. 한 화면에 둘이 같이 나오는 건 두 층을 나란히 비교할 때뿐이다.
- 모서리는 `{rounded.md}`(8px)가 기본. 타르트 틀의 완만한 곡선에서 왔고, 각지지도 둥글지도 않다.
- 그림자는 거의 안 쓴다. 층은 그림자가 아니라 **1px 헤어라인**(`{colors.hairline}`)과 배경 톤 차이로 만든다.
- 여백이 시스템의 절반이다. 주요 구획 사이 `{spacing.section}`(72px), 카드 안쪽 `{spacing.xl}`(32px).
- 한글이 본문이다. 모든 텍스트 블록에 `word-break: keep-all`을 건다 (아래 Typography 참조).
- 숫자는 표에서 **오른쪽 정렬 + tabular-nums**. 매출 자료가 주된 산출물이라 자릿수가 흔들리면 못 읽는다.

---

## Colors

> **측정 상태**: 아래 색은 **확인된 메뉴 구성과 운영 성격에서 유도한 값이고, 매장·패키지 실측이 아니다.** 캠프에서 실물과 대조해 교체할 것 (Known Gaps 참조). 유도 근거는 각 항목에 적었다.
>
> **공개된 곳에 브랜드 지정 hex는 없다** (2026-09-04 확인). 다만 후기 목격담으로 **오프더월은 파랑(차양)·초록(우산) 포인트**, **풀노리는 파랑 유리와 파스텔~무채색 소품**이 반복해 나온다 — 2층 강조색을 파랑 계열(`{colors.pungnori}`)로 둔 것은 이와 어긋나지 않는다. 목격담은 hex의 근거가 못 되므로 값은 만들지 않았다.

### Brand & Accent
- **Corn** (`{colors.corn}` — #E8B54D): 1층 오프더월의 시그니처. 인기 메뉴 4종 중 3종이 옥수수 라인(옥수수 타르트·옥수수 에그타르트·옥수수 밀크티)이고 협업 상품도 옥수수 아이스크림이다. 브랜드의 중심 재료라 강조색으로 올렸다.
- **Crust** (`{colors.crust}` — #8B5E34): 구운 타르트 껍질 톤. 제목·강조 텍스트, 아이콘 라인에 쓴다. 갈색 계열이지만 탁하지 않게.
- **Pungnori** (`{colors.pungnori}` — #3A5A6B): 2층 풀노리 전용. 1층의 따뜻한 계열과 확실히 갈리도록 차가운 청록-네이비 쪽으로 뒀다. **1층 자료에 이 색을 쓰지 않는다.**
- **Bake** (`{colors.bake}` — #C9832F): 옥수수와 크러스트 사이의 중간 톤. 그래프의 두 번째 계열, 강조 배지에 쓴다. **면으로만 쓴다** — 이 색 위 흰 글자는 3.10:1로 작은 글자에 못 쓴다(큰 글자만). 글자를 얹어야 하면 `{colors.ink}`(5.09:1).

### Surface
- **Canvas** (`{colors.canvas}` — #FAF7F1): 페이지 바닥. 크래프트 종이 쪽으로 반 걸음 물러난 오프화이트.
- **Surface Card** (`{colors.surface-card}` — #FFFFFF): 카드·표 바탕. 캔버스 위에서 한 단 떠 보이는 유일한 장치.
- **Surface Soft** (`{colors.surface-soft}` — #F2ECE1): 표 머리행, 접힌 영역, 보조 띠.
- **Surface Sunk** (`{colors.surface-sunk}` — #EBE3D5): 인용 블록, 코드 블록, 비활성 영역.

### Hairlines & Borders
- **Hairline** (`{colors.hairline}` — #E0D7C6): 1px 기본 구분선. 표 행 사이, 카드 테두리, 구획 나누기.
- **Hairline Strong** (`{colors.hairline-strong}` — #C9BCA4): 표 머리행 아래, 합계 행 위처럼 **의미가 있는 선**에만.

### Text
- **Ink** (`{colors.ink}` — #2A2119): 제목과 본문 기본색. 순검정 대신 크러스트 쪽으로 기울인 진갈색 — 종이 캔버스 위에서 순검정은 뜬다.
- **Body** (`{colors.body}` — #4A4038): 본문 문단.
- **Muted** (`{colors.muted}` — #736857): 캡션, 단위 표기, 각주, 표의 보조 열. 캔버스 위 대비 **5.11:1**(AA 통과).
- **On Accent** (`{colors.on-accent}` — #FFFFFF): `{colors.crust}`·`{colors.pungnori}` 배경 위 텍스트. **`{colors.corn}` 위에는 쓰지 않는다** — 대비가 모자란다. 옥수수 배경 위 글자는 `{colors.ink}`.

### Semantic
- **Up** (`{colors.up}` — #2F7D5C): 증가·달성. 매출이 늘어난 방향.
- **Down** (`{colors.down}` — #B0452F): 감소·미달. 붉은 계열이되 크러스트와 싸우지 않게 채도를 낮췄다.
- **Warn** (`{colors.warn}` — #8F6410): 조기 소진·재고 임박처럼 **지금 손봐야 하는** 신호. 캔버스 위 **4.91:1**, 이 색 위 흰 글자 **5.25:1** — 둘 다 AA.
- **Neutral** (`{colors.neutral}` — #736857): 변화 없음. `{colors.muted}`와 같은 값이다 — 중립은 강조가 아니라 배경이라는 뜻.

> 증감을 **색으로만** 표시하지 않는다. 항상 부호(▲▼ 또는 +/−)를 같이 쓴다 — 색맹 대응이자 흑백 인쇄 대응이다. 매출 자료는 실제로 인쇄된다.

---

## Typography

### Font Family

한글이 본문이므로 **Pretendard**를 기본으로 쓴다. 폴백 스택:

```
Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
"Malgun Gothic", "맑은 고딕", system-ui, sans-serif
```

숫자 표기는 `font-variant-numeric: tabular-nums`를 켠다 — 표에서 자릿수가 안 흔들려야 한다.

### 한글 조판 (필수 — 모든 HTML 산출물)

```css
body{ word-break:keep-all; overflow-wrap:break-word; line-break:strict; text-wrap:pretty; }
h1,h2,.headline,.display{ text-wrap:balance; }
```

- `keep-all` 없이는 한글이 **글자 단위로** 끊긴다("아닙니" + "다.").
- 헤드라인 `max-width`에 `ch` 단위를 쓰지 않는다 (라틴 "0" 폭 기준이라 한글엔 너무 좁다) → `vw`·`px`·`em`.
- 한글 자간은 `.06em`까지. 넓은 자간은 라틴 대문자 라벨에만.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xl}` | 44px | 700 | 1.25 | -0.01em | 보고서 표지 제목 |
| `{typography.display-lg}` | 32px | 700 | 1.3 | -0.01em | 큰 구획 제목 ("8월 격주 매출 정리") |
| `{typography.display-md}` | 24px | 700 | 1.35 | 0 | 절 제목 ("객단가 해부") |
| `{typography.title-lg}` | 19px | 600 | 1.45 | 0 | 카드 제목, 표 캡션 |
| `{typography.title-sm}` | 16px | 600 | 1.5 | 0 | 소제목, 표 머리행 |
| `{typography.body-md}` | 15px | 400 | 1.75 | 0 | 본문 기본. 한글은 행간을 넉넉히 |
| `{typography.body-sm}` | 13.5px | 400 | 1.7 | 0 | 표 안 본문, 보조 설명 |
| `{typography.metric-xl}` | 36px | 700 | 1.1 | -0.02em | KPI 카드의 큰 숫자 |
| `{typography.metric-delta}` | 14px | 600 | 1.3 | 0 | 증감 표기 (▲ +16.8%) |
| `{typography.label-caps}` | 11px | 600 | 1.3 | 0.08em | 라틴 대문자 라벨 (KPI, TOTAL). **한글에는 안 쓴다** |
| `{typography.caption}` | 12px | 400 | 1.6 | 0 | 단위·출처·각주 |

### Principles

한글 본문의 행간은 **1.7 이상**을 유지한다 — 라틴 기준 1.5를 그대로 쓰면 한글은 빽빽해 보인다. 굵기 대비는 700과 400 두 단만 쓰고 중간 굵기를 남발하지 않는다. 제목을 키워서 위계를 만들지, 굵기를 여러 단으로 쪼개 만들지 않는다.

**대문자 letterspacing은 라틴에만.** 한글에 자간을 벌리면 낱글자가 흩어져 읽기 어려워진다.

---

## Layout

### Spacing System
- **기본 단위**: 4px.
- **토큰**: `{spacing.xxs}` 4 · `{spacing.xs}` 8 · `{spacing.sm}` 12 · `{spacing.md}` 16 · `{spacing.lg}` 24 · `{spacing.xl}` 32 · `{spacing.xxl}` 48 · `{spacing.section}` 72.
- 주요 구획 사이 세로 여백은 `{spacing.section}`. 카드 안쪽 패딩은 `{spacing.xl}`. 표 셀 패딩은 세로 `{spacing.sm}` 가로 `{spacing.md}`.

### Grid & Container
- 본문 최대 폭 **760px** (A4 인쇄와 화면 읽기 모두 편한 폭).
- 대시보드형 산출물은 최대 **1120px**, 12컬럼, 거터 `{spacing.lg}`.
- KPI 카드는 4-up(데스크톱) → 2-up(태블릿) → 1-up(모바일).
- **표는 자기 컨테이너 안에서 가로 스크롤**(`overflow-x: auto`). 페이지 본문이 가로로 밀리면 안 된다.

### Whitespace Philosophy
다 담으려 하지 않는다. 만든 만큼만 파는 가게의 시스템이라 **한 화면에 밀어 넣는 것보다 덜어내는 쪽**이 맞다. 표가 길면 잘라서 "상위 5개"로 두고 나머지는 접는다. 여백은 남는 공간이 아니라 읽는 속도를 만드는 장치다.

---

## Elevation & Depth

| Level | 쓰임 | 값 |
|---|---|---|
| 0 | 페이지 바닥 | `{colors.canvas}`, 그림자 없음 |
| 1 | 카드·표 | `{colors.surface-card}` + 1px `{colors.hairline}` 테두리, 그림자 없음 |
| 2 | 강조 카드 (KPI, 요약) | Level 1 + `0 1px 3px rgba(42,33,25,.06)` |
| 3 | 떠 있는 것 (툴팁, 드롭다운) | `0 6px 20px rgba(42,33,25,.12)` |

**Level 3은 화면 전용이다.** 인쇄 산출물(PDF)에는 그림자를 넣지 않는다 — 회색 얼룩으로 찍힌다.

### Decorative Depth
장식용 깊이는 쓰지 않는다. 그라디언트·글로우·유리 효과 없음. 깊이가 필요하면 배경 톤을 한 단 바꾼다(`{colors.surface-soft}` → `{colors.surface-sunk}`).

---

## Shapes

### Border Radius Scale

| Token | 값 | 쓰임 |
|---|---|---|
| `{rounded.none}` | 0 | 표 셀, 전체 폭 띠 |
| `{rounded.sm}` | 4px | 배지, 태그, 인라인 칩 |
| `{rounded.md}` | 8px | **기본값** — 카드, 버튼, 입력창 |
| `{rounded.lg}` | 14px | 큰 요약 패널, 이미지 블록 |
| `{rounded.full}` | 999px | 원형 아이콘 버튼, 상태 점 |

### Photography Geometry
사진은 `{rounded.lg}`로 자른다. 인물보다 **실물**(타르트 단면, 박스, 매대)을 쓰고, 화면 전체를 덮는 풀블리드 사진은 쓰지 않는다 — 캔버스 자체가 이미 종이 톤이라 사진이 덮으면 브랜드 바닥이 사라진다.

---

## Components

### Top Navigation
높이 64px, 배경 `{colors.canvas}`, 하단 1px `{colors.hairline}`. 로고는 왼쪽 워드마크. 현재 위치는 `{colors.crust}` 텍스트 + 하단 2px 밑줄. 그림자 없음.

### Buttons
- **Primary**: 배경 `{colors.crust}`, 글자 `{colors.on-accent}`, `{rounded.md}`, 패딩 `{spacing.sm}` `{spacing.lg}`, 굵기 600. 호버 시 명도 −8%.
- **Secondary**: 배경 투명, 1px `{colors.hairline-strong}` 테두리, 글자 `{colors.ink}`. 호버 시 배경 `{colors.surface-soft}`.
- **Quiet**: 테두리 없음, 글자 `{colors.muted}`. 표 안 동작에만.
- 최소 높이 40px (터치 44px). **라벨은 한글 문장 그대로** — 억지 영문 대문자 라벨을 쓰지 않는다.

### Cards & Containers
배경 `{colors.surface-card}`, 1px `{colors.hairline}`, `{rounded.md}`, 패딩 `{spacing.xl}`. 카드 제목은 `{typography.title-lg}`, 제목과 내용 사이 `{spacing.md}`.

### Inputs & Forms
높이 40px, 배경 `{colors.surface-card}`, 1px `{colors.hairline-strong}`, `{rounded.md}`, 안쪽 패딩 `{spacing.md}`. 포커스 시 테두리 `{colors.crust}` + 2px 외곽선 `rgba(139,94,52,.18)`. 라벨은 입력창 위에 `{typography.title-sm}`.

### Signature Components

**층 배지 (Floor Badge)** — 이 시스템의 시그니처. 1층/2층 자료를 구분하는 작은 알약.
`{rounded.full}`, 패딩 `{spacing.xxs}` `{spacing.sm}`, `{typography.caption}`.
1층은 배경 `{colors.corn}` + 글자 `{colors.ink}`, 2층은 배경 `{colors.pungnori}` + 글자 `{colors.on-accent}`.
**두 사업장 숫자가 같이 나오는 표·그래프에는 반드시 붙인다** — 이 자료의 가장 흔한 오독이 "어느 층 숫자인지 헷갈리는 것"이다.

**KPI 카드** — 라벨(`{typography.label-caps}` 또는 한글이면 `{typography.title-sm}`) → 큰 숫자(`{typography.metric-xl}`, tabular-nums) → 증감(`{typography.metric-delta}`, 부호 + `{colors.up}`/`{colors.down}`) → **의미 한 줄**(`{typography.caption}`, `{colors.muted}`).
마지막 한 줄은 **생략 금지**다. 숫자만 있는 카드는 미완성으로 본다.

**소진 표시 (Sold-out Marker)** — 조기 마감·품절을 나타내는 표 안 표식. `{colors.warn}` 점 + 시각 텍스트. 배경을 통째로 칠하지 않는다.

### Footer
배경 `{colors.surface-soft}`, 상단 1px `{colors.hairline}`, 패딩 세로 `{spacing.xxl}`. 텍스트 `{colors.muted}`, `{typography.body-sm}`. 매장 정보(주소·영업시간·휴무)를 담는다.

---

## Do's and Don'ts

### Do
- 색은 파는 것에서 가져온다. 새 색이 필요하면 메뉴판을 먼저 본다.
- 1층 자료엔 `{colors.corn}`, 2층 자료엔 `{colors.pungnori}` — 하나씩만.
- 두 층 숫자가 한 화면에 있으면 **층 배지를 붙인다.**
- 숫자 옆에 항상 의미 한 줄.
- 증감은 색 + 부호를 같이.
- 한글 텍스트 블록에 `word-break: keep-all`을 건다.
- 표 숫자는 오른쪽 정렬 + tabular-nums.
- 표가 길면 상위 N개로 자르고 나머지는 접는다.

### Don't
- 페이지 바닥을 순백(#fff)으로 두지 않는다 — 캔버스는 `{colors.canvas}`.
- `{colors.corn}` 배경 위에 흰 글자를 쓰지 않는다 (대비 부족). `{colors.ink}`를 쓴다.
- 1층 자료에 `{colors.pungnori}`를 섞지 않는다. 그 반대도.
- 그라디언트·글로우·유리 효과를 쓰지 않는다.
- 인쇄 산출물에 그림자를 넣지 않는다.
- 한글에 letterspacing을 벌리지 않는다.
- 증감을 색으로만 표시하지 않는다.
- 풀블리드 배경 사진으로 화면을 덮지 않는다.

---

## Responsive Behavior

### Breakpoints

| 이름 | 폭 | 비고 |
|---|---|---|
| Mobile | ~479px | 매니저가 실제로 보는 화면. 카톡으로 링크가 간다 |
| Mobile L | 480~767px | |
| Tablet | 768~1023px | |
| Desktop | 1024~1279px | |
| Wide | 1280px~ | 최대 컨테이너 1120px에서 멈춘다 |

### Touch Targets
최소 44×44px. 표 안 동작 버튼도 예외 없음 — 매니저가 매장에서 휴대폰으로 연다.

### Collapsing Strategy
- KPI 4-up → 2-up(Tablet) → 1-up(Mobile).
- 표는 가로 스크롤로 유지한다. **모바일에서 표를 카드로 풀어 헤치지 않는다** — 매출 표는 열끼리 비교하는 게 목적이라 카드로 쪼개면 비교가 안 된다.
- 2단 본문은 Tablet 이하에서 1단.
- 사이드 주석은 Mobile에서 본문 아래로 내린다.

### Image Behavior
`max-width: 100%`, 비율 유지. 사진은 Mobile에서 `{rounded.md}`로 줄인다.

---

## Iteration Guide

1. **새 색이 필요하면 메뉴판·패키지를 먼저 본다.** 이 시스템의 색은 전부 파는 것에서 왔다 — 임의로 팔레트를 늘리면 그 규칙이 깨진다.
2. **강조색은 한 화면에 하나.** 둘째 강조가 필요하면 `{colors.bake}`를 쓰고, 셋째가 필요하면 그건 화면을 나눠야 한다는 신호다.
3. **깊이가 필요하면 그림자 대신 배경 톤을 한 단 바꾼다.**
4. **숫자를 추가할 때마다 의미 줄도 같이 추가한다.** 숫자만 늘리면 읽는 사람이 판단을 못 한다.
5. **한글 조판 규칙은 새 컴포넌트에도 그대로 붙인다** — `keep-all`을 body에 한 번 걸었다고 끝이 아니라, 별도 렌더 컨테이너(캔버스·iframe·PDF 템플릿)를 만들면 거기에도 건다.
6. **인쇄를 먼저 확인한다.** 이 브랜드의 산출물은 화면보다 종이로 자주 간다 — `Cmd+P` 미리보기에서 그림자·배경색이 어떻게 찍히는지 보고 나서 완료로 한다.
7. **두 층을 다루는 화면은 배지부터 붙이고 시작한다.** 나중에 붙이면 빠뜨린다.
8. **토큰 키로만 참조한다.** 산출물 코드에 hex를 직접 쓰면 다음 개편 때 못 찾는다.

---

## Known Gaps

- **색상 값 전부가 미실측이다.** 위 hex는 **확인된 메뉴 구성(옥수수 라인 중심)과 운영 성격(테이크아웃·소량 생산)에서 유도한 값**이고, 매장 간판·인테리어·패키지·인스타 피드에서 뽑은 값이 아니다. **캠프에서 이도훈 님께 실물(박스·컵·스티커·간판)을 한 번 보여달라고 해서 대조하고 교체한다.** 어긋나면 이 파일의 Colors 절만 고치면 나머지는 토큰 참조라 자동으로 따라온다.
- **풀노리 워드마크는 확인됐다** (`pulnori.com`, 2026-09-04) — 심볼 없이 **소문자 워드마크 단독**이고, 사이트 전체에서 `p u l n o r i`처럼 **글자 사이를 띄워** 표기한다. 사이트 CSS는 Montserrat 계열 산세리프를 지정한다. 풀노리 자료의 제목에 이 스페이싱을 쓰면 브랜드가 산다. **오프더월 로고는 여전히 미확인** — 계정 표시명이 소문자 `offthewall`인 것만 안다(세리프/산세리프·심볼 유무 모름).
- **풀노리의 독자 아이덴티티는 일부 확인됐다.** 톤은 1층과 갈리지 않는다(둘 다 밝음·따뜻함·여백 많음, 화이트/베이지/크림 계열). 매장은 우디+식물에 큰 창 자연광이고 무채색~파스텔 소품이 놓인다. 그래서 **지금의 "같은 뼈대 + 색 하나로 구분" 구조는 유지해도 된다.** 다만 위 스페이싱 워드마크는 풀노리만의 것이니 그것만 살린다.
- **참고 계정** — 오프더월 `@offthewall_cafe`, 풀노리 `@pulnori_shop`. 실물 대조 때 여기 피드를 먼저 본다.
- **사진 자산 없음.** Photography Geometry 절은 규칙만 있고 실제 쓸 사진이 없다.
- **인쇄 실측 안 함.** PDF 출력에서 `{colors.canvas}`가 어떻게 찍히는지(종이 흰색과의 차이) 확인하지 않았다. 캠프에서 한 장 뽑아 보고 필요하면 인쇄용으로 캔버스를 순백으로 내린다.
- **접근성 대비는 쟀다 (미확인 아님).** 15개 조합을 WCAG로 계산해 두 개가 떨어져서 고쳤다 — `{colors.muted}`를 #857A6C → **#736857**(3.93 → 5.11), `{colors.warn}`을 #C98A15 → **#8F6410**(2.75 → 4.91). 현재 본문·의미색은 전부 AA 이상이다. 다만 **색 자체가 미실측 유도값**이라, 실물 대조로 색이 바뀌면 이 계산을 다시 돌려야 한다.
