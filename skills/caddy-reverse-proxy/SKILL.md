---
name: caddy-reverse-proxy
description: Use when the user wants to expose a local service over HTTPS with a real domain, proxy multiple services through one server with TLS, get automatic certificate management without certbot or manual renewal, or says "set up a reverse proxy", "I need HTTPS for my service", or "proxy my Docker services".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [caddy, reverse-proxy, tls, lets-encrypt, caddyfile, docker]
    related_skills: [docker-umbrella]
---

# caddy-reverse-proxy

## Overview

Set up Caddy as a reverse proxy with automatic HTTPS. Caddy obtains and renews Let's Encrypt certificates automatically, handles HTTP-to-HTTPS redirects, and proxies requests to your backend services. No manual certificate management.

## When to Use

- The user wants to expose a local service over HTTPS with a real domain.
- The user wants to proxy multiple services through one server with TLS.
- The user wants automatic certificate management (no certbot, no manual renewal).
- The user says "set up a reverse proxy", "I need HTTPS for my service", or "proxy my Docker services".

## Prerequisites

- A server with a public IP address
- A domain name pointing to your server (A record)
- Ports 80 and 443 open

## Installation

### Linux

```bash
# Debian/Ubuntu (official repo)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### macOS

```bash
brew install caddy
```

### Docker

```bash
docker run -d --name caddy \
  -p 80:80 -p 443:443 \
  -v caddy_data:/data \
  -v caddy_config:/config \
  -v $PWD/Caddyfile:/etc/caddy/Caddyfile \
  caddy:latest
```

## Caddyfile Syntax

The Caddyfile is Caddy's configuration format. It's intentionally simple.

### Single site

```
example.com {
    reverse_proxy localhost:8080
}
```

This one block does:
1. Listens on ports 80 and 443 for `example.com`
2. Obtains a Let's Encrypt certificate automatically
3. Redirects HTTP to HTTPS
4. Proxies all requests to `localhost:8080`

### Multiple sites

```
app.example.com {
    reverse_proxy localhost:8080
}

api.example.com {
    reverse_proxy localhost:3000
}

docs.example.com {
    root * /var/www/docs
    file_server
}
```

### Reverse proxy with header manipulation

```
api.example.com {
    reverse_proxy localhost:3000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

### WebSocket support

Caddy supports WebSockets automatically — no special config needed:

```
chat.example.com {
    reverse_proxy localhost:3000
}
```

### Static files + API

```
example.com {
    # Serve static files
    handle /assets/* {
        root * /var/www/assets
        file_server
    }

    # Proxy API requests
    handle /api/* {
        reverse_proxy localhost:3000
    }

    # Everything else → frontend
    handle {
        reverse_proxy localhost:5173
    }
}
```

### Load balancing

```
api.example.com {
    reverse_proxy localhost:3000 localhost:3001 localhost:3002 {
        lb_policy round_robin
        health_uri /health
        health_interval 10s
    }
}
```

## Automatic HTTPS

Caddy handles certificates automatically:

| Feature | How it works |
|---|---|
| Certificate issuance | Caddy obtains certificates from Let's Encrypt on first request |
| Renewal | Caddy renews certificates 30 days before expiry |
| HTTP→HTTPS redirect | Automatic for all sites with a domain name |
| On-demand TLS | Optional — issue certificates on first request for any domain |

**On-demand TLS** (for wildcard/multi-tenant setups):

```
{
    on_demand_tls {
        ask https://api.example.com/check-domain
    }
}

https:// {
    tls {
        on_demand
    }
    reverse_proxy localhost:8080
}
```

Caddy will ask your API endpoint whether a domain is allowed before issuing a certificate.

## Running Caddy

### As a system service (Linux)

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
sudo systemctl status caddy

# Reload config without downtime
sudo systemctl reload caddy

# View logs
sudo journalctl -u caddy -f
```

### With Docker Compose

```yaml
version: "3"
services:
  caddy:
    image: caddy:latest
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - caddy_data:/data
      - caddy_config:/config
      - ./Caddyfile:/etc/caddy/Caddyfile
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  caddy_data:
  caddy_config:
```

Use `host.docker.internal` in the Caddyfile to proxy to services running on the host (not in Docker).

## Common Pitfalls

1. **No domain name.** Caddy's automatic HTTPS requires a domain name pointing to your server. Without a domain, Caddy can't obtain certificates. For local-only HTTPS, use Caddy's internal CA: `localhost:8080 { reverse_proxy localhost:3000 }` (generates a self-signed cert).
2. **Ports 80/443 not open.** Let's Encrypt uses the HTTP-01 challenge, which requires port 80 to be reachable. If your firewall blocks port 80, certificate issuance fails.
3. **Hitting Let's Encrypt rate limits.** Let's Encrypt allows 50 certificates per domain per week. Don't repeatedly restart Caddy with new domains in testing — you'll hit the limit and have to wait it out.
4. **Wrong host resolution in Docker.** If Caddy runs in Docker and your backend runs on the host, use `host.docker.internal` (with `extra_hosts` in compose). If both are in Docker, put them on the same network and use the container name instead.
5. **Restarting instead of reloading.** Use `caddy reload` (or `systemctl reload caddy`) to apply config changes without dropping connections. `caddy stop` + `caddy start` drops active connections.
6. **Large uploads silently rejected.** Caddy has a default body size limit. For large file uploads, set `request_body { max_size 100MB }` in the site block.

## Verification Checklist

- [ ] `curl -I https://<domain>` returns a valid certificate (no `-k` needed) and the expected backend response
- [ ] HTTP requests to the same domain redirect to HTTPS (`curl -I http://<domain>` shows a 301/308)
- [ ] `caddy validate --config Caddyfile` (or `docker exec caddy caddy validate`) passes before reload
- [ ] Config changes were applied with `caddy reload`, not a hard restart, if connections needed to stay up
- [ ] WebSocket-dependent backends were tested with an actual upgrade request, not just a plain GET
- [ ] Domain's A record resolves to the server's public IP before expecting certificate issuance to succeed
