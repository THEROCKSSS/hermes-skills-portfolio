---
name: docker-umbrella
description: "Consolidate multiple services under a single Docker front-end with routing, themed index, and health checks — agent + this skill = user gets one port for all their services."
version: 1.0.0
---

# docker-umbrella

Set up one Docker container that fronts every local service behind a single port:
a themed landing page plus path- or subdomain-based routing, optional TLS at the
edge, and a health check per proxied service. The user gets one address instead of
a row of ports.

## When to Use
- The user runs several local web UIs, dashboards, doc sites, or media servers and
  wants one address instead of a row of ports.
- "One page for all my apps", "group my containers", "declutter Docker Desktop",
  "a landing page that links my services".
- They want TLS at the edge or a single health-checked entry point.
- Do NOT use this for stateful runtimes you must operate directly — databases, game
  servers, bots. Link those from the hub; don't proxy them.

## Architecture
- One stock `nginx:alpine` container is the front-end. No custom baked image, so
  edits to the HTML or config show on reload with no rebuild.
- The landing page (`/`) is bind-mounted HTML that lists every service as a card.
- Proxied services are reached by `proxy_pass` to `host.docker.internal:<port>`
  (host network) or to a compose service name on a shared network.
- One published host port (e.g. `8080`) replaces one port per service.
- Optional TLS: a second `nginx` server block on `443`, or a Caddy sidecar that
  terminates and proxies to the umbrella on `80`.

```
                :8080 (one port)
   browser ──────────────►  umbrella (nginx:alpine)
                               │  /            → themed landing (bind-mounted html)
                               │  /dash/       → proxy_pass host.docker.internal:8080/
                               │  /docs/       → proxy_pass host.docker.internal:9000/
                               └  /media/      → proxy_pass host.docker.internal:8096/
```

## Workflow
1. Inventory services: `docker ps -a --format '{{.Names}}\t{{.Ports}}'`.
2. Confirm a free host port (`docker ps` / `ss -ltnp | grep LISTEN`).
3. Write `docker-compose.yml` (umbrella container + optional TLS sidecar).
4. Write `default.conf` with a landing `location /` and one `location /<path>/`
   per service.
5. Write `index.html` (themed; cards link to each `/<path>/`).
6. `docker compose up -d`.
7. Verify: each route returns 200, the landing renders, and healthchecks report
   healthy. Hand the live URL to the user for a visual confirm — agent-side curl
   is not enough.

## Configuration
`docker-compose.yml` (host-network routing via `host.docker.internal`):
```yaml
services:
  umbrella:
    image: nginx:alpine
    container_name: umbrella
    ports:
      - "8080:80"
    volumes:
      - ./hub:/usr/share/nginx/html:ro
      - ./default.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    # Linux Engine only — Docker Desktop resolves host.docker.internal already:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```
If the proxied apps live in the same compose file, skip `host.docker.internal` and
`proxy_pass` to the compose service name instead (e.g. `http://dashboard:8080`).

## Routing
Path-based (recommended for a single domain/host):
```nginx
server {
  listen 80;
  server_name _;

  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }

  location /dash/ {
    proxy_pass http://host.docker.internal:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```
The trailing slash on both `location /dash/` and `proxy_pass .../` rewrites
`/dash/foo` → `host:8080/foo`. Drop the trailing slash on `proxy_pass` to preserve
the prefix (`/dash/foo` → `host:8080/dash/foo`). Match the two consistently.

Subdomain-based (one hostname per service — needs DNS, a wildcard, or one
`server_name` block per host):
```nginx
server {
  listen 80;
  server_name dash.example.com;
  location / {
    proxy_pass http://host.docker.internal:8080/;
    # same proxy_set_header block as above
  }
}
```

## Theming
Set `data-theme` on `<html>` and swap CSS custom properties. Ship `light` / `dark`
plus one custom palette; persist the choice in `localStorage` so a refresh keeps
it. A two-button switcher is enough:
```html
<html data-theme="dark">
<head>
  <style>
    :root, [data-theme="dark"]  { --bg:#0e1116; --fg:#e6e6e6; --accent:#6ea8fe; --card:#161b22; }
    [data-theme="light"]        { --bg:#ffffff; --fg:#1a1a1a; --accent:#2563eb; --card:#f3f4f6; }
    [data-theme="custom"]       { --bg:#1a1423; --fg:#f3e8ff; --accent:#c084fc; --card:#241a30; }
    body { background:var(--bg); color:var(--fg); }
    .card { background:var(--card); border-left:3px solid var(--accent); }
  </style>
</head>
<body>
  <button onclick="setTheme('light')">Light</button>
  <button onclick="setTheme('dark')">Dark</button>
  <button onclick="setTheme('custom')">Custom</button>
  <script>
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    function setTheme(n){ localStorage.setItem('theme', n); document.documentElement.setAttribute('data-theme', n); }
  </script>
</body>
```
Define tokens once (`--bg`, `--fg`, `--accent`, `--card`) so every card inherits
them. Cards are plain links: `<a class="card" href="/dash/">Dashboard</a>`.

## Pitfalls
- **Port conflict**: check `ss -ltnp` before binding. A dead container holding the
  port blocks `up -d` ("address already in use").
- **`host.docker.internal` on Linux Engine**: needs
  `extra_hosts: ["host.docker.internal:host-gateway"]`. On Docker Desktop it
  resolves automatically. On a shared compose network, use the service name.
- **Binding `127.0.0.1` locks out the LAN**: publish on `0.0.0.0`
  (`"8080:80"` does this), not `"127.0.0.1:8080:80"`.
- **`nginx:alpine` ships no `wget`**: a healthcheck using `wget` reports
  `unhealthy` even when nginx serves 200. Use `curl -f`.
- **Trailing-slash mismatch**: `location /dash/` with `proxy_pass http://host:8080`
  (no slash) preserves `/dash/`; with a slash it strips it. Pick one and verify
  with `curl -i`.
- **Stale container holds the name**: an exited container with the same
  `container_name` blocks `up -d` ("Conflict ... already in use").
  `docker rm -f umbrella`, then retry.
- **Healthcheck on a redirecting root**: if `/` 302-redirects, `curl -f` fails the
  check. Hit a known-200 asset instead (`/index.html`, `/healthz`, `/static/app.js`).
- **TLS + plain HTTP both listening**: terminate TLS at the edge (a `443` server
  block or Caddy) and `proxy_pass http://...:80` internally; don't expose the same
  backend on both without intent.
- **`up -d` in an agent shell**: some shells trip a long-running-server guard and
  hang. If it does, run it as a bounded background task instead.
- **Hot edits to bind-mounts**: changing `default.conf` needs
  `docker exec umbrella nginx -s reload` (zero downtime) — `docker compose up -d`
  alone won't reload a changed config file.
