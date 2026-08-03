---
name: forgejo-self-host
description: "Use when the user wants a self-hosted, private Git server (repos, issues, pull requests, CI, wiki) running locally via Docker instead of relying on GitHub or GitLab."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [forgejo, self-hosted-git, docker-compose, ci-cd, gitea-fork]
    related_skills: [caddy-reverse-proxy, git-backup, github-actions-ci]
---

# forgejo-self-host

## Overview

Deploy a self-hosted Forgejo instance using Docker. Forgejo is a lightweight,
self-hosted Git server (a soft fork of Gitea) with repos, issues, pull requests,
Actions CI, and a wiki.

The whole skill turns on one decision: **configure the instance from environment
variables and skip the web install wizard**, rather than booting a blank
container and clicking through it. A container booted without that configuration
comes up in *install mode*, where the entire HTTP API is unreachable and the
admin CLI refuses to run — which is the failure most first-time setups hit.

## When to Use

- The user wants their own private Git server instead of GitHub/GitLab.
- The user wants to host repos locally for development or backup.
- The user wants CI/CD without relying on external services.
- The user says "set up Forgejo", "self-host my git", or "I want a local GitHub".

## Prerequisites

- **Docker Engine + Compose v2.** Check with `docker --version` and
  `docker compose version` (the space-separated v2 form, not `docker-compose`).
- **On Windows: Docker Desktop with the WSL2 backend.** The Linux-host tricks in
  most Forgejo guides (`/etc/timezone` bind mounts, `$(pwd)` in `docker run`) do
  not work there — see Pitfalls 2 and 9.
- **Two free host ports** — one for HTTP, one for SSH. Defaults below are `3000`
  and `2222`. Port `3000` collides with a lot of things (Grafana, Next.js, Rails,
  many dev servers), so check first:
  - Linux/macOS: `ss -ltnp | grep -E ':(3000|2222)\b'`
  - Windows: `netstat -an | findstr /R /C:":3000 " /C:":2222 "`
  If either is taken, change the **left** side of the port mapping and change
  `ROOT_URL` / `SSH_PORT` to match — see Pitfall 4.
- **A named Docker volume, not a host bind mount**, for `/data`. Forgejo runs as
  uid 1000 inside the container; a Windows or macOS bind mount will not carry
  that ownership and the container fails to write its repositories.

## Workflow

### Step 1: Create the Forgejo deployment

Create a directory and a `docker-compose.yml`:

```yaml
name: forgejo

services:
  forgejo:
    # Forgejo publishes NO `latest` tag — pin a major line.
    image: codeberg.org/forgejo/forgejo:15
    container_name: forgejo
    restart: unless-stopped
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      TZ: "UTC"
      # Skip the web install wizard. Without this the container boots into
      # install mode and the API + admin CLI are both unusable.
      FORGEJO__security__INSTALL_LOCK: "true"
      FORGEJO__database__DB_TYPE: sqlite3
      FORGEJO__database__PATH: /data/gitea/gitea.db
      # ROOT_URL must be the URL a BROWSER uses. Every generated link,
      # redirect, clone URL and OAuth callback is built from it.
      FORGEJO__server__DOMAIN: localhost
      FORGEJO__server__ROOT_URL: http://localhost:3000/
      # SSH_PORT is the PUBLISHED port (what users connect to).
      # SSH_LISTEN_PORT is the IN-CONTAINER port. They differ on purpose.
      FORGEJO__server__SSH_DOMAIN: localhost
      FORGEJO__server__SSH_PORT: "2222"
      FORGEJO__server__SSH_LISTEN_PORT: "22"
    volumes:
      - forgejo-data:/data
    ports:
      - "3000:3000"
      - "2222:22"

volumes:
  forgejo-data:
```

Do **not** add a `version:` key — Compose v2 warns `the attribute 'version' is
obsolete, it will be ignored`. Do **not** bind-mount `/etc/timezone` or
`/etc/localtime` (Pitfall 2); the `TZ` variable above replaces both portably.

Validate before starting — this parses the file and starts nothing:

```bash
docker compose -f docker-compose.yml config
```

### Step 2: Start Forgejo

```bash
docker compose up -d
```

First boot takes roughly 10-30 seconds to create the SQLite schema. Wait for the
health endpoint rather than guessing:

```bash
# /api/healthz needs no auth and works even on a private instance
curl -s http://localhost:3000/api/healthz
```

A configured instance returns `"status": "pass"` with a `database:ping` check.

Now confirm it is **not** stuck in install mode — this is the check that matters:

```bash
curl -s http://localhost:3000/ | grep -qi '<title>Installation' \
  && echo "STILL IN INSTALL MODE — INSTALL_LOCK not applied" \
  || echo "installed OK"
```

`/api/healthz` returns `200` *even in install mode*, so it proves the process is
alive, not that setup succeeded. The title check is what distinguishes them.

