#!/usr/bin/env python3
"""
네이버 블로그 본문 수집 (2단)
  1단계 API HUB 검색으로 목록(제목·링크·작성일) — 정식 경로
  2단계 각 링크의 본문을 모바일 URL에서 받아 본문 영역만 추출

왜 2단인가: API의 description은 115자 스니펫이고 본문의 5%다. 표본 28건 실측에서
불만 신호 89% · 가격 75% · 맥락 61%를 놓쳤다. 내용 분석을 하려면 본문이 필요하다.

주의 (본문 수집은 API 범위 밖이다):
  - blog.naver.com robots.txt의 `User-agent: *`는 글 본문 경로를 막지 않는다.
    다만 ClaudeBot·GPTBot 등 AI 봇은 이름으로 Disallow이고 "AI 학습·RAG 목적 금지"가
    주석으로 적혀 있다. 조사 목적 소량 열람과 대량 축적은 성격이 다르다.
  - 수집물을 재배포하거나 데이터셋으로 쌓아 서비스에 쓰지 말 것 (잡코리아-사람인 판례).
  - 캐시는 ~/.cache 에 둔다. 워크스페이스 안으로 들이지 않는다.

사용:
  python3 collect_blog.py "디카페인 원두" "디카페인 커피 추천" --n 60 --out deca.jsonl
  python3 collect_blog.py "원두 추천" --no-body     # 목록만 (API 정식 범위)
"""
import argparse, html, json, os, re, sys, time, urllib.error, urllib.request

from naver_search import headers, search, strip_tags

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
DELAY = 0.4                                   # 요청 간격(초) — 낮추지 말 것
CACHE = os.path.expanduser("~/.cache/naver-blog-body")

# 본문 컨테이너를 여는 태그. 스마트에디터 ONE → 구 에디터 → 기타 순.
# 끝 경계는 클래스명으로 찾지 않는다 — se-comment·post_footer 같은 이름을 경계로 쓰면
# 그런 클래스가 없는 페이지에서 조용히 문서 끝까지 삼켜 "닫기 카테고리 이 블로그 홈"
# 네비게이션과 JSON 메타데이터가 본문에 섞인다(실측 3/3 실패). div 깊이로 짝을 찾는다.
BODY_OPEN = [
    r'(?is)<div[^>]*class="[^"]*se-main-container[^"]*"[^>]*>',
    r'(?is)<div[^>]*id="viewTypeSelector"[^>]*>',
    r'(?is)<div[^>]*class="[^"]*post-view[^"]*"[^>]*>',
]


def slice_balanced(raw, open_re):
    """여는 div를 찾아 깊이를 세며 짝이 맞는 </div>까지 잘라낸다."""
    m = re.search(open_re, raw)
    if not m:
        return None
    i = m.end()
    depth = 1
    for t in re.finditer(r"<(/?)div\b", raw[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return raw[i:i + t.start()]
    return None


def to_text(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", h)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", " ", h))
    t = re.sub(r"[ \t​]+", " ", t)
    # 페이지 안 구조화 데이터(JSON 조각)가 본문에 딸려오는 경우 제거
    t = re.sub(r'\{"[a-zA-Z]+":.{0,400}?\}', " ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def extract_body(raw):
    for pat in BODY_OPEN:
        seg = slice_balanced(raw, pat)
        if seg:
            t = to_text(seg)
            if len(t) > 200:
                return t
    return None


def fetch_body(blog_id, post_no):
    """PC URL은 iframe 껍데기(2.8KB)라 안 되고 모바일 URL이라야 본문이 들어온다."""
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, f"{blog_id}_{post_no}.txt")
    if os.path.exists(cp):
        return open(cp, encoding="utf-8").read(), True
    req = urllib.request.Request(f"https://m.blog.naver.com/{blog_id}/{post_no}",
                                 headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    body = extract_body(raw)
    if body:
        open(cp, "w", encoding="utf-8").write(body)
    return body, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--n", type=int, default=100, help="쿼리당 목록 수집 건수 (한 쿼리 상한 1,099)")
    ap.add_argument("--out", default="collected.jsonl")
    ap.add_argument("--no-body", action="store_true", help="목록만 — API 정식 범위")
    a = ap.parse_args()

    H = headers()
    rows, seen = [], set()
    for q in a.queries:
        for it in search(H, "blog", q, a.n):
            if it["link"] in seen:
                continue
            seen.add(it["link"])
            rows.append({"query": q, "title": strip_tags(it["title"]), "link": it["link"],
                         "snippet": strip_tags(it["description"]),
                         "postdate": it.get("postdate"), "blogger": it.get("bloggername")})
    print(f"[1단계] API 목록 {len(rows)}건 (중복 제거 후)", file=sys.stderr)

    ok = cached = fail = skip = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for i, r in enumerate(rows, 1):
            if not a.no_body:
                m = re.match(r"https?://blog\.naver\.com/([\w-]+)/(\d+)", r["link"])
                if not m:
                    skip += 1                      # 네이버 블로그가 아닌 링크
                    r["body"] = None
                else:
                    try:
                        body, hit = fetch_body(m.group(1), m.group(2))
                        r["body"] = body
                        ok, cached, fail = ok + bool(body), cached + hit, fail + (not body)
                        if not hit:
                            time.sleep(DELAY)
                    except Exception as e:
                        fail += 1
                        r["body"], r["error"] = None, type(e).__name__
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            if not a.no_body and i % 25 == 0:
                print(f"  {i}/{len(rows)} · 본문 {ok} · 실패 {fail}", file=sys.stderr)

    if not a.no_body:
        print(f"[2단계] 본문 {ok} (캐시 {cached}) · 실패 {fail} · 대상외 {skip}", file=sys.stderr)
    print(f"[완료] {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
