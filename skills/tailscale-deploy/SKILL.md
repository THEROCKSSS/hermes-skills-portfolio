---
name: tailscale-deploy
description: Use when the user wants a service reachable privately from their own devices (laptop, phone) without exposing it to the public internet, wants to share a local dev server with a specific person on their tailnet, or says "deploy this on my tailnet" / "make this accessible via Tailscale".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tailscale, vpn, tailnet, wireguard, private-networking, docker-sidecar]
    related_skills: [caddy-reverse-proxy, docker-umbrella]
---

# tailscale-deploy

## Overview

Deploy a service on a Tailscale tailnet. The service becomes privately accessible from any device on the user's tailnet — no public exposure, no port forwarding, no cloud relay.

## When to Use

- The user wants to run a web service and access it from their laptop, phone, or other machines without exposing it to the internet.
- The user wants to share a local dev server with someone on their tailnet.
- The user wants to deploy a Docker service with private network access.
- The user says "deploy this on my tailnet", "make this accessible via Tailscale", or "I want to access this from my phone".

## Prerequisites

1. **Tailscale installed** — check with `tailscale status`. If not installed:
   - **Linux**: `curl -fsSL https://tailscale.com/install.sh | sh`
   - **macOS**: `brew install tailscale` or install from the App Store
   - **Windows**: download from https://tailscale.com/download

2. **Tailscale authenticated** — `tailscale up` if not already authenticated. The user needs a Tailscale account (free for personal use, up to 100 devices).

3. **Docker installed** — for container-based deployments. Check with `docker --version`.

## Workflow

### Step 1: Verify Tailscale is running

```bash
tailscale status
```

If the output shows the machine as `idle` or not connected, run:

```bash
sudo tailscale up
```

On Windows, run `tailscale up` in an elevated terminal.

### Step 2: Choose a deployment method

Two methods, depending on what the user is deploying:

**Method A — Direct serve (existing local service):**
The service is already running on a local port (e.g., `localhost:8080`). Use `tailscale serve` to expose it over the tailnet with HTTPS.

```bash
# Expose localhost:8080 over the tailnet with HTTPS
tailscale serve --https 8080
```

The service is now accessible at `https://<machine-name>.<tailnet-name>.ts.net` from any device on the tailnet.

To check what's being served:
```bash
tailscale serve status
```

To stop serving:
```bash
tailscale serve --https off
```

**Method B — Docker with Tailscale sidecar:**
Deploy a Docker container with a Tailscale sidecar that joins the tailnet and routes traffic to the service.

Create a `docker-compose.yml`:

```yaml
version: "3.8"
services:
  app:
    image: your-app-image
    restart: unless-stopped
    networks:
      - tsnet

  tailscale:
    image: tailscale/tailscale:latest
    restart: unless-stopped
    hostname: my-service
    environment:
      - TS_AUTHKEY=tskey-auth-XXXXX  # generate at https://login.tailscale.com/admin/settings/keys
    volumes:
      - tailscale-state:/var/lib/tailscale
    networks:
      - tsnet

networks:
  tsnet:
    driver: bridge

volumes:
  tailscale-state:
```

Then:
```bash
docker compose up -d
```

The service is accessible at `http://my-service.<tailnet-name>.ts.net:PORT` from any tailnet device.

### Step 3: Verify accessibility

From another device on the same tailnet:

```bash
# Method A
curl https://<machine-name>.<tailnet-name>.ts.net

# Method B
curl http://my-service.<tailnet-name>.ts.net:PORT
```

Or just open the URL in a browser on any tailnet device.

### Step 4: Clean up (when the user wants to stop)

```bash
# Method A
tailscale serve --https off

# Method B
docker compose down
```

## Tailscale Serve Reference

| Command | What it does |
|---|---|
| `tailscale serve --https PORT` | Expose localhost:PORT over HTTPS on the tailnet |
| `tailscale serve --http PORT` | Expose localhost:PORT over HTTP on the tailnet |
| `tailscale serve --https off` | Stop serving |
| `tailscale serve status` | Show what's being served |
| `tailscale funnel PORT` | Expose to the PUBLIC internet (not tailnet-only) — use with caution |

**Important:** `tailscale serve` is tailnet-only (private). `tailscale funnel` is public internet exposure. Most users want `serve`, not `funnel`. Always confirm with the user before using `funnel`.

## Common Pitfalls

1. **Docker sidecar `TS_AUTHKEY` expired or non-ephemeral.** Auth keys expire and non-ephemeral
   keys leave stale devices in the admin console after teardown. Generate a fresh ephemeral key
   at https://login.tailscale.com/admin/settings/keys for container use.
2. **Assuming `tailscale serve --https 8080` serves on localhost:8080.** It actually serves on
   port 443 of the *tailnet* interface; the local service keeps its original port. Don't look for
   it on `localhost:443`.
3. **Putting the app and the Tailscale sidecar on the default Docker network.** The sidecar can't
   route to the app unless both share a custom bridge network, as in the compose example — the
   default network isolates them.
4. **Reaching for `tailscale funnel` when `serve` was meant.** `funnel` exposes the service to the
   entire public internet; `serve` is tailnet-only. Default to `serve` and confirm explicitly
   before ever using `funnel`.
5. **Not checking `tailscale status` after `tailscale up`.** If the machine doesn't appear in the
   tailnet device list, `tailscale up` didn't complete — re-authenticate rather than assuming the
   service is reachable.
6. **Corporate/restrictive networks blocking WireGuard.** If UDP 41641 outbound is blocked,
   Tailscale falls back to its DERP relay automatically, but performance suffers — flag this to
   the user rather than treating a slow connection as a bug.

## Verification Checklist

- [ ] `tailscale status` shows the machine as connected (not `idle`) before deploying.
- [ ] Service responds to `curl` from a *second* device on the tailnet, not just from localhost
      on the host machine.
- [ ] Confirmed with the user whether `serve` (tailnet-only) or `funnel` (public) was intended —
      `funnel` was never used without explicit confirmation.
- [ ] For Docker sidecar deployments, `tailscale serve status` or the sidecar's logs show it
      joined the tailnet under the expected hostname.
- [ ] Cleanup step (`tailscale serve --https off` or `docker compose down`) documented for when
      the user wants to stop serving.
