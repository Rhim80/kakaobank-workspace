#!/usr/bin/env python3
"""네이버 플레이스(지도) 매장 리뷰 수집.

브랜드스토어(brand.naver.com)와 **다른 호스트**다 — nfront WAF를 안 탄다.
Selenium·로그인·XHR 인터셉터가 전부 불필요하고, 표준 라이브러리만으로 돈다.
naver-brand-reviews.py의 방식을 여기 가져오지 말 것 (2026-08-16 실측).

두 층으로 갈린다:
  얕게 (기본)  SSR HTML의 __APOLLO_STATE__ → 최근 20건. 의존성 0, 요청 1회.
  깊게 (--deep) pcmap-api GraphQL cursor 페이지네이션 → 50건씩.
               **브라우저 컨텍스트가 필수다** — 순수 HTTP는 405 + 캡차 페이지.
               1회 실측에서 2페이지(51건째)부터 405가 났다. 원인이 headless 지문인지
               그날의 IP 상태인지는 구분 못 했으니 50건을 확정 천장으로 읽지 말 것.
               다만 더 파려고 자동화 표식을 숨기지는 않는다 — 네이버 약관이 "기술적
               조치를 무력화하려는 일체의 행위"로 금지한 것이 정확히 그거다.

캐시는 없다. 같은 placeId를 두 번 돌리면 두 번 다 네트워크로 나간다 —
반복해서 보려면 --out으로 받아 파일을 재사용할 것.

사용 (상호명에 지역을 붙이면 잘 잡힌다):
  python3 naver-place-reviews.py find "<상호명> <지역>"
  python3 naver-place-reviews.py summary <placeId>
  python3 naver-place-reviews.py reviews <placeId> --out reviews.csv
  python3 naver-place-reviews.py reviews <placeId> --deep --max 200 --out reviews.json
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA_DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")

# 업종 세그먼트 — pcmap URL의 첫 칸. /place/ 로 넣으면 서버가 맞는 것으로 302 해준다.
PLACE_TYPES = "restaurant|place|cafe|hairshop|accommodation|attraction|hospital|beauty"

# --deep의 페이지 사이 간격. 고정 간격은 패턴으로 잡히니 반드시 흔들어서 쓴다.
# (얕은 경로는 요청이 1회라 간격 자체가 필요 없다.)
DELAY_MIN, DELAY_MAX = 5.0, 8.0


class Blocked(Exception):
    """네이버가 막았다. 조용히 0건으로 넘기지 않고 여기서 죽는다."""


class Partial(Exception):
    """수집 도중 막혀 일부만 받았다. 받은 것은 살리되 성공으로 끝내지 않는다."""

    def __init__(self, rows, message):
        super().__init__(message)
        self.rows = rows


def _sleep():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def _get(url, ua=UA_DESKTOP, referer=None, timeout=25):
    """GET 한 번. 실패는 전부 Blocked로 모아 생트레이스백이 사용자에게 안 가게 한다."""
    headers = {"User-Agent": ua, "Accept-Language": "ko",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code == 429 or "제한되었습니다" in body or "captcha" in body.lower():
            raise Blocked(f"HTTP {e.code} — 네이버가 이 IP를 일시 차단했다. "
                          f"place 플랫폼 전체(pcmap·m.place·api.place)가 같이 막힌다. "
                          f"수십 분 뒤 자동 해제된다. 그 사이 재시도하지 말 것.") from e
        raise Blocked(f"HTTP {e.code} — {url}\n  응답 앞부분: {body[:150]}") from e
    except urllib.error.URLError as e:
        # HTTPError의 부모다. 따로 안 잡으면 DNS·연결거부·타임아웃이 생트레이스백으로 샌다.
        raise Blocked(f"연결 실패 — {url}\n  {e.reason}") from e


def _load_json(raw, what):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise Blocked(f"{what} 응답이 JSON이 아니다 (캡차 페이지이거나 구조가 바뀌었다).\n"
                      f"  {e}\n  앞부분: {raw[:150]}") from e


def find(query, limit=5):
    """상호명 → placeId 후보.

    m.search.naver.com을 쓴다 — place 플랫폼과 **다른 레이트리밋 도메인**이라
    여기서 뽑아 쓰면 place 쪽 예산을 안 깎는다.

    경로에 등장한 id와 id/name 쌍을 교집합으로 걸러야 정거장·역이 안 섞인다.
    """
    limit = max(1, limit)
    url = "https://m.search.naver.com/search.naver?" + urllib.parse.urlencode({"query": query})
    html = _get(url, ua=UA_MOBILE)
    paths = set(re.findall(r"/(?:%s)/(\d{6,})" % PLACE_TYPES, html))
    pairs = re.findall(r'"id"\s*:\s*"(\d{6,})"[^{}]{0,200}?"name"\s*:\s*"([^"]{1,40})"', html)
    out, seen = [], set()
    for pid, name in pairs:
        if pid in paths and pid not in seen:
            seen.add(pid)
            out.append({"placeId": pid, "name": name})
            if len(out) >= limit:
                break
    if not out and paths:
        # 매장은 있는데 이름을 못 붙였다 = 파서가 낡은 것. "없다"와 구분해서 알린다.
        raise Blocked(f"매장 {len(paths)}곳이 페이지에 있는데 이름을 못 뽑았다 — "
                      f"검색 결과 HTML 구조가 바뀐 것 같다(파서를 고쳐야 한다). "
                      f"후보 id: {sorted(paths)[:5]}")
    return out


def summary(place_id):
    """이름·업종·주소·리뷰 카운트. 리뷰 본문은 안 나온다.

    Referer가 없으면 403이 온다.
    없는 placeId에도 네이버는 HTTP 200 + data:null을 준다 — 그래서 여기서 직접 막는다.
    """
    url = f"https://map.naver.com/p/api/place/summary/{place_id}"
    raw = _get(url, referer="https://map.naver.com/")
    d = ((_load_json(raw, "summary").get("data") or {}).get("placeDetail")) or {}
    if not d.get("name"):
        raise Blocked(f"placeId {place_id} 에 해당하는 매장이 없다 "
                      f"(네이버가 200 + 빈 응답을 준다 — 오타이거나 폐업했을 수 있다). "
                      f"`find \"<상호명>\"`으로 id를 다시 확인할 것.")
    return {
        "placeId": d.get("id"),
        "name": d.get("name"),
        "businessType": d.get("businessType"),
        "category": (d.get("category") or {}).get("category"),
        "roadAddress": (d.get("address") or {}).get("roadAddress"),
        # displayText는 "방문자 리뷰 707" 같은 문자열. GraphQL의 total(566)과 다르다 —
        # 별점만 남긴 리뷰가 포함/제외되는 기준이 서로 달라서다. 수집 완료 판정은 total로.
        "visitorReviews": (d.get("visitorReviews") or {}).get("displayText"),
        "blogReviews": (d.get("blogReviews") or {}).get("total"),
    }


def _norm(item, state):
    """APOLLO_STATE / GraphQL 응답의 리뷰 한 건 → 공통 형태.

    author가 APOLLO_STATE에서는 __ref, GraphQL에서는 객체로 온다.
    """
    author = item.get("author") or {}
    if isinstance(author, dict) and "__ref" in author and state:
        author = state.get(author["__ref"]) or {}
    kw = [k.get("name") for k in (item.get("votedKeywords") or []) if k.get("name")]
    reply = item.get("reply") or {}
    return {
        "id": item.get("id"),
        "date": item.get("visited") or item.get("created") or "",
        "rating": item.get("rating"),
        "content": (item.get("body") or "").strip(),
        "writer": author.get("nickname") or "",
        "visit_count": item.get("visitCount"),
        "keywords": " / ".join(kw),
        "owner_reply": (reply.get("body") or "").strip() if isinstance(reply, dict) else "",
        "cursor": item.get("cursor"),
    }


def reviews_shallow(place_id, limit=None):
    """SSR HTML에서 최근 20건. 브라우저·로그인 없이 이것만으로 끝난다."""
    url = f"https://pcmap.place.naver.com/place/{place_id}/review/visitor"
    html = _get(url)
    m = re.search(r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});", html, re.S)
    if not m:
        raise Blocked("__APOLLO_STATE__가 없다 — 차단됐거나 페이지 구조가 바뀌었다. "
                      "브라우저로 같은 URL을 열어 무엇이 보이는지 확인할 것.")
    # 리뷰 본문에 '};'가 들어오면 비탐욕 매치가 거기서 잘린다. 그때 JSONDecodeError를
    # 그대로 던지면 원인이 안 보이므로 Blocked와 같은 층의 안내로 바꾼다.
    state = _load_json(m.group(1), "리뷰 페이지의 __APOLLO_STATE__")
    items = [v for k, v in state.items() if k.startswith("VisitorReview:")]
    rows = [_norm(i, state) for i in items]
    return rows[:limit] if limit else rows


def reviews_deep(place_id, business_type, max_reviews):
    """GraphQL cursor 페이지네이션으로 50건씩.

    브라우저 컨텍스트가 필수다 — urllib·curl로 같은 요청을 보내면 405 + 캡차가 온다
    (2026-08-16 실측). ncaptcha 토큰을 손으로 만들 길은 없다(WASM이 브라우저 환경을
    분석해 만든다). 그래서 우회하지 않고 브라우저 안에서 부른다.

    도중에 막히면 받은 만큼을 Partial로 올린다 — 저장은 하되 종료코드는 0이 아니다.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "--deep은 playwright가 필요하다: pip3 install playwright && playwright install chromium\n"
            "설치가 어려우면 --deep 없이 쓸 것 (최근 20건은 그대로 나온다).")

    js = """
    async ([pid, bt, after, size]) => {
      const wtm = btoa(JSON.stringify({arg: pid, type: bt, source: 'place'})).replace(/=+$/, '');
      const q = `query getVisitorReviews($input: VisitorReviewsInput) {
        visitorReviews(input: $input) { total items {
          id rating body visited created cursor visitCount
          author { nickname } votedKeywords { name } reply { body } } } }`;
      const input = {businessId: pid, businessType: bt, item: '0', bookingBusinessId: null,
                     size: size, isPhotoUsed: false, includeContent: true, getUserStats: false,
                     includeReceiptPhotos: false, getReactions: false, getTrailer: false};
      if (after) input.after = after;
      const r = await fetch('https://pcmap-api.place.naver.com/graphql', {
        method: 'POST', credentials: 'include',
        headers: {'Content-Type': 'application/json', 'x-wtm-graphql': wtm},
        body: JSON.stringify([{operationName: 'getVisitorReviews', variables: {input}, query: q}])});
      if (!r.ok) return {status: r.status};
      return {status: 200, data: await r.json()};
    }"""

    out, after, total, stopped = [], None, None, None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:  # 예외가 나도 크로미움을 남기지 않는다 (이 기계엔 세션이 여럿 붙어 있다)
            page = browser.new_page(user_agent=UA_DESKTOP, locale="ko-KR")
            page.goto(f"https://pcmap.place.naver.com/{business_type}/{place_id}/review/visitor",
                      wait_until="domcontentloaded", timeout=40000)
            while len(out) < max_reviews:
                res = page.evaluate(js, [place_id, business_type, after, 50])
                if res.get("status") != 200:
                    # 실측 1회에서는 2페이지째 여기 걸렸다. 우회하지 않는다.
                    stopped = f"HTTP {res['status']}에서 네이버가 막았다(우회하지 않는다)"
                    break
                payload = res.get("data")
                node = (payload[0] if isinstance(payload, list) else payload) or {}
                data = node.get("data")
                if not data or not data.get("visitorReviews"):
                    stopped = f"GraphQL이 데이터를 안 줬다: {str(node.get('errors'))[:200]}"
                    break
                vr = data["visitorReviews"]
                total = vr.get("total")
                items = vr.get("items") or []
                if not items:
                    break
                out.extend(_norm(i, None) for i in items)
                after = items[-1].get("cursor")
                if not after:
                    break
                if len(out) < max_reviews:
                    _sleep()
        finally:
            browser.close()

    if total is not None:
        print(f"  (매장 전체 {total}건 중 {len(out)}건 수집)", file=sys.stderr)
    if stopped:
        raise Partial(out[:max_reviews], f"{len(out)}건에서 중단 — {stopped}. "
                                         f"더 필요하면 날을 나눠 받을 것.")
    return out[:max_reviews]


