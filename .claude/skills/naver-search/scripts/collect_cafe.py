#!/usr/bin/env python3
"""
네이버 카페 수요 수집 — 질문 제목 + 카페 세그먼트 + 회원수

카페는 본문이 안 온다(스니펫 117자가 전부, 로그인 벽). 대신 제목이 안 잘리고
카페 글 제목은 그 자체가 질문이라, 본문 없이도 "누가 뭘 찾고 있나"가 나온다.

원본은 오염이 심하다 — 한 쿼리에서 회원 2,867명짜리 카페가 결과의 47%를 차지했고
부업·재테크 카페의 제휴마케팅 글이 상위에 섞인다. 그래서 필터가 필수다.
핵심 장치는 도배 지수 = 검색에 잡힌 글 수 ÷ 회원수. 회원수는 카페 공개 홈의
"멤버수" 라벨에서 읽는다 (JSON memberCount 아님 — 그건 없다).

사용:
  python3 collect_cafe.py "디카페인 원두" "임산부 커피" --out cafe.jsonl
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request
from collections import Counter, defaultdict

from naver_search import headers, search, strip_tags

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

AD = ["바로가기", "사은품", "최저가", "할인", "이벤트", "구매대행", "공동구매", "제휴",
      "쿠팡", "파트너스", "무료배송", "특가", "증정", "체험단"]
BIZ = ["부업", "재테크", "창업", "N잡", "투잡", "영업", "보험", "대출", "구매대행",
       "지름신", "쇼핑매니아"]
SPAM_CUT = 3.0        # 도배 지수 컷 — 근거 있는 값이 아니라 실측을 보고 잡은 것

# 키워드는 부분문자열로 걸리니 짧고 흔한 글자('구','동','시')를 넣지 말 것
SEG = {
    "커피 전문": ["바리스타", "커피머신", "로스팅", "홈카페", "커피마루", "드롱기", "베제라"],
    "건강·질환": ["아토피", "역류", "위염", "담적", "성조숙", "갑상선", "이명", "당뇨", "불면"],
    "해외 한인": ["싱가폴", "싱가포르", "일본맘", "뉴욕", "뉴저지", "해외직구", "몰테일", "교민"],
    "자영업·B2B": ["사장", "자영업", "소상공인", "식품제조", "장사", "납품"],
    # '맘'은 앞 세그먼트(건강·질환 등)를 먼저 태운 뒤라 안전하다 — 순서가 곧 우선순위
    "임신·육아": ["맘", "마마", "임신", "시험관", "육아", "출산", "아기", "유아"],
    "지역 커뮤니티": ["신도시", "입주자", "수다방", "아지매", "동네"],
}


def cafe_members(cid, cache={}):
    """공개 카페 홈에서 회원수·clubid. 인코딩이 MS949/EUC-KR이라 charset을 봐야 한다."""
    if cid in cache:
        return cache[cid]
    try:
        raw = urllib.request.urlopen(urllib.request.Request(
            f"https://cafe.naver.com/{cid}", headers={"User-Agent": UA}), timeout=15).read()
        enc = "utf-8"
        m = re.search(rb'charset=["\']?([\w-]+)', raw[:2000], re.I)
        if m:
            enc = m.group(1).decode()
        page = raw.decode(enc, "replace")
        mem = re.search(r"멤버수[^0-9]{0,30}([\d,]+)", page)
        club = re.search(r'clubid[\'"]?\s*[:=]\s*[\'"]?(\d+)', page, re.I)
        cache[cid] = {"members": int(mem.group(1).replace(",", "")) if mem else None,
                      "clubid": club.group(1) if club else None}
    except Exception:
        cache[cid] = {"members": None, "clubid": None}
    time.sleep(0.3)
    return cache[cid]


def is_question(title):
    return "?" in title or re.search(r"(요|까|나)[ㅠㅜ~!]*$", title) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--out", default="cafe.jsonl")
    a = ap.parse_args()
    H = headers()

    rows = []
    for q in a.queries:
        for it in search(H, "cafearticle", q, a.n):
            m = re.match(r"https?://cafe\.naver\.com/([\w-]+)/(\d+)", it["link"])
            rows.append({"query": q, "title": strip_tags(it["title"]),
                         "snippet": strip_tags(it["description"]),
                         "cafe": it["cafename"], "cid": m.group(1) if m else None,
                         "link": it["link"]})
    rows = list({r["link"]: r for r in rows}.values())
    print(f"수집 {len(rows)}건 · 카페 {len(set(r['cafe'] for r in rows))}개", file=sys.stderr)

    cnt = Counter(r["cid"] for r in rows if r["cid"])
    targets = [c for c, n in cnt.items() if n >= 2]     # 1건짜리는 회원수 조회 생략
    print(f"회원수 조회 {len(targets)}개 카페", file=sys.stderr)
    meta = {c: cafe_members(c) for c in targets}

    spam = {c for c in targets
            if meta[c]["members"] and cnt[c] / meta[c]["members"] * 10000 > SPAM_CUT}
    if spam:
        print("도배 판정:", file=sys.stderr)
        for c in sorted(spam, key=lambda x: -cnt[x])[:5]:
            name = next(r["cafe"] for r in rows if r["cid"] == c)
            print(f"   {cnt[c]:>4d}건 / {meta[c]['members']:,}명  {name[:40]}", file=sys.stderr)

    clean = [r for r in rows
             if r["cid"] not in spam
             and not any(k in r["cafe"] for k in BIZ)
             and not any(k in r["title"] + r["snippet"] for k in AD)]
    ask = [r for r in clean if is_question(r["title"])]
    print(f"필터: {len(rows)} → 도배·상업·광고 제외 {len(clean)} → 질문형 {len(ask)}", file=sys.stderr)

    seg = defaultdict(list)
    for r in ask:
        r["members"] = meta.get(r["cid"], {}).get("members")
        r["segment"] = next((s for s, kws in SEG.items()
                             if any(k in r["cafe"] for k in kws)), "기타")
        seg[r["segment"]].append(r)

    print("\n세그먼트별 질문", file=sys.stderr)
    for s, rs in sorted(seg.items(), key=lambda x: -len(x[1])):
        # 카페 수와 회원 합계는 분모가 다르다 — 회원수는 2건 이상 나온 카페만 조회하므로
        # 둘을 한 dict로 세면 1건짜리 카페들이 통째로 "0곳"으로 사라진다
        cafes = {r["cid"] for r in rs}
        known = {r["cid"]: r["members"] for r in rs if r.get("members")}
        print(f"   {s:12s} {len(rs):>4d}건 · 카페 {len(cafes)}곳 "
              f"(회원수 확인 {len(known)}곳, 합 {sum(known.values()):,}명)", file=sys.stderr)
        for r in rs[:3]:
            print(f"      · [{r['cafe'][:20]}] {r['title'][:40]}", file=sys.stderr)

    with open(a.out, "w", encoding="utf-8") as f:
        for r in ask:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n[완료] {a.out} ({len(ask)}건)", file=sys.stderr)


if __name__ == "__main__":
    main()
