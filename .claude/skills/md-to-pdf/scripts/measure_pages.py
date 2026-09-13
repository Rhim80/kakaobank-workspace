#!/usr/bin/env python3
"""md-to-pdf 핸드아웃의 페이지 높이 실측 게이트 (root-cause 2026-08-10 항).

Step 4 Phase C가 "높이 검증"을 글로만 지시하고 재는 수단이 없어, 세션마다
content-budget 표를 눈대중으로 더했다 — 8/9 정리본은 페이지 아래 40%가 비고(과소),
8/10 HFK 핸드아웃은 6쪽이 넘쳤다(과다). 둘 다 조판을 끝낸 뒤에야 발견돼 재작업.
이 스크립트가 렌더해 실측한다 — 추정표는 초안 배치용, 판정은 여기.

    python .claude/skills/md-to-pdf/scripts/measure_pages.py <handout.html> [--json]

출력: 페이지마다 콘텐츠 높이/가용 높이(mm)·채움률·넘침 여부 + 블록별 높이
(재배치 계산용 — 어느 블록을 옮길지 mm 단위로 정할 수 있다).
종료코드: 넘침 있으면 1, 렌더 실패 2, 전부 정상 0.
`.page`는 overflow:hidden이라 넘침이 화면에선 잘림으로만 보인다 — 눈으로는 못 잡는다.
"""
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright가 필요합니다: python -m pip install playwright && python -m playwright install chromium")

PX2MM = 25.4 / 96.0
UNDERFILL = 0.62   # 마지막 아닌 페이지가 이 밑이면 "헐렁" 경고 (8/9 사고: 평균 75% 빔)

MEASURE_JS = """
() => {
  const pages = [...document.querySelectorAll('.page')];
  return pages.map(pg => {
    const cs = getComputedStyle(pg);
    const top = pg.getBoundingClientRect().top + parseFloat(cs.paddingTop);
    const capacity = pg.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    const blocks = [];
    let bottom = 0;
    for (const el of pg.children) {
      const ecs = getComputedStyle(el);
      if (ecs.position === 'absolute' || ecs.position === 'fixed') continue;  // 페이지번호·장식
      const r = el.getBoundingClientRect();
      const mt = parseFloat(ecs.marginTop), mb = parseFloat(ecs.marginBottom);
      blocks.push({tag: el.tagName.toLowerCase(),
                   cls: (el.className || '').toString().split(' ')[0] || '',
                   text: (el.textContent || '').trim().slice(0, 40),
                   height: r.height + mt + mb});
      bottom = Math.max(bottom, r.bottom - top + mb);
    }
    return {capacity, content: bottom, blocks};
  });
}
"""


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(args[0]).expanduser().resolve()
    if not path.is_file():
        print(f"파일 없음: {path}", file=sys.stderr)
        return 2

    try:
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(channel="chrome")
            except Exception:
                b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1000, "height": 1400})
            pg.goto(path.as_uri(), wait_until="networkidle")
            data = pg.evaluate(MEASURE_JS)
            b.close()
    except Exception as e:
        print(f"렌더 실패: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if not data:
        print("`.page` 요소가 없다 — md-to-pdf 산출물이 맞는지 확인", file=sys.stderr)
        return 2

    report, overflow_n = [], 0
    for i, d in enumerate(data, 1):
        cap, con = d["capacity"] * PX2MM, d["content"] * PX2MM
        fill = con / cap if cap else 0
        over = con > cap + 1  # 1mm 여유 (렌더 오차)
        if over:
            overflow_n += 1
        last = i == len(data)
        status = "넘침" if over else ("헐렁" if (fill < UNDERFILL and not last and i > 1) else "OK")
        report.append({"page": i, "capacity_mm": round(cap, 1), "content_mm": round(con, 1),
                       "fill": round(fill, 2), "status": status,
                       "blocks": [{**bl, "height_mm": round(bl.pop("height") * PX2MM, 1)}
                                  for bl in d["blocks"]]})

    if "--json" in sys.argv:
        print(json.dumps({"pages": report, "overflow": overflow_n}, ensure_ascii=False, indent=1))
    else:
        for r in report:
            print(f"[{r['status']:2s}] p{r['page']:>2}  {r['content_mm']:6.1f} / {r['capacity_mm']:.1f}mm"
                  f"  ({r['fill'] * 100:.0f}%)")
            if r["status"] != "OK":
                for bl in r["blocks"]:
                    print(f"        {bl['height_mm']:6.1f}mm  <{bl['tag']}.{bl['cls']}> {bl['text']}")
        print(f"페이지 {len(report)} · 넘침 {overflow_n} · "
              f"헐렁 {sum(1 for r in report if r['status'] == '헐렁')}")
    return 1 if overflow_n else 0


if __name__ == "__main__":
    sys.exit(main())
