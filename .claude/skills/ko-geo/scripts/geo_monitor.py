#!/usr/bin/env python3
"""
geo_monitor.py — ko-geo 검증 루프(GEO 인용 측정)

ko-geo가 콘텐츠를 변환한 뒤, 그 콘텐츠가 실제로 생성형 엔진(Perplexity·Gemini·ChatGPT)의
답변에 인용/언급되는지 측정한다. 변환→측정→재변환 루프의 "측정" 단계.

원리: 타깃 질문들을 엔진에 N번씩 던지고, 답변에 내 브랜드명/도메인이
나오는 비율(인용률·언급률)을 집계한다. 답변이 비결정적이라 1회가 아니라
여러 번 샘플링해 비율로 본다.

두 가지 모드
------------
1) manual  : API 키 없이. 엔진 채팅창에 질문을 직접 붙여넣고, 받은 답변을
             responses 파일에 모아 파싱. 비용 0원. (기본 권장 — 키 없어도 당장 됨)
2) run     : API 키가 있으면 자동 질의. Perplexity(sonar)·Gemini(google_search grounding).

명령
----
  init     <config.json>                 설정 파일 뼈대 생성
  template <responses.md>                manual 모드용 응답 파일 뼈대 생성 (config 기반)
  manual   <config.json> <responses.md> [--label baseline]   붙여넣은 답변 파싱·집계
  run      <config.json> [--label after] [--engine perplexity,gemini]   자동 질의·집계
  compare  <config.json> [--before baseline --after after]    두 회차 인용률 비교

집계 결과는 config의 log_path(기본 geo-monitor-log.md)에 사람용 마크다운으로,
같은 경로 + ".jsonl"에 기계용 레코드로 append 된다. compare는 jsonl을 읽는다.

키 설정(run 모드만): scripts/.env 또는 환경변수
  PERPLEXITY_API_KEY=...
  GEMINI_API_KEY=...     (Google AI Studio 무료 티어 가능)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv()
except Exception:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# 공통: 탐지 로직
# ─────────────────────────────────────────────────────────────────────────────
def detect(answer_text, citation_urls, brand):
    """답변 1건에서 브랜드 언급/인용 여부를 판정.

    - mention : 브랜드명 문자열이 답변 본문에 등장
    - cited   : 브랜드 도메인이 본문 또는 인용 URL 목록에 등장
    - pos     : 본문에서 브랜드명이 처음 나온 위치(작을수록 앞쪽=두괄). 없으면 -1
    """
    text_l = (answer_text or "").lower()
    names = [n.lower() for n in brand.get("names", []) if n.strip()]
    domains = [d.lower() for d in brand.get("domains", []) if d.strip()]
    urls_l = [(u or "").lower() for u in (citation_urls or [])]

    mention = any(n in text_l for n in names)
    cited = any(d in text_l for d in domains) or any(
        any(d in u for d in domains) for u in urls_l
    )
    positions = [text_l.find(n) for n in names if n in text_l]
    pos = min(positions) if positions else -1
    return mention, cited, pos


def competitor_hits(answer_text, competitors):
    text_l = (answer_text or "").lower()
    return [c for c in competitors if c.lower() in text_l]


def aggregate(samples, brand, competitors):
    """samples: [{"text":..., "citations":[...]}] → 질문 1개의 집계 결과."""
    n = len(samples)
    mention_n = cited_n = 0
    comp_counter = {c: 0 for c in competitors}
    for s in samples:
        m, c, _ = detect(s.get("text", ""), s.get("citations", []), brand)
        mention_n += 1 if m else 0
        cited_n += 1 if c else 0
        for hit in competitor_hits(s.get("text", ""), competitors):
            comp_counter[hit] += 1
    return {
        "samples": n,
        "mention_n": mention_n,
        "cited_n": cited_n,
        "mention_rate": round(mention_n / n, 3) if n else 0.0,
        "cited_rate": round(cited_n / n, 3) if n else 0.0,
        "competitors": comp_counter,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 엔진 호출 (run 모드)
# ─────────────────────────────────────────────────────────────────────────────
def call_perplexity(query, model="sonar"):
    """Perplexity sonar. 답변 본문 + citations(URL 목록) 반환."""
    import urllib.request
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY 없음 (.env 또는 환경변수)")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": query}],
    }).encode()
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    text = data["choices"][0]["message"]["content"]
    citations = data.get("citations") or [
        s.get("url") for s in data.get("search_results", []) if s.get("url")
    ]
    return {"text": text, "citations": citations}


def call_gemini(query, model="gemini-2.5-flash"):
    """Gemini + Google Search grounding. 본문 + grounding URL 반환."""
    import urllib.request
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 없음 (.env 또는 환경변수)")
    body = json.dumps({
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],
    }).encode()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    cand = data["candidates"][0]
    text = "".join(
        p.get("text", "") for p in cand.get("content", {}).get("parts", [])
    )
    citations = []
    gm = cand.get("groundingMetadata", {})
    for chunk in gm.get("groundingChunks", []):
        uri = chunk.get("web", {}).get("uri")
        if uri:
            citations.append(uri)
    return {"text": text, "citations": citations}


ENGINES = {"perplexity": call_perplexity, "gemini": call_gemini}


# ─────────────────────────────────────────────────────────────────────────────
# 입출력
# ─────────────────────────────────────────────────────────────────────────────
def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("competitors", [])
    cfg.setdefault("samples", 5)
    cfg.setdefault("engines", ["perplexity", "gemini"])
    cfg.setdefault("log_path", str(Path(path).parent / "geo-monitor-log.md"))
    return cfg


def write_run(cfg, label, per_query, engine_label):
    """집계 결과를 사람용 .md + 기계용 .jsonl 양쪽에 append."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    log = Path(cfg["log_path"])
    log.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"\n## [{ts}] {label} · {engine_label}\n"]
    lines.append("| 질문 | 인용률 | 언급률 | 표본 |")
    lines.append("|------|-------|-------|------|")
    for q, agg in per_query:
        lines.append(
            f"| {q[:40]} | {agg['cited_rate']*100:.0f}% "
            f"| {agg['mention_rate']*100:.0f}% | {agg['samples']} |"
        )
    # 경쟁사 점유(합산)
    comp_total = {}
    for _, agg in per_query:
        for c, n in agg["competitors"].items():
            comp_total[c] = comp_total.get(c, 0) + n
    if comp_total:
        lines.append("\n경쟁사 언급 합계: " + ", ".join(
            f"{c} {n}" for c, n in sorted(comp_total.items(), key=lambda x: -x[1])
        ))
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    record = {
        "ts": ts, "label": label, "engine": engine_label,
        "queries": [{"q": q, **agg} for q, agg in per_query],
    }
    with open(str(log) + ".jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log


# ─────────────────────────────────────────────────────────────────────────────
# 명령
# ─────────────────────────────────────────────────────────────────────────────
def cmd_init(args):
    sample = {
        "brand": {"names": ["브랜드명", "Brand"], "domains": ["example.com"]},
        "competitors": ["경쟁사A", "경쟁사B"],
        "queries": [
            "이 분야 추천 업체/서비스는?",
            "OO 할 때 가장 좋은 방법은?",
        ],
        "engines": ["perplexity", "gemini"],
        "samples": 5,
        "log_path": "geo-monitor-log.md",
    }
    with open(args.config, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"✅ 설정 뼈대 생성: {args.config}")
    print("   brand.names / domains / queries / competitors 를 실제 값으로 채우세요.")


def cmd_template(args):
    cfg = load_config(args.config)
    engines = cfg["engines"]
    blocks = [
        "<!-- geo_monitor manual 응답 파일. 각 블록의 답변 영역에 엔진이 준 답을 그대로 붙여넣으세요. -->",
        "<!-- 같은 질문을 여러 번 물어 여러 블록으로 만들면 표본이 늘어 비율이 정확해집니다. -->",
    ]
    for q in cfg["queries"]:
        for eng in engines:
            blocks.append(f"\n## QUERY: {q}")
            blocks.append(f"## ENGINE: {eng}")
            blocks.append("(여기에 답변 붙여넣기 — 답변에 포함된 출처 URL도 함께)")
            blocks.append("---")
    with open(args.responses, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks) + "\n")
    n = len(cfg["queries"]) * len(engines)
    print(f"✅ 응답 파일 뼈대 생성: {args.responses} (블록 {n}개)")
    print("   각 ENGINE 채팅창에 QUERY를 붙여넣고, 받은 답변을 블록에 채운 뒤")
    print(f"   geo_monitor.py manual {args.config} {args.responses} --label baseline")


