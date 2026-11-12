---
name: dartmouth-api-ipaas
description: Build integrations with, and look up data in, Dartmouth's enterprise iPaaS API (DartAPI, api.dartmouth.edu). Use when scaffolding client code in any language (JWT via POST /api/jwt, urn:dartmouth scopes, token caching, continuation_key pagination, filters, 401/404/422 handling), when looking up employees, students, people or assets endpoint schemas and controlled-vocabulary codes, or when asking which backend system (HRS, SIS/Banner, IDM, Advancement, Lenel, CSGOLD) owns a field. Also match "the Dartmouth API", "api-preprod", or "urn:dartmouth:...".
type: Agent Skill
title: Dartmouth iPaaS API (DartAPI) — integration and reference guide
tags: [dartmouth-api, dartapi, ipaas, jwt, employees, students, people, assets, integration]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Dartmouth iPaaS API (DartAPI)

DartAPI is Dartmouth College's internal enterprise API, aggregating identity, HR, and student-records systems behind one HTTPS/JSON interface.

- **Prod base URL:** `https://api.dartmouth.edu/api/`
- **Pre-prod base URL:** `https://api-preprod.dartmouth.edu/api` (no documented difference in scopes/data from prod — see `references/known-gaps.md`)
- **Generic error shape:** any non-200 response is `{"message": "..."}` — see `references/request-response-conventions.md` for the documented codes.
- This skill serves two purposes: **(a) generating integration code** (the primary use case — JWT auth, request wrappers, pagination, error handling, adapted to whatever language the target project uses) and **(b) reference lookup** (endpoint schemas, fields, controlled-vocabulary codes).

## Routing — load only what the task needs

| Task touches... | Load |
|---|---|
| Getting/caching/refreshing a JWT, scopes, authorization tiers | `references/auth-jwt.md` |
| Building filter queries, paging through results, response data-type/naming conventions | `references/request-response-conventions.md` |
| Assets (photos) endpoint/fields | `references/resource-assets.md` |
| Employees endpoint/fields | `references/resource-employees.md` |
| People endpoint/fields | `references/resource-people.md` |
| Students endpoint/fields | `references/resource-students.md` |
| Which backend system (HRS/SIS/IDM/ADV/Lenel/CSGOLD) owns a field | `references/systems-glossary.md` |
| Generating client/integration code in any language | `references/code-generation-patterns.md` |
| **Anything adjacent to a documented gap (see below)** | `references/known-gaps.md` — **load this first**, before answering |

Sample payloads (already anonymized) live under `assets/examples/` and are referenced from each `resource-*.md` file.

## Code-generation workflow

1. Identify the needed resource(s); read the matching `references/resource-*.md`.
2. Identify required scope(s) (`urn:dartmouth:{resource}:{level}`); read `references/auth-jwt.md` — note the three-tier, **non-inheriting** model and the rule that ungranted scopes are silently dropped from `accepted_scopes`, not errored.
3. Detect the target project's language/framework/HTTP-client/error-handling conventions from its manifest (`package.json`, `requirements.txt`/`pyproject.toml`, `Gemfile`, `go.mod`, `*.csproj`, ...) and existing code. If genuinely ambiguous (e.g. an empty repo), ask the user — never silently force one language.
4. Generate JWT acquisition + caching (cached by scope-set, `exp`-checked with a safety margin, refetched via `/api/jwt` — there's no separate refresh endpoint) per `references/code-generation-patterns.md`, translated idiomatically.
5. Generate the scope-aware resource client: request building (filters, `continuation_key` pagination looping) and response parsing (snake_case, `_date`, `is_`, `_link`, `data_sources[]` provenance).
6. Generate error handling for 401/404/422 against the generic `{"message": ...}` shape.
7. Before finalizing, cross-check against `references/known-gaps.md` — if the task touches a gap, say so explicitly instead of inventing a plausible-sounding answer.

For plain schema/field lookups (no code needed), skip straight to the relevant `resource-*.md` and answer directly, citing the required scope.

## Don't invent — documented gaps (always keep this in mind, full detail in `references/known-gaps.md`)

- No documented rate limits.
- No POST/PUT/DELETE examples exist for **any** resource, despite the verbs being mentioned generically.
- No webhook docs — only an undetailed polling "Resource Changes" mechanism.
- No SDK/client library exists anywhere; no OpenAPI/Swagger/Postman spec.
- No error codes beyond 401/404/422 are documented.
- Versioning is unclear — a `/api/v2/...` example in the source docs looks like unedited generic boilerplate; the real, confirmed paths are unversioned (`/api/employees/{netid}`, etc.).
- No documented prod-vs-preprod scope/data differences.
- `checkin_history` appears in student sample payloads but is undocumented in prose.
- **There is no alumni-specific endpoint.** Alumni data comes through the People API via IDM today; a full Advancement-sourced Alumni API is a stated future enhancement, not built.

If a question or code-gen task touches any of the above, say so plainly and suggest confirming with the DartAPI team, rather than fabricating specifics.
