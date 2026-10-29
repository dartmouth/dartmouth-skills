---
type: Reference
title: decide MCP server — decision models as a coding-agent tool
description: Install and configure the `decide` FastMCP 4 server so Claude Code, Codex, goose, OpenCode v2 and Cursor can call Clef or Jev on the Dartmouth Chat preprod API during a session, one input or many at once.
tags: [decision-models, clef, jev, dartmouth-chat, mcp, fastmcp, claude-code, codex, goose, opencode, cursor, litellm]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-29T15:52:00-04:00 }
stale_after: 2027-01-29T00:00:00Z
status: draft
sources:
  - id: rc-api
    resource: https://rc.dartmouth.edu/ai/online-resources/using-the-api
    title: How do I access and use the Dartmouth Chat API?
  - id: fastmcp-4
    resource: https://github.com/PrefectHQ/fastmcp/releases/tag/v4.0.0
    title: FastMCP v4.0.0 release notes
  - id: fastmcp-41
    resource: https://github.com/PrefectHQ/fastmcp/releases/tag/v4.1.0
    title: FastMCP v4.1.0 release notes
  - id: fastmcp-upgrade
    resource: https://gofastmcp.com/getting-started/upgrading/from-fastmcp-3
    title: FastMCP — Upgrading from FastMCP 3
  - id: opencode-v2-mcp
    resource: https://opencode.ai/v2/docs/mcp-servers/
    title: OpenCode v2 — MCP servers
  - id: goose-config
    resource: https://goose-docs.ai/docs/guides/config-files
    title: goose — Configuration files
  - id: goose-decisions-pr
    resource: https://github.com/aaif-goose/goose/pull/12418
    title: goose PR #12418 — decisions provider crate (OpenRouter, Jev)
  - id: litellm-pr-44236
    resource: https://github.com/BerriAI/litellm/pull/44236
    title: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
    last_modified: 2026-10-03T00:00:00Z
  - id: cf-clef
    resource: https://developers.cloudflare.com/workers-ai/models/clef/
    title: Cloudflare Workers AI — clef model page
---

# decide MCP server

No coding agent can call a decision model natively yet. goose's Rust SDK has a
decisions provider for app builders, but the agent itself doesn't use it.[^goose-decisions-pr]
The [`decide` server](../scripts/decide_mcp.py) fills the gap. It is a single-file
FastMCP 4.1 stdio server[^fastmcp-4][^fastmcp-41] that any MCP-capable agent can
load. The agent keeps its own LLM for reasoning and everyday navigation, and
calls `decide` / `decide_batch` when a decision model actually beats an LLM turn:
1. **Many-item triage, filtering, or reranking (`decide_batch`)** over search
   hits, issues, TODOs, logs, or candidate records in one packed pass.
2. **Interactive question design & calibration (`decide` / `decide_batch`)** to
   test questions on sample inputs while building a decision-model feature.
3. **Independent rubric / blast-radius checks (`decide`)** on a diff, migration,
   or log using a decorrelated model and calibrated probabilities.

## What it exposes

| Component | Purpose |
| --- | --- |
| tool `decide(state, questions, model?, image_paths?)` | One System One request about one input. Returns `{model, answers, usage, latency_ms, warnings}`. |
| tool `decide_batch(items, questions, model?, rank_by?, min_value?, top_k?)` | Asks the same questions of many items, packed up to 64 questions per request. Returns `results` keyed by your ids, plus an optional `ranking`. |
| tool `decision_models()` | Lists the decision models on each configured endpoint (`GET /v1/models`, filtered to Clef/Jev-looking ids), plus the default and escalation model. |
| resource `decide://guide` | Question-writing rules, readable by agents that load resources. |
| prompt `design_questions(task)` | Walks the agent through drafting, showing and running questions. OpenCode lists it as `/decide:design_questions`. |

All tools are marked read-only and idempotent, so clients that honour MCP
annotations can skip the approval prompt.

**Validation before sending.** The server rejects malformed questions before they
reach the model: a bad `type`, missing `instructions`, extra fields such as
`temperature`, wrong option or level counts, or ids containing `:`. The agent gets
the error and can fix the call.

