---
type: Reference
title: "DartAPI People API"
description: "Endpoints and fields of the DartAPI People API: directory data merged from HRS, SIS, IDM and Advancement."
tags: [dartmouth-api, people, idm]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# People API

High-level directory information (name, email, affiliation, contact info) about identities at Dartmouth. Data is sourced from whichever backend system "owns" the identity: HRS for employees, SIS for students, IDM for identities with no HR/SIS affiliation (sponsored/service/guest accounts), and today, Alumni too (via IDM — see `known-gaps.md`, there is no dedicated Alumni endpoint).

| Rating | Value |
|---|---|
| Cache refresh interval | Every 5 minutes |
| Filtering | Yes (see `request-response-conventions.md`) |

## Endpoint

```
GET /api/people/{netid}
```

## Required scopes (independent, non-inheriting tiers — see `auth-jwt.md`)

| Scope | Unlocks | Granted by |
|---|---|---|
| _(none)_ | minimal directory fields: `netid`, `name`, `first_name`, `last_name`, `middle_name`, `email`, `prefix`, `suffix`, `has_name_recording`, `cache_date`, `campus_address` | n/a |
| `urn:dartmouth:people:private` | adds `is_confidential` on top of the no-scope payload | Undergraduate Registrar's Office |
| `urn:dartmouth:people:read.sensitive` | adds legal name fields, `nickname`, `spouse`, `telephone_numbers`, `addresses`, `personal_email`, `primary_affiliation`, `dartmouth_affiliation`, `affiliations`, `gender_id`, `account_status`, `is_identity_claimed`, `is_confidential`, `is_phi_user`, `barcode`, `chosen_gender`, `chosen_pronoun`, citizenship fields, `dartcard_id`, `is_usa_citizen`, `religion_id`, `sis_person_id`, `created_date`, `expires_date` | data stewards of underlying sources; multiple approvals |
| `urn:dartmouth:people:read.highlysensitive` | adds `birth_date`, `legal_sex_id`, `is_veteran`, `ethnicity` | data stewards; multiple approvals |

Remember tiers don't stack automatically — request every scope whose fields you need.

## Multi-source merged collections

`telephone_numbers[]` and `addresses[]` merge records from multiple backend systems; each entry carries a `data_source` value (`idm`, `hrs`, `sis`, `adv` — see `systems-glossary.md`). Type codes (`telephone_type_id`, `address_type_id`) are namespaced per source to guarantee uniqueness: `sis`-sourced types are raw Banner codes; `hrs`-sourced telephone types are prefixed `HRS`, `hrs`-sourced address types prefixed `HR`; `idm` phone numbers get a synthetic type `IDMCP` (no real HR/SIS type exists for them). Look up human-readable descriptions via `/api/telephone_types` / `/api/address_types` (existence confirmed in docs; full shape not documented — see `known-gaps.md`).

## Citizenship derivation (complex, school-specific — summarize, don't hand-roll from scratch)

Four fields: `citizenship_type_id` (maps to `spbpers_citz_code`, look up via `/api/citizenship_types`), `is_usa_citizen`, `citizenship_country_id`, `citizenship_country2_id`. **Tuck** uses different derivation logic than all other schools (different `spbpers_citz_code` value sets and different fallbacks through `saracmt_comment_text`/`stvnatn_code` for country). If a consuming app needs to reproduce this logic client-side rather than just reading the returned fields, treat it as genuinely complex school-specific business logic — surface that complexity to the developer rather than approximating it.

## Gender / pronoun model (students only)

- `chosen_pronoun`: `{id, other_value}` — `other_value` is only meaningful when `id == "O"`; it can persist as stale data after the person switches to a different `id`.
- `chosen_gender`: `{id}` — valid ids come from `/api/genders`.
- `gender_id` mirrors `chosen_gender.id`, defaulting to `"MN"` for `legal_sex_id == "M"` and `"W"` for `legal_sex_id == "F"`.
- `legal_sex_id`: `"F"` or `"M"`.

## `dartmouth_affiliation` values

| Code | Meaning |
|---|---|
| ALUMNI | Alumni account |
| DART | Student, Faculty, Staff, or ExEmployee |
| DEPT | Departmental account |
| E-FAC | Emeritus faculty/staff — kept active regardless of HR status |
| ORG | Student organization |
| P-ADM | "private" senior-administration accounts |
| SERVICE | Service account (auth, mail, etc.) |
| SPON | Sponsored account |
| SPONLIM | Limited-access sponsored/guest/social-media account |
| TRUSTEE | Board of Trustees member (not an employee) |

Deprecated/obsolete (should only appear on Disabled accounts): `DHMC`, `GROUP`, `SEMINAR`, `S-FAC`.

## Resource Changes

A polling-based change-notification mechanism exists for People/Employees/Students — see `known-gaps.md`; the concrete endpoint isn't documented, and webhooks don't exist yet.

## Response codes
200 / 404, same pattern as other resources.

## Example

`assets/examples/people-merged-address.json` — one anonymized example under the `read.sensitive` scope showing the `adv`+`hrs` address/phone merge with `data_source` tags.
