# tailscale-deploy

Deploy a service on your Tailscale tailnet so it's privately accessible from any of your devices.

## What it does

The agent deploys a web service — Docker container, local dev server, or anything running on a port — onto your Tailscale tailnet. The service becomes reachable from your laptop, phone, and any other device on your tailnet. No public internet exposure, no port forwarding, no cloud relay.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/tailscale-deploy/SKILL.md
```

## How to use

**You have a local service running on port 8080 and want to access it from your phone:**

```
"Deploy localhost:8080 on my tailnet"
```

The agent runs `tailscale serve --https 8080` and gives you a URL like `https://my-machine.tailnet.ts.net` that opens on any tailnet device.

**You want to deploy a Docker container privately:**

```
"Deploy this Docker image on my tailnet so only I can access it"
```

The agent generates a `docker-compose.yml` with a Tailscale sidecar, brings it up, and verifies accessibility.

## Prerequisites

- [Tailscale](https://tailscale.com) installed and authenticated (`tailscale up`)
- Docker (for container deployments)
- A Tailscale account (free for personal use, up to 100 devices)

## What you get

| Method | Command | Result |
|---|---|---|
| Direct serve | `tailscale serve --https 8080` | HTTPS URL on your tailnet for an existing local service |
| Docker sidecar | `docker compose up -d` with Tailscale sidecar | Private Docker service accessible by hostname on your tailnet |

Both methods keep the service private to your tailnet. No public exposure unless you explicitly use `tailscale funnel`.

## Example

```
User: "I have a Flask app running on localhost:5000. I want to check it from my phone."

Agent:
  1. Verifies tailscale status → connected, machine is "laptop"
  2. Runs: tailscale serve --https 5000
  3. Returns: "Your app is now at https://laptop.tailnet.ts.net — open it on your phone."

User opens the URL on their phone (which is on the same tailnet) → the Flask app loads.
```
