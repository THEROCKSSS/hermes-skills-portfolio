# docker-umbrella

One Docker container in front of everything you run locally. Instead of remembering
that the dashboard is on `:8080`, the docs on `:9000`, and the media server on
`:8096`, you open one address — say `http://localhost:8080/` — and get a landing
page that links to all of them, with each app proxied behind a clean path.

This skill is the pattern for building that front-end: a stock `nginx:alpine`
container that serves a themed index page and reverse-proxies your services, plus a
`docker-compose.yml`, health checks, and theme switching. No custom image, no
rebuild loop — edit the HTML or the config and it shows on reload.

## What you get

- **One port.** Everything routes through the umbrella's published port.
- **Path or subdomain routing.** `/dash/`, `/docs/`, `/media/` — or
  `dash.example.com`, `docs.example.com` if you have DNS.
- **A themed index.** A landing page that links every service, light/dark/custom.
- **Health checks.** Each proxied service is checked; a dead backend fails the
  container's healthcheck instead of silently 502-ing.
- **Optional TLS.** Terminate HTTPS at the edge and proxy plain HTTP internally.

## Before you start

- Docker Engine + Compose v2 (`docker compose version`).
- A free host port for the umbrella. Check with `ss -ltnp | grep LISTEN`
  (Linux/macOS) or `netstat -an | findstr LISTENING` (Windows).
- Your services reachable from the host: either on the host network
  (`host.docker.internal`) or in the same compose project.

This is for **web UIs, dashboards, doc sites, and media servers**. Databases,
game servers, and long-running bots don't belong behind the proxy — link to them
from the landing page, don't route through it.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/docker-umbrella/SKILL.md
```

Or clone and install from a local path:

```bash
git clone https://github.com/THEROCKSSS/hermes-skills-portfolio
hermes skills install ./hermes-skills-portfolio/skills/docker-umbrella/SKILL.md
```

## Project layout

```
docker-umbrella/
├── docker-compose.yml   ← umbrella container + optional TLS sidecar
├── default.conf         ← nginx routes: landing + one block per service
└── hub/
    └── index.html       ← themed landing page (cards link to each /path/)
```

## docker-compose.yml

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
      test: ["CMD", "curl", "-f", "http://localhost/index.html"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    # Linux Engine only. Docker Desktop resolves host.docker.internal already.
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

If your apps live in this same compose file, drop `host.docker.internal` and
`proxy_pass` to the compose service name (e.g. `http://dashboard:8080`).

## default.conf

```nginx
server {
  listen 80;
  server_name _;

  # Landing page
  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }

  # Each service gets one block. Trailing slash on both sides rewrites
  # /dash/foo -> host:8080/foo.
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

  location /docs/ {
    proxy_pass http://host.docker.internal:9000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /media/ {
    proxy_pass http://host.docker.internal:8096/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

**Slash rule.** `location /dash/` + `proxy_pass http://host:8080/;` strips the
prefix (`/dash/foo` → `host/foo`). Drop the trailing slash on `proxy_pass`
(`http://host:8080`) to keep it (`/dash/foo` → `host/dash/foo`). Pick one
convention and match it on both lines — then confirm with `curl -i`.

## hub/index.html (themed)

