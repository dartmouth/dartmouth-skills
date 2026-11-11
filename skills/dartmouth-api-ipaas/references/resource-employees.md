# Employees API

Returns information about current/future active employees. **Does not** provide historical position data — only current-as-of-today jobs. Termination data (`last_date_employed`) is only populated for ExEmployees within their 18-month post-termination window.

| Rating | Value |
|---|---|
| Cache refresh interval | Hourly |
| Filtering | Yes (see `request-response-conventions.md`) |

## Endpoint

```
GET /api/employees/{netid}
```

## Required scope

`urn:dartmouth:employees:read.sensitive` — granted by the HR Office. This one scope covers the whole payload; there is no separate sensitive/highly-sensitive split for this resource (unlike People/Students).

## Top-level fields (selected)

| Field | Type | Description |
|---|---|---|
| `netid` | string | employee's netid |
| `cache_date` | date | last cache update, ISO8601 |
| `home_department` | string | deprecated — prefer `jobs[].is_home_department` |
| `person_type` | array\<string\> | `Employee`, `ExEmployee`, or `Non-Paid` (see below) |
| `primary_payroll` | string | `Monthly` / `Biweekly Staff` / `Non-Paid` — payroll of the job with the highest FTE |
| `i9_date` | date\|null | I-9 expiration; null if non-expiring |
| `i9_status` | string | see table below |
| `postdoc` | boolean | is a postdoc |
| `is_benefits_eligible` | boolean | | 
| `is_med_enrolled` | boolean | enrolled in Dartmouth's group health plan |
| `jobs` | array | see Jobs structure below |
| `faculty_data` | array\|null | present only for faculty appointments — rank/tenure per organization |
| `emeritus_data` | object\|null | present only for emeriti |
| `schedule_data` | object\|null | work schedule, when applicable |
| `last_date_employed` | date\|null | populated for ExEmployees |
| `last_date_paid` | date\|null | last date paid within the last 18 months; null for Non-Paid |

### `person_type` values
| Value | Meaning |
|---|---|
| `Employee` | active, currently paid |
| `ExEmployee` | terminated, Inactive for 18 months post-termination (supports online W-2 access) |
| `Non-Paid` | e.g. non-paid faculty appointments |

### `i9_status` values
`Waived`, `Expired`, `Non-Paid`, `Non-US Location`, `Not Entered`, `Pending (HR USE ONLY)`, `No`, `Yes`, and the documented-invalid value `Faculty Not Here Yet`.

### Jobs structure (each element of `jobs[]`)
`assignment_number`, `location {description, building_id, space_id}`, `is_home_department`, `job_base_status` (`Regular`/`Temporary`/`Non-Paid`), `job_current_status` (`Active`/`Inactive`), `job_end_date`, `job_group` (`Faculty` or `Staff` — see mapping below), `job_start_date`, `job_type`, `job_organization {academic_division, department, division, id, organization, organization_namespace, sub_division_or_school, subunit, unit}`, `original_job_start_date` (⚠ "still under construction" per source docs — don't treat as fully reliable), `payroll_type`, `position_title`, `position_number`, `supervisor_netid`, `maintenance_crew {crew_code, crew_shift, shop_lead}`.

`job_group` mapping: **Faculty** = job_type ∈ {Faculty, Fellow, Non-Paid, Research Associate A/B/C}. **Staff** = job_type ∈ {Exempt Staff, IATSE, Non-Exempt Staff, Non-Union Service, SEIU, DCLWU Non-Exempt/Exempt Staff}.

### Faculty Data structure (each element of `faculty_data[]`)
`as_of_indicator` (`"Today"` or `"Future - yyyy-mm-dd"`), `organization {...}`, `faculty_rank_code`, `faculty_rank_description`, `faculty_rank_rank_date`, `faculty_rank_status`, `tenure_code`, `tenure_description`, `tenure_tenure_date`, `tenure_asst_prof_start_term`.

**faculty_rank_code** is a large lookup table (selected common values — not exhaustive, query `/api/...` faculty rank lookup if one exists, see `known-gaps.md` on the missing lookup-endpoint catalog): `10`=Professor, `20`=Associate Professor, `30`=Assistant Professor, `40`=Instructor, `60`=Research Associate, `70`=Senior Lecturer, `71`=Lecturer, `90`=Research Fellow. (Full table has ~50 codes covering clinical/visiting/adjunct/research variants — ask if you need the complete list, don't guess intermediate codes.)

**faculty_rank_status**: `A`=Acting Chair, `C`=Chair, `D`=Director, `E`=Emeritus/a, `H`=Honorary, `I`=Interim Chair, `ID`=Interim Director, `V`=Vice Chair.

**tenure_status**: `NT`=Non-Tenured, `NT DMSC`/`NT DMSO`/`NT DMSR`=Non-Tenured DMS Clinical/Other/Research Faculty, `T`=Tenured, `TT`=Tenure Track.

### Emeritus Data structure
`salutation`, `year_of_appointment`, `emeritus_title`, `email_after_termination`, `status_grant_year`, `status_grant_month`, `emeritus_organization {...}`.

### Schedule Data structure
`work_schedule {start_time, end_time}`, `scheduled_daysoff` (array, e.g. `["SUN","SAT"]`).

## Response codes
200 (valid netid) / 404 (not found).

## Examples

Three canonical shapes, anonymized, in `assets/examples/`:
- `employee-staff.json` — ordinary active staff member, one job.
- `employee-faculty.json` — active faculty with tenure and multiple org appointments.
- `employee-exemployee-emeritus.json` — ExEmployee with emeritus_data populated, no active jobs.

## Gaps specific to this resource
No historical job data is available — only current jobs. `original_job_start_date` is explicitly noted in the source docs as not yet reliably computed. See `known-gaps.md` for cross-cutting gaps (no write examples, no rate limits, etc).
