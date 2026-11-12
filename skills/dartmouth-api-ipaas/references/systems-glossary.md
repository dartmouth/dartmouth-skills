---
type: Reference
title: "DartAPI backend systems glossary"
description: "Lookup of the backend systems behind DartAPI (HRS, SIS/Banner, IDM, ADV, Lenel, CSGOLD) and what each feeds."
tags: [dartmouth-api, systems, glossary]
status: draft
sources:
  - id: dartapi-portal
    resource: https://developer.dartmouth.edu
    title: Dartmouth Developer Portal (API keys and DartAPI documentation)
---

# Backend systems glossary

DartAPI is an aggregation layer over several backend systems. Resource docs reference these by name/`data_source` code — use this as the shared lookup.

| Code / name | System | What it feeds | Notes |
|---|---|---|---|
| `hrs` — **HRS** | HR system | Employees API primary source; org hierarchy, jobs, faculty rank/tenure, addresses/phones tagged `hrs` in the People API | |
| `sis` — **SIS / Banner** | Student Information System (Banner) | Students API primary source; addresses/phones tagged `sis` in the People API | PL/SQL/table references appear in the Students docs: `SGBSTDN` (student record existence — if a person has one, they're in the Students API), `SHRLGPA` (cumulative GPA), `SHRTGPA` (term GPA), `SPBPERS` (citizenship code `spbpers_citz_code`), function `DARTBAN.DF_U_F_UG_GPA(pidm)` computes undergrad GPA |
| `idm` — **IDM** | Identity Management | People API primary source for identities with no HR/SIS affiliation (sponsored accounts, service accounts, guest accounts); also the source for Alumni records today (see `known-gaps.md`) | IDM-sourced phone numbers get a synthetic `IDMCP` ("IDM Campus Phone") telephone type since IDM has no real telephone-type code |
| `adv` — **ADV / Advancement** | Advancement system | Partial contribution today — some addresses/phones tagged `adv` in the People API | A full, dedicated Alumni API sourced directly from Advancement is a stated **future** enhancement, not built yet |
| **Lenel** | Physical access / photo-ID system | `prox_id`, `dartcard_id` on People records; binary/metadata behind the Assets (photo) API | |
| **CSGOLD** | Campus dining system | Downstream consumer only — takes `dartcard_id` as its PIK number | Not itself part of DartAPI |

When a resource attribute is described as coming from one of these systems, or a merged collection's per-item `data_source` value matches one of the codes above, point back here rather than re-explaining the system in each resource file.
