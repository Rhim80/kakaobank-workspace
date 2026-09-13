# web-bypass

WebFetch가 차단/403/JS-required로 실패한 URL을 자동 우회 추출하는 Claude Code 스킬.
오픈소스 fetch 엔진을 vendoring + 캐싱 wrapper + 노트 저장 어댑터. (업스트림 출처·라이선스는 `NOTICE` 참고)

## 설치

```bash
# 기본 (curl_cffi + bs4 + pyyaml)
bash .claude/skills/web-bypass/scripts/install.sh

# Phase 3 Playwright 케이스까지 (chromium ~300MB)
bash .claude/skills/web-bypass/scripts/install.sh --with-playwright
```

## 사용

Claude Code 세션에서 SKILL.md description의 트리거 키워드(WebFetch 실패, 403 우회, Reddit/HN/arXiv API, Twitter 본문, RSS, TLS 지문, wayback 등)를 언급하면 자동 실행. 명시 호출:

```bash
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>"

# 옵션
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" \
  --save-to-pkm "/path/to/note.md" \    # frontmatter + 본문 markdown 저장
  --no-cache \                           # 캐시 무시하고 강제 fetch
  --ttl 3600 \                           # 캐시 TTL (초, 기본 86400)
  --force \                              # --save-to-pkm 경로 덮어쓰기
  --no-playwright                        # Phase 3 비활성화 (curl 전용)
```

## 책임 경계 (다른 스킬과 충돌 회피)

| 시나리오 | 사용 스킬 | 이유 |
|---|---|---|
| URL 한 개 본문 요약 (가벼움) | `WebFetch` | 80% 케이스 충분 |
| WebFetch 403/blocked/JS-required | **web-bypass** | Phase 1~3 우회 |
| "이 URL 텍스트만 노트로 저장" | **web-bypass** | `--save-to-pkm` |
| "이 URL 이미지 OCR 포함 아카이빙" | `web-crawler-ocr` | Gemini OCR 20MB |
| 네이버 브랜드스토어 리뷰 | `review-crawl` | selenium + ingest API 전용 |
| 다나와/네이버 일반 리뷰 분석 | `review-analyzer` | 4단계 분석 프레임워크 |
| YouTube URL | `youtube-content-analyzer` | 자막 + 메타 |
| 라이브러리 공식 문서 | `context7` | REST API |
| Reddit/HN/arXiv/Twitter/RSS/Wayback | **web-bypass** | json-api/twitter/rss/cache-archive reference |
| 클릭/폼 인터랙션 | `mcp__plugin_playwright_playwright__*` | web-bypass는 fetch만 |

핸드오프 룰: WebFetch 실패 → web-bypass → 사용자가 "이미지도 다 따와줘" 요청 시 → web-crawler-ocr.

## 캐시 동작

- 위치: `~/.cache/web-bypass/<sha256-prefix-16>.json`
- TTL: 기본 24h (`--ttl <초>`로 조정)
- Hit 시 응답 < 50ms (engine 호출 안 함)
- v1은 만료 캐시 자동 삭제 안 함. 누적 시 `rm -rf ~/.cache/web-bypass/*` 수동 정리

## 노트 저장 형식

`--save-to-pkm <path>` 사용 시:

```markdown
---
source: "https://..."
fetched_at: "2026-04-25T10:00:00Z"
verdict: "strong_ok"
profile: "reddit-json"
phase: "phase1"
cache_hit: false
---

(engine이 추출한 본문)
```

이미지 OCR 필요한 케이스는 web-crawler-ocr로.

## 디렉토리 구조

```
web-bypass/
├── SKILL.md                   # Claude Code 진입점 (frontmatter + 가이드)
├── README.md                  # 이 파일
├── LICENSE                    # 업스트림 MIT
├── NOTICE                     # vendoring 출처 + 변경사항
├── upstream.txt               # 현재 동기화된 commit SHA + 버전
├── scripts/
│   ├── install.sh             # venv + python -m pip install [+ --with-playwright]
│   ├── fetch.sh               # 메인 wrapper (thin shell)
│   ├── fetch.py               # Python 본 wrapper (캐싱 + 노트 저장)
│   ├── sync-upstream.sh       # 업스트림 동기화
│   ├── requirements.txt       # curl_cffi/bs4/pyyaml
│   └── venv/                  # gitignored
├── engine/                    # 업스트림 vendored (수정 금지)
│   ├── __main__.py, fetch_chain.py, validators.py, waf_detector.py,
│   ├── waf_profiles.yaml, executor.py, url_transforms.py, templates/
└── references/                # 업스트림 vendored 12개
    └── jina/json-api/public-api/media/twitter/naver/rss/
        tls-impersonate/playwright/cache-archive/metadata/fallback.md
```

## 업스트림 동기화

```bash
bash .claude/skills/web-bypass/scripts/sync-upstream.sh
```

- vendored 영역(`engine/`, `references/`, `LICENSE`)만 갱신
- `scripts/`, `SKILL.md`, `README.md`, `NOTICE`는 우리 자산이라 보존
- engine CLI signature 변경 시 자동 경고 (fetch.py wrapper 영향 가능)

## 라이선스

MIT. 업스트림 출처와 vendoring 변경 내역은 `NOTICE` 참고.

## v2 로드맵 (TBD)

현재 v1 범위 제외 항목:

- 한국 사이트 reference 보강 (다음/티스토리/디씨/한국 언론사 페이월) - `references/ko-sites.md`
- 만료 캐시 자동 정리 (`--cleanup` 또는 cron)
- OpenClaw(보리) 통합 (process-queue 스킬 hook)
- PDF fetch + pdf-to-md 자동 체이닝
- 다중 URL 배치 처리 (`--urls-file`)
- Ghost frontmatter / structured JSON 출력 어댑터
