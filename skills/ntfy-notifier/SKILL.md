---
name: ntfy-notifier
description: "Send push notifications to your phone and desktop via ntfy — agent + this skill = user gets instant alerts without a mobile app SDK."
version: 1.0.0
---

# ntfy-notifier

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

## Pitfalls

- **Public topics are public** — Anyone who guesses your topic name can read your notifications. Use a long, random topic name (e.g., `alerts-k7m3x9p2q4`). For sensitive notifications, self-host.
- **No authentication on public server** — The public ntfy.sh server doesn't require auth. Anyone can publish to any topic. If you need auth, self-host and configure access control.
- **Rate limiting on public server** — The public server rate-limits to ~60 requests/hour per IP. For higher volume, self-host.
- **Topic name collisions** — If two people use the topic "test", they'll see each other's notifications. Always use unique topic names.
- **No delivery guarantees** — ntfy is fire-and-forget. If no client is subscribed when you send, the notification is lost (unless you enable message caching on a self-hosted server).
- **Self-hosted needs HTTPS for iOS** — iOS push notifications require HTTPS. If self-hosting, put ntfy behind Caddy or nginx with TLS for iOS clients to receive push in the background.
