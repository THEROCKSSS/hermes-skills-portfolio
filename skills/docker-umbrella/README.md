# docker-umbrella

One Docker container in front of everything you run locally. Instead of remembering
that the dashboard is on `:9000`, the docs on `:9001`, and the media server on
`:8096`, you open one address — say `http://localhost:8090/` — and get a landing
page that links to all of them.

This skill is the pattern for building that front-end: a stock `nginx:alpine`
container that serves a themed index page and reverse-proxies your services, plus a
`docker-compose.yml`, health checks, and theme switching. No custom image, no
rebuild loop — edit the HTML or the config and it shows on reload.

## The one decision that matters

How each app is mounted, chosen **per app**:

| Mount | Works with | Cost |
|---|---|---|
| **Link-only** — card links to the app's own port | Everything | Still a row of ports, but zero risk |
| **Own-port proxy** — one nginx per app, proxying at `/` | Everything, including apps with hardcoded absolute paths | One port per app |
| **Path-mounted** — `/dash/` on the hub's single port | Only apps you can tell they live under a prefix | Breaks silently otherwise |

Path mounting is what people picture when they ask for this, and it is the one
that fails. An app mounted at `/dash/` still emits `href="/assets/app.css"` — a
root-relative link the browser resolves against the *hub's* root. That request
misses the `/dash/` block and is answered by the landing page. With an SPA-style
`try_files` fallback it returns **`200 text/html`**, so the stylesheet request
receives HTML: the page renders completely unstyled while every `curl` check
reports success.

Path-mount only when the app has a `ROOT_URL` / `base href` / `--base-path`
setting, or when you accept rewriting its HTML with `sub_filter`. Otherwise give
it its own port.

## What you get

- **One landing page.** A themed index linking every service, light/dark/custom.
- **Routing that survives contact with real apps.** Own-port proxying by default,
  path mounting where the app supports it.
- **Health checks.** A dead hub fails its container healthcheck instead of
  silently serving a stale page.
- **Optional TLS.** Terminate HTTPS at the edge and proxy plain HTTP internally.

## Before you start

- Docker Engine + Compose v2 (`docker compose version`).
- A free host port for the hub — and it must be **different from every backend
  port** you intend to proxy (see Pitfalls). Check with `ss -ltnp | grep LISTEN`
  (Linux/macOS) or `netstat -an | findstr LISTENING` (Windows).
- `hub/index.html` and `default.conf` must exist **before** `docker compose up -d`.
  Docker creates a *directory* in place of a missing bind-mount source, and nginx
  then fails with `is a directory`.
- Your services reachable from the container: published on the host (reach via
  `host.docker.internal`) or on a shared compose network (reach by service name).

This is for **web UIs, dashboards, doc sites, and media servers**. Databases,
game servers, and long-running bots don't belong behind the proxy — link to them
from the landing page, don't route through it.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/docker-umbrella/SKILL.md
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
├── upgrade.conf         ← the $connection_upgrade map (websockets)
└── hub/
    └── index.html       ← themed landing page
```

## docker-compose.yml

```yaml
name: umbrella

services:
  umbrella:
    image: nginx:alpine
    container_name: umbrella
    ports:
      # Must not collide with any backend port this proxies.
      - "8090:80"
    volumes:
      - ./hub:/usr/share/nginx/html:ro
      - ./default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./upgrade.conf:/etc/nginx/conf.d/upgrade.conf:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost/index.html"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    # Required on Linux Engine; harmless on Docker Desktop.
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

No `version:` key — Compose v2 warns that it is obsolete and ignores it.

If your apps live in this same compose file, drop `host.docker.internal` and
`proxy_pass` to the compose service name (e.g. `http://dashboard:8080`). Service
names only resolve between containers sharing a network.

## upgrade.conf

```nginx
map $http_upgrade $connection_upgrade {
  default upgrade;
  ''      close;
}
```

Hardcoding `proxy_set_header Connection "upgrade"` sends an upgrade header on
every ordinary request, breaking keepalive. The map sends it only when the client
actually asked to upgrade.

## default.conf

```nginx
server {
  listen 80;
  server_name _;

  # Landing page. `index`, NOT `try_files ... /index.html` — the SPA fallback
  # turns every missing asset into a 200 and hides broken routes.
  location / {
    root /usr/share/nginx/html;
    index index.html;
  }

  # Path-mounted app that CAN be told it lives under /docs/
  # (configure the app's own base-path setting to match).
  location ^~ /docs/ {
    proxy_pass http://host.docker.internal:9001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
  }

  # Path-mounted app that CANNOT — rewrite its root-relative links on the way out.
  location ^~ /dash/ {
    proxy_pass http://host.docker.internal:9000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # sub_filter cannot patch a compressed body.
    proxy_set_header Accept-Encoding "";
    sub_filter_once off;
    sub_filter 'href="/' 'href="/dash/';
    sub_filter 'src="/'  'src="/dash/';
  }
}
```

`^~` stops a later regex `location` from winning. `sub_filter` only rewrites HTML
bodies — absolute paths built by JavaScript at runtime still escape it, and those
apps need their own port.

