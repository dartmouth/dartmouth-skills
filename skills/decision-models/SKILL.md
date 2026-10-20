---
name: decision-models
license: MIT
description: Build software with Clef and Jev decision models (`cloudflare.clef`, `clef`, `clef-flash`, `jev`) through Dartmouth's LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu`, `POST /v1/systemone` or `POST /systemone` for System One payloads; `POST /v1/decisions` for OpenAI Decisions schema). Decision models read `state` and typed `questions` (`noul`, `choice`, `score`) and return a calibrated probability for every allowed option without generating free-form text. Use when a feature needs a fast semantic judgment (routing, triage, tool or handler selection, extraction by selection, verification, moderation, reranking) or when an LLM prompt-and-parse step should become a structured decision. Also ships `decide`, a FastMCP 4 server that lets coding agents (Claude Code, Codex, goose, OpenCode, Cursor) call a decision model as a tool during a session, for one input or packed batches.
type: Agent Skill
title: Build with Clef and Jev decision models
resource: https://huggingface.co/Cloudflare/clef
tags: [decision-models, clef, jev, litellm, vllm, system-one, classification, routing, mcp, fastmcp]
generated: { by: opencode/gemini-4-argon, at: 2026-10-20T09:55:00-04:00 }
stale_after: 2027-01-20T00:00:00Z
status: draft
sources:
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
stdio server[^fastmcp-tools] that talks to the LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu`).
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
- **Always call through the LiteLLM gateway endpoints below** rather than calling
  `api.typesafe.ai` directly.

## Endpoints and access

- **Gateway URL:** `https://llm-proxy-preprod.dartmouth.edu`
- **API Key:** Request an API key from **ai.support@dartmouth.edu**.
- **No direct vLLM access:** Direct access to the underlying vLLM server is not currently available at this time. All requests must go through the LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu`), which means only **text and JSON `state`** are currently available (LiteLLM's native route does not pass `images` or `videos` through).

| Use case | Endpoint / SDK |
| --- | --- |
| **Text & JSON state (Clef or Jev)** | **LiteLLM Proxy (`https://llm-proxy-preprod.dartmouth.edu`):** `POST /v1/systemone` (or `POST /systemone` for System One `state` + `questions` dict)<br>JS SDK: TypeSafe JS SDK (`systemOne()`) pointed at the proxy[^litellm-pr-44236][^typesafe-docs] |

> Why `/v1/systemone`? In LiteLLM ≥ v1.105.1, `POST /v1/systemone` (and `/systemone`) takes the System One schema (`model`, `state`, and `questions` object) for both Clef and Jev while handling gateway keys, budgets, and `metadata.tags` (`POST /v1/decisions` uses the OpenAI Decisions schema: `input` + `questions` array).[^litellm-pr-44236] Gateway responses can add `id`, `object` and per-question `diagnostics` (`label_mass`, `argmax_is_label`): treat `argmax_is_label: false`, or a `label_mass` well below 1, as an unreliable answer. Request the gateway's model alias (e.g. `cloudflare.clef`); the response's `model` is the served name (`clef`).

## Pick the model: Clef vs Jev

Check `GET /v1/models` on `https://llm-proxy-preprod.dartmouth.edu` for the exact deployed model names (such as `cloudflare.clef`, `cloudflare.clef-flash`, or `jev`).

| Model | Origin & Hosting | Modalities & Limits | Best for |
| --- | --- | --- | --- |
| **`cloudflare.clef`** (`clef`) | **Cloudflare** open-weight (Apache 2.0, Qwen3.8-27B + joint schema head), **hosted on Dartmouth vLLM via LiteLLM**[^hf-clef][^vllm-decisions-doc] | Text & JSON via gateway (`16,384` ctx; `choice` `2..26` options) | **Default on Dartmouth's gateway.** Fast, private classification, routing, triage, tool selection (BANKING77, BFCL), and scoring. |
| **`cloudflare.clef-flash`** (`clef-flash`) | **Cloudflare** open-weight (Apache 2.0, Qwen3.5-9B + joint schema head), **hosted on vLLM via LiteLLM**[^hf-clef][^vllm-decisions-doc] | Text & JSON via gateway (`16,384` ctx; `choice` `2..26` options) | Smaller 9B variant for high-throughput paths when deployed alongside `clef`. |
| **`jev`** | **TypeSafe** proprietary System One flagship model, **cloud-hosted API** (routed via LiteLLM)[^typesafe-docs][^litellm-pr-44236] | **Text & JSON only** (`choice` `2..255` options) | Leads on reasoning-heavy decision sets (GPQA, MMLU-Pro, BBH, When2Call). Returns `{"type": "noul", "noul": 0.97}` on `noul` (without the extra `probabilities`/`confidence` fields vLLM adds on `noul`). |

Because TypeSafe created the System One API for **Jev** and Cloudflare built **Clef** to speak that exact same schema, switching or A/B testing between `cloudflare.clef`, `cloudflare.clef-flash`, and `jev` on LiteLLM's `/v1/systemone` is just changing `"model"` in config.

## Request contract

Send only `model`, `state`, and `questions`.[^litellm-pr-44236][^vllm-decisions-doc] Never add LLM chat fields (`messages`, `temperature`, `max_tokens`, `system`, `stream`, or top-level `instructions`).

- **`model`** (string): deployed gateway model name (e.g. `cloudflare.clef`).
- **`state`** (required, string, JSON object, or JSON array): what the questions are about.
  - Context limit is **16,384 tokens**.[^vllm-decisions-doc] Questions are counted first; if they don't fit, the request fails with `400`. Otherwise, long `state` is **silently truncated** to fit. Chunk or pre-select long text in code.
- **`questions`** (required, object): `1..64` questions mapping `<question_id>` -> question definition.[^vllm-decisions-doc] Question IDs must be non-empty strings without `:` or newlines.
  - **`noul`** (yes/no): `instructions` (string) and optional `criteria: {"true": "...", "false": "..."}` saying what yes and no mean.
    - Returns `{"type": "noul", "noul": 0.98, "probabilities": {"yes": 0.98, "no": 0.02}, "confidence": 0.98}` (`noul` is `P(yes)`).[^vllm-decisions-doc]
  - **`choice`** (pick one): `instructions` (string) and `criteria` mapping option ID -> description (`string` or `null`), **`2..26` options**.[^vllm-decisions-doc]
    - Returns `{"type": "choice", "choice": "<winner>", "probabilities": {"<option>": 0.96, ...}, "confidence": 0.96}`.
  - **`score`** (ordered scale): `instructions` (string) and `criteria` as an ordered array of **`2..10` level descriptions**, lowest first (indexed from `0`).[^vllm-decisions-doc]
    - Returns `{"type": "score", "score": 1.96, "legend": {"0": "...", ...}, "probabilities": {"0": 0.01, ...}, "confidence": 0.96}`. `score` is the probability-weighted expected index (can be fractional).

### Example: HTTP `POST /v1/systemone`

```bash
curl -sS "https://llm-proxy-preprod.dartmouth.edu/v1/systemone" \
  -H "Authorization: Bearer $LITELLM_KEY" \
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

[^litellm-pr-44236]: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
[^vllm-decisions-doc]: vLLM — Structured Decisions Models (/v1/systemone)
[^hf-clef]: Cloudflare/clef model card and weights (Apache 2.0)
[^typesafe-docs]: TypeSafe Jev / System One documentation
[^typesafe-skill]: TypeSafe AI skill (MIT-licensed source adaptation)
[^fastmcp-tools]: FastMCP — Tools (v4)