def parse_responses_file(path):
    """## QUERY / ## ENGINE / 본문 / --- 블록을 파싱."""
    entries = []
    cur = None
    body = []
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("## QUERY:"):
            if cur:
                cur["text"] = "\n".join(body).strip()
                entries.append(cur)
            cur = {"query": line[len("## QUERY:"):].strip(), "engine": "manual"}
            body = []
        elif line.startswith("## ENGINE:") and cur is not None:
            cur["engine"] = line[len("## ENGINE:"):].strip()
        elif line.strip() == "---":
            if cur:
                cur["text"] = "\n".join(body).strip()
                entries.append(cur)
                cur = None
                body = []
        elif cur is not None:
            body.append(line)
    if cur:
        cur["text"] = "\n".join(body).strip()
        entries.append(cur)
    # URL 추출(본문에 박힌 출처)
    import re
    for e in entries:
        e["citations"] = re.findall(r"https?://[^\s)\]]+", e["text"])
    # 붙여넣기 안 한 빈 블록 제거
    return [e for e in entries if e["text"] and not e["text"].startswith("(여기에")]


def cmd_manual(args):
    cfg = load_config(args.config)
    entries = parse_responses_file(args.responses)
    if not entries:
        print("❌ 붙여넣은 답변이 없습니다. 템플릿 블록에 답변을 채웠는지 확인하세요.")
        sys.exit(1)
    # 질문별 그룹
    by_q = {}
    for e in entries:
        by_q.setdefault(e["query"], []).append(e)
    per_query = [(q, aggregate(s, cfg["brand"], cfg["competitors"]))
                 for q, s in by_q.items()]
    log = write_run(cfg, args.label, per_query, "manual")
    _print_summary(per_query)
    print(f"\n📝 기록: {log}")


