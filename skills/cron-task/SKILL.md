---
name: cron-task
description: "Set up scheduled agent tasks with delivery to messaging platforms — agent + this skill = user gets recurring automated work that reports back."
version: 1.0.0
---

# cron-task

Create scheduled tasks that run an agent or script on a recurring schedule and deliver results to a messaging platform (Telegram, Discord, Slack, email). The task runs autonomously — no human needs to be present.

## When to Use

- The user wants a recurring task (daily summary, weekly report, hourly check).
- The user wants to be notified on a schedule (server health check, price alert, feed monitor).
- The user says "run this every day", "schedule a task", "check this hourly", or "send me a daily summary".

## Schedule Syntax

Three formats are supported:

| Format | Example | Meaning |
|---|---|---|
| Duration | `30m`, `2h`, `6h` | Every 30 min, 2 hours, 6 hours |
| Cron expression | `0 9 * * *` | At 9:00 AM every day |
| ISO timestamp | `2026-07-20T09:00:00` | One-shot at a specific time |

Cron fields (5 fields, minute-level granularity):
```
┌───── minute (0-59)
│ ┌───── hour (0-23)
│ │ ┌───── day of month (1-31)
│ │ │ ┌───── month (1-12)
│ │ │ │ ┌───── day of week (0-6, Sunday=0)
0 9 * * *   → every day at 9 AM
*/30 * * * * → every 30 minutes
0 9 * * 1   → every Monday at 9 AM
0 0 1 * *   → first of every month at midnight
```

## Task Types

| Type | Description | Use case |
|---|---|---|
| **Agent-driven** | The agent runs a prompt on schedule | Summarize a feed, write a report, analyze data |
| **Script-only** | A script runs and its output is delivered | Server health check, log scan, metric threshold |

Agent-driven tasks: the scheduler runs the agent with the given prompt. The agent has tool access (web, terminal, file) and produces a response that gets delivered.

Script-only tasks: the scheduler runs a script (bash or Python). The script's stdout is delivered verbatim. No agent, no tokens, no model call. If the script produces no output, nothing is delivered (silent on no-news).

## Delivery

Results are delivered to one or more messaging platforms:

| Platform | Delivery format |
|---|---|
| Telegram | Message to a chat or topic |
| Discord | Message to a channel or thread |
| Slack | Message to a channel |
| Email | Plain-text or HTML email |
| SMS | Short text message |

The delivery includes a header identifying the job, the content, and a footer. The message is not mirrored into the target session — it's a one-way delivery that preserves session integrity.

## Workflow

### Step 1: Define the task

Confirm with the user:
- What should the task do? (the prompt or script)
- How often? (the schedule)
- Where should results go? (the delivery target)

### Step 2: Create the job

**Via the Hermes CLI:**
```bash
hermes cron create "0 9 * * *" --prompt "Check server health and report any issues" --deliver telegram
```

**Via the cronjob tool (in-session):**
```
cronjob(action="create", schedule="0 9 * * *", prompt="Check server health and report any issues", deliver="telegram")
```

### Step 3: Script-only task (if no agent needed)

```
cronjob(
    action="create",
    schedule="*/30m",
    script="scripts/health_check.py",
    no_agent=True,
    deliver="telegram"
)
```

The script runs every 30 minutes. Non-empty stdout is delivered. Empty stdout = silent (nothing sent). Non-zero exit = error alert sent.

### Step 4: Chain jobs (optional)

One job's output can feed into another:

```
cronjob(
    action="create",
    schedule="0 6 * * *",
    prompt="Collect overnight metrics and summarize",
    name="metrics-collector"
)

cronjob(
    action="create",
    schedule="0 9 * * *",
    prompt="Write a daily briefing from the collected metrics",
    context_from=["metrics-collector"],
    deliver="telegram"
)
```

The second job receives the first job's most recent output as context.

### Step 5: Verify

```bash
hermes cron list          # see all jobs
hermes cron run <id>      # trigger immediately for testing
```

## Common Patterns

| Pattern | Schedule | Type | Example |
|---|---|---|---|
| Daily briefing | `0 9 * * *` | Agent | "Summarize overnight activity and news" |
| Hourly health check | `1h` | Script | `health_check.py` — silent unless failure |
| Weekly report | `0 18 * * 5` | Agent | "Generate weekly metrics report" |
| Price alert | `*/30m` | Script | `price_check.py` — silent unless threshold hit |
| Feed monitor | `1h` | Agent | "Check the RSS feed for new entries, notify if any" |

## Pitfalls

- **Silent failures** — A script that crashes with a non-zero exit code sends an error alert. But a script that runs successfully but produces wrong output won't alert. Test scripts before scheduling.
- **Rate limits** — Messaging platforms have rate limits. A task running every minute that sends a message every time will hit Telegram's rate limit within an hour. Only deliver when there's something to say.
- **Long-running tasks** — There's a 3-minute hard interrupt per run. If your prompt or script takes longer, it gets killed. Break long work into chunks or use a background process.
- **Timezone confusion** — Cron expressions run in the host's local timezone by default. Confirm the timezone with the user if the schedule needs to be exact.
- **Duplicate ticks** — A lock file prevents duplicate runs across processes. Don't try to work around it — if a tick is locked, the previous run is still going.
- **Delivering to the wrong chat** — The delivery target must be configured in the gateway. Verify the target exists before scheduling. A misconfigured delivery silently fails.
- **Context bloat in chained jobs** — `context_from` injects the full output of the upstream job. If the upstream produces a large report, the downstream job's prompt gets inflated. Keep upstream outputs concise.
