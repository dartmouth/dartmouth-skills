# Skills Update Log

## 2026-11-09
* **Update**: [decision-models](/decision-models/SKILL.md), new [references/images.md](/decision-models/references/images.md), [references/decide-mcp.md](/decision-models/references/decide-mcp.md), `scripts/decide_mcp.py` and `scripts/test_decide_mcp.py`: image support on `https://chat.dartmouth.edu/api`. Clef takes an `images` list (data URLs, at most 2) and Jev takes referenced `assets` (PNG/JPEG, 280–1568 px per side) and Box questions, also via `input_image` on `/api/v1/decisions`. Written for the production rollout on 2026-11-10; formats and limits were tested live on preprod on 2026-11-09. `decide` now sends images on the default `litellm` backend without needing `DECIDE_MEDIA_BASE_URL` (still an optional override), converts images to referenced `assets` with the `TypeSafe-Danger-Zone-Images` header for Jev models, rejects WebP for Jev, and explains Jev's minimum image size on error; tests added (status: draft, unverified).

## 2026-11-06
* **Update**: [references/decide-mcp.md](/decision-models/references/decide-mcp.md): the OpenCode v2 section now says where the config file goes (project `opencode.json` or global `~/.config/opencode/opencode.json`, or `opencode mcp add decide --global`) (status: draft, unverified).
* **Update**: `scripts/decide_mcp.py`, `scripts/test_decide_mcp.py`, and [references/decide-mcp.md](/decision-models/references/decide-mcp.md): `decision_models` now always lists the model each endpoint is configured for (default or `DECIDE_ROUTES` key) first, even when the gateway serves it under a different name and omits it from `/v1/models` (seen on `https://chat.dartmouth.edu/api`, which serves `cloudflare.clef` as `clef`); tests added (status: draft, unverified).
* **Update**: [decision-models](/decision-models/SKILL.md) and [references/agents-md-template.md](/decision-models/references/agents-md-template.md): cross-references to the new [langchain-dartmouth](/langchain-dartmouth/SKILL.md) skill — point Python users to `DartmouthDecisions` (`langchain_dartmouth`) instead of raw HTTP, linking the library repo and the 18-decision-models cookbook recipe; noted in [index.md](/index.md) (status: draft, unverified).
* **Update**: [decision-models](/decision-models/SKILL.md), [references/decide-mcp.md](/decision-models/references/decide-mcp.md), [references/agents-md-template.md](/decision-models/references/agents-md-template.md), `scripts/decide_mcp.py`, `scripts/test_decide_mcp.py`, and [index.md](/index.md): switched all endpoint references from the Dartmouth Chat preprod host (`https://chat-preprod.dartmouth.edu/api`) to production Dartmouth Chat (`https://chat.dartmouth.edu/api`); the `DECIDE_BASE_URL` default and test updated to match (status: draft, unverified).

## 2026-11-05
* **Creation**: Added [langchain-dartmouth](/langchain-dartmouth/SKILL.md), built from the library source (`../langchain-dartmouth/src/langchain_dartmouth`) and cookbook notebooks (`../langchain-dartmouth-cookbook`): authentication keys, choosing model classes, basic usage quirks, chains/RAG notebook map, and `DartmouthDecisions` usage (status: draft, unverified).

## 2026-10-29
* **Update**: [decision-models](/decision-models/SKILL.md), [references/decide-mcp.md](/decision-models/references/decide-mcp.md) and [references/agents-md-template.md](/decision-models/references/agents-md-template.md): switched from the LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu`) to the Dartmouth Chat preprod API (`https://chat-preprod.dartmouth.edu/api`, `POST /api/v1/systemone` and `/api/v1/decisions`, personal Dartmouth Chat API key). Model IDs are now `cloudflare.clef` and `typesafe.jev` (no `clef-flash` on preprod). Documented the OpenAI Decisions request format and that images are dropped. `decide_mcp.py` now defaults to the new base URL and also reads `DCHAT_KEY`, with tests added. Tested live against preprod on 2026-10-29 (status: draft, unverified).

