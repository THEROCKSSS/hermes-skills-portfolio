---
name: searxng-self-host
description: "Self-host a private SearXNG meta-search engine — agent + this skill = user gets their own search engine that queries Google, Bing, DuckDuckGo without tracking."
version: 1.0.0
---

# searxng-self-host

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

## Pitfalls

- **Secret key not set** — The `secret_key` in settings.yml must be changed from the default. Generate a random one: `openssl rand -hex 32`.
- **JSON API disabled by default** — The `json` format must be listed under `search.formats` in settings.yml for the API to work.
- **Google rate limiting** — Google will rate-limit or block your instance if you search too frequently. SearXNG rotates engines, but heavy use from one IP will get noticed. Use multiple engines to distribute load.
- **No HTTPS by default** — SearXNG serves HTTP by default. Use a reverse proxy (Caddy/nginx) for HTTPS. Without HTTPS, search queries are visible on the network.
- **Bot detection** — Some search engines (Google especially) may show CAPTCHAs if they detect automated queries. SearXNG has built-in anti-bot measures, but aggressive use can still trigger blocks.
- **Container permissions** — The SearXNG container needs `CHOWN`, `SETGID`, `SETUID` capabilities to write to the settings directory. Don't run with `--privileged` — the specific caps in the compose file are sufficient.
