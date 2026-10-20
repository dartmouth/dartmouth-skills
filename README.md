

# Dartmouth skills

Agent Skills ([agentskills.io](https://agentskills.io/specification)) for Dartmouth services. Every markdown file carries [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md) frontmatter, so each file records where it came from and when it should be refreshed.

## Skills

| Skill | What it does |
|---|---|
| [`dartmouth-chat`](skills/dartmouth-chat/SKILL.md) | Helps end users with chat.dartmouth.edu: access, credits, models, privacy, features, Workspace, the API, and coding-agent setup. |
| [`dartmouth-branding`](skills/dartmouth-branding/SKILL.md) | Helps users apply Dartmouth College's official brand and design standards when creating communications. |
| [`research-container-deployment`](skills/research-container-deployment/SKILL.md) | Helps researchers deploy containerized web apps and databases on the Dartmouth Computing Dashboard. |
| [`decision-models`](skills/decision-models/SKILL.md) | Build software with Clef and Jev decision models (`cloudflare.clef`, `clef`, `clef-flash`, `jev`) through Dartmouth's LiteLLM gateway (`https://llm-proxy-preprod.dartmouth.edu/v1/systemone`) for fast calibrated classification, routing, scoring, and selection, plus the `decide` MCP server for coding agents. |

## Install

(change dartmouth-chat to a different skill above if you want)

```bash
# Any agent (Claude Code, Codex, Cursor, Copilot, …) → ./.agents/skills/ 
npx skills add dartmouth/dartmouth-skills --list
npx skills add dartmouth/dartmouth-skills@dartmouth-chat
npx skills add dartmouth/dartmouth-skills@dartmouth-chat -g   # global: ~/.agents/skills/

# Claude Code plugin marketplace
/plugin marketplace add <org>/dartmouth-skills
/plugin install dartmouth-skills@dartmouth-skills
```

Without the CLI, copy `skills/<name>/` into `.agents/skills/`, and symlink it into `.claude/skills/` for Claude Code.

## Layout

```
.claude-plugin/        marketplace.json + plugin.json (Claude plugin distribution)
skills/
  index.md             OKF catalog (okf_version: "0.2")
  log.md               OKF change log
  <skill>/
    SKILL.md           frontmatter: Agent Skills (name, description) + OKF fields
    references/        long-form docs the skill loads on demand
```

See [AGENTS.md](AGENTS.md) for authoring rules.
