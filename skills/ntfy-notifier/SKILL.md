---
name: ntfy-notifier
description: Use when the user wants push notifications to their phone or desktop from a script, cron job, or agent task — via ntfy's HTTP pub/sub topics — without setting up Firebase, APNS, or a mobile SDK. Covers the public ntfy.sh server and self-hosting via Docker.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [notifications, ntfy, push, pub-sub, alerting, self-hosted]
    related_skills: [webhook-receiver, uptime-kuma-self-host, cron-task]
---

# ntfy-notifier

## Overview

Send push notifications to any device using ntfy — a simple HTTP-based pub/sub notification service. No SDK, no mobile app integration, no APNS/FCM setup. Just HTTP POST to a topic URL and the notification appears on any subscribed device.

## When to Use

- The user wants push notifications for their scripts or agent tasks.
- The user wants alerts on their phone when a cron job fails or a deploy completes.
- The user wants a simple notification channel without setting up Firebase, APNS, or email.
- The user says "send me a notification", "alert my phone", or "I want push notifications from my scripts".

## Setup

### Option A: Public server (fastest)

Use the public ntfy server at `https://ntfy.sh`. No setup needed — just pick a topic name and start sending.

1. Install the ntfy app on your phone:
   - **iOS**: App Store → "ntfy"
   - **Android**: Play Store → "ntfy" or F-Droid
2. Open the app, tap "+", subscribe to a topic (e.g., `my-alerts-abc123`)
3. Send a notification to that topic from any device

### Option B: Self-hosted (private)

```yaml
# docker-compose.yml
version: "3"
services:
  ntfy:
    image: binwiederhier/ntfy:latest
    container_name: ntfy
    restart: unless-stopped
    ports:
      - "8090:80"
    volumes:
      - ntfy-data:/var/lib/ntfy
    command: serve

volumes:
  ntfy-data:
```

```bash
docker compose up -d
```

In the phone app, set the server URL to `http://your-server:8090` and subscribe to a topic.

## Sending Notifications

### curl (simplest)

```bash
# Basic notification
curl -d "Deploy complete" ntfy.sh/my-alerts-abc123

# With title and priority
curl \
  -H "Title: Server Alert" \
  -H "Priority: high" \
  -H "Tags: warning,server" \
  -d "CPU usage at 95%" \
  ntfy.sh/my-alerts-abc123
```

### Python

```python
import requests

# Basic
requests.post("https://ntfy.sh/my-alerts-abc123", data="Build complete")

# With options
requests.post("https://ntfy.sh/my-alerts-abc123",
    data="Disk space critical: 2% remaining",
    headers={
        "Title": "Disk Alert",
        "Priority": "urgent",
        "Tags": "warning,disk",
        "Actions": "view, Open Dashboard, https://grafana.example.com"
    }
)
```

### With actions (buttons in the notification)

```bash
curl \
  -H "Title: Deploy Ready" \
  -H "Actions: view, Open PR, https://github.com/me/repo/pull/42; http, Approve, https://api.example.com/approve" \
  -d "PR #42 is ready for review" \
  ntfy.sh/my-alerts-abc123
```

The notification shows buttons: "Open PR" (opens URL) and "Approve" (sends HTTP request).

## Topics and Subscriptions

Topics are pub/sub channels identified by a name. No registration — anyone with the topic name can publish or subscribe.

- **Pick a unique topic name** — `my-alerts-abc123` is better than `alerts` (which anyone could read)
- **Subscribe on your phone** — open the ntfy app, add the topic
- **Subscribe via CLI** — `ntfy subscribe my-alerts-abc123`
- **Subscribe via curl** — `curl -s ntfy.sh/my-alerts-abc123/sse` (Server-Sent Events stream)

## Priority Levels

| Priority | Behavior |
|---|---|
| `default` | Normal notification, no sound |
| `high` | Notification sound, may bypass Do Not Disturb |
| `urgent` | Notification sound, bypasses Do Not Disturb, may repeat |

```bash
curl -H "Priority: urgent" -d "Server is DOWN" ntfy.sh/my-alerts-abc123
```

## Common Patterns

| Pattern | Command |
|---|---|
| Script success | `curl -d "Backup complete" ntfy.sh/my-topic` |
| Script failure | `curl -H "Priority: high" -d "Backup FAILED" ntfy.sh/my-topic` |
| Cron job heartbeat | `curl -d "Job ran OK" ntfy.sh/my-topic` (send after each run) |
| Deploy notification | `curl -H "Title: Deploy" -d "v1.2.3 live" ntfy.sh/my-topic` |
| With action button | `curl -H "Actions: view, Logs, https://..." -d "Build failed" ntfy.sh/my-topic` |

## Common Pitfalls

1. **Public topics are public.** Anyone who guesses your topic name can read your notifications. Use a long, random topic name (e.g., `alerts-k7m3x9p2q4`), never a plain word like `alerts`. For sensitive notifications, self-host.
2. **No authentication on the public server.** The public ntfy.sh server doesn't require auth — anyone can publish to any topic they can guess. If you need auth, self-host and configure access control.
3. **Rate limiting on the public server.** ntfy.sh rate-limits to roughly 60 requests/hour per IP. For higher volume (e.g., per-line log streaming), self-host instead.
4. **Topic name collisions.** Two unrelated users on the same topic name (e.g., both picking "test") will see each other's notifications. Always use a unique, hard-to-guess topic name.
5. **No delivery guarantees by default.** ntfy is fire-and-forget — if no client is subscribed when a message is sent, it's lost unless message caching is enabled on a self-hosted server.
6. **Self-hosted push silently fails on iOS without HTTPS.** iOS requires HTTPS for background push delivery. Put a self-hosted ntfy instance behind Caddy or nginx with TLS, or iOS clients won't receive notifications when the app is backgrounded.

## Verification Checklist

- [ ] A test `curl -d "test" ntfy.sh/<topic>` (or self-hosted equivalent) returns HTTP 200
- [ ] The notification actually arrives on the subscribed device/app, not just a 200 from the API
- [ ] Topic name is long/random enough that it isn't guessable (not `alerts`, `test`, `notify`)
- [ ] Priority level matches the alert's urgency (`urgent` for outages, `default` for routine heartbeats)
- [ ] For self-hosted setups: the server is reachable over HTTPS if iOS clients are involved
- [ ] Any `Actions` buttons open the correct URL / fire the correct HTTP request when tapped