def cmd_run(args):
    cfg = load_config(args.config)
    engines = args.engine.split(",") if args.engine else cfg["engines"]
    samples = cfg["samples"]
    for eng in engines:
        if eng not in ENGINES:
            print(f"⚠️  지원하지 않는 엔진: {eng} (perplexity|gemini)")
            continue
        try:
            per_query = []
            for q in cfg["queries"]:
                results = []
                for i in range(samples):
                    try:
                        results.append(ENGINES[eng](q))
                    except Exception as e:
                        print(f"  · '{q[:30]}' 표본{i+1} 실패: {e}")
                if results:
                    per_query.append((q, aggregate(results, cfg["brand"], cfg["competitors"])))
            if per_query:
                log = write_run(cfg, args.label, per_query, eng)
                print(f"\n=== {eng} ===")
                _print_summary(per_query)
                print(f"📝 기록: {log}")
        except Exception as e:
            print(f"❌ {eng} 실행 실패: {e}")


def cmd_compare(args):
    cfg = load_config(args.config)
    jsonl = Path(str(cfg["log_path"]) + ".jsonl")
    if not jsonl.exists():
        print("❌ 비교할 기록 없음. 먼저 manual 또는 run 으로 2회 이상 측정하세요.")
        sys.exit(1)
    records = [json.loads(l) for l in open(jsonl, encoding="utf-8") if l.strip()]
    before = _pick(records, args.before, -2)
    after = _pick(records, args.after, -1)
    if not before or not after:
        print("❌ 비교할 회차를 찾지 못함. --before/--after 라벨을 확인하세요.")
        sys.exit(1)
    bmap = {q["q"]: q for q in before["queries"]}
    print(f"\n비교: [{before['label']} {before['ts']}] → [{after['label']} {after['ts']}]\n")
    print("| 질문 | 인용률 | 언급률 |")
    print("|------|-------|-------|")
    for q in after["queries"]:
        b = bmap.get(q["q"])
        if b:
            dc = (q["cited_rate"] - b["cited_rate"]) * 100
            dm = (q["mention_rate"] - b["mention_rate"]) * 100
            print(f"| {q['q'][:36]} | {b['cited_rate']*100:.0f}%→{q['cited_rate']*100:.0f}% ({dc:+.0f}p) "
                  f"| {b['mention_rate']*100:.0f}%→{q['mention_rate']*100:.0f}% ({dm:+.0f}p) |")
        else:
            print(f"| {q['q'][:36]} | (신규) {q['cited_rate']*100:.0f}% | {q['mention_rate']*100:.0f}% |")


def _pick(records, label, default_idx):
    if label:
        matches = [r for r in records if r["label"] == label]
        return matches[-1] if matches else None
    return records[default_idx] if len(records) >= abs(default_idx) else None


def _print_summary(per_query):
    print("\n| 질문 | 인용률 | 언급률 | 표본 |")
    print("|------|-------|-------|------|")
    for q, agg in per_query:
        print(f"| {q[:40]} | {agg['cited_rate']*100:.0f}% "
              f"| {agg['mention_rate']*100:.0f}% | {agg['samples']} |")


def main():
    p = argparse.ArgumentParser(description="ko-geo 검증 루프: GEO 인용 측정")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("config"); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("template"); s.add_argument("config"); s.add_argument("responses"); s.set_defaults(fn=cmd_template)
    s = sub.add_parser("manual"); s.add_argument("config"); s.add_argument("responses"); s.add_argument("--label", default="baseline"); s.set_defaults(fn=cmd_manual)
    s = sub.add_parser("run"); s.add_argument("config"); s.add_argument("--label", default="run"); s.add_argument("--engine", default=""); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("compare"); s.add_argument("config"); s.add_argument("--before", default=""); s.add_argument("--after", default=""); s.set_defaults(fn=cmd_compare)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
