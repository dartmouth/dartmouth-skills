# Code-generation patterns for DartAPI clients

These are language-neutral patterns to translate idiomatically into whatever language/framework the target repository already uses. **Do not default to one language** — detect the target project's conventions first (see SKILL.md's workflow), then apply these patterns using that project's existing HTTP client, config/secrets loading, and error-handling style. Treat this file as the spec for *behavior*, not as a template to transliterate line-by-line.

## 1. JWT acquisition + caching

Behavior required:
- Read the API key from wherever the target project keeps secrets (env var, secrets manager, config service) — never hardcode it.
- Build the requested scope list explicitly; never omit `scope` expecting a sane default (there isn't one — see `auth-jwt.md`).
- `POST /api/jwt` with `Authorization: {api_key}` and the space-separated `scope` query param.
- **Validate `accepted_scopes` against the requested list and fail loudly on any gap** — this is the single most important correctness rule in the whole API (see `auth-jwt.md`).
- Cache the resulting JWT **keyed by the exact scope-set requested** (different callers needing different scopes should not collide on one cached token).
- Before reusing a cached JWT, check `exp` against current time with a safety margin (e.g. refuse to reuse a token expiring within the next request's expected duration); if expired or near-expiry, call `/api/jwt` again — there is no separate refresh endpoint.
- Thread-safety / concurrent-refresh: if the target language has concurrency, guard the refetch so parallel callers don't all trigger simultaneous logins (a simple mutex/lock around "check-then-refetch" is normally sufficient; don't over-engineer this unless the target app already has a pattern for it).

## 2. Scope-aware resource client

Behavior required:
- Each resource method should declare the scope(s) it needs (see the relevant `resource-*.md`), and check the currently-cached JWT's `accepted_scopes` before firing the request — fail with a clear "scope X required for this call was not granted" error rather than making the call and receiving a truncated/unexpected payload.
- Build request URLs/query strings using the filter operators and pagination parameters documented in `request-response-conventions.md` — implement filter-building as a small helper/DSL appropriate to the language rather than raw string concatenation scattered through call sites, to keep the escaping/wildcard/operator rules in one place.
- Parse dates (`_date` suffix) into the target language's native date/time type from the ISO8601 UTC string; treat `is_`-prefixed fields as booleans; treat `_link` objects as `{link, content-type?, size?}`.
- When surfacing `data_sources[]` or per-item `data_source` values (see `request-response-conventions.md`), preserve them as provenance metadata rather than discarding them — downstream consumers frequently need to know which backend system a merged field came from.
- **Netid (or other single-identifier) lookups should be case-insensitive, even though the API isn't.** `GET /api/{resource}/{netid}` does a case-sensitive identifier match, so a netid entered/stored in an unexpected case can 404 for a person who genuinely exists (observed via testing, not stated in the source docs). Any generated "look up by netid" call should: 1) try the direct path lookup with the value as given; 2) on 404, fall back to the collection filter form with a **trailing-only** wildcard, `GET /api/{resource}?netid=<value>*` (see `request-response-conventions.md` on why trailing-only `*` is a case-insensitive *exact* match, not a substring one) and take the single match if exactly one comes back; 3) once resolved, reuse that resolved/canonical netid for any further calls about the same person (employees/students/assets lookups, etc.) instead of re-using the originally-typed casing.

## 3. Pagination

Implement the loop described in `request-response-conventions.md`:
1. First request: original filter query string + `pagesize`.
2. Capture `X-Request-ID` → `continuation_key`, and `X-Total-Count` → expected total, from the **first** response only.
3. Subsequent requests: `continuation_key` + incremented `page` + `pagesize` (drop the original filter parameters — they're implied by the continuation key).
4. Stop when a page returns zero records.
5. Sanity-check accumulated record count against `X-Total-Count`; surface a clear error if they don't match (this catches server-side found-set expiry — the found set is only cached 12 hours).
6. If the target language has an idiomatic lazy-iteration/generator/async-stream construct, prefer yielding pages (or individual records) through it over building one big in-memory list — especially for People, which can return 100,000+ records unfiltered.

## 4. Error handling

- Any non-200 response body is `{"message": "...", ...}` (see `request-response-conventions.md`). Map this into the target project's existing error/exception convention rather than introducing a new one; include the original `message` text and the HTTP status in whatever error type you raise.
- Explicitly handle the three documented codes (401 invalid/missing auth, 404 not found, 422 invalid attributes on write) with distinct, catchable error types/cases where the target language supports that (e.g. custom exception subclasses, a tagged union/enum, or discriminated error codes) — callers frequently want to handle "not found" differently from "auth expired."
- Any other status code should be treated as unspecified/unexpected (see `known-gaps.md`) — don't build specific handling for a 429 or 5xx contract that isn't documented; a generic "unexpected API error" fallback that surfaces the status and body is appropriate.

## 5. Adapt, don't force

Before generating anything:
1. Look at the target repo's manifest (`package.json`, `pyproject.toml`/`requirements.txt`, `Gemfile`, `go.mod`, `*.csproj`, etc.) and existing source for: HTTP client already in use (fetch/axios/requests/httpx/Faraday/net/http/HttpClient/...), existing auth/middleware patterns, existing error-handling/exception conventions, and test framework.
2. Match those, rather than introducing a second HTTP client or a parallel error-handling scheme.
3. If the repo is empty/new and there's no existing convention to match, ask the user which language/framework/HTTP client to target rather than silently picking one.
4. Name things consistently with DartAPI's own vocabulary (`netid`, `scope`, `accepted_scopes`, `continuation_key`, resource names) so generated code reads naturally against the docs — don't invent different terminology for the same concepts.

## Before finalizing generated code

Cross-check the specific fields/endpoints/behaviors you generated against `known-gaps.md`. If the requested feature touches a gap (rate limiting, a write endpoint, webhooks, versioning, prod/pre-prod differences, `checkin_history`, an alumni-specific endpoint), say so explicitly in your response rather than quietly generating code that assumes an undocumented contract.
