---
name: rss-monitor
description: Use when the user wants to be notified when a blog, news feed, or other RSS/Atom source publishes new content, or wants to track updates from multiple feeds in one place — triggers include "monitor this RSS feed", "notify me when this blog updates", or "watch for new entries".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [rss, atom, feed-monitoring, notifications, cron, feedparser]
    related_skills: [ntfy-notifier, cron-task, email-send, telegram-bot-build, discord-bot-build]
---

# rss-monitor

## Overview

Monitor RSS and Atom feeds for new entries. The agent sets up a feed monitoring loop that checks feeds on a schedule, detects new entries, and delivers notifications via your preferred channel (Telegram, Discord, email, ntfy).

## When to Use

- The user wants to know when a blog publishes a new post.
- The user wants to monitor news feeds for specific topics.
- The user wants to track updates from multiple sources in one place.
- The user says "monitor this RSS feed", "notify me when this blog updates", or "watch for new entries".

## Prerequisites

- Python 3.8+ with `feedparser` installed: `pip install feedparser`
- A notification channel (ntfy, Telegram, Discord, or email)

## Feed Discovery

### Find the RSS/Atom feed for a site

```bash
# Check for <link rel="alternate"> in the HTML
curl -s https://example.com | grep -oP '(?<=href=")[^"]*(rss|atom|feed)[^"]*'

# Common feed paths to try
curl -s -o /dev/null -w "%{http_code}" https://example.com/feed/
curl -s -o /dev/null -w "%{http_code}" https://example.com/rss/
curl -s -o /dev/null -w "%{http_code}" https://example.com/atom.xml
curl -s -o /dev/null -w "%{http_code}" https://example.com/feed.xml
```

### Verify a feed is valid

```python
import feedparser

feed = feedparser.parse("https://example.com/feed/")
print(f"Feed: {feed.feed.get('title', 'Unknown')}")
print(f"Entries: {len(feed.entries)}")
for entry in feed.entries[:3]:
    print(f"  - {entry.title}")
```

## Monitoring Loop

### Simple monitor script

```python
#!/usr/bin/env python3
"""Monitor RSS feeds for new entries. Notifies via ntfy on new content."""
import feedparser
import requests
import json
import os
import time
from datetime import datetime, timezone

FEEDS = [
    "https://blog.example.com/feed/",
    "https://news.ycombinator.com/rss",
]

STATE_FILE = os.path.expanduser("~/.rss-monitor-state.json")
NTFY_TOPIC = "rss-alerts-abc123"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def notify(title, body):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode('utf-8'),
        headers={"Title": title, "Tags": "rss,new"}
    )

def check_feeds():
    state = load_state()
    new_entries = []

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        seen_ids = state.get(feed_url, [])

        for entry in feed.entries:
            entry_id = entry.get('id', entry.get('link', ''))
            if entry_id not in seen_ids:
                new_entries.append({
                    'feed': feed.feed.get('title', feed_url),
                    'title': entry.title,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', '')
                })

        # Update seen IDs (keep last 100)
        all_ids = [e.get('id', e.get('link', '')) for e in feed.entries]
        state[feed_url] = list(set(seen_ids + all_ids))[-100:]

    save_state(state)

    for entry in new_entries:
        title = f"New: {entry['title'][:60]}"
        body = f"{entry['feed']}\n{entry['link']}"
        notify(title, body)
        print(f"New entry: {entry['feed']} — {entry['title']}")

    if not new_entries:
        print(f"No new entries ({datetime.now().isoformat()})")

if __name__ == "__main__":
    check_feeds()
```

### Schedule with cron

```bash
# Check every hour
crontab -e
# Add:
0 * * * * /usr/bin/python3 /path/to/rss-monitor.py

# Or with Hermes cron
hermes cron create "1h" --prompt "Run the RSS monitor script at scripts/rss-monitor.py and report any new entries"
```

## Change Detection

The monitor tracks seen entry IDs to detect what's new. Two approaches:

| Approach | How | Tradeoff |
|---|---|---|
| **Entry ID tracking** | Store entry IDs in a JSON state file | Reliable, but misses entries if IDs change |
| **Timestamp threshold** | Notify on entries newer than last check | Simpler, but misses backdated entries |

The script above uses entry ID tracking — more reliable for most feeds.

## Filtering

### Keyword filter

```python
KEYWORDS = ["python", "ai", "agents", "llm"]

def matches_keywords(entry):
    text = (entry.title + " " + entry.get('summary', '')).lower()
    return any(kw in text for kw in KEYWORDS)

# In check_feeds, before notifying:
if matches_keywords(entry):
    notify(title, body)
```

### Regex filter

```python
import re

PATTERNS = [
    re.compile(r'\b(funding|series [a-c])\b', re.IGNORECASE),
    re.compile(r'\b(security|vulnerability|cve)\b', re.IGNORECASE),
]

def matches_patterns(entry):
    text = entry.title + " " + entry.get('summary', '')
    return any(p.search(text) for p in PATTERNS)
```

## Notification Delivery

| Channel | How |
|---|---|
| **ntfy** | `requests.post(f"https://ntfy.sh/{topic}", data=body, headers={"Title": title})` |
| **Discord** | Webhook URL: `requests.post(discord_webhook_url, json={"content": f"**{title}**\n{body}"})` |
| **Telegram** | Bot API: `requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": f"{title}\n{body}"})` |
| **Email** | See the `email-send` skill |

## Common Pitfalls

1. **Feed URL changes silently.** Sites sometimes change their feed URL without redirecting — a 404 from a previously-working feed means the site needs a new feed URL found.
2. **Polling too frequently.** Most publishers don't update more than a few times per day — checking every 15-30 minutes is sufficient; checking every minute risks the monitor's IP getting blocked.
3. **Entry ID instability causing duplicates.** Some feeds don't provide stable entry IDs — if `id` changes between checks, fall back to using the entry link as the dedup key.
4. **Partial feed content.** Some feeds only include a summary, not the full article — follow the entry link and scrape the page if full text is needed.
5. **Inconsistent date fields.** Feeds vary between `published`, `updated`, and `created` — use `feedparser`'s parsed fields (`entry.published_parsed`, a `time.struct_time`) rather than string-parsing.
6. **State file corruption causing re-notification.** A corrupted state JSON makes the monitor treat every entry as new — handle JSON decode errors gracefully and fall back to a fresh state rather than crashing.
7. **Authenticated feeds.** Private Substacks and paid newsletters require auth headers — fetch with `requests` using auth, then pass the response text to `feedparser.parse()` instead of the URL.

## Verification Checklist

- [ ] Feed URL verified valid with `feedparser.parse()` returning a non-empty `entries` list
- [ ] State file (`~/.rss-monitor-state.json` or equivalent) created and persists entry IDs across runs
- [ ] A test run against a feed with a known new entry actually triggers a notification
- [ ] Polling interval is 15+ minutes (not aggressive enough to risk IP blocking)
- [ ] Notification channel (ntfy/Discord/Telegram/email) confirmed to deliver by checking for the message
- [ ] Keyword/regex filters (if used) tested against both matching and non-matching sample entries
