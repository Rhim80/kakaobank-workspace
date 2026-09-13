#!/usr/bin/env python3
"""
네이버 검색광고 API (SA) — 조사용 2종만 담는다: 검색량·연관키워드 + 입찰 예상실적

키: 같은 폴더의 .env (또는 워크스페이스 루트 .env)
API HUB(naver_search.py)와 인증이 완전히 다르다 — 요청마다 HMAC-SHA256 서명.
광고 운영(캠페인·광고그룹·소재)은 범위 밖 — 필요해지면 별도 파일로.

CLI:
  python3 searchad.py keywords 디카페인 "디카페인 원두"      # 연관키워드 포함 (기본 상위 30)
  python3 searchad.py keywords 디카페인원두 --exact          # 입력 키워드 행만
  python3 searchad.py estimate 디카페인원두 --device MOBILE  # 입찰가별 예상 노출·클릭·비용
"""
import argparse, base64, hashlib, hmac, json, os, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://api.searchad.naver.com"
WS_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "..", ".."))


def load_keys(env_path=None):
    # .env 탐색: ① 이 폴더 안 → ② 워크스페이스 루트 (naver_search.headers()와 같은 규칙)
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    root = os.path.join(WS_ROOT, ".env")
    p = (os.path.expanduser(env_path) if env_path
         else local if os.path.exists(local) else root)
    if not os.path.exists(p):
        sys.exit(f".env 파일이 없습니다. 둘 중 한 곳에 만드세요:\n"
                 f"  {local}\n  {root}\n"
                 f"(같은 폴더의 .env.example 을 복사해 키를 채우면 됩니다)")
    env = {}
    for line in open(p):
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v
    for k in ("NAVER_AD_API_KEY", "NAVER_AD_SECRET_KEY", "NAVER_AD_CUSTOMER_ID"):
        if k not in env:
            sys.exit(f"{k} 없음: {p}")
    return env


def _call(env, method, path, query=None, body=None):
    # 서명은 path까지만 — 쿼리스트링을 넣으면 401
    ts = str(int(time.time() * 1000))
    msg = f"{ts}.{method}.{path}"
    sig = base64.b64encode(hmac.new(env["NAVER_AD_SECRET_KEY"].encode(),
                                    msg.encode(), hashlib.sha256).digest()).decode()
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    h = {"X-Timestamp": ts, "X-API-KEY": env["NAVER_AD_API_KEY"],
         "X-Customer": env["NAVER_AD_CUSTOMER_ID"], "X-Signature": sig}
    data = None
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        raise SystemExit(f"[API 실패] HTTP {e.code} {url}\n  {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[연결 실패] {url}\n  {e.reason}")


def _num(v):
    # 검색량이 적으면 숫자 대신 "< 10" 문자열이 온다 — 정렬용으로만 0 취급
    return v if isinstance(v, (int, float)) else 0


def keywords(env, hints):
    """keywordstool. hintKeywords는 한 호출 최대 5개 — 입력이 많으면 나눠 부른다.
    응답은 입력 키워드 행 + 연관키워드 행이 한 리스트로 온다 (연관은 호출당 수백 건)."""
    out, seen = [], set()
    for i in range(0, len(hints), 5):
        batch = [h.replace(" ", "") for h in hints[i:i + 5]]  # 공백 있으면 400
        d = _call(env, "GET", "/keywordstool",
                  query={"hintKeywords": ",".join(batch), "showDetail": "1"})
        for row in d.get("keywordList", []):
            if row["relKeyword"] in seen:
                continue
            seen.add(row["relKeyword"])
            out.append(row)
        time.sleep(0.1)
    return out


def estimate(env, keyword, device="MOBILE", bids=None):
    """입찰가별 예상 노출·클릭·비용 (월 기준). 광고를 안 하더라도
    '이 키워드 시장이 얼마짜리인가'를 읽는 용도."""
    body = {"device": device, "keywordplus": False, "key": keyword,
            "bids": bids or [100, 200, 300, 500, 700, 1000, 1500, 2000]}
    return _call(env, "POST", "/estimate/performance/keyword", body=body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["keywords", "estimate"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--n", type=int, default=30, help="keywords 출력 상한 (0=전체)")
    ap.add_argument("--exact", action="store_true", help="입력 키워드 행만")
    ap.add_argument("--device", default="MOBILE", choices=["MOBILE", "PC"])
    ap.add_argument("--bids", default=None, help="쉼표 구분 입찰가 (원)")
    ap.add_argument("--json", action="store_true", help="가공 없이 JSON 줄로")
    a = ap.parse_args()
    env = load_keys()

    if a.cmd == "keywords":
        rows = keywords(env, a.args)
        if a.exact:
            # API가 라틴 문자를 대문자로 돌려줘(iphone→IPHONE) 대소문자 무시 비교
            targets = {h.replace(" ", "").upper() for h in a.args}
            rows = [r for r in rows if r["relKeyword"].upper() in targets]
        rows.sort(key=lambda r: _num(r["monthlyPcQcCnt"]) + _num(r["monthlyMobileQcCnt"]),
                  reverse=True)
        if a.n and not a.exact:
            rows = rows[:a.n]
        if a.json:
            for r in rows:
                print(json.dumps(r, ensure_ascii=False))
        else:
            print(f"{'키워드':20s} {'PC':>8s} {'모바일':>8s} {'클릭계':>8s} {'경쟁':>4s}")
            for r in rows:
                clk = _num(r.get("monthlyAvePcClkCnt")) + _num(r.get("monthlyAveMobileClkCnt"))
                print(f"{r['relKeyword']:20s} {str(r['monthlyPcQcCnt']):>8s} "
                      f"{str(r['monthlyMobileQcCnt']):>8s} {clk:>8.1f} {r['compIdx']:>4s}")
        print(f"# {len(rows)}건", file=sys.stderr)
    elif a.cmd == "estimate":
        bids = [int(b) for b in a.bids.split(",")] if a.bids else None
        d = estimate(env, a.args[0], a.device, bids)
        print(f"{a.args[0]} ({d['device']}) — 월 예상")
        print(f"{'입찰가':>7s} {'노출':>9s} {'클릭':>7s} {'비용':>10s}")
        for e in d["estimate"]:
            print(f"{e['bid']:>6,}원 {e['impressions']:>9,} {e['clicks']:>7,} {e['cost']:>9,}원")


if __name__ == "__main__":
    main()
