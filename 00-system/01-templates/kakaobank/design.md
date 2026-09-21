# 카카오뱅크 — 디자인 가이드

> 9/22 워크숍 슬라이드·안내물·HTML 산출물을 카카오뱅크 톤으로 만들 때 참조하는 단일 출처.
> 조사 2026-09-21. 근거는 둘이다 — ① 카카오뱅크 공식 「브랜드 리소스」 페이지(`kakaobank.com/view/about/brand/resource`)와 거기서 받는 Brand Identity Guidelines V2.0(2024.8, 27쪽) ② kakaobank.com 실제 CSS(`reset.css`·`common.css`·`components.css`·`style.css`)에서 센 값.
> 공식 가이드가 정한 것은 **로고와 색 다섯 개뿐**이다. 글꼴·크기·여백·모서리는 가이드에 없고, 웹사이트 코드에서 센 값이다 — 절마다 어느 쪽인지 적었다.

---

## Overview

카카오뱅크의 캔버스는 **흰 바탕과 검은 글자**이고, 노랑은 그 위에 드물게 얹힌다. 공식 가이드는 노랑을 "색상이 적용되는 모든 브랜드 표현의 중심"이라 부르지만, 실제 웹사이트 CSS의 색 선언 392개 중 노랑은 6개다. 나머지는 흑백 변수 301개, 빨강·파랑·초록 18개. 노랑은 넓게 칠하는 색이 아니라 **브랜드를 상징할 때 한 번 찍는 색**으로 쓰인다.

심볼은 은행의 'B'와 그 중심에 서 있는 'I(나)'를 합친 형태로, 가이드의 말로 **"내가 중심이 되는 은행"**이다. 로고는 노랑·검정·흰색 세 가지로만 쓰고, 비율·색·서체를 바꾸지 않는다.

화면 글꼴은 Pretendard 하나다. 굵기는 500·600·700이 대부분이고, 글자 간격을 조금 좁힌다(-1~-2%). 모서리는 둥글고(카드 16~20px, 버튼 8px) 그림자는 쓰지 않는다. 깊이는 옅은 회색 바탕 면으로 만든다.

**Key Characteristics:**
- 바탕은 흰색(`{colors.canvas}`)과 아주 옅은 회색(`{colors.surface}`). 글자는 검정.
- 노랑(`{colors.kb-yellow}`)은 드물게, 상징하는 자리에만. 비슷한 다른 노랑을 쓰지 않는다(가이드 명시).
- 공식 보조색은 무채색 넷(흰·검·회·연회)뿐. "지정되지 않은 회색은 사용하지 않는 것을 원칙으로 합니다"(가이드 26쪽).
- 글꼴은 Pretendard, 제목 700·본문 500. 글자 간격 약간 좁게.
- 모서리 둥글게, 그림자 없음(CSS `box-shadow` 0건).
- 버튼은 검정 바탕 흰 글자가 기본, 모서리 8px.
- 로고는 받은 파일 그대로 — 비율·색·서체·효과·아웃라인 변경 금지.

## Colors

