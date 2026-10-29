---
name: decision-models
license: MIT
description: Build software with Clef and Jev decision models (`cloudflare.clef`, `typesafe.jev`) through the Dartmouth Chat preprod API (`POST https://chat-preprod.dartmouth.edu/api/v1/systemone` for System One payloads; `POST /api/v1/decisions` for the OpenAI Decisions schema). Decision models read `state` and typed `questions` (`noul`, `choice`, `score`) and return a calibrated probability for every allowed option without generating free-form text. Use when a feature needs a fast semantic judgment (routing, triage, tool or handler selection, extraction by selection, verification, moderation, reranking) or when an LLM prompt-and-parse step should become a structured decision. Also ships `decide`, a FastMCP 4 server that lets coding agents (Claude Code, Codex, goose, OpenCode, Cursor) call a decision model as a tool during a session, for one input or packed batches.
type: Agent Skill
title: Build with Clef and Jev decision models
resource: https://huggingface.co/Cloudflare/clef
tags: [decision-models, clef, jev, dartmouth-chat, litellm, vllm, system-one, classification, routing, mcp, fastmcp]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-29T15:52:00-04:00 }
stale_after: 2027-01-29T00:00:00Z
status: draft
sources:
  - id: rc-api
    resource: https://rc.dartmouth.edu/ai/online-resources/using-the-api
    title: How do I access and use the Dartmouth Chat API?
  - id: litellm-pr-44236
    resource: https://github.com/BerriAI/litellm/pull/44236
    title: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
    last_modified: 2026-10-03T00:00:00Z
  - id: vllm-decisions-doc
    resource: https://raw.githubusercontent.com/vllm-project/vllm/main/docs/models/structured_decisions_models.md
    title: vLLM — Structured Decisions Models (/v1/systemone)
  - id: hf-clef
    resource: https://huggingface.co/Cloudflare/clef
    title: Cloudflare/clef model card and weights (Apache 2.0)
  - id: typesafe-docs
    resource: https://docs.typesafe.ai/llms.txt
    title: TypeSafe Jev / System One documentation
  - id: typesafe-skill
    resource: https://github.com/typesafe-ai/skills
    title: TypeSafe AI skill (MIT-licensed source adaptation)
  - id: fastmcp-tools
    resource: https://gofastmcp.com/servers/tools
    title: FastMCP — Tools (v4)
---

# Build with Clef and Jev

Clef and Jev (System One) are decision models, not LLMs.[^hf-clef][^typesafe-docs] You send `state` and typed `questions`;
the model reads them once and scores every allowed option of every question together.
Output is probabilities only, so an answer can never be an option you didn't
define and there is no JSON to repair.[^typesafe-skill]

Code owns the workflow; the decision model supplies judgment where code needs understanding.
A coding agent keeps its own LLM. Clef or Jev is called either by the code the
agent writes, or by the agent itself through the `decide` MCP tool (below).
For a drop-in `AGENTS.md` template guiding coding agents on when to pick a
decision model vs an LLM vs plain code, see
[references/agents-md-template.md](references/agents-md-template.md).

## Call from a coding agent: the `decide` MCP

[`scripts/decide_mcp.py`](scripts/decide_mcp.py) is a single-file FastMCP 4
stdio server[^fastmcp-tools] that talks to the Dartmouth Chat preprod API (`https://chat-preprod.dartmouth.edu/api`).
It exposes `decide` for one input, `decide_batch` for the same questions over
many items or to rerank candidates, and `decision_models`, plus a
`decide://guide` resource and a `design_questions` prompt. It validates questions
before sending and returns warnings for unsure answers. Setup for each agent,
environment variables, and tests are in [references/decide-mcp.md](references/decide-mcp.md).

Don't call `decide` for everyday single-item choices you already have in context
(such as picking which file to read or which tool to run next)—serialising the
tool call costs more tokens and time than deciding directly. Reach for `decide` /
`decide_batch` in three situations:
- **Many-item triage, filtering, or reranking (`decide_batch`):** scoring or
  filtering dozens of search hits, TODOs, issues, log lines, or candidate records
  against one rubric in a packed batch (`item` in `instructions`), instead of
  looping or emitting a long LLM table.
- **Interactive question design & calibration (`decide` / `decide_batch`):** when
  writing decision questions for application code, test them on sample inputs in-session
  to verify clean separation (no `noul ≈ 0.5` or `label_mass` warnings) before
  committing them.
- **Independent rubric / blast-radius checks (`decide`):** scoring a diff,
  migration, or log against a fixed checklist (touches auth/credentials?
  irreversible data change?) with a decorrelated model.

