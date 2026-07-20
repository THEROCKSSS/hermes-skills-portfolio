# uptime-kuma-self-host

Self-host an uptime monitoring dashboard that tracks your services and alerts you when they go down.

## What it does

The agent deploys Uptime Kuma with Docker, creates an admin account, and helps you add monitors for your services. You get a web UI showing real-time status, historical uptime, and response times. Alerts go to Discord, Slack, email, Telegram, or a webhook when a service goes down or comes back up.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/uptime-kuma-self-host/SKILL.md
```

## How to use

```
"Set up uptime monitoring for my three web services with Discord alerts"
```

The agent:
1. Creates a docker-compose.yml with Uptime Kuma
2. Starts the container on port 3001
3. Opens the setup page for your admin account
4. Adds HTTP monitors for your services
5. Configures Discord webhook notifications

## Prerequisites

- Docker and Docker Compose
- A free port (default: 3001)

## What you get

| Component | URL | Notes |
|---|---|---|
| Dashboard | `http://localhost:3001` | Web UI for all monitors |
| Status page | `http://localhost:3001/status/<name>` | Public uptime page |
| Push API | `http://localhost:3001/api/push/<id>` | For passive monitors |

## Monitor types

| Type | Example |
|---|---|
| HTTP(s) | `https://mysite.com` — checks for 2xx response |
| TCP Port | `mysite.com:5432` — checks port is open |
| Ping | `192.168.1.1` — ICMP echo |
| DNS | `mysite.com` — checks resolution |
| Push | Passive — your service calls Kuma's API |
| Docker | Container running check via Docker socket |

## Example

```
User: "Monitor my blog and API, alert me on Discord if either goes down"

Agent:
  1. Deploys Uptime Kuma on port 3001
  2. Adds HTTP monitor: https://myblog.com (check every 60s)
  3. Adds HTTP monitor: https://api.myblog.com/health (check every 30s)
  4. Adds Discord notification webhook
  5. Returns: "Monitoring started. Dashboard at http://localhost:3001"
```
