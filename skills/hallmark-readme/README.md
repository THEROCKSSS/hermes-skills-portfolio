# hallmark-readme

Write a README that doesn't sound like an LLM generated it.

## What it does

The agent reads your project and writes a README that follows anti-AI-slop rules: no filler phrases, no invented metrics, no templated structure, honest about limitations, concrete examples, real voice. The result reads like a human wrote it because it follows the patterns that distinguish human writing from LLM defaults.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/hallmark-readme/SKILL.md
```

## How to use

```
"Write a README for my project"
```

The agent reads your project files, identifies the audience, and writes a README with:
- A one-sentence description of what it does (not what it is)
- Install instructions near the top
- One concrete, runnable example
- Real section headings (not generic "Features" / "Getting Started")
- A limitations section naming what the project doesn't do
- No filler, no invented metrics, no badge spam

## What it checks for

| AI tell | This skill |
|---|---|
| "empower", "seamless", "leverage", "robust" | Banned — deleted on sight |
| "Trusted by 50,000+ developers" | Never invented — omitted if no real number exists |
| Title → Badges → Features → Installation → Usage | Structure varies by project type, not templated |
| No limitations section | Always includes real limitations |
| "This project enables developers to..." | First person or direct second person, not corporate third |
| `my-tool --input <file>` | Concrete examples with real values, not placeholders |

## Example

**Before (AI-generated):**

```markdown
# Awesome Tool

A powerful, comprehensive tool that empowers developers to seamlessly leverage
cutting-edge features. Built with love. Trusted by 50,000+ teams worldwide.

## Features
- Robust architecture
- Seamless integration
- Comprehensive documentation
```

**After (hallmark-readme):**

```markdown
# tailscale-deploy

Deploy a service on your Tailscale tailnet so it's privately accessible from any of your devices.

## What it does

The agent deploys a web service onto your Tailscale tailnet. The service becomes reachable
from your laptop, phone, and any other device on your tailnet.

## Install

  hermes skills install https://github.com/...

## Example

  User: "Deploy localhost:8080 on my tailnet"
  Agent: runs tailscale serve --https 8080
  Result: https://my-machine.tailnet.ts.net

## Limitations

- Requires Tailscale installed and authenticated on both the host and the accessing device.
- `tailscale serve` is tailnet-only; `tailscale funnel` exposes to the public internet.
```

The second one sounds like a person wrote it because it follows the rules: no filler, no invented numbers, real structure, concrete example, honest limitations.
