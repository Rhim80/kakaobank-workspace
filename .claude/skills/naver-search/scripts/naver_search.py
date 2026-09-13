#!/usr/bin/env python3
"""
NAVER API HUB 공통 클라이언트 (검색 · 검색어트렌드 · 쇼핑인사이트)

키: 같은 폴더의 .env (또는 워크스페이스 루트 .env)
경로 규칙은 공식 개요 문서 예시와 다르다 — 실측한 것만 여기 적는다.

CLI:
  python3 naver_search.py blog "디카페인 원두" --n 100
  python3 naver_search.py cafe "디카페인 원두" --n 100
  python3 naver_search.py total "디카페인 원두" "원두 추천"
  python3 naver_search.py trend "브랜드A" "브랜드B" --from 2026-01-01 --to 2026-06-30
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://naverapihub.apigw.ntruss.com"

# 실측 확인된 경로 (2026-08-14). 문서 개요의 /search/news · /datalab/trend 는 404.
EP_SEARCH = BASE + "/search/v1/{kind}"          # blog·cafearticle·news·image·local (GET)
EP_TREND = BASE + "/search-trend/v1/search"      # 검색어 트렌드 (POST)
EP_SHOP_CAT = BASE + "/shopping/v1/categories"   # 쇼핑인사이트 카테고리 (POST)
EP_SHOP_AGE = BASE + "/shopping/v1/category/age"
EP_SHOP_GENDER = BASE + "/shopping/v1/category/gender"
EP_SHOP_DEVICE = BASE + "/shopping/v1/category/device"
EP_SHOP_KEYWORDS = BASE + "/shopping/v1/category/keywords"

MAX_DISPLAY = 100     # 초과 시 400 SE02
MAX_START = 1000      # 초과 시 400 SE03 → 한 쿼리 상한 1,099건

strip_tags = lambda s: re.sub("<[^>]+>", "", s or "")

# 이 파일 위치: <워크스페이스>/.claude/skills/naver-search/scripts/ → 4단계 위가 루트
WS_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "..", ".."))


def headers(env_path=None):
    # .env 탐색: ① 이 폴더(scripts/) 안 → ② 워크스페이스 루트.
    # 어느 쪽이든 되고, 없으면 두 자리를 모두 알려주고 멈춘다.
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
    for k in ("NAVER_APIHUB_CLIENT_ID", "NAVER_APIHUB_CLIENT_SECRET"):
        if k not in env:
            sys.exit(f"{k} 없음: {p}")
    return {"X-NCP-APIGW-API-KEY-ID": env["NAVER_APIHUB_CLIENT_ID"],
            "X-NCP-APIGW-API-KEY": env["NAVER_APIHUB_CLIENT_SECRET"]}


def _call(url, H, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(H)
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h,
                                 method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        # 401 = 그 API가 Application에 활성화 안 됨 (콘솔에서 추가해야 함)
        raise SystemExit(f"[API 실패] HTTP {e.code} {url}\n  {detail}")
    except urllib.error.URLError as e:
        # DNS·연결거부·타임아웃 — HTTPError의 상위라 따로 잡아야 생 트레이스백이 안 뜬다
        raise SystemExit(f"[연결 실패] {url}\n  {e.reason}")


def search(H, kind, query, n=100, sort="sim"):
    """kind: blog · cafearticle · news · image · local

    한 쿼리 상한 1,099건 = start 최대 1000 + display 100.
    start를 100씩 더하면 1001로 건너뛰어 1000을 못 밟으므로(→ 1000건에서 멈춤)
    마지막 한 번은 start=1000으로 눌러 1000~1099를 받는다. 겹치는 1건은 link로 제거.

    주의: 기간 필터 파라미터는 없다. startDate 등을 넣으면 에러 없이 조용히 무시된다."""
    out, seen, start, tail_done = [], set(), 1, False
    while len(out) < n and start <= MAX_START:
        p = {"query": query, "display": min(MAX_DISPLAY, n - len(out)),
             "start": start, "sort": sort}
        d = _call(EP_SEARCH.format(kind=kind) + "?" + urllib.parse.urlencode(p), H)
        items = d.get("items", [])
        if not items:
            break
        for it in items:
            key = it.get("link")
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        start += len(items)
        if start > MAX_START and not tail_done and len(out) < n:
            start, tail_done = MAX_START, True      # 마지막 배치 1000~1099
        time.sleep(0.05)
    return out[:n]


def total(H, kind, query):
    """그 키워드의 문서수. 정상적인 AND 검색이라 경쟁강도·포화지수에 쓸 수 있다.
    단 브랜드명에 흔한 일반어가 섞여 있으면 부풀려진다."""
    d = _call(EP_SEARCH.format(kind=kind) + "?" +
              urllib.parse.urlencode({"query": query, "display": 1}), H)
    return d.get("total", 0)


def trend(H, groups, start, end, unit="month", device=None, gender=None, ages=None):
    """groups: {"브랜드A": ["브랜드A", "brand a"], ...}
    그룹 안 키워드는 합산된다(비교 아님). 그룹은 최대 5개. 값은 상대값(최고점=100)."""
    body = {"startDate": start, "endDate": end, "timeUnit": unit,
            "keywordGroups": [{"groupName": k, "keywords": v} for k, v in groups.items()]}
    for k, v in (("device", device), ("gender", gender), ("ages", ages)):
        if v:
            body[k] = v
    return _call(EP_TREND, H, body)


def shopping(H, kind, category, start, end, unit="month", **kw):
    """kind: categories · age · gender · device · keywords
    category = 네이버쇼핑 URL의 cat_id (API가 이름을 안 돌려주므로 손으로 확인해야 함)"""
    url = {"categories": EP_SHOP_CAT, "age": EP_SHOP_AGE, "gender": EP_SHOP_GENDER,
           "device": EP_SHOP_DEVICE, "keywords": EP_SHOP_KEYWORDS}[kind]
    body = {"startDate": start, "endDate": end, "timeUnit": unit}
    if kind == "categories":
        body["category"] = [{"name": category, "param": [category]}]
    else:
        body["category"] = category
    body.update(kw)
    return _call(url, H, body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["blog", "cafe", "total", "trend"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--sort", default="sim", choices=["sim", "date"])
    ap.add_argument("--from", dest="start", default="2026-01-01")
    ap.add_argument("--to", dest="end", default="2026-06-30")
    a = ap.parse_args()
    H = headers()

    if a.cmd in ("blog", "cafe"):
        kind = "blog" if a.cmd == "blog" else "cafearticle"
        rows = search(H, kind, a.args[0], a.n, a.sort)
        for it in rows:
            print(json.dumps({k: strip_tags(v) if isinstance(v, str) else v
                              for k, v in it.items()}, ensure_ascii=False))
        print(f"# {len(rows)}건", file=sys.stderr)
    elif a.cmd == "total":
        for q in a.args:
            print(f"{q:24s} 블로그 {total(H,'blog',q):>10,} · 카페 {total(H,'cafearticle',q):>9,}")
    elif a.cmd == "trend":
        d = trend(H, {q: [q] for q in a.args[:5]}, a.start, a.end)
        for r in d["results"]:
            pts = " ".join(f"{x['period'][:7]}={x['ratio']:.0f}" for x in r["data"])
            print(f"{r['title']:14s} {pts}")


if __name__ == "__main__":
    main()
