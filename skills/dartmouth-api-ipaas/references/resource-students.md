---
type: Reference
title: "DartAPI Students API"
description: "Endpoints, fields, status history and academic data of the DartAPI Students API (Banner-sourced)."
tags: [dartmouth-api, students, sis, banner]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Students API

Returns information about every student represented in Banner — if a person has a Banner `SGBSTDN` record, they're in this API (see `systems-glossary.md`). Includes current status, complete academic history (including non-Dartmouth institutions), advisors, and full status/dplan/GPA history.

| Rating | Value |
|---|---|
| Cache refresh interval | Every 5 minutes |
| Filtering | Yes (see `request-response-conventions.md`) |

## Endpoint

```
GET /api/students/{netid}
```

## Required scopes

| Scope | Unlocks | Granted by |
|---|---|---|
| `urn:dartmouth:students:read.sensitive` | student information generally | Undergraduate Registrar's Office |
| `urn:dartmouth:students:read.highlysensitive` | GPA (`gpa_history`) | Undergraduate Registrar's Office |
| `urn:dartmouth:people:private` | FERPA-protected ("confidential") identities | Undergraduate Registrar's Office |

## Critical business logic: current vs. future term handling

Top-level attributes (`school_id`, `class_year`, `grad_term`, `student_type_id`, `student_status_id`) are computed relative to each school's own **current term** (controlled by that school's registrar). For students with **only a future status** (incoming class, exchange student, matriculating transfer), the top level reflects that **future** status instead: `is_future_status` is `true` and `term_code_eff` names the term the status takes effect. This guarantees every student — current or future — has a record.

**Any code deciding "is this student active right now" must check `is_future_status`**, not just assume top-level fields mean "today." For logic that spans terms (registration for a future term, Dplan selection, "will this student be enrolled next term"), use the full `status_history[]` array with term-based comparisons instead of the top-level snapshot — the `/api/academic/terms` endpoint's `current_term_offset` attribute helps locate relative terms (endpoint named in source docs; full shape not documented, see `known-gaps.md`).

## Top-level fields (selected)

`netid`, `cache_date`, `term_code_eff`, `is_future_status`, `school_id` (== deprecated `school_code`; values include `UG`, `TH`, `TU`, `DM`), `class_year`, `student_type_id` (lookup: `/api/school_types`), `admission_type_id` (lookup: `/api/admission_types`), `current_admit_term_code`, `grad_term`, `student_status_id` (lookup: `/api/student_statuses`), `is_fysep_participant`, `is_firstgen_student`, `varsity_sports` (array of `{id}`), `class` (`{code, name}` as of current term).

## Nested collections

- **`academic_history[]`** — full history including non-Dartmouth institutions (Dartmouth programs prefixed `"Dartmouth - ..."` in `institution.name`). Each entry: `institution {name, type, category}`, `start_date`, `completion_date`, `admit_term_code`, `degree {level, status, disciplines[]}` (disciplines have `name`, `type` [MAJOR/MINOR], `status`, and nested `concentrations[]`), `source {code, name}`.
- **`advisors[]`** — `{netid, term_code_effective, is_primary, type}` (e.g. `"Undergraduate Class Dean"`, `"Thayer Advisor"`, `"Faculty Advisor (first year)"`); some payloads also show `advisor_type_id`.
- **`other_attributes[]`** — special tags; **currently Thayer-only** (e.g. `EABE` "Thayer AB/BE Students", `ENDD` "Engineering Dual Degree"). Other schools' attributes are still in governance review — don't assume other schools' tags exist yet.
- **`status_history[]`** — full history of status changes: `term_code_eff, school_id, class_year, student_type_id, grad_term, student_status_id` (plus `class_code` in some payload variants).
- **`dplans[]`** — current/last/future Dplans only, **not historical** ones: `term_code, dplan_id, dplan_description, dplan_source_id, dplan_source_description, student_status_id`.
- **`gpa_history`** — `{cumulative_gpa: [...], term_gpa: [...]}`, each entry `{school_id, gpa_type_ind, gpa_value[, sis_term_code for term_gpa]}`. Backed by Banner `SHRLGPA`/`SHRTGPA` tables (see `systems-glossary.md`); requires `read.highlysensitive`.
- **`curriculum[]`** — `{college_id, degree_id, program, school_id, term_code, term_code_end[, program_name, priority]}`.
- **`checkin_history[]`** — ⚠ **undocumented in prose** (see `known-gaps.md`); observed shape from samples only: `{school_id, term_code, start_date, is_confirmed, confirmed_date}`.

## Response codes
200 / 404, same pattern as other resources.

## Examples

Three canonical shapes, anonymized, in `assets/examples/` (collapsed from the source material's six near-duplicate payloads — see build notes):
- `student-undergrad.json` — current UG student, one Dartmouth degree sought, no prior institutions.
- `student-grad-phd.json` — Thayer PhD student with a multi-institution academic history and long dplan/checkin history.
- `student-dual-degree.json` — Thayer dual-degree (BE) student with a transfer-institution history and `is_future_status` context.

## Gaps specific to this resource
`checkin_history` field is real (appears in every sample) but undocumented in prose. `original_job_start_date`-style "still under construction" caveats don't apply here, but see `known-gaps.md` for the cross-cutting gaps (no write examples, unclear versioning, etc).
