# cron-task

Set up scheduled agent tasks that run on a recurring schedule and deliver results to your messaging platform.

## What it does

The agent creates a scheduled task — either agent-driven (runs a prompt) or script-only (runs a script) — that executes on a schedule you define and delivers results to Telegram, Discord, Slack, or email. The task runs autonomously. You get the output in your chat; you don't need to be at a terminal.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/cron-task/SKILL.md
```

## How to use

**Daily server health check delivered to Telegram:**
```
"Send me a server health check every morning at 9 AM on Telegram"
```

The agent creates a cron job with schedule `0 9 * * *`, the health-check prompt, and delivery to Telegram. You get a message at 9 AM every day with the results.

**Silent script that only alerts on failure:**
```
"Check my API every 30 minutes, only message me if it's down"
```

The agent creates a script-only job that runs every 30 minutes. The script exits silently (empty stdout) when the API is healthy. On failure, it outputs an error message that gets delivered to you.

## Schedule formats

| Format | Example | Meaning |
|---|---|---|
| Duration | `30m`, `2h` | Every 30 minutes, every 2 hours |
| Cron | `0 9 * * *` | Daily at 9 AM |
| Cron | `0 18 * * 5` | Every Friday at 6 PM |
| ISO timestamp | `2026-07-20T09:00:00` | One-shot at a specific time |

## Task types

| Type | How it works | Best for |
|---|---|---|
| Agent-driven | Agent runs a prompt with tool access | Summaries, reports, analysis |
| Script-only | Script runs, stdout is delivered | Health checks, threshold alerts, log scans |

Script-only tasks are silent when there's nothing to report (empty stdout = no message sent). This is the watchdog pattern — only alert on failure.

## Example

```
User: "Check my website every 5 minutes and text me if it's down"

Agent:
  1. Creates a script-only job: schedule */5m
  2. Script: curl -sf https://mysite.com > /dev/null || echo "SITE DOWN"
  3. Delivery: SMS
  4. Tests: hermes cron run <id> → "SITE DOWN" (if actually down) or silent
  5. Returns: "Monitoring started. You'll get a text only if the site is unreachable."
```