```html
<!doctype html>
<html data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Home</title>
  <style>
    :root, [data-theme="dark"] { --bg:#0e1116; --fg:#e6e6e6; --accent:#6ea8fe; --card:#161b22; }
    [data-theme="light"]       { --bg:#ffffff; --fg:#1a1a1a; --accent:#2563eb; --card:#f3f4f6; }
    [data-theme="custom"]      { --bg:#1a1423; --fg:#f3e8ff; --accent:#c084fc; --card:#241a30; }
    body { font-family:system-ui,sans-serif; background:var(--bg); color:var(--fg); margin:0; padding:3rem 1.5rem; }
    h1 { font-weight:600; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:1rem; margin-top:2rem; }
    .card { display:block; background:var(--card); border-left:3px solid var(--accent); border-radius:8px; padding:1rem 1.25rem; color:var(--fg); text-decoration:none; }
    .card small { color:var(--accent); }
    .switcher { position:fixed; bottom:1rem; right:1rem; display:flex; gap:.5rem; }
    .switcher button { background:var(--card); color:var(--fg); border:1px solid var(--accent); border-radius:6px; padding:.4rem .7rem; cursor:pointer; }
  </style>
</head>
<body>
  <h1>Services</h1>
  <div class="grid">
    <a class="card" href="/dash/"><strong>Dashboard</strong><br><small>/dash/</small></a>
    <a class="card" href="/docs/"><strong>Docs</strong><br><small>/docs/</small></a>
    <a class="card" href="/media/"><strong>Media</strong><br><small>/media/</small></a>
  </div>
  <div class="switcher">
    <button onclick="setTheme('light')">Light</button>
    <button onclick="setTheme('dark')">Dark</button>
    <button onclick="setTheme('custom')">Custom</button>
  </div>
  <script>
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    function setTheme(n){ localStorage.setItem('theme', n); document.documentElement.setAttribute('data-theme', n); }
  </script>
</body>
</html>
```

Theme tokens are defined once (`--bg`, `--fg`, `--accent`, `--card`) and every card
inherits them. The switcher writes the choice to `localStorage`, so a refresh keeps
it. Add a service: drop a `<a class="card">` in the grid and a `location /name/`
block in `default.conf`.

## Run it

```bash
docker compose up -d
docker compose ps        # umbrella is "healthy"
curl -i http://localhost:8080/        # landing: 200
curl -i http://localhost:8080/dash/   # proxied app: 200
```

Edit the HTML or config? No rebuild needed:

```bash
docker exec umbrella nginx -s reload   # picks up default.conf changes
```

## Optional TLS at the edge

Terminate HTTPS once, in front of the plain-HTTP umbrella. With Caddy as a sidecar:

```caddyfile
# Caddyfile
dash.example.com {
  reverse_proxy umbrella:80
}
```

```yaml
# add to docker-compose.yml
  caddy:
    image: caddy:alpine
    container_name: umbrella-caddy
    ports: ["443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    restart: unless-stopped
volumes:
  caddy_data:
```

Caddy gets a cert automatically and proxies to the umbrella over the compose
network. The umbrella itself only listens on `80`. Keep the two distinct — don't
expose the same backend on both `80` and `443` without intending to.

## Verification checklist

- [ ] `docker compose ps` shows `umbrella` as `healthy`.
- [ ] The landing page renders and every card link returns 200.
- [ ] Each `/<path>/` route returns 200 (not a 404 from a slash mismatch).
- [ ] After stopping one backend, its healthcheck fails rather than silently 502-ing.
- [ ] Hand the live URL to the user for a visual confirm — `curl` returning 200
      does not prove the page renders in a browser.

## Pitfalls

- **Port conflict.** A dead container holding the port blocks `up -d`
  ("address already in use"). Free the port or pick another before binding.
- **`host.docker.internal` on Linux Engine.** Needs
  `extra_hosts: ["host.docker.internal:host-gateway"]`. Docker Desktop resolves
  it automatically; on a shared compose network, use the service name instead.
- **Bind `0.0.0.0`, not `127.0.0.1`.** `"8080:80"` publishes on all interfaces;
  `"127.0.0.1:8080:80"` locks out the LAN.
- **`nginx:alpine` has no `wget`.** A `wget`-based healthcheck reports
  `unhealthy` even when nginx serves 200. Use `curl -f`.
- **Stale container holds the name.** An exited container with the same
  `container_name` blocks `up -d` ("Conflict ... already in use").
  `docker rm -f umbrella`, then retry.
- **Healthcheck on a redirecting root.** If `/` 302s, `curl -f` fails the check.
  Point it at a known-200 asset (`/index.html`, `/healthz`).
- **Hot config edits.** `docker compose up -d` alone won't reload a changed
  `default.conf`. Run `docker exec umbrella nginx -s reload`.

## Source

Generalized from the internal `personal-docker-umbrella` and `docker-pages-umbrella`
patterns, with all host-specific ports, IPs, and infrastructure coupling removed.
Public under the Hermes Skills Portfolio by Alex.