Rules when calling `decide`:
- Batch every independent question about one state into one call, put full
  meaning in `instructions`, add an `other` exit, and keep math and dates out.
- Treat `warnings` as a signal to rewrite the question or ask the user. Never
  act irreversibly on them.
- If `decide` isn't configured, don't fake it. Fall back to your own reasoning
  and say so.

## Read the live docs

When designing a new decision workflow or checking primitives and patterns, consult
TypeSafe's live documentation index (`https://docs.typesafe.ai/llms.txt`)[^typesafe-docs]—every
concept and cookbook applies to both Jev and Clef:
- Mintlify serves Markdown by appending `.md` to any page path (e.g.
  `https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md`,
  `https://docs.typesafe.ai/concepts/state.md`,
  `https://docs.typesafe.ai/primitives.md`,
  `https://docs.typesafe.ai/confidence.md`).
- Inspect the closest cookbook (`function_calling.md`, `pre_parsed_value_extraction_cookbook.md`,
  `rerank_typesafe.md`, `hierarchical_classification.md`, `citation_check.md`, `sde_cascade.md`)
  for decomposition patterns.
- **Always call through the Dartmouth Chat API endpoints below** rather than calling
  `api.typesafe.ai` directly.

## Endpoints and access

- **Base URL:** `https://chat-preprod.dartmouth.edu/api` (Dartmouth Chat preprod, which forwards decision requests to Dartmouth's LiteLLM gateway). Paths below are relative to the host.
- **API key:** your personal Dartmouth Chat key: chat-preprod.dartmouth.edu › Profile › Settings › Account › API Key.[^rc-api] It shares your account's credit budget (`GET /api/v1/credits/balance`). Keep it in `DCHAT_KEY` and send it as `Authorization: Bearer $DCHAT_KEY`.
- **Text and JSON `state` only.** Images sent in `images` are silently dropped (the model answers as if none were attached), and there is no direct vLLM access.

| Use case | Endpoint |
| --- | --- |
| System One schema (`state` + `questions` object), Clef or Jev | `POST /api/v1/systemone`[^litellm-pr-44236][^typesafe-docs] |
| OpenAI Decisions schema (`input` + `questions` array) | `POST /api/v1/decisions`[^litellm-pr-44236] |
| List models | `GET /api/v1/models` (decision models have `"mode": "evaluation"`) |

> Use `/api/v1/...`. `/api/systemone` returns 405, and `/api/chat/completions` rejects decision models. A `GET` to an unknown path returns the web app's HTML with status 200, so check for a JSON body. Responses can add `id`, `object` and per-question `diagnostics` (`label_mass`, `argmax_is_label`): treat `argmax_is_label: false`, or a `label_mass` well below 1, as an unreliable answer. Request the model ID (e.g. `cloudflare.clef`); the response's `model` is the served name (`clef`, `jev-1.14.0`).

**OpenAI Decisions format** (`/api/v1/decisions`): `questions` is a list; each item has `name`, `type` (`predicate` for yes/no, `choice`, `score`) and `instructions`. Choice options are `choices: [{"value": "billing", "description": "..."}]`, and score levels are `levels: [{"label": "No impact"}, ...]`, lowest first. `answers` comes back as a list: `{"type": "predicate", "name": ..., "probability": 0.98}`, and `choice`/`score` answers carry `probabilities` as a list of `{value, probability}`. Prefer `/api/v1/systemone` unless your client already speaks OpenAI Decisions.

## Pick the model: Clef vs Jev

Check `GET https://chat-preprod.dartmouth.edu/api/v1/models` for the deployed IDs. As of 2026-10-29 preprod serves `cloudflare.clef` and `typesafe.jev`; `clef-flash` is not deployed there.

| Model | Origin & Hosting | Modalities & Limits | Best for |
| --- | --- | --- | --- |
| **`cloudflare.clef`** (`clef`) | **Cloudflare** open-weight (Apache 2.0, Qwen3.8-27B + joint schema head), **hosted on Dartmouth vLLM**[^hf-clef][^vllm-decisions-doc] | Text & JSON (`16,384` ctx; `choice` `2..26` options) | **Default.** Fast, private classification, routing, triage, tool selection (BANKING77, BFCL), and scoring. |
| **`typesafe.jev`** (`jev-1.14.0`) | **TypeSafe** proprietary System One flagship model, **cloud-hosted API**[^typesafe-docs] | **Text & JSON only** (`choice` `2..255` options) | Leads on reasoning-heavy decision sets (GPQA, MMLU-Pro, BBH, When2Call). Returns `{"type": "noul", "noul": 0.95}` on `noul` (without the extra `probabilities`/`confidence` fields vLLM adds). |

Because TypeSafe created the System One API for **Jev** and Cloudflare built **Clef** to speak that exact same schema, switching or A/B testing between `cloudflare.clef` and `typesafe.jev` on `/api/v1/systemone` is just changing `"model"`.

## Request contract

Send only `model`, `state`, and `questions`.[^litellm-pr-44236][^vllm-decisions-doc] Never add LLM chat fields (`messages`, `temperature`, `max_tokens`, `system`, `stream`, or top-level `instructions`).

- **`model`** (string): deployed model ID (e.g. `cloudflare.clef`).
- **`state`** (required, string, JSON object, or JSON array): what the questions are about.
  - Context limit is **16,384 tokens**.[^vllm-decisions-doc] Questions are counted first; if they don't fit, the request fails with `400`. Otherwise, long `state` is **silently truncated** to fit. Chunk or pre-select long text in code.
- **`questions`** (required, object): `1..64` questions mapping `<question_id>` -> question definition.[^vllm-decisions-doc] Question IDs must be non-empty strings without `:` or newlines.
  - **`noul`** (yes/no): `instructions` (string) and optional `criteria: {"true": "...", "false": "..."}` saying what yes and no mean.
    - Returns `{"type": "noul", "noul": 0.98, "probabilities": {"yes": 0.98, "no": 0.02}, "confidence": 0.98}` (`noul` is `P(yes)`).[^vllm-decisions-doc]
  - **`choice`** (pick one): `instructions` (string) and `criteria` mapping option ID -> description (`string` or `null`), **`2..26` options**.[^vllm-decisions-doc]
    - Returns `{"type": "choice", "choice": "<winner>", "probabilities": {"<option>": 0.96, ...}, "confidence": 0.96}`.
  - **`score`** (ordered scale): `instructions` (string) and `criteria` as an ordered array of **`2..10` level descriptions**, lowest first (indexed from `0`).[^vllm-decisions-doc]
    - Returns `{"type": "score", "score": 1.96, "legend": {"0": "...", ...}, "probabilities": {"0": 0.01, ...}, "confidence": 0.96}`. `score` is the probability-weighted expected index (can be fractional).

### Example: HTTP `POST /api/v1/systemone`

```bash
curl -sS "https://chat-preprod.dartmouth.edu/api/v1/systemone" \
  -H "Authorization: Bearer $DCHAT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cloudflare.clef",
    "state": {
      "ticket": "The checkout crashes every time I pay. I cannot place an order."
    },
    "questions": {
      "is_defect": {
        "type": "noul",
        "instructions": "Is the customer reporting a software defect?"
      },
      "team": {
        "type": "choice",
        "instructions": "Which team should handle this ticket?",
        "criteria": {
          "billing": "payments, charges, and checkout failures",
          "shipping": "deliveries and tracking",
          "other": null
        }
      },
      "severity": {
        "type": "score",
        "instructions": "Rate the impact of this issue.",
        "criteria": ["No impact", "Minor inconvenience", "Cannot complete a purchase"]
      }
    }
  }'
```

Response:

```json
{
  "model": "clef",
  "answers": {
    "is_defect": {
      "type": "noul",
      "noul": 0.98,
      "probabilities": {"yes": 0.98, "no": 0.02},
      "confidence": 0.98
    },
    "team": {
      "type": "choice",
      "choice": "billing",
      "confidence": 0.96,
      "probabilities": {"billing": 0.96, "shipping": 0.03, "other": 0.01}
    },
    "severity": {
      "type": "score",
      "score": 1.96,
      "confidence": 0.96,
      "legend": {"0": "No impact", "1": "Minor inconvenience", "2": "Cannot complete a purchase"},
      "probabilities": {"0": 0.01, "1": 0.02, "2": 0.97}
    }
  },
  "usage": {"input_tokens": 184, "output_tokens": 0}
}
```

## Find the useful shape

Start from what the app should show, select, change, or hand off, and work
backward to the judgments needed. Rules, arithmetic, counting, date math, exact
lookups, and execution stay in code.[^typesafe-skill]

- **Route and fill arguments.** Pick a handler plus its typed parameters in one
  request; ask branch-specific questions speculatively, consume only the
  relevant ones.
- **Select, don't generate.** Find candidates in code (regex, parser, retrieval),
  have Clef pick one, then copy or normalize it. It cannot pick an omitted value.
- **Judge evidence.** Rerank retrieved chunks; hierarchical classification.
- **Score once, reuse.** Store per-dimension scores; let code change weights and
  thresholds without rerunning inference. Scores make good ML features.
- **Verify and escalate.** Check claims or fields against evidence; send
  low-confidence or failing cases to a human or a reasoning LLM.
- **Gate an agent.** Decide next tool, whether a step is done, or whether an
  action needs approval, while an LLM does the actual work.

## Design the questions

Question IDs are NOT used by the model to understand the question; put the full
meaning in `instructions`.[^typesafe-docs][^vllm-decisions-doc] Reference parts of state with backticked paths
like `ticket.messages[0].text`. Prefer named JSON fields when state has several
parts.

- **One narrow, coherent judgment per question.** Say what counts ("names the
  browser and the action that triggers it", not "has repro steps"). Use strings
  for simple questions, or structured objects/arrays in `instructions` or
  `criteria` when definitions, contrasts, exclusions, or examples clarify meaning.
- **State each speculative premise explicitly:** because questions in one request
  run in parallel and cannot see each other's answers, write branch-specific
  questions so they make sense on their own (e.g. "Assuming the customer is
  asking for a refund, which item is it for?").
- **Every `choice` that might not fit gets an exit:** `other: null` or `"not stated"`
  (or pair it with a separate `noul` presence check when presence is independently
  useful).
- **Score levels describe concrete situations and stand alone.**
- **Multi-label:** one `noul` per label, not a `choice`.
- **No arithmetic, counts, or dates inside questions.**
- **A `noul` near `0.5` means equal probability for yes and no, not "medium
  intensity"** (use a `score` for intensity/degree). A `noul` near `0.5` or low
  `confidence` usually means a vague question—rewrite it before blaming the model.

## Compose and verify

- **Send all independent questions about one state in ONE request** (speculative
  fan-out; they run in parallel in a single pass and can't see each other). Never
  loop over questions. Make a second request only when an answer decides what to
  fetch next.
- **Pack many small items into one request.** When many items need the same
  questions, put them under one `state` (`{"items": {"a": ..., "b": ...}}`) with
  per-item question ids (`a.sensitive`, `b.sensitive`) up to 64 questions per request.
  One integration went from more than 60 s (one call per entity, timing out) to
  about 0.2 s (21 entities × 3 questions per call). Keep packed state well under
  the context limit, and spot-check packed answers against single-item calls.
- **Rerank in one pass, and never let a threshold return nothing.** Score every
  candidate on one `score` rubric in a single request, sort, then filter. Vague
  queries can push every candidate into the same middle bucket, so if the filter
  would drop everything, fall back to the top-k by score.
- **Size timeouts for batches and degrade gracefully.** Size HTTP timeouts for
  packed batches rather than a single call, and fall back to rules or regex when
  the decision endpoint is slow or unreachable instead of failing the feature.
- **Give each component one role.** Exact lookups and joins go in code or the
  database, retrieval goes to embeddings, judgments over the retrieved candidates
  go to the decision model, and only written output goes to an LLM.
- **Confidence measures distribution concentration, not permission to act.** Gate
  irreversible actions on thresholds tuned on labeled data, with human or LLM
  fallback. Note that several acceptable options can spread probability—low
  confidence does not invalidate a harmless preference choice. Ignore uncertainty
  on branches you don't use.
- **Keep policy explicit in code:** weighted scores suit compensating trade-offs,
  whereas an "any serious violation" rule needs separate `noul` conditions.
- **Keep all questions, model choice, and thresholds in one reviewable file.**
- **Log the `model` field, your config version, and `usage.input_tokens` per call.**
- **Typed output guarantees the interface, not truth.** Build a 20–100 example
  labeled set early; rerun it on every question edit or model change.
- **Keep API tokens server-side.**
- **For failures, inspect exact state (was it truncated at 16K?), questions,
  candidates, answers, and composition before blaming the model.**

[^rc-api]: How do I access and use the Dartmouth Chat API?
[^litellm-pr-44236]: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
[^vllm-decisions-doc]: vLLM — Structured Decisions Models (/v1/systemone)
[^hf-clef]: Cloudflare/clef model card and weights (Apache 2.0)
[^typesafe-docs]: TypeSafe Jev / System One documentation
[^typesafe-skill]: TypeSafe AI skill (MIT-licensed source adaptation)
[^fastmcp-tools]: FastMCP — Tools (v4)
