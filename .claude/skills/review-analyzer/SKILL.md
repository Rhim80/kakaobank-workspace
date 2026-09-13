---
name: review-analyzer
description: 네이버 리뷰를 로그인 없이 수집하고 4단계 프레임워크로 분석해 실행 아이디어를 도출. 상품 리뷰(브랜드스토어)와 매장 리뷰(플레이스·지도) 둘 다. "네이버 리뷰", "브랜드스토어 리뷰", "매장 리뷰", "플레이스 리뷰", "카페/식당 리뷰", "리뷰 크롤링", "리뷰 분석", "경쟁사 리뷰", "리뷰 인사이트" 등을 언급하면 자동 실행.
---

# Review Analyzer

네이버 리뷰를 **로그인 없이** 수집하고, CSV/JSON으로 저장한 뒤, 4단계 프레임워크로 분석하여 **실행 가능한 아이디어**를 도출하는 스킬. 두 종류를 다룬다 — **상품 리뷰**(브랜드스토어)와 **매장 리뷰**(플레이스·지도). 둘은 호스트가 달라 방식도 다르니 아래에서 절이 갈린다.

## 핵심 워크플로우

```
[제품 URL] → [ID 자동 추출] → [크롤링(로그인 X)] → [CSV/JSON] → [4단계 분석] → [아이디어]
```

경쟁사 상품, 자사 상품, 벤치마킹 대상 등 **공개된 브랜드스토어 상품이면 무엇이든** 대상이 된다.

---

## 사전 요구사항

- **Python + Selenium + Chrome**: **상품 리뷰(브랜드스토어·다나와)에만** 필요하다 — 브라우저 세션으로 리뷰 API를 캡처한다
- **매장 리뷰(플레이스)는 파이썬만 있으면 된다** — 표준 라이브러리로 돈다. `--deep`을 쓸 때만 playwright가 추가로 필요
- **로그인 불필요**: 공개 리뷰는 페이지가 익명 방문자에게도 리뷰 API를 호출한다. 자격증명 없이 수집 가능

### 설치 (워크스페이스 .venv 권장)

```bash
# 워크스페이스 루트에서
source .claude/venv.sh         # 없으면: python3 -m venv .venv && source .claude/venv.sh
                               # (윈도우 Git Bash는 python3 대신 python 또는 py)
python -m pip install -r .claude/skills/review-analyzer/scripts/requirements.txt
```

`selenium>=4.6`은 Chrome 드라이버(chromedriver)를 자동 관리하므로 별도 설치가 필요 없다. Chrome 브라우저만 설치돼 있으면 된다.

---

## 사용법

### Step 1: 제품 페이지 URL 확보

크롤링할 브랜드스토어 상품의 URL만 있으면 된다.

```
https://brand.naver.com/<스토어명>/products/<상품ID>
예: https://brand.naver.com/nike/products/11659509026
```

`merchantNo`·`originProductNo`는 스킬이 페이지에서 **자동 추출**하므로 직접 찾을 필요 없다.

### Step 2: 크롤링 (권장 — 로그인 없음)

```bash
# 최신순 50개를 CSV로
python3 .claude/skills/review-analyzer/scripts/naver-brand-reviews.py \
  --no-login \
  --referer 'https://brand.naver.com/nike/products/11659509026' \
  --max 50 --sort RECENT --output reviews.csv

# 낮은 별점순 100개 (불만 분석용)
python3 .claude/skills/review-analyzer/scripts/naver-brand-reviews.py \
  --no-login \
  --referer 'https://brand.naver.com/nike/products/11659509026' \
  --max 100 --sort RATING_LOW --output low.csv
```

실행하면 Chrome 창이 뜨고, 리뷰 탭을 자동으로 열어 페이지의 리뷰 API 응답을 가로채 수집한다.

### 정렬 옵션 (`--sort`)

| 옵션 | 설명 |
|------|------|
| RANKING | 랭킹순 (기본) |
| RECENT | 최신순 |
| RATING_HIGH | 별점 높은순 |
| RATING_LOW | 별점 낮은순 (불만·개선점 분석에 유용) |

### 주요 인자

| 인자 | 설명 |
|------|------|
| `--no-login` | 로그인 없이 익명 세션으로 크롤 (권장) |
| `--referer` | 제품 페이지 URL (`--no-login` 필수, 여기서 ID 자동 추출) |
| `--max` | 최대 수집 수 (기본 200) |
| `--sort` | 정렬 (위 표) |
| `--output` | 출력 파일 (`.csv` 또는 `.json`) |

### 출력 컬럼 (CSV)

`date, rating, content, writer, product_name, product_option, has_photo, image_count`

---

## 매장 리뷰 (네이버 플레이스 / 지도)