**Warnings.** A `noul` between 0.35 and 0.65 (can't tell) or a `confidence` under
0.5 is flagged in `warnings`, so the agent rewrites the question or asks instead
of acting on it.

## decide_batch: many items, few requests

One call per item is the slow path. In a live knowledge-graph integration, a privacy
review made one decision call per entity and timed out after more than 60 seconds.
Packing 21 entities × 3 questions (63 questions) into each request brought it down
to about 0.2 seconds. `decide_batch` packs the same way:

- **Packing.** Each item goes into `state.items.<slot>`, and each question is copied
  per item as `<slot>.<id>`. Write instructions against `item` (for example
  `` `item.title` ``); the server rewrites that to the item's slot. A question that
  never mentions `item` gets an explicit "About `items.<slot>` only:" prefix.
- **Chunking.** Each request carries at most 64 questions, and at most
  `DECIDE_BATCH_MAX_STATE_CHARS` (default 24,000) of item JSON so the state stays
  under the context limit.
- **Splitting.** If the backend answers 400 or 413, the chunk is halved and retried.
- **Ranking.** `rank_by` sorts items by a `noul` (P(yes)) or a `score` (expected
  level), highest first. `min_value` filters, and `top_k` caps the list. If the
  filter would drop every item, the top items come back unfiltered with a warning.
  This guards against a real failure: vague reranking queries scored every
  candidate in the same middle bucket, so a fixed threshold returned nothing.
- **Accuracy.** Packing puts several items in one context. Spot-check a few
  packed answers against single `decide` calls on your own data before relying on
  them for anything important.

## Backends

| `DECIDE_BACKEND` | Endpoint | Notes |
| --- | --- | --- |
| `litellm` (default) | `{DECIDE_BASE_URL}/v1/systemone` | The Dartmouth Chat preprod API (`https://chat-preprod.dartmouth.edu/api`), which forwards to Dartmouth's LiteLLM gateway. Use your Dartmouth Chat API key (Profile › Settings › Account › API Key)[^rc-api] in `DECIDE_API_KEY` or `DCHAT_KEY`. It serves System One payloads on `/api/v1/systemone` and OpenAI Decisions payloads on `/api/v1/decisions`.[^litellm-pr-44236] Only text/JSON `state` is supported; images are dropped. |
| `cloudflare` | Workers AI `ai/run/@cf/cloudflare/{model}` | Needs `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AUTH_TOKEN`; the `{success, result}` envelope is unwrapped.[^cf-clef] |

**Diagnostics.** Clef on vLLM (behind LiteLLM) returns per-question `diagnostics` with
`label_mass` (how much probability landed on your options before
renormalising) and `argmax_is_label`. The server flags answers whose
`argmax_is_label` is false, or whose `label_mass` is below 0.9. A joint-schema
head scores only your options, so its `label_mass` is always 1.0. If you see
lower values, the server is scoring next-token label probabilities instead, and
it's worth checking how the model is served.

**Model aliases.** Use the model ID from `GET /api/v1/models` (e.g.
`cloudflare.clef`, `typesafe.jev`; `decision_models` lists the decision models on the endpoint).
The response's `model` field is the upstream served name (`clef`).

**Retries and audit log.** The server retries 429, 502, 503, 504 and transport
errors twice with backoff. Other 4xx responses fail immediately and return the
server's message. `DECIDE_LOG=<path>` appends one JSONL line per call with the
tool, backend, model, question ids, item count, usage and latency. It never logs
`state`.

Other settings are `DECIDE_MODEL` (default `cloudflare.clef`),
`DECIDE_BASE_URL` (default `https://chat-preprod.dartmouth.edu/api`),
`DECIDE_API_KEY` (falls back to `DCHAT_KEY`, then `LITELLM_API_KEY`, then `LITELLM_KEY`),
`DECIDE_MAX_CHOICE_OPTIONS` (default 26; raise it to 255 for Jev or Workers AI)
and `DECIDE_TIMEOUT` (default 15 seconds per attempt).

## Install

`scripts/decide_mcp.py` declares its dependency inline (`fastmcp>=4.1,<5`), so
`uv` runs it without a virtualenv. It works against clients on either MCP protocol
era. It uses no elicitation, sampling or session state, so nothing in it depends
on the handshake era.[^fastmcp-upgrade]

```bash
uv run --script /path/to/decide_mcp.py   # starts on stdio; Ctrl-C to stop
```

Create an API key in Dartmouth Chat preprod (Profile › Settings › Account ›
API Key) and keep it in your shell environment (`DCHAT_KEY` or
`DECIDE_API_KEY`) rather than hard-coding it in agent config files. The
examples below rely on the agent passing your environment through.

**OpenCode v2** (`opencode.json` / `opencode.jsonc`; servers live under `mcp.servers`).[^opencode-v2-mcp]
`codemode: false` keeps the tools on the model's native tool list, where OpenCode
names them `decide_decide`, `decide_decide_batch` and so on.

```jsonc
{
  "mcp": {
    "servers": {
      "decide": {
        "type": "local",
        "command": ["uv", "run", "--script", "/path/to/decide_mcp.py"],
        "codemode": false,
        "environment": {
          "DECIDE_BACKEND": "litellm",
          "DECIDE_BASE_URL": "https://chat-preprod.dartmouth.edu/api",
          "DECIDE_MODEL": "cloudflare.clef"
        }
      }
    }
  }
}
```

**Claude Code**

```bash
claude mcp add decide \
  -e DECIDE_BACKEND=litellm \
  -e DECIDE_BASE_URL=https://chat-preprod.dartmouth.edu/api \
  -e DECIDE_MODEL=cloudflare.clef \
  -- uv run --script /path/to/decide_mcp.py
```

**Codex**

```bash
codex mcp add decide \
  --env DECIDE_BACKEND=litellm \
  --env DECIDE_BASE_URL=https://chat-preprod.dartmouth.edu/api \
  --env DECIDE_MODEL=cloudflare.clef \
  -- uv run --script /path/to/decide_mcp.py
```

**goose** (`~/.config/goose/config.yaml`, or `goose configure` → add a command-line extension).[^goose-config]

```yaml
extensions:
  decide:
    name: decide
    type: stdio
    enabled: true
    timeout: 60
    cmd: uv
    args: ["run", "--script", "/path/to/decide_mcp.py"]
    description: Decision-model judgments (Clef / Jev)
    envs:
      DECIDE_BACKEND: litellm
      DECIDE_BASE_URL: https://chat-preprod.dartmouth.edu/api
      DECIDE_MODEL: cloudflare.clef
```

**Cursor** (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "decide": {
      "command": "uv",
      "args": ["run", "--script", "/path/to/decide_mcp.py"],
      "env": {
        "DECIDE_BACKEND": "litellm",
        "DECIDE_BASE_URL": "https://chat-preprod.dartmouth.edu/api",
        "DECIDE_MODEL": "cloudflare.clef"
      }
    }
  }
}
```

## Test

```bash
# offline against a mock backend; fastmcp is stubbed if not installed
python3 -m unittest skills/decision-models/scripts/test_decide_mcp.py
# with FastMCP installed, also runs the in-memory MCP round trip (tools, prompt, resource)
uv run --with "fastmcp>=4.1,<5" python3 -m unittest skills/decision-models/scripts/test_decide_mcp.py
```

## Privacy

Every call sends `state` to the configured backend. `cloudflare.clef` on
`https://chat-preprod.dartmouth.edu/api` runs on Dartmouth hardware, so code,
logs, and project state stay on-premises. `typesafe.jev` is a cloud API, so
state sent to it leaves Dartmouth. Keep the Cloudflare Workers AI backend
for public or synthetic content.

[^fastmcp-4]: FastMCP v4.0.0 release notes
[^fastmcp-41]: FastMCP v4.1.0 release notes
[^fastmcp-upgrade]: FastMCP — Upgrading from FastMCP 3
[^opencode-v2-mcp]: OpenCode v2 — MCP servers
[^goose-config]: goose — Configuration files
[^goose-decisions-pr]: goose PR #12418 — decisions provider crate (OpenRouter, Jev)
[^rc-api]: How do I access and use the Dartmouth Chat API?
[^litellm-pr-44236]: LiteLLM PR #44236 — Unified /v1/decisions and /decisions endpoint
[^cf-clef]: Cloudflare Workers AI — clef model page
