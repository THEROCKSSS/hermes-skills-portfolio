---
name: searxng-self-host
description: Use when the user wants to self-host a private, meta-search engine that aggregates results from Google, Bing, DuckDuckGo, Wikipedia, etc. without tracking — triggers include "set up SearXNG", "self-host my search", or "I want private search".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [searxng, self-hosting, docker, meta-search, privacy, reverse-proxy]
    related_skills: [caddy-reverse-proxy, docker-umbrella, forgejo-self-host, uptime-kuma-self-host]
---

# searxng-self-host

## Overview

Deploy a self-hosted SearXNG instance with Docker. SearXNG is a privacy-focused meta-search engine that aggregates results from multiple search engines (Google, Bing, DuckDuckGo, Wikipedia, etc.) without tracking users or sharing search queries.

## When to Use

- The user wants a private search engine that doesn't track them.
- The user wants to self-host search for their team or family.
- The user says "set up SearXNG", "self-host my search", or "I want private search".

## Prerequisites

- Docker and Docker Compose installed
- A free port (default: 8080)

## Docker Deployment

### Step 1: Create the deployment

```yaml
# docker-compose.yml
version: "3"
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
```

### Step 2: Create the settings file

```bash
mkdir -p searxng
cat > searxng/settings.yml << 'EOF'
use_default_settings: true

general:
  instance_name: "My Search"
  debug: false

search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "en"
  formats:
    - html
    - json

server:
  secret_key: "CHANGE_ME_TO_A_RANDOM_STRING"
  bind_address: "0.0.0.0"
  port: 8080

engines:
  - name: google
    engine: google
    shortcut: g
    disabled: false
  - name: bing
    engine: bing
    shortcut: b
    disabled: false
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    disabled: false
  - name: github
    engine: github
    shortcut: gh
    disabled: false

outgoing:
  request_timeout: 3.0
  max_request_timeout: 10.0
  useragent_suffix: ""
EOF
```

### Step 3: Start

```bash
docker compose up -d
```

### Step 4: Verify

```bash
curl -s http://localhost:8080/search?q=test\&format=json | python -m json.tool | head -20
```

Open `http://localhost:8080` in a browser to see the search interface.

## Configuration

### Search engines

Enable or disable individual engines in `settings.yml`:

```yaml
engines:
  - name: google
    engine: google
    shortcut: g
    disabled: false     # enabled
  - name: brave
    engine: brave
    shortcut: br
    disabled: false
  - name: yahoo
    engine: yahoo
    shortcut: y
    disabled: true      # disabled
```

Popular engines: Google, Bing, DuckDuckGo, Brave, Yahoo, Wikipedia, GitHub, Stack Overflow, Reddit, YouTube.

### Privacy settings

```yaml
# In settings.yml
server:
  method: "POST"          # POST instead of GET (hides query from URL/logs)
  image_proxy: true       # Proxy images so the search engine doesn't see the user's IP
  
outgoing:
  request_timeout: 3.0
  # Use a proxy for all outgoing requests
  proxies:
    all://: "socks5h://127.0.0.1:9050"   # via Tor (optional)
```

### Reverse proxy setup

For HTTPS and custom domains, put SearXNG behind Caddy or nginx:

**Caddy (automatic HTTPS):**
```
search.mydomain.com {
    reverse_proxy localhost:8080
}
```

**nginx:**
```nginx
server {
    listen 80;
    server_name search.mydomain.com;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API Usage

SearXNG has a JSON API (must be enabled in settings):

```bash
# Search
curl "http://localhost:8080/search?q=python+async+guide&format=json"

# Search specific categories
curl "http://localhost:8080/search?q=python+async&categories=it&format=json"

# Search specific engines
curl "http://localhost:8080/search?q=python+async&engines=google,bing&format=json"
```

```python
import requests

results = requests.get('http://localhost:8080/search', params={
    'q': 'python async guide',
    'format': 'json',
    'categories': 'it'
}).json()

for result in results['results'][:5]:
    print(f"{result['title']} — {result['url']}")
```

## Common Pitfalls

1. **Default secret key left unchanged.** `secret_key` in settings.yml must be replaced — generate one with `openssl rand -hex 32` before exposing the instance.
2. **JSON API disabled by default.** The `json` format must be explicitly listed under `search.formats` in settings.yml, or API requests return HTML instead of JSON.
3. **Google rate limiting.** Searching too frequently from one IP gets noticed and blocked — distribute load across multiple engines rather than hammering one.
4. **No HTTPS by default.** SearXNG serves plain HTTP — queries are visible on the network until a reverse proxy (Caddy/nginx) terminates TLS in front of it.
5. **Bot detection / CAPTCHAs.** Aggressive automated querying can trigger CAPTCHAs from upstream engines (Google especially) despite SearXNG's built-in anti-bot measures.
6. **Missing container capabilities.** The container needs `CHOWN`, `SETGID`, `SETUID` to write to the settings directory — don't reach for `--privileged`; the specific caps in the compose file are sufficient and safer.

## Verification Checklist

- [ ] `secret_key` in settings.yml changed from the placeholder default
- [ ] `curl http://localhost:8080/search?q=test&format=json` returns valid JSON, not an error page
- [ ] Web UI loads at `http://localhost:8080` (or the reverse-proxied domain) with search results rendering
- [ ] At least 2-3 engines enabled and returning results (not all disabled/erroring)
- [ ] HTTPS confirmed working if a reverse proxy was configured
- [ ] Container running with only the specific capabilities listed (`CHOWN`, `SETGID`, `SETUID`), not `--privileged`