상품이 아니라 **매장**의 방문자 리뷰를 볼 때. 카페·식당·미용실처럼 지도에 뜨는 곳이면 된다.

```bash
S=.claude/skills/review-analyzer/scripts/naver-place-reviews.py

python3 $S find "<상호명> <지역>"        # 상호명 → placeId (지역을 붙이면 잘 잡힌다)
python3 $S summary <placeId>             # 업종·주소·리뷰 수 (본문 없음)
python3 $S reviews <placeId> --out r.csv # 최근 20건
```

**브랜드스토어와 달리 로그인도 브라우저도 필요 없다.** 페이지가 서버에서 그려져 나와
리뷰가 HTML 안에 이미 들어 있다 — 위쪽 상품 리뷰의 복잡한 절차를 여기 가져오지 말 것.
위 「사전 요구사항」의 Selenium·Chrome도 이 경로에는 필요 없다(파이썬 표준 라이브러리만 쓴다).

CSV 컬럼: `id, date, rating, content, writer, visit_count, keywords, owner_reply`
`keywords`는 "커피가 맛있어요 / 친절해요" 같은 네이버 평가 키워드, `owner_reply`는 사장님 답글이다.
`.json`으로 저장하면 페이지네이션용 `cursor`가 한 칸 더 붙는다.

20건보다 더 필요하면 `--deep --max 100`. 이때만 playwright가 필요하다
(`python -m pip install playwright && playwright install chromium`).
**1회 실측에서 2페이지(51건째)부터 네이버가 막았다** — 원인이 headless 지문인지 그날의 IP
상태인지는 구분 못 했으니 50건을 확정 천장으로 읽지 말 것(n=1이다). 더 필요하면 날을 나눠 받는다.

### 이 도구를 쓰는 선

