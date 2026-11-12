---
type: Reference
title: "DartAPI request/response conventions"
description: "Shared filtering, wildcard, pagination, and response data-type and naming conventions across DartAPI resources."
tags: [dartmouth-api, filtering, pagination, conventions]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Request/response conventions shared across resource APIs

These conventions apply to `employees`, `people`, and `students` (and any future filterable resource) — read this once, not per-resource.

## Filtering (query parameters)

| Operator | Meaning | Wildcard? | Example | Notes |
|---|---|---|---|---|
| `=` | equal | yes (`*`) | `?last_name=Smith` | exact match is case-sensitive; `*` makes matching case-insensitive, e.g. `?name=*smith` |
| `=!` | not equal | no | `?last_name=!Smith` | |
| `=\|` | equal-OR-list | yes | `?affiliations.name=\|Staff,Faculty` | matches any value in the list |
| `=^` | equal-AND-list | yes | `?affiliations.name=^Staff,Student` | record must match **all** values (only meaningful against array attributes) |
| `=>` | greater than | no | `?last_name=>Smith` | |
| `=<` | less than | no | `?last_name=<Smith` | |

- Nested attributes use dot notation: `telephone_numbers.data_source=sis`, `affiliations.name=Staff`.
- Multiple different query parameters are ANDed together.
- Null querying: `?middle_name=null` / `?middle_name=!null`. This means searching for the literal string `"null"` without a wildcard will fail — use `?field=null*` if you need to match a value that merely contains "null".
- Empty-array querying: `?dplans=[]` / `?dplans=![]` — no values may be placed inside the brackets. Use `=|`/`=^` to test for presence of specific values in an array attribute.

**Wildcard position controls substring-vs-exact, independently of the case-insensitivity it also turns on (observed via testing — not spelled out in the source docs, so treat the exact-match claim below as empirical, not contractual):**
- `*` on **both** sides (or a bare leading `*`), e.g. `?name=*smith*` / `?name=*smith` — case-insensitive **substring** match.
- `*` on the **trailing side only**, e.g. `?netid=D12345A*` — case-insensitive but still an **exact-length match** against the given value (the `*` only matches zero-or-more characters *after* the given value, and there's nothing after a complete value) — i.e. this is the pattern to reach for when you have a full, known value (a netid, an exact code) and just don't know its stored casing, as opposed to a genuine partial/substring search.
- This matters concretely for netid lookups: `GET /api/{resource}/{netid}` (the path-parameter form) appears to do a case-sensitive identifier match, so a netid typed/stored in the "wrong" case can 404 there even though the person exists. Falling back to the collection filter form with a trailing-only wildcard (`GET /api/people?netid=<value>*`) and taking the single match works around this — see `code-generation-patterns.md` for how a generated client should structure that fallback.

**Important quirk to defend against in generated code:** *the API does not validate that a queried attribute is spellable or authorized under the current scope — an unknown or unauthorized filter attribute is silently discarded, not rejected.* A typo'd field name or a filter on an attribute your JWT's scope doesn't expose returns results **as if that filter term were never supplied**, with no error. Generated query-building code should not assume "no error thrown" means "the filter took effect" — where correctness matters, validate filter field names against the documented schema for that resource before sending the request, since the API won't catch the mistake for you.

## Pagination

- `page` (1-based, default 1) and `pagesize` (default 1000, hard max 1000).
- First filter request returns:
  - `X-Request-ID` header → reuse as the `continuation_key` query parameter on subsequent page requests to stay pinned to the same found-set (server-side cache, 12 hours).
  - `X-Total-Count` header → total records matching the filter, across all pages.
  - `X-Next-Page` header (when present) → a ready-to-use full URL for the next page; simplifies paging loops when available, but don't assume it's always present.
- After page 1, pass `continuation_key` (not the original filter query) plus incremented `page`.
- An empty array response (`X-Total-Count: 0`, or paging past the end) is normal, not an error.

Canonical paging loop (language-neutral — see `code-generation-patterns.md` for the idiomatic translation):
```
page = 1
continuation_key = null
results = []
loop:
  if page == 1: request with the original filter querystring + pagesize
  else:         request with continuation_key + pagesize + page
  on first response: capture continuation_key from X-Request-ID, total_count from X-Total-Count
  append page's records to results
  if page's record count == 0: stop
  page += 1
assert len(results) == total_count   # sanity check
```

## JSON data-type and naming conventions

- **snake_case** for all attribute names, with one exception: the hypermedia `content-type` attribute keeps its hyphen.
- **Dates**: any attribute ending in `_date` is an ISO 8601 UTC string, `YYYY-MM-DDTHH:MM:SSZ` (the `Z` denotes UTC).
- **Booleans**: any attribute prefixed `is_` is a boolean.
- **Hypermedia objects**: any attribute ending in `_link` is `{ "link": "<url>", "content-type": "<mime>", "size": <bytes|null> }` (content-type and size optional).
- **`data_sources[]`**: resources that aggregate data from multiple backend systems include a top-level `data_sources` array of `{name, link, cache_date, update_date}` describing each contributing source. Distinct from the **per-item** `data_source` attribute seen on merged collections like `addresses`/`telephone_numbers` (see `resource-people.md`), which tags which system a specific array entry came from — don't confuse the two.
- **Null/empty conventions**: every documented attribute is always present in a GET response, even when empty — a resource never silently omits a documented field. Strings/numbers/objects use `null` for absent; arrays use `[]` (never `null` for an empty array).
- Full JSON payloads are minified in practice; docs show pretty-printed examples for readability only.

## Errors

Any non-200 response returns a single JSON object with (at minimum) a `message` field:
```json
{ "message": "Couldn't find Employee with netid = zz99999" }
```
Documented codes: **401** (missing/invalid API key or JWT), **404** (resource/id not found), **422** (invalid attributes on a write — though no write example is actually documented anywhere, see `known-gaps.md`). Treat any other status code your generated error-handling encounters as unspecified behavior, not as a documented contract (see `known-gaps.md` on 50x/rate-limit responses).

## Change notifications

A polling-based "Resource Changes" mechanism exists for tracking changes to People/Employees/Students without full reloads. The concrete endpoint/payload shape is not documented in the source material — treat this as a named-but-undetailed feature (see `known-gaps.md`) rather than inventing a subscription API shape.
