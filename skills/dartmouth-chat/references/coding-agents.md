---
type: Reference
title: Connecting coding agents to the Dartmouth Chat API
description: Full client configs for Claude Code, OpenCode, Kilo Code and Mistral Vibe against chat.dartmouth.edu/api.
tags: [dartmouth-chat, api, claude-code, opencode, kilo-code, mistral-vibe]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-05T09:09:52-04:00 }
stale_after: 2027-01-05T00:00:00Z
status: draft
sources:
  - id: rc-clients
    resource: https://rc.dartmouth.edu/ai/online-resources/connecting-ai-clients
    title: How do I connect my coding tool to Dartmouth Chat API?
    author: team:dartmouth-rcd
    last_modified: 2026-05-20T00:00:00Z
---

# Connecting coding agents

All of these clients use the same settings:[^rc-clients]

- **Base URL:** `https://chat.dartmouth.edu/api`
- **Key:** your API key, created at Profile › Settings › Account › API Key. To use a Credit Group's budget, use its Virtual Key instead.
- **Model IDs:** must exactly match `GET https://chat.dartmouth.edu/api/models`. The IDs below were current when the source page was written. Check them before use.

## Claude Code

Install it first: https://code.claude.com/docs/en/overview

On macOS, store the key in Keychain. The command prompts for the key twice:

```bash
security add-generic-password -s "dartmouth-chat-api-key" -a "$USER" -w
mkdir -p ~/.claude
```

Merge this into `~/.claude/settings.json`. If the file already exists, edit it; don't append with `>>`, which produces invalid JSON.

```json
{
  "apiKeyHelper": "security find-generic-password -s \"dartmouth-chat-api-key\" -w",
  "env": {
    "ANTHROPIC_BASE_URL": "https://chat.dartmouth.edu/api",
    "ANTHROPIC_MODEL": "anthropic.claude-sonnet-4-6",
    "DISABLE_NON_ESSENTIAL_MODEL_CALLS": "1",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"
  }
}
```

Then run `claude` in any directory. For the VS Code extension, set its default model to `anthropic.claude-sonnet-4-6`.

## OpenCode

Install it first: https://opencode.ai/docs#install

```bash
mkdir -p ~/.config/opencode && cat << 'EOF' > ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": { "*": "ask", "edit": "allow" },
  "provider": {
    "Dartmouth": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Dartmouth Chat",
      "options": {
        "baseURL": "https://chat.dartmouth.edu/api",
        "apiKey": "your_api_key_goes_here",
        "timeout": 600000,
        "chunkTimeout": 300000
      },
      "models": {
        "openai.gpt-oss-120b": { "name": "GPT-OSS 120b", "attachment": true, "reasoning": true, "tool_call": true },
        "google.gemma-4-31B-it": { "name": "Gemma 4 31b", "attachment": true, "reasoning": true, "tool_call": true,
          "limit": { "context": 262144, "output": 262144 } },
        "qwen.qwen3.5-122b": { "name": "Qwen3.5 122b", "attachment": true, "tool_call": true },
        "anthropic.claude-haiku-4-5-20251001": { "name": "Claude Haiku 4.5", "attachment": true, "reasoning": true, "tool_call": true },
        "anthropic.claude-sonnet-4-6": { "name": "Claude Sonnet 4.6", "attachment": true, "reasoning": true, "tool_call": true },
        "anthropic.claude-opus-4-6": { "name": "Claude Opus 4.6", "attachment": true, "tool_call": true },
        "mistral.devstral-2512": { "name": "Mistral Devstral 2", "attachment": true }
      }
    }
  }
}
EOF
```

This overwrites any existing config. If you already have one, merge the `provider` block into it instead.

Run `opencode`, then press ctrl-p and choose a Dartmouth Chat model.

## Kilo Code (VS Code)

1. Install **Kilo Code** from the VS Code Marketplace (`kilocode.Kilo-Code`).
2. Click the Kilo Code icon in the activity bar, then go to **Settings › Providers**. At the bottom, choose **Custom provider › Connect** and enter:
   - Provider ID: `dartmouth-chat`
   - Display Name: `Dartmouth Chat`
   - Base URL: `https://chat.dartmouth.edu/api`
   - API Key: your key
   - Models: a Claude or GPT model plus a local one such as `openai.gpt-oss-120b`. Click **Add model(s)**.
3. Click **Submit**. To find the models, type "Dartmouth" in the Model Selector.

## Mistral Vibe

Install it first: https://github.com/mistralai/mistral-vibe

```bash
mkdir -p ~/.vibe && cat << 'EOF' > ~/.vibe/config.toml
auto_compact_threshold = 200000

[[providers]]
name = "Dartmouth Chat"
api_base = "https://chat.dartmouth.edu/api"
api_style = "openai"
backend = "generic"

[[models]]
name = "anthropic.claude-sonnet-4-6"
provider = "Dartmouth Chat"
alias = "sonnet-4.6"
temperature = 1
input_price = 3000.0
output_price = 15000.0

[[models]]
name = "openai.gpt-oss-120b"
provider = "Dartmouth Chat"
alias = "gpt-oss"
temperature = 0.5
input_price = 0.0
output_price = 0.0
EOF

echo 'MISTRAL_API_KEY=your_dartmouth_chat_api_key' > ~/.vibe/.env
```

The source page also lists `anthropic.claude-haiku-4-5-20251001`, `mistral.mistral-large-2512` and `mistral.devstral-2512`. The source page writes the env path as `~/.vibe/.env/`; the trailing slash is a typo.

Run `vibe` in any directory.

# Troubleshooting

| Symptom | Fix |
|---|---|
| `model not found` | Copy the ID exactly from `/api/models`, including the `provider.` prefix. |
| 401 | Regenerate the key in Settings › Account. |
| 429 / out of credits | Switch to a local model (e.g. `openai.gpt-oss-120b`) or set up a Credit Group. |
| Timeouts on long generations | Raise the client timeout (OpenCode `timeout`/`chunkTimeout`, Claude Code `API_TIMEOUT_MS`). |

[^rc-clients]: How do I connect my coding tool to Dartmouth Chat API?
