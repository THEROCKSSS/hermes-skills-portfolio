# forgejo-self-host

Set up a self-hosted Forgejo Git server with Docker — repos, issues, pull requests, and CI.

## What it does

The agent deploys a Forgejo instance using Docker Compose, creates an admin account and an API token, and shows you how to push code. Forgejo is a lightweight self-hosted Git server (soft fork of Gitea) with a web UI, issues, pull requests, wiki, and Actions CI. It runs on your machine and holds your repos privately.

The skill configures the instance entirely from environment variables so it comes up ready to use. A Forgejo container started without that configuration boots into its **web install wizard**, and in that state the HTTP API returns 404 and the admin CLI refuses to run — the setup looks healthy while nothing works. Avoiding that is most of what this skill does.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/forgejo-self-host/SKILL.md
```

## How to use

```
"Set up Forgejo on my machine"
```

The agent:
1. Generates a `docker-compose.yml` for Forgejo + SQLite, with the install wizard pre-locked
2. Validates it with `docker compose config`, then runs `docker compose up -d`
3. Verifies the instance is past install mode — not merely responding
4. Creates an admin user and an API token in one command
5. Shows you how to create repos and push code

## Prerequisites

- Docker Engine + Compose v2 (`docker compose version`)
- On Windows: Docker Desktop with the WSL2 backend
- Two free host ports (defaults: `3000` web, `2222` SSH) — `3000` collides often, check it first
- A named Docker volume for `/data` (not a host bind mount — Forgejo runs as uid 1000)

## What you get

| Component | Default | Notes |
|---|---|---|
| Web UI | `http://localhost:3000` | Repos, issues, PRs, wiki, settings |
| SSH git | `localhost:2222` | Published port; `SSH_PORT` must match it or clone URLs are wrong |
| API | `http://localhost:3000/api/v1` | Token-authenticated; may 403 anonymously on a private instance |
| Health | `http://localhost:3000/api/healthz` | No auth required — but returns 200 in install mode too |
| CI | Forgejo Actions | Optional, needs a runner container |
| Storage | Docker volume `forgejo-data` | SQLite by default; PostgreSQL once you add concurrency |

## Image tags

Forgejo publishes **no `latest` tag** — `codeberg.org/forgejo/forgejo:latest` fails to pull with `manifest unknown`. Pin a major line (`:15`) or an exact version (`:15.0.3`). Major upgrades migrate the database irreversibly, so pinning is not just tidiness.

## Three settings that decide whether it works

| Variable | Why it matters |
|---|---|
| `FORGEJO__security__INSTALL_LOCK` | `true` skips the web install wizard. Without it the container serves the installer at `/`, `/api/v1/version` 404s, and the admin CLI aborts with "Unable to load config file for a installed Forgejo instance". |
| `FORGEJO__server__ROOT_URL` | Every generated link, login redirect, clone URL and webhook payload is built from it. Must be the URL a **browser** uses. Behind a reverse proxy or on a remapped port, leaving it at `http://localhost:3000/` bounces users to a dead address after login. |
| `FORGEJO__server__SSH_PORT` | The port written into the SSH clone URLs the UI shows. It is the **published** port (`2222`), not the in-container listen port (`SSH_LISTEN_PORT`, `22`). Mismatched, users copy a clone URL that tries port 22 and fails. |

## Example

```
User: "I want a local Git server for my projects."

Agent:
  1. Writes docker-compose.yml (Forgejo + SQLite, INSTALL_LOCK set, ROOT_URL and SSH_PORT matched to the published ports)
  2. docker compose config  → validates, then docker compose up -d
  3. Confirms /api/healthz reports "status": "pass" AND that / is not the install wizard
  4. docker exec -u git forgejo forgejo admin user create ... --access-token
     → creates the admin and prints its API token in one step
  5. Creates the first repo: POST /api/v1/user/repos → 201
  6. Returns: "Forgejo is running at http://localhost:3000. Your first repo is at
     http://localhost:3000/your-user/my-project"

User pushes code:
  git remote add forgejo http://your-user:token@localhost:3000/your-user/my-project.git
  git push -u forgejo main
```

## Verifying it actually worked

`curl http://localhost:3000/api/healthz` returning `200` is **not** proof of a working install — it returns `200` while the instance is still sitting on the install wizard. The distinguishing check:

```bash
curl -s http://localhost:3000/ | grep -qi '<title>Installation' \
  && echo "STILL IN INSTALL MODE" || echo "installed OK"
```

Full checklist is in `SKILL.md`.

## Windows note

Git Bash rewrites any `docker` argument starting with `/` into a Windows path. `-v $(pwd):/backup` therefore mounts somewhere unintended and backups silently land nowhere. Prefix with `MSYS_NO_PATHCONV=1` or write the source as `"/$(pwd)"`. Guides that bind-mount `/etc/timezone` and `/etc/localtime` fail outright on Windows — use the `TZ` environment variable instead.
