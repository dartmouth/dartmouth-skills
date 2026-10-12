---
name: dartmouth-chat
description: Help Dartmouth community members use Dartmouth Chat (chat.dartmouth.edu), the Open WebUI-based AI chat platform run by Research Computing & Data (RCD). Use when someone asks about access/eligibility, daily credits and credit groups, choosing models and what the model tags mean, privacy of local vs cloud models, UI features (tools, web search, file uploads, memory, study mode, temporary chat, compaction, image generation, X-Ray), Workspace (custom models, knowledge bases, prompts, skills, automations), or using the Dartmouth Chat API and connecting coding agents (Claude Code, OpenCode, Kilo Code, Mistral Vibe, LangChain).
type: Agent Skill
title: Dartmouth Chat — end-user guide
resource: https://chat.dartmouth.edu
tags: [dartmouth-chat, open-webui, llm, api, end-user, rcd]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-05T09:09:52-04:00 }
verified: { by: human:tivon.n.luker, at: 2026-10-12T17:09:45-04:00 }
stale_after: 2027-01-05T00:00:00Z
status: stable
sources:
  - id: rc-online-resources
    resource: https://rc.dartmouth.edu/ai/online-resources/
    title: Using Dartmouth Chat (index of all user articles)
    author: team:dartmouth-rcd
  - id: rc-faq
    resource: https://rc.dartmouth.edu/ai/online-resources/faq
    title: Dartmouth Chat — FAQs (access, privacy, usage limits)
    author: team:dartmouth-rcd
    last_modified: 2026-06-18T00:00:00Z
  - id: rc-tags
    resource: https://rc.dartmouth.edu/ai/online-resources/understanding-tags
    title: What do the tags mean?
    author: team:dartmouth-rcd
    last_modified: 2025-12-11T00:00:00Z
  - id: rc-choosing-model
    resource: https://rc.dartmouth.edu/ai/online-resources/choosing-the-right-model
    title: How do I choose the right model?
    author: team:dartmouth-rcd
    last_modified: 2026-06-01T00:00:00Z
  - id: rc-credits
    resource: https://rc.dartmouth.edu/ai/online-resources/checking-credits
    title: How do I check my available credits?
    author: team:dartmouth-rcd
    last_modified: 2025-09-04T00:00:00Z
  - id: rc-credit-groups
    resource: https://rc.dartmouth.edu/ai/online-resources/setting-up-credit-groups
    title: Setting up a credit group
    author: team:dartmouth-rcd
    last_modified: 2026-05-27T00:00:00Z
  - id: rc-reasoning
    resource: https://rc.dartmouth.edu/ai/online-resources/reasoning-settings
    title: Reasoning settings
    author: team:dartmouth-rcd
    last_modified: 2026-03-17T00:00:00Z
  - id: rc-tools
    resource: https://rc.dartmouth.edu/ai/online-resources/using-tools
    title: What are Tools and how do I use them?
    author: team:dartmouth-rcd
    last_modified: 2026-07-15T00:00:00Z
  - id: rc-compaction
    resource: https://rc.dartmouth.edu/ai/online-resources/chat-compaction
    title: Chat Compaction
    author: team:dartmouth-rcd
    last_modified: 2026-08-25T00:00:00Z
  - id: rc-memory
    resource: https://rc.dartmouth.edu/ai/online-resources/using-memory
    title: What is Memory and how do I use it?
    author: team:dartmouth-rcd
    last_modified: 2026-08-25T00:00:00Z
  - id: rc-workspace
    resource: https://rc.dartmouth.edu/ai/online-resources/workspace
    title: Workspace (models, knowledge, prompts, skills)
    author: team:dartmouth-rcd
    last_modified: 2026-03-17T00:00:00Z
  - id: rc-workspace-models
    resource: https://rc.dartmouth.edu/ai/online-resources/workspace-models
    title: How do I build my own custom model?
    author: team:dartmouth-rcd
    last_modified: 2026-07-30T00:00:00Z
  - id: rc-automation
    resource: https://rc.dartmouth.edu/ai/online-resources/automation
    title: What is Automation?
    author: team:dartmouth-rcd
    last_modified: 2026-05-27T00:00:00Z
  - id: rc-api
    resource: https://rc.dartmouth.edu/ai/online-resources/using-the-api
    title: How do I access and use the Dartmouth Chat API?
    author: team:dartmouth-rcd
    last_modified: 2026-03-17T00:00:00Z
  - id: rc-api-tutorial
    resource: https://rcweb.dartmouth.edu/~d20964h/2024-12-11-dartmouth-chat-api
    title: Dartmouth Chat API tutorial
  - id: rc-clients
    resource: https://rc.dartmouth.edu/ai/online-resources/connecting-ai-clients
    title: How do I connect my coding tool to Dartmouth Chat API?
    author: team:dartmouth-rcd
    last_modified: 2026-05-20T00:00:00Z
  - id: rc-gpt5
    resource: https://rc.dartmouth.edu/ai/online-resources/gpt5-notes
    title: Using the GPT-5 model family
    author: team:dartmouth-rcd
    last_modified: 2025-09-09T00:00:00Z
  - id: rc-policies
    resource: https://rc.dartmouth.edu/ai/online-resources/policies-bias-responsible-use
    title: Policies, Bias, and Responsible Use
    author: team:dartmouth-rcd
    last_modified: 2025-12-11T00:00:00Z
  - id: rc-computing
    resource: https://rc.dartmouth.edu/ai/computing-resources/
    title: Computing Resources for AI Projects
    author: team:dartmouth-rcd
