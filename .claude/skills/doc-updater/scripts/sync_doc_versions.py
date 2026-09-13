#!/usr/bin/env python3
"""doc-versions.json을 선언이 아니라 **파생**으로 만든다.

동기화 버전의 원본은 가이드 5종 헤더의 `**Updated**: YYYY-MM-DD (vX.Y.Z)`다.
json은 그 파싱 결과의 캐시일 뿐 — 실행이 갱신을 잊어도 다음 실행이 헤더에서
다시 파생하므로 값이 틀릴 자리가 없다.

    python .claude/skills/doc-updater/scripts/sync_doc_versions.py          # 파싱 → json 갱신 + 상태 출력
    python .claude/skills/doc-updater/scripts/sync_doc_versions.py --check  # json 안 쓰고 상태만

경로는 워크스페이스 루트 기준(SKILL.md config와 동일). 루트 판별은 스크립트 위치에서 파생.
docs_synced_version = 문서별 버전의 최솟값 (가장 뒤처진 문서가 동기화 상태를 정한다).
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # .claude/skills/doc-updater/scripts/ → 워크스페이스 루트
DOCS_DIR = ROOT / "30-knowledge/37-claude-code/37.00-official-docs"
CACHE = ROOT / ".cache/doc-updater"
GUIDES = ["skills-guide.md", "subagents-guide.md", "claude-md-guide.md",
          "rules-guide.md", "plugins-guide.md"]
UPDATED = re.compile(r"\*\*Updated\*\*:\s*\d{4}-\d{2}-\d{2}\s*\(v(\d+\.\d+\.\d+)\)")


def vkey(v: str):
    return tuple(int(x) for x in v.split("."))


def main() -> int:
    if not DOCS_DIR.is_dir():
        print(f"ERROR: 가이드 폴더 없음: {DOCS_DIR} — 워크스페이스 구조 확인", file=sys.stderr)
        return 2
    docs, missing = {}, []
    for g in GUIDES:
        p = DOCS_DIR / g
        m = UPDATED.search(p.read_text(encoding="utf-8")[:2000]) if p.is_file() else None
        if m:
            docs[g] = m.group(1)
        else:
            missing.append(g)
    if missing:
        # 파생의 재료가 없으면 조용히 0.0.0으로 넘기지 않는다 — 전량 재반영 사고가 된다
        print(f"ERROR: 헤더에서 버전을 못 읽음: {', '.join(missing)} "
              f"(형식: **Updated**: YYYY-MM-DD (vX.Y.Z))", file=sys.stderr)
        return 2

    synced = min(docs.values(), key=vkey)
    changelog = None
    cl = CACHE / "changelog.md"
    if cl.is_file():
        m = re.search(r"^## (\d+\.\d+\.\d+)", cl.read_text(encoding="utf-8"), re.M)
        changelog = m.group(1) if m else None

    state = {
        "changelog_version": changelog,
        "docs_synced_version": synced,
        "last_checked": datetime.date.today().isoformat(),
        "docs": docs,
        "_derived": "이 파일은 가이드 헤더에서 파생된 캐시다 — 손으로 고치지 말 것 (sync_doc_versions.py)",
    }
    if "--check" not in sys.argv:
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / "doc-versions.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
