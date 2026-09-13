---
name: web-bypass
description: WebFetch가 403/차단/JS-required로 실패한 URL을 12개 reference 패턴(Jina·JSON API·RSS·TLS 우회·Playwright·Wayback 등)으로 우회 추출, 24h 캐싱. "WebFetch 실패", "403 우회", "차단 우회", "web-bypass" 등을 언급하면 자동 실행. 단순 URL 요약은 WebFetch, OCR 아카이빙은 web-crawler-ocr, 리뷰 분석은 review-analyzer 우선.
context: fork
background: false
allowed-tools:
  - Bash
  - Read
---

# web-bypass

WebFetch가 못 잡는 URL을 5단계 적응형 fetch chain으로 자동 우회한다.
오픈소스 fetch 엔진을 vendoring + 캐싱 wrapper + 노트 저장 어댑터. (출처·라이선스는 NOTICE 참고)

> **처음 쓰기 전 1회**: `bash .claude/skills/web-bypass/scripts/install.sh`
> 의존성(curl_cffi·bs4·pyyaml)을 이 스킬 안 venv에 깔아 둔다. 멱등성이 있어 여러 번 돌려도 안전하고, Playwright·CloakBrowser가 필요하면 `--with-playwright`·`--with-cloak`을 붙인다.

## 호출 시점

다음 중 하나면 이 스킬을 쓴다.

- WebFetch가 403/blocked/JS-required/empty SPA로 실패
- Reddit/HN/arXiv/Bluesky/Mastodon/Stack Overflow/GitHub 같은 **공개 API가 있는 사이트**에서 깔끔한 데이터 필요
- Twitter/X 본문 추출 (syndication endpoint)
- RSS/Atom 피드 파싱
- 페이월·지역 차단 → Wayback/AMP 캐시
- 네이버 검색/블로그/뉴스/금융

다음이면 **다른 스킬**을 쓴다.

| 상황 | 사용할 스킬 |
|---|---|
| 단순 URL 본문 요약 (가벼운 케이스) | `WebFetch` |
| "이 URL 이미지 OCR 포함 아카이빙" | `web-crawler-ocr` (Gemini OCR 20MB) |
| 다나와/네이버 리뷰 분석 | `review-analyzer` |
| 클릭·폼 입력 등 인터랙션 | Playwright MCP (이 스킬은 fetch만 한다) |

## 실행 흐름

### Step 1. 의존성 확인 (한 번만)

```bash
# Mac·Linux는 venv/bin, 윈도우 Git Bash는 venv/Scripts — 둘 중 하나면 설치된 것
test -x .claude/skills/web-bypass/scripts/venv/bin/python \
  || test -x .claude/skills/web-bypass/scripts/venv/Scripts/python.exe
```

존재하면 Step 2로. **없으면** 사용자에게 안내하고 중단:

```
의존성 미설치. 다음 명령으로 설치하세요:
  bash .claude/skills/web-bypass/scripts/install.sh

(차단 사이트 Phase 3까지 가는 케이스도 다루려면)
  bash .claude/skills/web-bypass/scripts/install.sh --with-playwright

(Cloudflare/Turnstile/DataDome 챌린지를 실제로 통과해야 하면)
  bash .claude/skills/web-bypass/scripts/install.sh --with-cloak
```

`--with-cloak`은 CloakBrowser(스텔스 Chromium)를 챌린지 폴백에 추가한다.
미설치 상태로 챌린지 프로파일에 걸려도 자동으로 기존 Playwright 폴백으로
내려가므로 비치명적 — CAPTCHA/봇 벽이 실제로 막는 케이스에서만 설치하면 된다.

### Step 2. fetch.sh 호출

```bash
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>"
```

옵션:

```bash
# 노트로 저장 (frontmatter 포함 markdown)
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" \
  --save-to-pkm "/path/to/note.md"

# 캐시 무시하고 강제 재fetch
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" --no-cache

# TTL 조정 (초 단위, 기본 86400 = 24h)
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" --ttl 3600

# Playwright 비활성화 (curl 전용으로 빠르게)
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" --no-playwright

# --save-to-pkm 경로가 이미 있으면 덮어쓰기
bash .claude/skills/web-bypass/scripts/fetch.sh "<URL>" \
  --save-to-pkm "/path/to/note.md" --force
```

### Step 3. 결과 파싱

stdout으로 압축 JSON이 옵니다 (full content는 캐시에만, 메인 컨텍스트 보호용).

```json
{
  "cache_hit": false,
  "cache_age_seconds": null,
  "url": "https://...",
  "fetched_at": "2026-04-25T10:00:00Z",
  "ok": true,
  "verdict": "strong_ok",
  "profile_used": "reddit-json",
  "last_phase": "phase1",
  "attempt_count": 2,
  "content_length": 14521,
  "content_preview": "최초 500자...",
  "summary": "..."
}
```

판단:

- `ok: true` → 성공. content_preview로 충분하면 사용자에게 요약 반환. 더 필요하면 캐시 파일(`~/.cache/web-bypass/<hash>.json`) Read로 전체 content 접근
- `ok: false` → 실패. `verdict`(login_required/blocked/empty/error)와 `summary` 사용자에게 그대로 전달. 단, R7 hint("API-first") 떴다면 그 가이드 우선

### Step 4. 실패 시 reference 가이드 (progressive disclosure)

