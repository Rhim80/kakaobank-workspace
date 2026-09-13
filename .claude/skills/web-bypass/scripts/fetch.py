#!/usr/bin/env python3
"""web-bypass: WebFetch fallback with 24h caching + optional PKM save.

Calls the vendored insane-search engine as a library (not via -m engine CLI),
because the engine's --json mode omits content. We need both content and meta.

Outputs a compact JSON summary to stdout (content_length + 500-char preview)
to avoid flooding the main conversation context. Full content lives in the
cache file and (optionally) in the --save-to-pkm markdown file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from engine import fetch as engine_fetch  # noqa: E402

CACHE_DIR = Path.home() / ".cache" / "web-bypass"
DEFAULT_TTL = 86400  # 24h
PREVIEW_CHARS = 500


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def cache_path(url: str) -> Path:
    return CACHE_DIR / f"{url_hash(url)}.json"


def read_cache(url: str, ttl: int) -> dict | None:
    p = cache_path(url)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        fetched = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - fetched).total_seconds()
        if age > ttl:
            return None
        data["cache_hit"] = True
        data["cache_age_seconds"] = int(age)
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def write_cache(url: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(url).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def call_engine(url: str, *, device: str, enable_playwright: bool,
                timeout: int, max_attempts: int) -> dict:
    result = engine_fetch(
        url,
        device_class=device,
        enable_playwright=enable_playwright,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    last_phase = None
    if result.trace:
        try:
            last_phase = result.trace[-1].to_dict().get("phase")
        except Exception:
            pass
    return {
        "url": url,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": bool(result.ok),
        "verdict": result.verdict,
        "profile_used": result.profile_used,
        "summary": result.summary or "",
        "last_phase": last_phase,
        "attempt_count": len(result.trace),
        "content": result.content or "",
    }


def yaml_quote(s: str | None) -> str:
    if s is None:
        return '""'
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def save_to_pkm(payload: dict, path: Path, force: bool) -> None:
    if path.exists() and not force:
        print(
            f"ERROR: {path} 이미 존재. --force 옵션으로 덮어쓰기 가능.",
            file=sys.stderr,
        )
        sys.exit(3)
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        "---\n"
        f"source: {yaml_quote(payload['url'])}\n"
        f"fetched_at: {yaml_quote(payload['fetched_at'])}\n"
        f"verdict: {yaml_quote(payload.get('verdict'))}\n"
        f"profile: {yaml_quote(payload.get('profile_used'))}\n"
        f"phase: {yaml_quote(payload.get('last_phase'))}\n"
        f"cache_hit: {str(payload.get('cache_hit', False)).lower()}\n"
        "---\n\n"
    )
    path.write_text(frontmatter + (payload.get("content") or ""), encoding="utf-8")
    print(f"saved: {path}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="web-bypass",
        description="WebFetch fallback wrapper (caching + PKM save).",
    )
    p.add_argument("url", help="Target URL.")
    p.add_argument("--save-to-pkm", metavar="PATH",
                   help="결과를 frontmatter + 본문 markdown으로 저장.")
    p.add_argument("--no-cache", action="store_true",
                   help="캐시 무시하고 강제 fetch.")
    p.add_argument("--ttl", type=int, default=DEFAULT_TTL,
                   help=f"캐시 TTL 초 (기본 {DEFAULT_TTL}).")
    p.add_argument("--force", action="store_true",
                   help="--save-to-pkm 경로 덮어쓰기 허용.")
    p.add_argument("--device", choices=("auto", "desktop", "mobile"),
                   default="auto")
    p.add_argument("--no-playwright", action="store_true",
                   help="Playwright fallback 비활성화 (curl 전용).")
    p.add_argument("--timeout", type=int, default=25)
    p.add_argument("--max-attempts", type=int, default=12)
    args = p.parse_args()

    payload: dict | None = None
    if not args.no_cache:
        payload = read_cache(args.url, args.ttl)

    if payload is None:
        payload = call_engine(
            args.url,
            device=args.device,
            enable_playwright=not args.no_playwright,
            timeout=args.timeout,
            max_attempts=args.max_attempts,
        )
        payload["cache_hit"] = False
        write_cache(args.url, payload)

    if args.save_to_pkm:
        save_to_pkm(payload, Path(args.save_to_pkm).expanduser(), args.force)

    content = payload.get("content") or ""
    summary = {
        "cache_hit": payload.get("cache_hit", False),
        "cache_age_seconds": payload.get("cache_age_seconds"),
        "url": payload["url"],
        "fetched_at": payload["fetched_at"],
        "ok": payload.get("ok"),
        "verdict": payload.get("verdict"),
        "profile_used": payload.get("profile_used"),
        "last_phase": payload.get("last_phase"),
        "attempt_count": payload.get("attempt_count"),
        "content_length": len(content),
        "content_preview": content[:PREVIEW_CHARS],
        "summary": payload.get("summary", ""),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
