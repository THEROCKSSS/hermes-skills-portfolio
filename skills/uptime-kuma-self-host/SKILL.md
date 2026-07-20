---
name: uptime-kuma-self-host
description: "Self-host an uptime monitoring dashboard — agent + this skill = user gets a visual monitoring panel for their services."
version: 1.0.0
---

# uptime-kuma-self-host

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

## Pitfalls

- **Port 3001 conflicts** — If another service uses 3001 (like Forgejo on some setups), change the port mapping in docker-compose.yml.
- **Data volume is the backup** — All monitor configs, history, and settings are in the `uptime-kuma-data` volume. Back it up regularly.
- **No built-in HTTPS** — Uptime Kuma serves HTTP. For HTTPS, put it behind Caddy or a reverse proxy.
- **False positives on HTTP monitors** — A 3xx redirect is not a failure by default, but a 5xx is. Configure the "Accepted Status Codes" field if you need custom thresholds.
- **Notification spam on flapping** — If a service goes up and down rapidly, you'll get many notifications. Set a "Retry" count (e.g., retry 2 times before sending a down notification) to reduce flapping alerts.
- **Push monitor interval** — If your service stops pushing, Kuma waits for the full interval before marking it down. Set the interval to match how often your service checks in.