엔진이 실패했지만 **특정 도메인 패턴이 보이면** 해당 reference를 Read 해서 전략을 잡는다. 인라인하지 말고 필요할 때만.

| 상황 | Read |
|---|---|
| 일반 텍스트 추출 깔끔하게 | `references/jina.md` |
| Reddit/HN/Wikipedia/npm/PyPI | `references/json-api.md` |
| Bluesky/Mastodon/arXiv/Stack Overflow/GitHub | `references/public-api.md` |
| YouTube 외 미디어 (Vimeo/Twitch/SoundCloud 등 1858개) | `references/media.md` |
| Twitter/X 단일 트윗 또는 타임라인 | `references/twitter.md` |
| 네이버 검색·블로그·뉴스·금융 | `references/naver.md` |
| RSS/Atom 피드 | `references/rss.md` |
| WAF 우회 (curl_cffi 지문, identity spoofing) | `references/tls-impersonate.md` |
| JS 렌더링 필요 (snapshot/evaluate/network_requests) | `references/playwright.md` |
| 페이월·지역 차단·삭제된 페이지 | `references/cache-archive.md` |
| OGP/JSON-LD/RSC payload 추출 | `references/metadata.md` |
| Phase 0~3 에스컬레이션 의사결정 | `references/fallback.md` |

### Step 5. 사용자에게 결과 반환

- 성공: content_preview로 답변 + 필요 시 `~/.cache/web-bypass/<hash>.json` Read로 전체 본문
- 노트로 저장한 경우: 저장 경로 명시
- 실패: `verdict` + `summary` + 다음 옵션 제시 ("이미지도 다 따와줘" → web-crawler-ocr / "직접 클릭 인터랙션" → playwright MCP)

## 캐시 동작

- 위치: `~/.cache/web-bypass/<sha256-prefix-16>.json`
- TTL: 기본 24h, `--ttl <초>`로 조정
- `cache_hit: true`이면 응답 < 50ms (engine 호출 안 함)
- `--no-cache`로 강제 재fetch
- v1은 만료 캐시 자동 삭제 안 함. 누적 시 `rm -rf ~/.cache/web-bypass/*` 수동 정리

## 노트 저장 형식

`--save-to-pkm <path>` 사용 시 다음 형식 markdown 저장:

```markdown
---
source: "https://..."
fetched_at: "2026-04-25T10:00:00Z"
verdict: "strong_ok"
profile: "reddit-json"
phase: "phase1"
cache_hit: false
---

(engine이 추출한 본문 — HTML/markdown/JSON-LD 텍스트)
```

이미지 OCR이 필요한 케이스는 web-crawler-ocr로 핸드오프.

## 알려진 한계

- **아주 짧은 페이지는 본문을 정상으로 받아왔는데도 `verdict: challenge`로 실패 판정된다.** 이럴 땐 `content_preview`를 먼저 확인한다 — 내용이 멀쩡하면 성공으로 취급해도 된다.
  - **원인**: engine에는 "본문이 `tiny_body` 기준보다 짧으면 제대로 못 받아온 것"이라는 판정 규칙이 있다(차단 페이지가 대개 짧기 때문). engine에 `success_selectors`(예: `["h1","p"]`)를 넘기면 "이 태그가 있으면 성공"이라는 호출자 정의를 신뢰해 그 규칙을 건너뛰는데, **`scripts/fetch.py`는 이 인자를 넘기지 않는다.** 그래서 짧은 페이지는 실패로 판정되고 `--max-attempts` 기본값 12까지 헛시도한다.
  - 실측(2026-07-31): `example.com`(559바이트) — `fetch.py` 경유는 `challenge`/`cloudflare_turnstile`(8회 시도), `success_selectors=["h1","p"]`를 넘기는 `engine/tests/test_smoke.py`는 `strong_ok`.
  - `news.ycombinator.com`(34KB)은 `fetch.py` 경유로도 1회 시도에 통과. 일반적인 웹페이지는 이 기준을 훨씬 넘으므로 실사용에서 자주 걸리지는 않는다.
  - 자주 걸린다면 `fetch.py`에 `--success-selectors` 인자를 추가해 engine으로 전달하면 된다(현재 미구현).

## 종료 코드

| 코드 | 의미 |
|---|---|
| 0 | 성공 (engine ok=True) |
| 1 | 실패 (blocked/페이월/네트워크 오류 등) |
| 2 | CLI 인자 오류 또는 venv 미설치 |
| 3 | --save-to-pkm 경로 충돌 (--force 없이 덮어쓰기 시도) |

## 업스트림 동기화

엔진 업데이트 받기:

```bash
bash .claude/skills/web-bypass/scripts/sync-upstream.sh
```

- vendored 영역(`engine/`, `references/`, `LICENSE`)만 갱신
- `scripts/`, `SKILL.md`, `README.md`, `NOTICE`는 우리 자산이라 보존
- rsync 직후 `scripts/cloakbrowser.patch`를 engine에 자동 재적용 (sync가 덮어쓴 로컬 개선분 복원: cloakbrowser 통합 + validators 오탐 수정). 패치 적용 실패 시 경고 출력 — engine 구조가 바뀌었다는 신호
- engine CLI signature 변경 시 경고 (fetch.py wrapper 영향 가능)

상세는 `README.md` 참고.

---

Made by Do Better Things
