---
name: docker-umbrella
description: Use when the user runs several local web UIs, dashboards, doc sites, or media servers and wants one address instead of a row of ports, or says "one page for all my apps", "group my containers", "declutter Docker Desktop", or "a landing page that links my services". Do not use for stateful runtimes that must be operated directly — databases, game servers, bots — link those from the hub instead of proxying them.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [docker-compose, nginx, reverse-proxy, service-hub, self-hosting]
    related_skills: [caddy-reverse-proxy]
---

# docker-umbrella

## Overview

Set up one Docker container that fronts every local service: a themed landing
page plus routing to each app, optional TLS at the edge, and a health check.
The user gets one address instead of a row of ports.

The decision that determines whether this works is **how each app is mounted**,
and it is made per app, not once for the whole hub:

- **Link-only** — the hub renders a card that links to the app on its own port.
  Always correct, zero proxy risk. Default to this.
- **Own-port proxy** — a small nginx that proxies the app at `/` on a dedicated
  port. Correct for any app, including ones with hardcoded absolute paths.
- **Path-mounted** (`/dash/`) — one port covers everything, but **only works if
  the app can be told it lives under a prefix**. Path-mounting an app that emits
  root-relative links produces a page that returns `200` and renders completely
  unstyled. See "Path mounting" below before choosing this.

Most self-hosted apps fail path mounting. Reach for it only when the app has a
`base href` / `ROOT_URL` / `--base-path` setting, or when you are willing to
rewrite its HTML with `sub_filter`.

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
- One published host port replaces one port per service.
- Optional TLS: a Caddy sidecar that terminates and proxies to the umbrella on `80`.

```
                :8090 (the hub's own port)
   browser ──────────────►  umbrella (nginx:alpine)
                               │  /            → themed landing (bind-mounted html)
                               │  /docs/       → proxy_pass host.docker.internal:9000/
                               └  /media/      → proxy_pass host.docker.internal:8096/

   the hub's port and every backend port must be DIFFERENT — see Pitfall 1
```

## Prerequisites
- **Docker Engine + Compose v2** (`docker compose version` — the v2 space form).
- **A free host port for the hub**, distinct from every backend port:
  - Linux/macOS: `ss -ltnp | grep LISTEN`
  - Windows: `netstat -an | findstr LISTENING`
- **The bind-mount sources must exist before `up -d`.** If `./default.conf` does
  not exist, Docker creates a *directory* with that name and nginx fails to start
  with `is a directory`. Create `hub/index.html` and `default.conf` first.
- **Backends reachable from the container** — either published on the host (reach
  them via `host.docker.internal`) or on a shared compose network (reach them by
  service name).
- On Docker Desktop, `host.docker.internal` resolves automatically. On Linux
  Engine it does not; add the `extra_hosts` entry shown below. Including it on
  Docker Desktop is harmless, so include it always.

## Workflow
1. Inventory services: `docker ps -a --format '{{.Names}}\t{{.Ports}}'`.
2. Confirm a free host port for the hub that is **not** one of the backend ports.
3. Decide per app: link-only, own-port proxy, or path-mounted.
4. Write `docker-compose.yml`.
5. Write `default.conf` — a landing `location /` plus one block per path-mounted app.
6. Write `hub/index.html` (themed; cards link to each app).
7. `docker compose config` to validate, then `docker compose up -d`.
8. Verify by asserting on **content and content-type**, not status codes — a
   misrouted path returns `200` with the wrong body. See Verification.

## Configuration
`docker-compose.yml`:
```yaml
name: umbrella

services:
  umbrella:
    image: nginx:alpine
    container_name: umbrella
    ports:
      # Host port must not collide with any backend this proxies.
      - "8090:80"
    volumes:
      - ./hub:/usr/share/nginx/html:ro
      - ./default.conf:/etc/nginx/conf.d/default.conf:ro
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
No `version:` key — Compose v2 warns `the attribute 'version' is obsolete`.

If the proxied apps live in the same compose file, skip `host.docker.internal`
and `proxy_pass` to the compose service name instead (e.g. `http://dashboard:8080`).
A service name only resolves if both containers share a network — a backend in a
*different* compose project is not reachable by name unless you attach the
umbrella to that project's network with a top-level `networks: { external: true }`.