### Brand & Accent — 공식 가이드
- **KakaoBank Yellow** (`{colors.kb-yellow}` — #FFE300 · RGB 255/227/0 · CMYK 0/10/100/0 · PANTONE Yellow 012 C/U — 가이드 PDF에는 "Yellow C/U"): 주요 색상. 브랜드를 명확하거나 상징적으로 전달할 때 최우선. 웹사이트 CSS 변수 `--primary`도 같은 값이다.

### Neutrals — 공식 가이드 보조 색상
- **White** (`{colors.white}` — #FFFFFF)
- **Black** (`{colors.kb-black}` — #1E1E1E · RGB 30/30/30): 로고·브랜드 표현의 검정
- **Gray** (`{colors.gray}` — #A3A3A3 · PANTONE Cool Gray 6 C/U)
- **Light Gray** (`{colors.light-gray}` — #CCCCCC · PANTONE Cool Gray 3 C/U)

### Surface — 웹사이트 CSS
- **Canvas** (`{colors.canvas}` — #FFFFFF, `--white100`)
- **Surface** (`{colors.surface}` — #F7F7F7, `--black15`): 카드·연한 버튼 바탕. 웹사이트에서 가장 많이 쓰는 바탕 회색
- **Surface Strong** (`{colors.surface-strong}` — #E6E6E6, `--black30`): 연한 버튼의 hover

### Text — 웹사이트 CSS
- **Ink** (`{colors.ink}` — #000000, `--black100`): 제목·본문 기본. 사용 86회로 가장 많다
- **Body Strong** (`{colors.body-strong}` — #444444, `--black80`): 보조 본문(37회)
- **Muted** (`{colors.muted}` — #888888, `--black60`): 설명·캡션(35회)

### Semantic — 웹사이트 CSS
- **Red** (`{colors.red}` — #EC4343) · **Blue** (`{colors.blue}` — #425EFF) · **Green** (`{colors.green}` — #00D080): 상태 표시용. 합쳐 18회로 드물다

> **가이드와 사이트가 갈리는 곳** — 가이드는 무채색을 넷으로 제한하지만 사이트는 `--black5`~`--black100` 20단계 회색을 쓰고, 글자 검정도 가이드의 #1E1E1E가 아니라 #000000이다. 사이트 안에 가이드와 다른 노랑(#FFE500 투자 배너, #FFFC00 브랜드 페이지 한 칸)도 있다. **이 워크숍 산출물은 가이드 쪽을 따른다** — 로고·노랑·검정은 가이드 값, 회색이 더 필요할 때만 사이트의 `{colors.surface}`·`{colors.muted}`를 쓴다.

## Typography — 웹사이트 CSS (가이드에 서체 규정 없음)

### Font Family
**Pretendard Variable** (웹폰트, SIL OFL — 무료 사용 가능). 사이트 `font-family: 'Pretendard Variable', sans-serif`. 대체 순서 `Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif`.
워드마크는 "카카오 공동체의 CI 규정을 따릅니다"(가이드 6쪽) — 워드마크를 글꼴로 흉내 내지 않고 로고 파일을 쓴다.

### Hierarchy
사이트는 `html { font-size: 62.5% }`라 1rem = 10px. 괄호는 CSS에서 그 크기가 나온 줄 수(실측). **굵기·행간·자간의 짝은 60px 줄만 CSS에서 확인했고(700 / 1.24 / -1.2px), 나머지 짝은 사이트에 많이 쓰인 값을 크기에 배정한 것이다 — 추측입니다.**

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xl}` | 60px (8) | 700 | 1.24 | -1.2px | 섹션 대제목 |
| `{typography.display-lg}` | 40px (11) | 700 | 1.24 | -0.02em | 큰 제목 |
| `{typography.display-md}` | 32px (11) | 700 | 1.36 | -0.02em | 중제목 |
| `{typography.title-lg}` | 24px (24) | 700 | 1.36 | -0.02em | 카드 제목 |
| `{typography.title-md}` | 20px (41) | 600 | 1.44 | -0.01em | 소제목 |
| `{typography.body-lg}` | 18px (80) | 500 | 1.44 | -0.18px | 강조 본문·큰 버튼 |
| `{typography.body-md}` | 16px (110) | 500 | 1.5 | -0.16px | 기본 본문 |
| `{typography.body-sm}` | 14px (58) | 500 | 1.5 | -0.14px | 보조 설명 |
| `{typography.caption}` | 12px (11) | 500 | 1.5 | 0 | 각주 |

### Principles
굵기는 500(95회)·600(94회)·700(83회)이 거의 전부이고 400 이하는 각 1회다. 가는 글씨로 멋을 내지 않는다. 글자 간격은 크기의 약 -1%(본문)~-2%(제목)로 좁힌다. 행간은 본문 1.5, 제목 1.24~1.36.

### Note on Font Substitutes
Pretendard가 없는 PC면 `Apple SD Gothic Neo`(맥)·`Malgun Gothic`(윈도우). 슬라이드는 Pretendard 웹폰트를 CDN으로 불러 쓴다(`cdn.jsdelivr.net/npm/pretendard`) — 사내 PC에서 외부 주소가 막히면 대체 글꼴로 떨어진다.

## Layout — 웹사이트 CSS

### Spacing System
사이트에 간격 토큰 체계는 따로 없다. 쓰는 값: 버튼 안쪽 12px 24px, 버튼 아이콘과 글자 사이 8px, 거터 12·16·20px(`--gutter`).
- `{spacing.xs}` 8px · `{spacing.sm}` 12px · `{spacing.md}` 16px · `{spacing.lg}` 24px · `{spacing.xl}` 40px · `{spacing.section}` 80px — **xl·section은 사이트에서 센 값이 아니다(추측입니다)**. 슬라이드에서 쓸 때 조정

### Grid & Container
콘텐츠 폭 최대 1460px(`.container`). 컬럼 12(데스크톱)·10·8·4(모바일)(`--col-base`).

### Whitespace Philosophy
흰 바탕 넓게, 한 화면에 한 덩이. 장식 없이 여백과 회색 면으로 구역을 가른다.

## Elevation & Depth

| Level | 처리 | Use |
|---|---|---|
| 0 | `{colors.canvas}` 흰 바탕 | 페이지 |
| 1 | `{colors.surface}` #F7F7F7 면 | 카드·연한 버튼 |
| 2 | `{colors.ink}` 검정 면 + 흰 글자 | 강조 버튼·반전 구역 |

그림자는 쓰지 않는다(CSS `box-shadow` 0건). 버튼에 `backdrop-filter: blur(37px)`가 있어 사진 위에서 뒤가 흐리게 비친다.

## Shapes — 웹사이트 CSS

### Border Radius Scale

| Token | Value | 횟수 | Use |
|---|---|---|---|
| `{rounded.sm}` | 8px | 10 | 버튼 |
| `{rounded.md}` | 16px | 58 | 카드 |
| `{rounded.lg}` | 20px | 42 | 큰 카드·배너 |
| `{rounded.xl}` | 30px | 8 | 큰 둥근 면 |
| `{rounded.full}` | 50% | 18 | 원형 아이콘 버튼 |

### Photography Geometry
공식 미디어 패키지(CI·사옥·대표이사·임직원 사진)가 브랜드 리소스 페이지에 있다. 사진 위치·잘림 규칙은 확인 안 함(Known Gaps).

## Components

### Buttons — `components.css` 실측
- `{component.button-primary}`: 바탕 `{colors.ink}` · 글자 흰색 · `{rounded.sm}` · 600 · 높이 48~51px · hover 시 #444444
- `{component.button-light}`: 바탕 `{colors.surface}` · 글자 `{colors.ink}` · hover `{colors.surface-strong}`
- `{component.button-white}`: 바탕 흰색 · 글자 `{colors.ink}` (검정·사진 바탕 위)
- 원형 아이콘 버튼 48×48, `{rounded.full}`

### Cards & Containers
바탕 `{colors.surface}`, `{rounded.md}`~`{rounded.lg}`, 테두리·그림자 없음.

### Logo — 공식 가이드
- 심볼 · 워드마크 · 시그니처(가로형 우선, 세로형 제한적) 세 형태. 시그니처는 두 요소의 크기 비례·간격을 바꾸지 않는다
- 최소 여백: 심볼·워드마크·가로 시그니처 0.5X, 세로 시그니처 0.4X
- 최소 크기: 화면 12px(인쇄 5mm)·8px(인쇄 3mm). 세 형태 중 어느 것이 8px인지는 그림으로만 나와 텍스트로 확인 못 함
- 색: 노랑·검정·흰색 셋만. 배경과 톤온톤이 되지 않게(노랑 배경에 노랑 로고 X)
- 파일: 브랜드 리소스 페이지 「브랜드 어셋 다운로드」 = `KakaoBank_BrandAsset_V2.0.zip`(Symbol·Wordmark·Signature × Digital·Print, SVG·PNG·AI)

### Signature Components
- **노랑 한 면** — 흰 바탕 속에 `{colors.kb-yellow}` 면 하나(브랜드 리소스 페이지의 색상 칸·투자 배너가 이 모양). 한 화면에 하나

## Do's and Don'ts

**Do**
- 노랑은 #FFE300 하나만 쓴다
- 흰 바탕 + 검정 글자를 기본으로 하고 노랑은 상징하는 자리에만
- 로고는 받은 파일 그대로, 최소 여백을 지켜 넣는다
- 글꼴은 Pretendard, 제목 700
- 구역은 회색 면과 여백으로 가른다

**Don't** (로고 항목은 가이드 18·19·23쪽 금지 목록)
- 비슷한 다른 노랑(#FEE500·#FFE500 등) 쓰기
- 지정되지 않은 회색 늘리기
- 로고 비율 변경·아웃라인·마스크·임의 색·형태 왜곡·복잡한 패턴과 조합
- 시그니처의 워드마크 변형·임의 조합·임의 서체·앱 아이콘과 조합
- 그림자로 깊이 만들기

## Responsive Behavior — 웹사이트 CSS

### Breakpoints

| 이름 | 조건 |
|---|---|
| 데스크톱 대 | 1600px 이상 |
| 데스크톱 | ≤1599px |
| 태블릿 | ≤1023px |
| 모바일 | ≤767px |

### Touch Targets
버튼 높이 45·48·51px, 아이콘 버튼 48×48.

### Collapsing Strategy
컬럼 12 → 10 → 8 → 4. 좌우 안쪽 여백이 거터의 배수로 바뀐다.

### Image Behavior
확인 안 함.

## Iteration Guide

1. 새 산출물은 흰 바탕 + 검정 글자로 시작하고, 노랑은 마지막에 한 자리만 넣는다
2. 색은 hex를 직접 쓰지 않고 이 파일의 토큰 이름으로 부른다
3. 로고가 들어가면 zip의 SVG를 쓰고 최소 여백을 잰다
4. 제목과 본문 굵기 차이(700 vs 500)를 유지한다
5. 카드는 `{colors.surface}` + `{rounded.md}`, 그림자 없이
6. 강조 버튼·반전 구역은 검정 면 + 흰 글자
7. 가이드와 사이트가 갈리면 가이드를 따른다
8. 이 파일에 없는 값이 필요하면 "추측입니다"라고 적고 쓴다

## Known Gaps

- 공식 가이드에 **서체·여백·그리드·사진·일러스트 규정이 없다** — 이 절들은 웹사이트 코드에서 센 값이다
- 카카오뱅크 **앱 화면**의 디자인은 조사하지 않았다(웹사이트만)
- 사내 문서·발표 양식(사내 PPT 템플릿)이 따로 있는지 모른다 — 있다면 참가자 쪽이 더 정확한 원본
- 로고 최소 크기 8px이 세 형태 중 어느 것인지 텍스트로 확인 못 함
- 미디어 패키지 사진은 열어 보지 않았다
- **배포 제한** — 가이드 PDF 2쪽: "가이드는 지정된 파트너 이외에 누구에게도 전달, 배포할 수 없습니다", "타 브랜드의 같거나 유사한 작업에 참고, 활용할 수 없습니다". 그래서 PDF와 로고 zip은 저장소에 넣지 않았다. 색 값은 공개 브랜드 리소스 페이지에도 그대로 나와 있다
