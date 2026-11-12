---
type: Reference
title: "DartAPI authentication — login service and JWT"
description: "Obtain, cache and refresh DartAPI JWTs: API keys, scopes, the three-tier non-inheriting authorization model, and accepted_scopes behavior."
tags: [dartmouth-api, jwt, auth, scopes]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Authentication: the DartAPI Login Service (JWT)

Every call to DartAPI (other than the login call itself) requires a short-lived JWT in an `Authorization: Bearer {jwt}` header. The JWT is obtained by exchanging a long-lived API key for it.

## Getting an API key (one-time, human process)

Not something to automate in code — a developer requests a Dartmouth Service Account through the Help Desk, then generates a key at `developer.dartmouth.edu` under "Manage Keys." Keys should be scoped to a use case (so retiring an app means deleting its key without affecting others) and stored in a secrets manager, never committed to source. This is out of scope for generated code beyond reading the key from an environment variable / secrets store.

## Exchanging the API key for a JWT

```
POST /api/jwt
Authorization: {api_key}
```

Optional query parameter `scope` — a **space-separated** list of scope strings, each shaped `urn:dartmouth:{resource}:{level}`, e.g.:

```
POST /api/jwt?scope=urn:dartmouth:employees:read.sensitive urn:dartmouth:people:read.sensitive
```

Space characters may need explicit URL-encoding depending on the HTTP client/language — some libraries handle this automatically, others don't.

**There is no default "give me everything" call.** If `scope` is omitted, you get an `Authenticated`-level JWT only. Request only the scopes you actually need — service accounts can hold 10s–100s of granted scopes and a smaller JWT is cheaper to pass/decode on every call.

### Response

```json
{
  "jwt": "<encoded JWT>",
  "payload": {
    "sub": "<netid of the identity behind the service account>",
    "iss": "https://api.dartmouth.edu/api/jwt",
    "aud": "https://api.dartmouth.edu",
    "name": "<service account display name>",
    "email": "<service account email>",
    "exp": 1774241483,
    "iat": 1774230683,
    "scope": "urn:dartmouth:people:private urn:dartmouth:students:read.sensitive"
  },
  "accepted_scopes": [
    "urn:dartmouth:people:private",
    "urn:dartmouth:students:read.sensitive"
  ]
}
```

`exp`/`iat` are Unix epoch seconds.

### The rule every client MUST follow: check `accepted_scopes`

**A scope you request but haven't been granted is silently dropped, not errored.** The JWT call still returns 200 even if zero of your requested scopes were accepted. Any generated client must diff the requested scope list against `accepted_scopes` in the response and fail loudly (raise/throw, not just log) if a scope the calling code depends on wasn't accepted — otherwise the code will silently receive smaller payloads than expected from downstream resource calls, which is a hard-to-diagnose bug class.

```python
# pattern, not a literal snippet to paste — adapt per code-generation-patterns.md
requested = set(scopes.split(" "))
accepted = set(response_json["accepted_scopes"])
missing = requested - accepted
if missing:
    raise Exception(f"Scopes not granted to this service account: {missing}")
```

## Using the JWT

Every subsequent call:

```
Authorization: Bearer {jwt}
```

There is no separate refresh-token endpoint (see `known-gaps.md`) — when the JWT is near/past `exp`, call `POST /api/jwt` again with the API key to get a new one.

## Authorization model

Three independent, **non-inheriting** tiers, per resource, for both read and write:

| Tier | Scope suffix | Notes |
|---|---|---|
| Authenticated | (none needed beyond a valid JWT) | baseline, public/directory-level data only |
| Sensitive | `read.sensitive` (or `write.*`) | additional attributes, typically requires an approval from the data steward/office that owns the resource |
| Highly Sensitive | `read.highlysensitive` | most restricted attributes (e.g. GPA, ethnicity, legal sex) |

"Non-inheriting" means holding `read.highlysensitive` does **not** also grant you the `read.sensitive` attributes — request every tier you need explicitly.

There's also a separate FERPA-related scope, `urn:dartmouth:people:private`, required to view "confidential"-flagged identities at all (independent of the sensitivity tiers above), and named special-purpose roles that don't fit the resource:level:tier pattern, e.g.:
- **Private User Viewers** — access to confidential identities
- **General Ledger Transaction Creators** — allowed to post GL transactions (`urn:dartmouth:general_ledger:write.transaction`) — no documented write example exists, see `known-gaps.md`
- **View Photo Users** — access to Lenel-sourced ID photos

Each resource doc (`resource-*.md`) documents exactly which scope(s) it needs and what each tier unlocks.