---

# Dartmouth Chat

Dartmouth Chat (https://chat.dartmouth.edu) is a web chat app for large language models, offered by Dartmouth Libraries and Research Computing & Data (RCD). It provides open-weight **local** models hosted on Dartmouth hardware and **cloud** models from OpenAI, Anthropic, Google and Mistral. Use is free up to a daily limit.

The canonical docs are https://rc.dartmouth.edu/ai/online-resources/. Each topic below links to its page. Models, versions and menu labels change often. If a detail matters, fetch the linked page and use what it says now over this file.

## Ground rules for answering

- **Model IDs change.** Never present a model list from this file as current. Point users to the model dropdown or `GET https://chat.dartmouth.edu/api/models`. IDs have the form `provider.model`, e.g. `openai.gpt-oss-120b`, `anthropic.claude-sonnet-4-6`.
- **Cost and privacy follow LOCAL vs CLOUD.**
  - LOCAL (FREE) models are free and unlimited, and data stays on Dartmouth systems.
  - CLOUD ($–$$$) models use daily credits and fall under the provider's business terms.
- **Don't promise what isn't published.** The docs give no numeric limits for file size, upload count or knowledge-base tokens.
- **Support routes:**
  - Help: research.computing@dartmouth.edu
  - Outages: https://status.dartmouth.edu (under "Research Computing")
  - What's new: https://dartgo.org/dchat-blog, or Settings › About › "see what's new"

## Access

- **Eligible:** users whose *primary* affiliation is Faculty, Staff, Student, Emeritus Faculty, or a Sponsored account. Sign in with Dartmouth credentials.
- **Not eligible:** alumni. There are no individual exceptions.[^rc-faq] Send alumni to alumni.help@dartmouth.edu.
- **Group-limited:** some features, such as Workspace, and some usage limits vary by group.
- **Sensitive or regulated data:** for a more secure LLM service, contact research.computing@dartmouth.edu.

FAQ: https://rc.dartmouth.edu/ai/online-resources/faq

## Credits and cost

- **Daily allowance:** cloud models draw on **2,000 credits per day**.[^rc-credits] The counter is at the upper right. Hover it to see the reset time.
  - More `$` on a model means it costs more per token and uses the allowance faster.
  - Out of credits: switch to a FREE/LOCAL model or wait for the reset.
- **Hidden costs:** reasoning tokens are billed even when the "thinking" isn't shown. Side-by-side model comparison roughly doubles usage. Memory adds tokens on cloud models. Automations can use a lot.
- **Estimating cost:** the Dartmouth Tokenizer at https://ai-tools.dartmouth.edu/dtok gives free relative-cost estimates.
- **Credit Groups** extra credits for a person, class or program, billed monthly for what's used:
  1. Request: https://services.dartmouth.edu/TDClient/1806/Portal/Requests/ServiceDet?ID=56401 (group description + members' NetIDs/emails). Members must be Dartmouth community members. External collaborators need a Sponsored Account.
  2. You receive a **Virtual Key**.
  3. In Dartmouth Chat: Profile › Settings › Connections › add a connection with
     - URL `https://llm-proxy.dartmouth.edu`
     - Key = the Virtual Key
     - Prefix ID = a 3–6 character label for the group
  4. Save the connection, then save Settings.
  5. In the model selector, use the **Direct** filter to pick the group's models. The group allowance then shows at the upper right.
  6. For API-only use, use the Virtual Key in place of your personal API key.

  Docs: https://rc.dartmouth.edu/ai/online-resources/setting-up-credit-groups

## Privacy

- **All chats:** history and uploads are stored on Dartmouth infrastructure. Data isn't shared between users or used by Dartmouth for training. ITC keeps no logs of prompts beyond what session persistence needs. Data is handled under the policy [Access to User-Related Electronic Information](https://policies.dartmouth.edu/policy/access-user-related-electronic-information-dartmouth).
- **LOCAL models:** prompts, files and images never leave Dartmouth systems.
- **CLOUD models** run under each provider's business/API terms, not consumer terms:
  - **Anthropic:** Claude is served via Vertex AI with request/response logging off. Prompts aren't used for training. *Exception:* Mythos-class models (e.g. "Fable 5") retain prompts and outputs for 30 days for trust and safety.[^rc-faq]
  - **Google:** prompts may be logged for a limited period for abuse detection, and kept up to 60 days under Google's Advanced AI Safety Addendum.
  - **OpenAI, Mistral:** no training on customer data.
- **To keep a chat out of history:** turn on **Temporary Chat** (toggle, top right).

## Choosing a model

Open the dropdown at the upper left, or click the tag icon next to a model to see its tags:

| Tag | Meaning |
|---|---|
| FREE / $ – $$$ | FREE = local, no credits. More $ = higher relative cost. |
| LOCAL / CLOUD | LOCAL runs at Dartmouth (private, free). CLOUD runs at the provider. |
| VISION | Accepts images (needed to interpret uploaded images). |
| REASONING | Thinks by default. |
| HYBRID REASONING | Answers directly unless you raise Reasoning Effort. |
| ADAPTIVE REASONING | Picks its own thinking depth (e.g. GPT-5.1 Instant/Codex). |
| TOOL CALLING | Required for any Tools to work.[^rc-tools] |

Tag definitions: see the tags page.[^rc-tags]

- **Compare models:** click `+` next to the model name to run two side by side. Settings carry over.
- **Model health:** the **Model Status** link in the bottom toolbar shows availability. A `?` means there's no live status; click it to open the provider's status page.
- **Reasoning Effort:** use the lightbulb icon by the prompt box, or Chat Controls › Reasoning Effort.
  - Common values: `high` / `medium` / `low`, plus `minimal` / `none` on some GPT models.
  - Click **Custom** to reset to the default.
- **GPT-5 family:** these models skip Markdown by default. Add a system prompt in Chat Controls › System Prompt asking for Markdown, and repeat it every 3–5 messages. See https://rc.dartmouth.edu/ai/online-resources/gpt5-notes

## Chat features

Most toggles are under the **Integration** menu below the prompt box.

| Want to… | How |
|---|---|
| Upload documents (RAG) | `+` › Upload Files. Only VISION models read images. |
| Use specific webpages / YouTube | `+` › Attach Webpage (YouTube pulls the transcript) |
| Search the web | Integration › Tools › Web Search Tools |
| Generate or edit images | Integration › Tools › Image Tools, then refine with follow-up prompts |
| Make Word/Excel/PowerPoint files | Integration › Tools › Create Document Tool |
| Let the model ask clarifying questions | Integration › Tools › Ask Question Tool |
| Other tools | Knowledge, Chats (query past chats), Notes, Time Utility, Visualization, Email (sends only to your own address) |
| Set default tools | Avatar › Settings › Personalization |
| Learn rather than get answers | Integration › Study Mode. Options icon edits the tutor instructions. |
| Assistant persona | Integration › DChat Persona. Options icon edits it; Default restores it. |
| Remember facts across chats | Integration › Memory (off by default; brain icon shows when on). Manage in Settings › Personalization › Memory. |
| Inspect raw API messages | Integration › X-Ray, then the magnifying glass under a reply |
| Context usage | Hover the ⓘ circle under a reply. Click it for details or **Compact Now**. |
| Auto-summarize long chats | Settings › Chat Compaction (off by default). Threshold % of the context window, e.g. 75% of 128K = 96K. Not available in temporary chats. |
| Regenerate | Circular-arrows icon: Try Again / Add Details / More Concise |
| Organize chats | Left sidebar. Each chat's `…` menu: Rename / Share / Clone / Download / Delete. Use tags and folders. |
| Folder defaults | A folder can hold a system prompt and/or knowledge base for new chats in it. Folders can't be shared. |
| Save or share results | `…` at top right: Share link (recipients can clone), or Download as .json / .txt / .pdf |
| Reopen the welcome tour | User menu › Welcome Guide |

**Tool caveats:**

- Tools are enabled by the user but triggered by the model. If the model doesn't use one, ask it to explicitly.
- Tools only work on TOOL CALLING models.
- The wrench icon in the message bar shows how many tools are active.

## Workspace (build your own chatbot)

Open it from the left sidebar. Every item is **Private by default**. Models and knowledge bases are shared via **Access**; prompts and skills via group Read/Write.

- **Models:** Workspace › Models › New Model. Fields:
  - Name, Base Model, Description, Avatar, Tags
  - System Prompt, Prompt Suggestions
  - Knowledge, Tools, Skills, Filters, Capabilities
  - **Freeze Model Configuration**: turn this on before sharing so others can't change the setup.
- **Knowledge:** Workspace › Knowledge › New Knowledge.
  - Accepts files or a synced folder (Word, PDF, text…). Content must be machine-readable; scanned PDFs often aren't. Review the extracted text.
  - Ways to use it:
    - Type `#` and pick the collection (forces its use).
    - `+` › Attach Knowledge.
    - Attach it to a custom model.
    - Turn on the Knowledge Tool (the model decides whether to use it).
  - Only a limited number of tokens from the collection is sent per message.
- **Prompts:** Workspace › Prompts › New Prompt. Supports `{{variable}}` placeholders. Run with `/`.
- **Skills:** Markdown instructions the model loads when needed. Workspace › Skills › New Skill. Run with `$`.
- **Automations:** scheduled runs of a custom model + prompt.
  - Create: Settings › Automations › New Automation (title, prompt, model, schedule). Supports `{{CURRENT_DATE}}`.
  - Results land in a sidebar folder.
  - They use a lot of credits, so schedule them sensibly.

## API

- **Getting a key:** chat.dartmouth.edu › Profile (lower left) › Settings › Account › API Key / Create new secret key. The key shares your account's credit limits.
- **Base URL:** `https://chat.dartmouth.edu/api`
- **Compatible with:** OpenAI Chat Completions, OpenAI Responses and Anthropic Messages clients.[^rc-api]

```bash
export DCHAT_KEY=...   # your API key

# List model IDs
curl -s https://chat.dartmouth.edu/api/models \
  -H "Authorization: Bearer $DCHAT_KEY" | jq -r '.data[].id'

# Chat completion (local model = no credits)
curl -s https://chat.dartmouth.edu/api/chat/completions \
  -H "Authorization: Bearer $DCHAT_KEY" -H "Content-Type: application/json" \
  -d '{"model":"openai.gpt-oss-120b",
       "messages":[{"role":"user","content":"What is deep learning?"}],
       "stream":false}' | jq -r '.choices[0].message.content'
```

**More resources:**

- Python: `pip install langchain-dartmouth`
- Cookbook: https://dartmouth.github.io/langchain-dartmouth-cookbook/00-intro.html
- Tutorial: https://rcweb.dartmouth.edu/~d20964h/2024-12-11-dartmouth-chat-api

Docs: https://rc.dartmouth.edu/ai/online-resources/using-the-api

## Connecting coding agents

Full, current configs: https://rc.dartmouth.edu/ai/online-resources/connecting-ai-clients. All of them use the base URL `https://chat.dartmouth.edu/api` and the user's API key.[^rc-clients] For best results, pick a Claude or GPT model, with a free local model such as `openai.gpt-oss-120b` as a fallback.

Step-by-step configs for each tool are in [references/coding-agents.md](references/coding-agents.md). Load that file when a user is setting one up:

| Tool | Config location | Key points |
|---|---|---|
| Claude Code | `~/.claude/settings.json` | `ANTHROPIC_BASE_URL` = base URL; key via `apiKeyHelper` (macOS Keychain) |
| OpenCode | `~/.config/opencode/opencode.json` | `@ai-sdk/openai-compatible` provider; long timeouts |
| Kilo Code (VS Code) | Settings › Providers › Custom provider | ID `dartmouth-chat` |
| Mistral Vibe | `~/.vibe/config.toml` + `~/.vibe/.env` | `api_style = "openai"`, `backend = "generic"` |

**Troubleshooting:**

- **"model not found":** the ID must exactly match `/api/models`, including the `provider.` prefix.
- **401:** regenerate the key.
- **429 or exhausted credits:** switch to a local model or set up a Credit Group.

## Beyond chat

- **Custom AI applications:** RCD's Research Software Engineering team. See https://rc.dartmouth.edu/ai/development-resources/
- **Coursework and responsible-use policies** (students, Geisel, Guarini, Thayer, Tuck, staff): https://rc.dartmouth.edu/ai/online-resources/policies-bias-responsible-use

[^rc-faq]: Dartmouth Chat — FAQs (access, privacy, usage limits)
[^rc-credits]: How do I check my available credits?
[^rc-tags]: What do the tags mean?
[^rc-tools]: What are Tools and how do I use them?
[^rc-api]: How do I access and use the Dartmouth Chat API?
[^rc-clients]: How do I connect my coding tool to Dartmouth Chat API?
