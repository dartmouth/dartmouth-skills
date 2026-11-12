---
type: Reference
title: "DartAPI known documentation gaps"
description: "What the DartAPI documentation does not cover (rate limits, writes, webhooks, SDKs, versioning, error codes); read before answering adjacent questions."
tags: [dartmouth-api, gaps, limitations]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Known gaps — read before answering anything adjacent to these topics

This is the single source of truth for what Dartmouth's DartAPI documentation does **not** cover. Every other reference file in this skill links back here instead of restating these points. When a task touches any item below, say so explicitly and suggest the developer confirm with the DartAPI team — do not invent a plausible-sounding number, payload shape, or endpoint to fill the gap.

- **No documented rate limits.** Nothing in the source docs specifies a requests-per-second/minute/day quota, throttling behavior, or how a throttled request is signaled. Don't state a specific number.
- **No write examples for any resource.** The intro doc describes generic POST (create) / PUT (update) / DELETE semantics, and a `urn:dartmouth:general_ledger:write.transaction` scope is named in the auth doc, but no resource doc shows an actual write request, request body, or response for any endpoint (employees, students, people, assets, or GL). Every documented example across all resources is a GET. Do not fabricate a write payload shape.
- **No webhook/push notifications.** `references/resource-people.md` mentions a polling-based "Resource Changes" subscription mechanism, but the actual subscription endpoint, request format, and response/payload shape are never documented. A "future enhancement may support webhook notifications" per the source doc — webhooks do not exist today.
- **No SDK or client library.** There is no official JS/Python/Ruby/etc. client, and no OpenAPI/Swagger or Postman collection exists in the source material. All code must be hand-written against the documented conventions in `references/code-generation-patterns.md`.
- **No consolidated error-code reference beyond 401 / 404 / 422.** These three are the only client error codes documented anywhere, each returning `{"message": "..."}`. No 50x error contract is documented.
- **Versioning scheme is unclear.** The introduction doc's client-error example shows a URL containing `/api/v2/...`, but this appears to be unedited boilerplate copied from generic Rails-API-docs examples (Every other real example in every other doc uses unversioned `/api/...` paths, e.g. `/api/employees/{netid}`). Don't treat `/api/v2/` as a real, callable path — the real base paths are `/api/` (prod) and the pre-prod equivalent, with no version segment.
- **No documented prod vs. pre-prod differences in scopes or data.** Pre-prod (`api-preprod.dartmouth.edu`) is mentioned only as a testing environment; nothing states whether it has separate API keys, separate scope grants, or synthetic vs. real data.
- **`checkin_history` is undocumented in prose.** It appears as a populated field in every students-API sample payload but has no entry in `600_students.md`'s field-description tables. Its shape (from samples): an array of `{school_id, term_code, start_date, is_confirmed, confirmed_date}` objects — treat this as observed-from-samples only, not as a documented contract, and flag it as such if asked.
- **There is no alumni-specific endpoint.** Per `400_people.md`: "Alumni affiliated records are also coming from IDM [via the People API]. Future enhancements will return data directly from the Advancement system." One of the original source sample files was named "alumni-example" but its request actually hits `/api/students`, not any alumni-specific resource — it was mislabeled and is not evidence of a real alumni endpoint. If asked for an alumni API, say it doesn't exist yet; alumni data today comes through `GET /api/people/{netid}` for identities with `dartmouth_affiliation: "ALUMNI"`.
- **The assets scope-grant workflow is undocumented.** `references/resource-assets.md` notes the source doc has an unfilled placeholder for how the `urn:dartmouth:assets:people_photo:read` scope is actually granted, and the referenced "agreements API" (for the confidential-photo labeling/acknowledgement requirement) is named but never documented itself.
- **No lookup-endpoint catalog.** Docs repeatedly *reference* lookup endpoints in passing (e.g. `/api/telephone_types`, `/api/address_types`, `/api/citizenship_types`, `/api/genders`, `/api/schools`, `/api/school_types`, `/api/admission_types`, `/api/student_statuses`, `/api/academic/terms`, `/api/human_resources/organizations`) but there is no master index of all available resources. Treat any such reference as "this lookup endpoint is named in passing, its full shape is not documented here" rather than assuming completeness.
- **No token-refresh endpoint.** There is no separate "refresh" call — a new JWT is obtained by calling `POST /api/jwt` again with the API key. Don't invent a refresh-token flow.
