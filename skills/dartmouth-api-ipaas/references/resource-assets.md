---
type: Reference
title: "DartAPI Assets API"
description: "Endpoints and fields of the DartAPI Assets API (identification photos sourced from Lenel)."
tags: [dartmouth-api, assets, photos]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Assets API

Returns metadata and binary content for digital assets. Currently the only asset type available is identification photo images of people (sourced from Lenel — see `systems-glossary.md`).

## Endpoints

```
GET /api/assets/{id}         → asset metadata (JSON)
GET /api/assets/{id}/asset   → the binary asset itself
```

`{id}` is the person's netid for identification photos.

## Required scope

`urn:dartmouth:assets:people_photo:read` — required to view photo images/metadata at all.

**Gap:** the source documentation has an unfilled placeholder for exactly how this scope is granted, and it references an "agreements API" for the confidential-photo labeling/acknowledgement workflow (see below) that is itself never documented. Don't invent either — flag both as unknown if asked (see `known-gaps.md`).

## Privacy/compliance obligation (must be surfaced in any generated code that displays photos)

The scope allows access to photos of "confidential"-flagged people. Any application displaying such a photo must, per Dartmouth policy:
- Label the photo with a standard icon/HTML markup (to be provided by the unspecified "agreements API")
- Require the application's users to view and acknowledge the confidentiality policy/guidelines before viewing (acknowledgement status also tracked via that same undocumented agreements API)

When scaffolding a photo-display feature, call this obligation out explicitly rather than silently skipping it — it's a compliance requirement, not an optional nicety, even though the enforcement mechanism isn't documented here.

## Response codes

| Code | Meaning |
|---|---|
| 200 | valid asset id |
| 404 | invalid/nonexistent asset id |

## Sample metadata response (anonymized)

```json
{
  "id": "d00000a",
  "content_type": "image/jpeg",
  "size": null,
  "timestamp": null,
  "creator": "<photos svc acct>",
  "type": "people_photo",
  "metadata": {
    "type": "identification",
    "netid": "d00000a"
  },
  "link": "https://api.dartmouth.edu/api/assets/d00000a/asset",
  "is_public": false
}
```

The binary endpoint (`/asset`) returns the raw image bytes with a `content-type` of e.g. `image/jpeg` — not JSON.

See `assets/examples/jwt-response.json` and the other resource files for the auth flow that precedes this call; assets requests use the same `Authorization: Bearer {jwt}` pattern as every other resource.
