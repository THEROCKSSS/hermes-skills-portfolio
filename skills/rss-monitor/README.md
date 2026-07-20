# rss-monitor

Monitor RSS and Atom feeds for new entries — get notified when new content appears on any feed you follow.

## What it does

The agent sets up a feed monitoring script that checks your RSS/Atom feeds on a schedule, detects new entries by tracking entry IDs, and sends you a notification (via ntfy, Discord, Telegram, or email) when new content appears. Silent when there's nothing new — you only hear about it when there's something to read.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/rss-monitor/SKILL.md
```

## How to use

```
"Monitor the Hacker News RSS feed and notify me on ntfy when new entries appear"
```

The agent:
1. Verifies the feed URL is valid
2. Writes a monitoring script with entry ID tracking
3. Schedules it with cron (every hour)
4. Tests by running it once — you get a notification for current entries
5. Future runs only notify on new entries

## Prerequisites

- Python 3.8+ with `feedparser` (`pip install feedparser`)
- A notification channel (ntfy, Discord, Telegram, or email)

## Example

```
User: "Watch three tech blogs and text me when they post something about AI"

Agent:
  1. Adds the three feed URLs
  2. Adds keyword filter: ["ai", "llm", "machine learning", "gpt"]
  3. Writes monitor script with ntfy notification
  4. Schedules: crontab 0 * * * * python3 rss-monitor.py
  5. Returns: "Monitoring started. You'll get a push only when a matching post appears."
```

## Filtering options

| Filter | Example |
|---|---|
| Keywords | Only notify if title/summary contains "python" or "ai" |
| Regex | Notify on `\b(funding|series [a-c])\b` |
| No filter | Notify on every new entry |