공개된 페이지를 사람처럼 읽는 것과, 남의 데이터를 쌓아 자기 서비스에 쓰는 것은 다르다.
국내 판례에서 문제된 것은 **읽은 행위가 아니라 쌓아서 재사용한 쪽**이다(잡코리아 대 사람인,
야놀자 대 여기어때 — 후자는 형사 무죄인데 민사로 10억을 물었다. 판단 인자가 "조직적·장기간·
반복 대량수집"과 "경쟁 서비스로의 대체"였다).

그래서 이렇게 쓴다:

- **자기 조사용 소량으로.** 관심 매장 몇 곳을 훑는 것과 한 지역을 전수로 긁는 것은 다르다
- **수집한 원문을 재배포하거나 데이터셋으로 쌓아 서비스에 넣지 않는다.** 인사이트를 남기고 원문은 버린다
- **요청 간격을 지킨다.** `--deep`의 페이지 사이에 5~8초를 흔들어 넣는다 (고정 간격은 패턴으로
  잡힌다). 기본 20건은 요청이 1회라 간격 자체가 필요 없다
- **캐시는 아직 없다.** 같은 매장을 두 번 돌리면 두 번 다 네트워크로 나간다 — `--out`으로 받아
  파일을 재사용할 것
- **막히면 멈춘다.** 첫 페이지부터 막히면 0건으로 죽고, 도중에 막히면 **받은 만큼 저장한 뒤
  종료코드 1**로 끝난다(부분 수집을 성공으로 위장하지 않는다). 재시도·IP 변경·탐지 회피를 하지
  않는다 — 네이버 약관이 "기술적 조치를 무력화하려는 일체의 행위"로 금지한 것이 정확히 그거다

막히면 place 플랫폼 전체가 같이 죽고 수십 분 뒤 자동으로 풀린다. 그 사이 재시도하지 말 것.

---

## 분석 프레임워크 (4단계)

수집한 CSV를 읽고 아래 순서로 분석한다. "이 리뷰 분석해줘: reviews.csv" 처럼 요청하면 실행.

### Stage 1: 리뷰 분류
| 카테고리 | 설명 |
|----------|------|
| Pain Point | 불만, 문제점 |
| Praise | 칭찬, 만족 |
| Feature Request | 기능/개선 요청 |
| Comparison | 타사 비교 언급 |
| Switching | 구매/이탈 이유 |

### Stage 2: 테마 클러스터링
- 유사 Pain Point 그룹핑
- 빈도 + 강도 기준 정렬

### Stage 3: 우선순위 매트릭스
```
           빈도 높음          빈도 낮음
         +-------------+-------------+
강도 높음 | Must Fix    | Watch       |
         +-------------+-------------+
강도 낮음 | Quick Win   | Nice to Have|
         +-------------+-------------+
```

### Stage 4: 아이디어 도출
- Pain Point → 해결책
- 경쟁사 약점 → 차별화 기회
- Feature Request → 신제품 아이디어

> 팁: `--sort RATING_LOW`로 낮은 별점을 모으면 Pain Point가 집중적으로 잡혀 Stage 1~2가 빨라진다.

---

## 동작 원리 (왜 이 방식인가) — 상품 리뷰 한정

아래는 `brand.naver.com`(상품 리뷰) 이야기다. **매장 리뷰가 사는 `pcmap.place.naver.com`은 nfront WAF 뒤가 아니라서 이 절차가 전부 필요 없다** — 여기 나온 대응을 그쪽에 가져가지 말 것.

네이버 nfront WAF는 외부에서 직접 호출하는 리뷰 API 요청을 차단한다:
- `curl`/`requests`: TLS 핑거프린팅으로 차단 (HTTP 204)
- `curl_cffi`(TLS 위장): 다음 방어선인 429 에러페이지로 차단
- Selenium `execute_script`로 만든 XHR/fetch: Selenium 컨텍스트 감지로 차단

유일하게 통하는 방법은 **페이지 자체가 만드는 리뷰 API 호출을 가로채기**(XHR 인터셉터)다. 그래서 Selenium으로 실제 페이지를 열고, 리뷰 탭 클릭·페이지네이션으로 API 호출을 유발한 뒤 응답을 캡처한다. 리뷰는 공개 데이터라 로그인이 필요 없다.

- **리뷰 API**: `/n/v1/contents/reviews/group-products/query-pages` (XHR, POST)
- **페이지네이션**: 리뷰 전체보기 모달 → 스크롤 → 다음 페이지 (페이지당 20개)

---

## 파일 구조

```
review-analyzer/
├── SKILL.md                      # 이 파일
├── .env.example                  # (선택) 로그인 모드용 자격증명 템플릿
└── scripts/
    ├── naver-brand-reviews.py    # 상품 리뷰 CLI (크롤 + 파싱 + 저장)
    ├── naver-place-reviews.py    # 매장 리뷰 CLI (표준 라이브러리만, --deep만 playwright)
    ├── cookie_extractor.py       # 세션 + XHR 인터셉터 엔진 (NaverSession) — 상품 리뷰 전용
    └── requirements.txt
```

`cookie_extractor.py`의 `NaverSession`이 인터셉터 설치·리뷰 트리거·응답 캡처를 담당한다.

---

## 트러블슈팅

### 리뷰가 수집되지 않음 (인터셉터 타임아웃)
- 리뷰 탭/페이지네이션 클릭이 안 되면 네이버 페이지 구조 변경 가능성 → `cookie_extractor.py`의 셀렉터 업데이트 필요
- 정렬이 "not found"로 나오면 정렬 버튼 텍스트 변경 → `change_sort`의 매칭 로직 확인 (현재는 `<button>` + '…정렬하기' 텍스트 기준)

### ID 자동 추출 실패
- 페이지 구조가 바뀌어 `extract_ids_from_page`의 정규식이 안 맞을 수 있음
- 우회: F12 → Network → `query-pages` 요청 Payload에서 `checkoutMerchantNo`(merchantNo), `originProductNos`(productNo)를 확인해 인자로 직접 지정
  ```bash
  python3 .../naver-brand-reviews.py <merchantNo> <productNo> --no-login --referer '<제품URL>'
  ```

### Chrome/드라이버 오류
- `python -m pip install -U selenium` (4.6+ 자동 드라이버 관리)
- Chrome 브라우저가 설치돼 있는지 확인

---

## (선택) 로그인 모드 · 구글 시트 업로드

공개 리뷰엔 불필요하지만, 필요 시:
- **로그인 모드**: `.env.example`을 `.env`로 복사해 `NAVER_ID`/`NAVER_PW` 입력 후 `--no-login` 대신 `--selenium` 사용 (`pyperclip`, `python-dotenv` 필요)
- **구글 시트 업로드**: `--sheet '<시트URL>'` 사용. 본인 Google 서비스 계정(`~/.config/gspread/service_account.json`)과 시트 편집 권한이 필요 (`gspread`, `google-auth` 필요)

---

## 버전

- v2.0.0 (2026-08-16): **매장 리뷰(네이버 플레이스) 추가** — `naver-place-reviews.py`. `pcmap.place.naver.com`은 nfront WAF 뒤가 아니라 표준 라이브러리만으로 SSR HTML에서 20건이 나온다(Selenium·Chrome 불필요). `--deep`만 playwright. 「이 도구를 쓰는 선」 절 신설(소량·비재배포·간격·막히면 멈춤)
- v1.0.0 (2026-07-04): 전역 review-analyzer v4.1.0에서 워크스페이스용으로 이식. 네이버 브랜드스토어 크롤(로그인 불필요, URL→ID 자동 추출, 4정렬), 4단계 분석 프레임워크 포함. 개인 자격증명·다나와·개인 시트 의존 제거

---

Made by Do Better Things
