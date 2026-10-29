---
type: Reference
title: AGENTS.md template — LLM vs decision model guidance
description: Drop-in AGENTS.md rules for projects that combine LLMs with Clef and Jev decision models.
tags: [decision-models, clef, jev, dartmouth-chat, litellm, vllm, system-one, agents-md, llm, routing, classification]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-29T15:52:00-04:00 }
stale_after: 2027-01-29T00:00:00Z
status: draft
sources:
  - id: litellm-pr-44236
    resource: https://github.com/BerriAI/litellm/pull/44236
    title: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
    last_modified: 2026-10-03T00:00:00Z
  - id: vllm-decisions-doc
    resource: https://raw.githubusercontent.com/vllm-project/vllm/main/docs/models/structured_decisions_models.md
    title: vLLM — Structured Decisions Models (/v1/systemone)
  - id: typesafe-skill
    resource: https://github.com/typesafe-ai/skills
    title: TypeSafe AI skill (MIT-licensed source adaptation)
---

# AGENTS.md template: LLM or decision model?

Copy or adapt the sections below into a project's `AGENTS.md` when the codebase uses both LLMs and decision models (Clef / Jev).[^litellm-pr-44236][^vllm-decisions-doc][^typesafe-skill]

## LLM or decision model?

This project uses two kinds of model. Pick by what the output IS, not by how
hard the task feels.

**Decision model (Clef / Jev):** the answer is one of a set of outcomes you can list
in advance.[^vllm-decisions-doc]

- Classify, route, triage, tag, moderate, pick a handler or tool.
- Yes/no checks (`noul`): "does this ask for a refund?", "does this screenshot show a key?"
- Rate on a described scale (`score`): severity, relevance, frustration, quality.
- Pick one value from candidates your code already found (`choice` — selection, not generation).
- Rerank retrieved items, verify a claim against evidence, decide whether to escalate.
- Hot paths, high volume, or anything where code branches on the result.

**LLM:** the answer must be written, or the options can't be listed.

- Generate text: replies, summaries, explanations, code, translations.
- Multi-step reasoning, math-heavy or knowledge-heavy questions, planning.
- Open-ended extraction where candidates can't be found in code first.
- Handling low-confidence cases a decision model escalates.

**Plain code:** anything a rule, regex, lookup, count or date comparison decides
exactly. Never send arithmetic or dates to either model.

Tie-breakers: if you're about to prompt an LLM for JSON with an enum field, or
parse "yes"/"no" out of its text, use a decision model instead. If you'd need
more than 10 score levels or more than 26 choices, or the options depend on
reasoning you can't state, use an LLM.[^vllm-decisions-doc] Combining them is normal: decision model
gates or routes, LLM does the writing, code enforces policy.

## Using the `decide` MCP tool during your session

Don't call `decide` for single-item choices you already have in context (such as picking which file to read or which tool to run)—writing the tool call costs more tokens and time than deciding directly. Call `decide` / `decide_batch` when:

- **You have many items to judge or rerank (`decide_batch`):** triaging search hits, TODOs, issues, log lines, or candidate records against one rubric in a packed batch (not a loop).
- **You are designing or testing decision questions (`decide` / `decide_batch`):** verifying that questions you are writing for application code produce clean separation (not `noul ≈ 0.5` or low `label_mass`) on sample inputs before committing them.
- **You want an independent rubric or blast-radius check (`decide`):** scoring a diff, migration, or log against a fixed safety checklist (`warnings` mean rewrite the question or ask the user, never act irreversibly).

## Writing application code that calls decision models

- Use the `decision-models` skill.
- Call `POST https://chat-preprod.dartmouth.edu/api/v1/systemone` for text/JSON System One state (`POST /api/v1/decisions` uses the OpenAI Decisions schema). Authenticate with a Dartmouth Chat API key (`DCHAT_KEY`), kept server-side. Only text/JSON `state` is supported; images are dropped.[^litellm-pr-44236][^vllm-decisions-doc]
- Default `cloudflare.clef`; use `typesafe.jev` only where labeled examples show Clef failing on reasoning-heavy decisions.
- Request has only `model`, `state`, `questions` (`1..64` questions, `choice` `2..26` options, `score` `2..10` levels). No other fields.[^vllm-decisions-doc]
- All independent questions about one state go in one request.
- Full meaning in `instructions`; question IDs aren't used by the model to understand the question.
- Every `choice` that might not fit has `other: null` or `"not stated"`.
- Questions, thresholds, and model choice live in `src/decisions/questions.*`.
- Gate irreversible actions on tuned confidence thresholds; fall back to a human or an LLM.
- Long `state` is silently truncated at 16K tokens; chunk in code.[^vllm-decisions-doc]
- Keep API tokens server-side. Log model name and config version per call.
- Changing a question or threshold means rerunning the labeled eval set.

[^litellm-pr-44236]: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
[^vllm-decisions-doc]: vLLM — Structured Decisions Models (/v1/systemone)
[^typesafe-skill]: TypeSafe AI skill (MIT-licensed source adaptation)