### Step 3: Create the admin user and its API token

With `INSTALL_LOCK=true` there is no wizard and no "first registered user becomes
admin" step — you create the admin directly. One command creates the user *and*
prints an API token:

```bash
docker exec -u git forgejo forgejo admin user create \
  --username <admin-name> \
  --email <admin-email> \
  --password '<password>' \
  --admin \
  --must-change-password=false \
  --access-token \
  --access-token-name cli \
  --access-token-scopes "write:repository,write:issue,write:user"
```

It prints `New user '<admin-name>' has been successfully created!` followed by
`Access token was successfully created... <token>`. **Store that token now** — it
is not shown again.

`-u git` is required: the Forgejo process and everything under `/data` are owned
by the `git` user, and the CLI must run as that user.

Need another token later:

```bash
docker exec -u git forgejo forgejo admin user generate-access-token \
  --username <admin-name> --token-name ci \
  --scopes "write:repository,write:issue,write:user"
```

**Scope note:** `POST /api/v1/user/repos` (Step 4) requires **`write:user`**, not
`write:repository`. A token scoped only to repositories is rejected with
`token does not have at least one of required scope(s): [write:user]`.

### Step 4: Create your first repo

Via web UI: log in at `http://localhost:3000`, click "+" → New Repository.

Via API — returns `201 Created`:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST "http://localhost:3000/api/v1/user/repos" \
  -H "Authorization: token <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-project","description":"My project","private":false,"auto_init":true}'
```

### Step 5: Push code to Forgejo

```bash
cd my-project
git init
git add -A
git commit -m "Initial commit"

# HTTPS with a token
git remote add forgejo http://<admin-name>:<token>@localhost:3000/<admin-name>/my-project.git
git push -u forgejo main
```

Embedding the token in the remote URL writes it to `.git/config` in plaintext.
For anything long-lived use a credential helper or the SSH remote below instead.

### Step 6: (Optional) Set up CI with Forgejo Actions

Get a registration token from Site Administration → Actions → Runners → Register
New Runner.

Register once (a one-shot container that exits), then run the daemon:

```bash
# 1. Register — this writes .runner into the volume, then exits.
docker run --rm \
  -v forgejo-runner-data:/data \
  -w /data \
  codeberg.org/forgejo/runner:latest \
  forgejo-runner register --no-interactive \
    --instance http://host.docker.internal:3000 \
    --token <runner-registration-token> \
    --name local-runner

# 2. Run the daemon — this is the long-lived container.
docker run -d --name forgejo-runner --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v forgejo-runner-data:/data \
  -w /data \
  --add-host host.docker.internal:host-gateway \
  codeberg.org/forgejo/runner:latest \
  forgejo-runner daemon
```

`register` and `daemon` are two different commands. Running `register` with
`-d` and then `docker start` re-runs *registration* every boot and never starts a
daemon — the runner will never appear as online.

Then add `.forgejo/workflows/ci.yml` to a repo:

```yaml
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "CI is running"
```

## SSH Git Access

The container listens on `22` internally and is published on `2222`. Because
Step 1 sets `SSH_PORT: "2222"`, the UI and API hand out clone URLs carrying the
published port:

```
ssh://git@localhost:2222/<admin-name>/my-project.git
```

```bash
git remote add forgejo ssh://git@localhost:2222/<admin-name>/my-project.git
```

Add your public key first under Settings → SSH / GPG Keys, or the push fails with
`Permission denied (publickey)`.

Optional `~/.ssh/config` entry — scope it to a dedicated alias rather than
`Host localhost`, which would hijack every other SSH connection to localhost:

```
Host forgejo-local
  HostName localhost
  Port 2222
  User git
```

Then the remote becomes `forgejo-local:<admin-name>/my-project.git`.

## Backup

Use Forgejo's own dump command. It quiesces the database and produces a single
consistent archive — `tar`-ing a live SQLite file can capture a torn write:

```bash
docker exec -u git forgejo forgejo dump --type tar.gz --file /data/backup.tar.gz
docker cp forgejo:/data/backup.tar.gz ./forgejo-backup-$(date +%Y%m%d).tar.gz
docker exec -u git forgejo rm /data/backup.tar.gz
```

If you must snapshot the raw volume instead, stop the container first, and note
the Windows path caveat in Pitfall 9:

```bash
docker compose stop forgejo
MSYS_NO_PATHCONV=1 docker run --rm -v forgejo-data:/data -v "$(pwd)":/backup \
  alpine tar czf /backup/forgejo-volume-$(date +%Y%m%d).tar.gz /data
