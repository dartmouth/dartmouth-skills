---
type: Agent Instructions
title: AGENTS.md — repository guide
description: Rules for agents adding, editing, or reviewing skills in the dartmouth-skills repo.
tags: [agents, conventions, skills, okf]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-05T09:09:52-04:00 }
verified: Tivon Luker
stale_after: 2027-01-05T00:00:00Z
status: stable
sources:
  - id: agentskills-spec
    resource: https://agentskills.io/specification
    title: Agent Skills specification
  - id: okf-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
    title: Open Knowledge Format v0.2
---

# Rules (in priority order)

1. **One skill per directory:** `skills/<name>/SKILL.md`. `name` must equal `<name>`: lowercase letters, digits and hyphens, at most 64 characters.[^agentskills-spec]
2. **`description` tells agents when to use the skill.** Say what it does and when to use it, in one line under 1024 characters. It also serves as the OKF description.
3. **Every `.md` needs OKF frontmatter with a `type`.** The only exceptions are `index.md` and `log.md`.[^okf-spec] Use:
   - `Agent Skill` for `SKILL.md`
   - `Reference` for `references/*.md`
   - `Readme` / `Agent Instructions` for repo docs
4. **Provenance and trust fields:**
   - `generated.by` follows the actor convention: `<agent>/<model>` for agents, `human:<netid>` for people.
   - New or agent-edited content is `status: draft` with an empty `verified`.
   - Only a human review adds `verified: { by: human:<netid>, at: … }` and sets `status: stable`.
5. **Sources:**
   - Every `sources` entry has an `id` and a `resource`.
   - Cite key claims with footnotes keyed by that `id` (`[^rc-faq]`).
   - Set `last_modified` to the source page's own "last modified" date.
6. **Freshness:**
   - Set `stale_after` no more than 3 months out for content that names models or prices.
   - When a file is past `stale_after`, re-check its sources before trusting it.
7. **Keep the `SKILL.md` body lean (target under 300 lines, excluding frontmatter).** Move long configs and walkthroughs into `references/` and link to them by relative path.
8. **Public information only.** No internal infrastructure details, secrets, keys, or non-public vendor terms.
9. **Record every change.** Add an entry to `skills/log.md` (newest first, `## YYYY-MM-DD`). Update `skills/index.md` when adding a skill.

# Validate

```bash
python3 scripts/validate.py
```

[^agentskills-spec]: Agent Skills specification
[^okf-spec]: Open Knowledge Format v0.2