def check_outpath(path):
    """수집 **전에** 저장 가능한지 본다.

    --deep은 수백 건을 모은 뒤 마지막에 save()가 죽으면 그 결과가 통째로 증발하고
    레이트리밋 예산만 태운다. 그래서 입구에서 거부한다.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".csv", ".json"):
        raise SystemExit(f"--out 확장자는 .csv 또는 .json 이어야 한다 (받은 것: '{ext or '없음'}')")
    parent = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(parent):
        raise SystemExit(f"--out 상위 폴더가 없다: {parent}")
    if not os.access(parent, os.W_OK):
        raise SystemExit(f"--out 상위 폴더에 쓸 수 없다: {parent}")
    if os.path.isdir(path):
        raise SystemExit(f"--out 이 폴더다: {path}")


def save(rows, path):
    if os.path.splitext(path)[1].lower() == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    else:
        # cursor는 페이지네이션용 내부값이라 CSV에서는 뺀다 (.json에는 그대로 남는다).
        cols = ["id", "date", "rating", "content", "writer", "visit_count",
                "keywords", "owner_reply"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    print(f"저장: {path} ({len(rows)}건)")


def preview(rows):
    for r in rows[:5]:
        star = r["rating"] if r["rating"] is not None else "별점없음"
        print(f"[{star}] {r['date']} {r['writer']}: "
              f"{r['content'][:60].replace(chr(10), ' ')}")
    print(f"... 총 {len(rows)}건 (--out으로 저장)")


def positive(v):
    n = int(v)
    if n < 1:
        raise argparse.ArgumentTypeError("1 이상이어야 한다")
    return n


def main():
    ap = argparse.ArgumentParser(description="네이버 플레이스 매장 리뷰 수집")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find", help="상호명 → placeId 후보")
    p.add_argument("query")
    p.add_argument("--limit", type=positive, default=5)

    p = sub.add_parser("summary", help="매장 정보·리뷰 카운트 (본문 없음)")
    p.add_argument("place_id")

    p = sub.add_parser("reviews", help="리뷰 수집")
    p.add_argument("place_id")
    p.add_argument("--deep", action="store_true", help="20건 넘게 (브라우저 필요)")
    p.add_argument("--max", type=positive, default=100,
                   help="상한 (기본 100). --deep 없으면 20건이 천장이라 그 안에서만 잘린다")
    p.add_argument("--out", help="저장 경로 (.csv 또는 .json)")

    a = ap.parse_args()
    try:
        if a.cmd == "find":
            hits = find(a.query, a.limit)
            if not hits:
                print("못 찾았다. 상호명에 지역을 붙여 다시 (예: '<상호명> 연남동').",
                      file=sys.stderr)
                return 1
            for h in hits:
                print(f"{h['placeId']}\t{h['name']}")
            return 0

        if a.cmd == "summary":
            print(json.dumps(summary(a.place_id), ensure_ascii=False, indent=1))
            return 0

        if a.cmd == "reviews":
            if a.out:
                check_outpath(a.out)
            partial = None
            if a.deep:
                bt = summary(a.place_id).get("businessType") or "restaurant"
                _sleep()
                try:
                    rows = reviews_deep(a.place_id, bt, a.max)
                except Partial as e:
                    rows, partial = e.rows, str(e)
            else:
                rows = reviews_shallow(a.place_id, a.max)
            if not rows:
                print("0건 — 이 매장에 방문자 리뷰가 없다 "
                      "(차단이면 위에 [차단]이 먼저 찍힌다).", file=sys.stderr)
                return 1
            if a.out:
                save(rows, a.out)
            else:
                preview(rows)
            if partial:
                print(f"[부분] {partial}", file=sys.stderr)
                return 1      # 받은 건 살리되 성공으로 끝내지 않는다
            return 0
    except Blocked as e:
        print(f"[차단] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
