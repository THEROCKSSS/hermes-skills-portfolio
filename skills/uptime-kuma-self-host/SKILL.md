---
name: uptime-kuma-self-host
description: Use when the user wants to self-host uptime monitoring for their services (HTTP, TCP, DNS, ping) with alerting to Discord/Slack/email/webhook, or wants a public status page, or says "set up uptime monitoring" / "I want to know when my site goes down".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [uptime-kuma, uptime-monitoring, docker, status-page, alerting]
    related_skills: [ntfy-notifier, caddy-reverse-proxy, docker-umbrella]
---

# uptime-kuma-self-host

## Overview

Deploy Uptime Kuma — a self-hosted monitoring tool that tracks the uptime of your services (HTTP, TCP, DNS, ping) and sends alerts when something goes down. It runs as a Docker container with a web UI for managing monitors and viewing status pages.

## When to Use

- The user wants to monitor their self-hosted services.
- The user wants uptime alerts sent to Discord, Slack, email, or webhook.
- The user wants a public status page for their services.
- The user says "set up uptime monitoring", "I want to know when my site goes down", or "monitor my services".

## Prerequisites

- Docker and Docker Compose installed
- A free port (default: 3001)

## Docker Deployment

### Step 1: Create the deployment

```yaml
# docker-compose.yml
version: "3"
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma-data:/app/data

volumes:
  uptime-kuma-data:
```

### Step 2: Start

```bash
docker compose up -d
```

### Step 3: Initial setup

Open `http://localhost:3001` in a browser. Create an admin account (username + password). This is a one-time setup.

### Step 4: Add monitors via the UI

1. Click "Add New Monitor"
2. Choose a monitor type
3. Enter the target URL/host
4. Set the check interval
5. Save

### Step 5: Add notifications

1. Go to Settings → Notifications
2. Add a notification channel (Discord webhook, Slack webhook, email, etc.)
3. Test the notification
4. Assign the notification to monitors

## Monitor Types

| Type | What it checks | Example |
|---|---|---|
| HTTP(s) | Is a URL responding with 2xx? | `https://mysite.com` |
| HTTP(s) - Keyword | Does the response contain a keyword? | `https://mysite.com` looking for "OK" |
| TCP Port | Is a TCP port open? | `mysite.com:5432` |
| DNS | Does a domain resolve? | `mysite.com` → A record |
| Ping | Does a host respond to ICMP? | `192.168.1.1` |
| Push | Wait for a push (passive monitor) | `https://kuma:3001/api/push/STATUS?msg=OK&ping=100` |
| Docker Container | Is a Docker container running? | Container name via Docker socket |

## Notification Channels

| Channel | Setup |
|---|---|
| Discord | Webhook URL from Discord channel settings |
| Slack | Webhook URL from Slack app config |
| Email | SMTP server + credentials |
| Webhook | Custom HTTP POST on status change |
| Telegram | Bot token + chat ID |
| ntfy | ntfy.sh topic URL |
| Signal | via signal-cli-rest-api |
| Pushover | User key + app key |

## Status Pages

Uptime Kuma can generate public status pages showing the uptime of your services:

1. Go to Status Pages → Add Status Page
2. Name it (e.g., "My Services")
3. Add monitors to display
4. Set a custom domain (optional)
5. Share the URL: `http://localhost:3001/status/my-services`

## API (Push Monitors)

Push monitors are passive — they wait for your service to "check in":

```bash
# Your service calls this URL on a schedule
# If Kuma doesn't hear from it within the interval, it's marked down
curl "http://localhost:3001/api/push/ABCD1234?msg=OK&ping=42"
```

Use this for services behind firewalls that Kuma can't reach directly.

## Monitoring a Docker Host

To monitor Docker containers on the host, bind-mount the Docker socket:

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    volumes:
      - uptime-kuma-data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock  # for container monitoring
```

Then add a "Docker Container" monitor type pointing to the container name.

## Common Pitfalls

1. **Port 3001 collides with another service.** Forgejo and some other self-hosted tools default
   to nearby ports. Check `docker ps` / `netstat` first and remap in `docker-compose.yml` if
   3001 is taken.
2. **Treating the data volume as disposable.** All monitor configs, history, and notification
   settings live only in the `uptime-kuma-data` volume — there's no external config file to
   fall back on. Back it up regularly.
3. **Assuming HTTPS is built in.** Uptime Kuma serves plain HTTP. Put it behind Caddy or another
   reverse proxy if the status page or dashboard needs to be reachable over TLS.
4. **Not configuring "Accepted Status Codes."** A 3xx redirect is treated as healthy by default;
   only 5xx (and non-matching codes outside the accepted set) count as down. Set this explicitly
   if the monitored service redirects normally.
5. **Leaving "Retry" at its default on a flapping service.** A service that goes up/down rapidly
   sends one notification per transition. Raise the retry count (e.g., 2 failed checks before
   alerting) to suppress flap noise.
6. **Setting a push-monitor interval shorter than the service's real check-in cadence.** Kuma
   waits the full interval before marking a push monitor down — if the interval doesn't match how
   often the service actually pushes, you get false "down" alerts or delayed detection.

## Verification Checklist

- [ ] `docker compose ps` shows `uptime-kuma` running and `http://localhost:3001` loads the
      dashboard.
- [ ] Admin account created (one-time setup completed, not left on the setup screen).
- [ ] At least one monitor added and showing a status (up/down/pending), not stuck on "PENDING".
- [ ] Test notification sent successfully from Settings → Notifications before assigning it to
      monitors.
- [ ] `uptime-kuma-data` volume confirmed present (`docker volume inspect`) and included in the
      user's backup plan.