**Slash rule.** `location /dash/` + `proxy_pass http://host:9000/;` strips the
prefix. Drop the trailing slash on `proxy_pass` to keep it. Pick one and confirm
with `curl -i`.

## Own-port proxy (the safe default)

For anything with hardcoded absolute paths — Forgejo, most media servers,
anything with a `/login` redirect — give it a dedicated port and proxy at `/`:

```nginx
server {
  listen 80;
  server_name _;
  client_max_body_size 0;

  location / {
    proxy_pass http://host.docker.internal:3000;   # no trailing slash
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
  }
}
```

Nothing rewrites paths, so the app behaves exactly as it does direct. The hub
links to it by port.

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
    <a class="card" href="http://localhost:8096/"><strong>Media</strong><br><small>own port</small></a>
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

Theme tokens are defined once and every card inherits them. The switcher writes
the choice to `localStorage`. Add a service: drop an `<a class="card">` in the
grid, and a `location` block only if you are path-mounting it.

## Run it

```bash
docker compose config     # validate, starts nothing
docker compose up -d
docker compose ps         # umbrella is "healthy"
```

Then verify by content, not status — see below.

Edit the HTML or config? No rebuild needed, but test before reloading or a syntax
error takes the hub down:

```bash
docker exec umbrella nginx -t && docker exec umbrella nginx -s reload
```

## Optional TLS at the edge

Terminate HTTPS once, in front of the plain-HTTP umbrella:

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
    ports:
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

`caddy_data` holds the certificates — losing it means re-issuing and risking
rate limits, so keep it a named volume. Caddy proxies to the umbrella over the
compose network; the umbrella itself only listens on `80`.

Behind TLS, make every nginx redirect scheme-aware —
`return 301 $scheme://$http_host/foo/;`. A bare `return 301 /foo/;` emits
`http://` and drops the user out of HTTPS.

## Verification checklist

A `200` proves almost nothing here — the two worst failure modes both return
`200` with the wrong body.

```bash
# The route serves the BACKEND's content, not the hub's landing page
curl -s http://localhost:8090/dash/ | grep -q "<title>Dashboard" && echo OK

# A path-mounted app's own asset has the right content-type.
# "200 text/html" means the landing page answered a stylesheet request.
curl -s -o /dev/null -w '%{http_code} %{content_type}\n' \
  http://localhost:8090/dash/assets/app.css

# A bogus path 404s (proves no try_files mask)
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8090/definitely-not-real
```

- [ ] `docker compose config` parses with no `version` obsolete warning.
- [ ] `docker compose ps` shows `umbrella` as `healthy`.
- [ ] The hub's published port appears in **no** `proxy_pass` line.
- [ ] Each route returns the backend's content; each path-mounted asset returns
      its real content-type.
- [ ] A bogus path returns `404`, not `200`.
- [ ] The landing page renders in a real browser with the devtools console clear
      of 404s and MIME-type errors — `curl` returning 200 does not prove this.

## Pitfalls

- **The hub proxying itself.** Publishing the umbrella on `8080:80` *and* writing
  `proxy_pass http://host.docker.internal:8080/` points the route back at the
  hub. `/dash/` returns `200` with the landing page and never reaches the app.
  Keep the hub's port distinct from every backend port.
- **Root-relative links break path mounts.** The dominant failure — assets
  resolve against the hub root and are answered by the landing page. Fix with the
  app's own base-path setting, `sub_filter`, or an own-port proxy.
- **`try_files $uri $uri/ /index.html` masks every 404**, which is what makes the
  above so hard to spot. Use `index index.html;` on a static hub.
- **`nginx:alpine` ships both `curl` and `wget`** (verified on 1.31.3). The trap
  is that `wget` is the BusyBox applet, not GNU wget — GNU-only flags fail, so a
  healthcheck copied from a Debian example reports `unhealthy` while nginx serves
  `200`. Older tags shipped no `curl` at all; pin the tag you tested.
- **Missing bind-mount source becomes a directory.** `up -d` before creating
  `default.conf` makes Docker create a directory of that name and nginx fails
  with `is a directory`.
- **`host.docker.internal` on Linux Engine.** Needs
  `extra_hosts: ["host.docker.internal:host-gateway"]`. Harmless on Docker
  Desktop, so include it always.
- **Stale container holds the name.** An exited container with the same
  `container_name` blocks `up -d`. `docker rm -f umbrella`, then retry.
- **Healthcheck on a redirecting root.** If `/` 302s, `curl -f` fails. Point it
  at a known-200 path.
- **Scheme-downgrading redirects behind TLS.** Use `$scheme://$http_host`.
- **`sub_filter` no-ops on compressed responses.** Send
  `proxy_set_header Accept-Encoding "";` in any block that uses it.
- **Bind `0.0.0.0` vs `127.0.0.1` deliberately.** `"8090:80"` publishes on all
  interfaces; loopback-only is the right default for anything unauthenticated.
- **Hot config edits.** `docker compose up -d` won't reload a changed
  `default.conf`. Run `nginx -t && nginx -s reload`.

## Source

Generalized from the internal `personal-docker-umbrella` and
`forgejo-pages-umbrella` patterns, with all host-specific ports, IPs, and
infrastructure coupling removed. Public under the Hermes Skills Portfolio by Alex.