## 2026-10-20
* **Update**: [decision-models](/decision-models/SKILL.md) and [references/agents-md-template.md](/decision-models/references/agents-md-template.md): added the `decide` FastMCP 4 server (`scripts/decide_mcp.py`, `scripts/test_decide_mcp.py`, and [references/decide-mcp.md](/decision-models/references/decide-mcp.md)) configured for Dartmouth's LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu`, default `cloudflare.clef`, API key from `ai.support@dartmouth.edu`, no direct vLLM access), updated LiteLLM System One endpoint guidance to `/v1/systemone` (LiteLLM ≥ v1.105.1), and added packed batching and rerank-filter fallback guidance (status: draft, unverified).

## 2026-10-14
* **Creation**: Added [decision-models](/decision-models/SKILL.md) and [references/agents-md-template.md](/decision-models/references/agents-md-template.md) for building with decision models served by vLLM through LiteLLM (`/v1/decisions` and `/decisions`) and guiding coding agents on LLM vs decision model selection (status: draft, unverified).

## 2026-10-13
* **Verification**: [research-container-deployment](/research-container-deployment/SKILL.md) and [references/kubernetes-manifests.md](/research-container-deployment/references/kubernetes-manifests.md) reviewed by human:f003q1r (status: stable).
* **Update**: [research-container-deployment](/research-container-deployment/SKILL.md): Kubernetes Deploy creates a `k8s-<name>` repo in the Dartmouth GitHub org, one folder per environment, synced by Argo CD about every 5 min; Rancher access is Kubernetes Deploy only (Container Deploy users go through RCD for logs).
* **Creation**: Added [references/kubernetes-manifests.md](/research-container-deployment/references/kubernetes-manifests.md) from the Dashboard's Container Deploy template and Kubernetes Deploy sample: generated resources, adapting the sample, sealing secrets with kubeseal (status: draft, unverified).
* **Update**: [research-container-deployment](/research-container-deployment/SKILL.md): Container Deploy manifests are Dashboard-managed, Kubernetes Deploy manifests are user-edited; SealedSecret requirement; Container Deploy runtime constraints (UID 101 non-root, ports ≥ 1024, no persistent storage, restricted egress, with the project's own databases reachable because namespace = project; requests = limits). Reset to draft pending re-review.
* **Verification**: [research-container-deployment](/research-container-deployment/SKILL.md) and its walkthrough reviewed by human:f003q1r (status: stable).
* **Update**: [research-container-deployment](/research-container-deployment/SKILL.md): image builders require Dartmouth GitHub org membership; added account setup and Dashboard invitation-request steps.
* **Update**: [research-container-deployment](/research-container-deployment/SKILL.md): HTTPS `<appname>.dartmouth.edu` addresses come from a Load Balancing Management TDX request; the `-app.c.dartmouth.edu:<port>` address always exists.
* **Creation**: Added [research-container-deployment](/research-container-deployment/SKILL.md), built from the RCD Dashboard workshop page and Dashboard UI screenshots (status: draft, unverified).
* **Creation**: Added [references/todo-walkthrough.md](/research-container-deployment/references/todo-walkthrough.md) with the workshop's Todo app example.

## 2026-10-12
* **Update**: Added OKF frontmatter to [dartmouth-branding](/dartmouth-branding/SKILL.md): `name` now matches the directory, one-line description, provenance and source (status: draft, unverified).
* **Fix**: Aligned AGENTS.md rules 4–6 with OKF v0.2 (`verified` format, no empty `verified` key, timestamps); corrected `verified` in AGENTS.md and dartmouth-chat to `human:` actor form.

## 2026-10-05
* **Creation**: Added [dartmouth-chat](/dartmouth-chat/SKILL.md), built from the rc.dartmouth.edu/ai/online-resources pages (status: draft, unverified).
* **Creation**: Split the coding-agent configs into [references/coding-agents.md](/dartmouth-chat/references/coding-agents.md).
* **Initialization**: Set up the repo layout, OKF v0.2 frontmatter, and Claude plugin manifests.