## Routing

### Own-port proxy (default, always works)
One small nginx per app, each on its own host port, proxying the app at `/`.
Nothing rewrites paths, so hardcoded absolute URLs, `/login` redirects and
WebSocket upgrades all behave exactly as they do direct:

```nginx
server {
  listen 80;
  server_name _;
  client_max_body_size 0;          # large uploads / git push

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

`$connection_upgrade` needs a `map` at the `http` level — put it in a file
mounted at `/etc/nginx/conf.d/upgrade.conf`:

```nginx
map $http_upgrade $connection_upgrade {
  default upgrade;
  ''      close;
}
```

Hardcoding `proxy_set_header Connection "upgrade"` instead sends an upgrade
header on every ordinary request, which breaks keepalive and confuses some
backends. The `map` sends it only when the client actually asked to upgrade.

### Path mounting
`location /dash/` + `proxy_pass .../` rewrites `/dash/foo` → `backend/foo`. The
request reaches the app correctly. The **response** is the problem: the app emits
links relative to *its* root — `href="/assets/app.css"`, `src="/api/..."` — which
the browser resolves against the hub's root, not `/dash/`. Those URLs miss the
`location /dash/` block entirely and fall through to the landing page.

With a typical SPA-style landing (`try_files $uri $uri/ /index.html`) they do not
even 404: every missing asset returns **`200 text/html`** containing the landing
page. The CSS request receives HTML, so the page renders unstyled and its scripts
throw — while every `curl` check reports `200`.

Two ways to make it work:

**A. Tell the app it lives under a prefix.** Always prefer this. Most apps have a
setting (`ROOT_URL`, `base href`, `--base-path`, `SUBURL`). Set it to `/dash/`,
and the app emits correct links on its own.

**B. Rewrite the HTML on the way out** when the app has no such setting:

```nginx
location ^~ /dash/ {
  proxy_pass http://host.docker.internal:9000/;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  # sub_filter cannot patch a compressed body — force plain text upstream.
  proxy_set_header Accept-Encoding "";

  sub_filter_once off;
  sub_filter 'href="/' 'href="/dash/';
  sub_filter 'src="/'  'src="/dash/';
  sub_filter "href='/" "href='/dash/";
  sub_filter "src='/"  "src='/dash/";
}
```

`^~` matters: it stops nginx from letting a later regex `location` win. And drop
the `try_files ... /index.html` fallback from `location /` (use `index
index.html;`) so a genuinely missing asset returns `404` instead of a misleading
`200`.

This is a patch, not a fix — it only touches HTML bodies, so absolute paths built
in JavaScript at runtime still escape. Apps that do that need option A or an
own-port proxy.

### Subdomain-based
One hostname per service — needs DNS or a wildcard record. Behaves like the
own-port pattern (the app is at `/`), so it avoids the prefix problem entirely:
```nginx
server {
  listen 80;
  server_name dash.example.com;
  location / {
    proxy_pass http://host.docker.internal:9000;
    # same proxy_set_header block as the own-port example
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

## Common Pitfalls
1. **The hub proxying itself.** Publishing the umbrella on `8080:80` and also
   writing `proxy_pass http://host.docker.internal:8080/` points the route back at
   the hub's own published port. `/dash/` then returns **`200` with the landing
   page** — the route looks fine to `curl` and never reaches the app. Keep the
   hub's host port distinct from every backend port, and re-read the compose
   `ports:` line against every `proxy_pass` before starting.
2. **Root-relative links break path mounts.** The dominant failure. A path-mounted
   app's assets resolve against the hub root and are answered by the landing page
   with `200 text/html`. See "Path mounting" — fix with the app's own prefix
   setting, `sub_filter`, or an own-port proxy.
3. **`try_files $uri $uri/ /index.html` masks every 404.** The SPA fallback turns
   missing assets into `200` landing-page HTML, which is what makes pitfall 2 so
   hard to spot. Use `index index.html;` on a static hub and reserve the fallback
   for an actual SPA.
4. **`nginx:alpine` ships both `curl` and `wget`.** (Verified on `nginx:alpine`
   1.31.3: `/usr/bin/curl` and `/usr/bin/wget`.) The real trap is that `wget` is
   the **BusyBox** applet, not GNU wget — it rejects GNU-only flags such as
   `--version` and `--spider` semantics differ, so a healthcheck copied from a
   Debian example reports `unhealthy` while nginx serves `200`. Older
   `nginx:alpine` tags shipped no `curl` at all, so pin the tag you tested.
5. **Trailing-slash mismatch.** `location /dash/` with `proxy_pass http://host:9000`
   (no slash) preserves `/dash/`; with a slash it strips it. Match the two
   deliberately and confirm with `curl -i`.
6. **Port conflict on `up -d`.** A dead container holding the port blocks the
   bind ("address already in use"). Check listeners first; free the port or pick
   another.
7. **Stale container holds the name.** An exited container with the same
   `container_name` blocks `up -d` ("Conflict ... already in use").
   `docker rm -f umbrella`, then retry.
8. **Missing bind-mount source becomes a directory.** `up -d` before creating
   `default.conf` makes Docker create a directory of that name; nginx then fails
   with `is a directory`. Delete the directory, create the file, restart.
9. **Healthcheck on a redirecting root.** If `/` 302-redirects, `curl -f` fails
   the check. Hit a known-200 path instead (`/index.html`, `/healthz`, or an app's
   `/user/login`).
10. **Scheme-downgrading redirects behind TLS.** `return 301 /foo/;` and nginx's
    automatic directory redirect emit `http://` even when the user arrived over
    HTTPS, bouncing them out of TLS. Write redirects scheme-aware:
    `return 301 $scheme://$http_host/foo/;`
11. **Binding `127.0.0.1` locks out the LAN.** `"8090:80"` publishes on all
    interfaces; `"127.0.0.1:8090:80"` does not. Choose deliberately — loopback-only
    is the right default for anything unauthenticated.
12. **Hot edits to bind-mounts don't reload.** `docker compose up -d` will not
    reload a changed `default.conf`. Always test before reloading, or a syntax
    error takes the hub down:
    `docker exec umbrella nginx -t && docker exec umbrella nginx -s reload`
13. **`sub_filter` silently does nothing on compressed responses.** If the
    upstream gzips, the filter never matches. Send
    `proxy_set_header Accept-Encoding "";` in any block using `sub_filter`.
14. **`up -d` hangs in an agent shell.** Some shells trip a long-running-server
    guard. If it does, run it as a bounded background task instead.

## Verification Checklist

A `200` proves almost nothing here — pitfalls 1, 2 and 3 all return `200` with
the wrong body. Assert on what came back.

- [ ] `docker compose config` parses with no `version` obsolete warning
- [ ] `docker ps` shows `umbrella` as `healthy`, not `starting` or `unhealthy`
- [ ] The hub's published port appears in **no** `proxy_pass` line:
      `grep proxy_pass default.conf` checked against the compose `ports:` entry
- [ ] Each route returns the **backend's** content, not the hub's — e.g.
      `curl -s http://localhost:8090/dash/ | grep -q "<title>Dashboard"`, not just a status check
- [ ] For every path-mounted app, one of its own assets returns the right
      content-type: `curl -s -o /dev/null -w '%{http_code} %{content_type}\n' http://localhost:8090/dash/assets/app.css`
      shows `200 text/css` — `200 text/html` means the landing page answered it
- [ ] A deliberately bogus path returns `404`, not `200` (proves no `try_files` mask)
- [ ] Landing page renders in an actual browser with every card link working —
      open the devtools console and confirm no 404s or MIME-type errors
- [ ] Config edits were applied with `nginx -t && nginx -s reload`, and the reload
      was confirmed by re-checking a changed route
- [ ] If TLS terminates at the edge, redirects stay on `https://` (pitfall 10)
