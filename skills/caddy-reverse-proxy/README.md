# caddy-reverse-proxy

Set up a Caddy reverse proxy with automatic HTTPS — no certbot, no manual certificate renewal.

## What it does

The agent installs Caddy, writes a Caddyfile for your services, and starts the proxy. Caddy automatically obtains Let's Encrypt TLS certificates, redirects HTTP to HTTPS, and proxies requests to your backend services. You get production-grade HTTPS without managing certificates.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/caddy-reverse-proxy/SKILL.md
```

## How to use

```
"Proxy my API at api.mysite.com to localhost:3000 with HTTPS"
```

The agent:
1. Installs Caddy (or uses Docker)
2. Writes a Caddyfile:
   ```
   api.mysite.com {
       reverse_proxy localhost:3000
   }
   ```
3. Starts Caddy
4. Verifies: `curl https://api.mysite.com/health` returns 200

## Prerequisites

- A server with a public IP
- A domain name pointing to your server (A record)
- Ports 80 and 443 open

## What you get

| Feature | Automatic? |
|---|---|
| TLS certificate issuance | Yes — Let's Encrypt |
| Certificate renewal | Yes — 30 days before expiry |
| HTTP→HTTPS redirect | Yes |
| WebSocket proxying | Yes — no config needed |
| Multiple sites | Yes — one block per domain |

## Example

```
User: "I have three services: a web app on :5173, an API on :3000, and docs on :8080. I want them all under my domain with HTTPS."

Agent:
  1. Writes Caddyfile:
     mysite.com { reverse_proxy localhost:5173 }
     api.mysite.com { reverse_proxy localhost:3000 }
     docs.mysite.com { reverse_proxy localhost:8080 }
  2. Starts Caddy via Docker Compose
  3. Verifies all three domains return 200 over HTTPS
  4. Returns: "All three services are live with HTTPS."
```