docker compose start forgejo
```

## Common Pitfalls

1. **`:latest` does not exist.** `codeberg.org/forgejo/forgejo:latest` fails the
   pull with `manifest unknown` — Forgejo publishes no `latest` tag. Use a major
   line (`:15`) or an exact version (`:15.0.3`). Pinning also matters because a
   major upgrade migrates the database irreversibly; there is no downgrade path
   once it runs.
2. **Do not bind-mount `/etc/timezone` and `/etc/localtime`.** Nearly every
   Forgejo guide copies these two lines from a Linux-host example. On Windows the
   daemon fails the container with
   `Error response from daemon: mkdir C:\Program Files\Git\etc\timezone: Access is denied`,
   because there is no such host path. Set `TZ` instead — it works on every host.
3. **Boot without `INSTALL_LOCK` and the instance is inert.** The container
   serves the *install wizard at `/`* (not at `/install`, which 404s), and every
   other route is swallowed by the installer: `/api/v1/version` returns a `404`
   HTML page, and `forgejo admin user create` aborts with
   `[F] Unable to load config file for a installed Forgejo instance`. Setting
   `FORGEJO__security__INSTALL_LOCK=true` plus the database settings skips it.
4. **`ROOT_URL` is the single most common misconfiguration.** It is not
   cosmetic — redirects after login, asset URLs, clone URLs, webhook payloads and
   OAuth callbacks are all generated from it. If you remap the host port to
   `3001`, or front the instance with a reverse proxy at
   `https://git.example.com/`, `ROOT_URL` must be changed to exactly that
   browser-facing URL. Left at `http://localhost:3000/` behind a proxy, users log
   in and get bounced to `localhost:3000`, and assets fail to load.
5. **`SSH_PORT` vs `SSH_LISTEN_PORT`.** `SSH_LISTEN_PORT` is where sshd listens
   inside the container (`22`); `SSH_PORT` is the port that goes into the clone
   URLs the UI shows. Publishing `2222:22` while leaving `SSH_PORT` at its `22`
   default makes the UI advertise `git@host:<repo>.git`, which clients try on
   port 22 and fail. Set `SSH_PORT` to the published port.
6. **Anonymous API access may be disabled.** On an instance with
   `REQUIRE_SIGNIN_VIEW = true` (the common choice for a private server),
   `curl http://localhost:3000/api/v1/version` returns
   `403 {"message":"Only signed in user is allowed to call APIs."}` — the server
   is perfectly healthy. Use `/api/healthz` for unauthenticated liveness, or send
   the token with the request.
7. **SQLite is fine for one person; switch on concurrency, not size.** SQLite
   holds a single writer lock, so concurrent CI runners plus web users produce
   `database is locked` errors. Move to PostgreSQL when you add runners or users,
   by swapping the `FORGEJO__database__*` variables — but do it on a fresh
   instance or via `forgejo dump`/restore; changing `DB_TYPE` on a running
   instance does not migrate existing data.
8. **Runner can't reach the instance.** Inside the runner container `localhost`
   is the runner itself. Use `http://host.docker.internal:3000` (adding
   `--add-host host.docker.internal:host-gateway` on Linux Engine), or put both
   containers on one Compose network and use the service name.
9. **Windows/Git Bash mangles POSIX paths in `docker` arguments.** Any argument
   starting with `/` is rewritten to a Windows path by MSYS, so
   `-v $(pwd):/backup` silently mounts somewhere unexpected and the backup file
   never appears where you asked for it. Prefix the command with
   `MSYS_NO_PATHCONV=1`, or write the source as `"/$(pwd)"` with a leading slash.
   PowerShell and Linux/macOS shells are unaffected.
10. **`--must-change-password` defaults to forcing a reset.** An admin created
    without `--must-change-password=false` must change its password at first web
    login, and API calls before that can be rejected. Pass the flag explicitly.
11. **Port 3000 collides constantly.** If you remap to `3001:3000`, change
    `ROOT_URL` to `http://localhost:3001/` in the same edit — remapping the port
    alone leaves every generated link pointing at 3000.

## Verification Checklist

- [ ] `docker compose -f docker-compose.yml config` parses with no `version` obsolete warning
- [ ] `docker compose ps` shows the container `running`
- [ ] `curl -s http://localhost:3000/api/healthz` reports `"status": "pass"` including `database:ping`
- [ ] `curl -s http://localhost:3000/ | grep -i '<title>Installation'` returns **nothing** — the instance is past the install wizard, not merely alive
- [ ] `forgejo admin user create` printed both the user confirmation and an access token
- [ ] The token creates a repo: `POST /api/v1/user/repos` returns `201` (not `403 ... [write:user]`)
- [ ] `GET /api/v1/repos/<user>/<repo>` shows a `clone_url` and an `ssh_url` whose host and port match how you actually reach the server — not `localhost:3000` when you browse it at another address
- [ ] Admin login succeeds in a real browser, and a page reload keeps you logged in (a wrong `ROOT_URL` shows up here as a redirect bounce)
- [ ] A test repo pushes over the configured remote (HTTPS token or SSH on the published port)
- [ ] If Actions was configured: the runner shows **online** under Site Administration → Actions → Runners, and a sample workflow run succeeds
