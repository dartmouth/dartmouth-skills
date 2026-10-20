---
okf_version: "0.2"
---

# Skills

* [dartmouth-chat](dartmouth-chat/SKILL.md) - End-user guide to Dartmouth Chat (chat.dartmouth.edu): access, credits, models, privacy, features, Workspace, API, coding agents.
* [dartmouth-branding](dartmouth-branding/SKILL.md) - helps users apply Dartmouth College's official brand and design standards when creating communications
* [research-container-deployment](research-container-deployment/SKILL.md) - End-user guide to deploying containerized research apps on the Dartmouth Computing Dashboard: projects, databases, image builders, Container Deploy, Kubernetes Deploy.
* [decision-models](decision-models/SKILL.md) - Build software with Clef and Jev decision models (`cloudflare.clef`, `clef`, `clef-flash`, `jev`) through Dartmouth's LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu/v1/systemone`) for fast calibrated routing, classification, scoring, and selection, plus the `decide` MCP server for coding agents.

# dartmouth-chat references

* [Connecting coding agents](dartmouth-chat/references/coding-agents.md) - Full client configs for Claude Code, OpenCode, Kilo Code and Mistral Vibe.

# research-container-deployment references

* [Todo app walkthrough](research-container-deployment/references/todo-walkthrough.md) - Workshop end-to-end example: Streamlit Todo app + PostgreSQL on Container Deploy.
* [Kubernetes manifests](research-container-deployment/references/kubernetes-manifests.md) - What Container Deploy generates (Dashboard-managed), the Kubernetes Deploy sample (user-edited), adapting it, sealing secrets with kubeseal.

# decision-models references

* [AGENTS.md template — LLM vs decision model guidance](decision-models/references/agents-md-template.md) - Drop-in AGENTS.md rules for projects that combine LLMs with Clef decision models.
* [decide MCP server — decision models as a coding-agent tool](decision-models/references/decide-mcp.md) - Install and configure the `decide` FastMCP 4 server for Claude Code, Codex, goose, OpenCode v2, and Cursor against Dartmouth's LiteLLM gateway.
