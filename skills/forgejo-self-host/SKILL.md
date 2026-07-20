---
name: forgejo-self-host
description: "Set up a self-hosted Forgejo instance with repos, issues, and CI — agent + this skill = user gets their own private Git server running locally."
version: 1.0.0
---

# forgejo-self-host

Deploy a self-hosted Forgejo instance using Docker. Forgejo is a lightweight, self-hosted Git server (a soft fork of Gitea) with repos, issues, pull requests, Actions CI, and a wiki. This skill gets it running on the user's machine in minutes.

## When to Use

- The user wants their own private Git server instead of GitHub/GitLab.
- The user wants to host repos locally for development or backup.
- The user wants CI/CD without relying on external services.
- The user says "set up Forgejo", "self-host my git", or "I want a local GitHub".

## Prerequisites

- **Docker** and **Docker Compose** installed. Check with `docker --version` and `docker compose version`.
- A free port (default: 3000 for web, 2222 for SSH git).

## Workflow

### Step 1: Create the Forgejo deployment

Create a directory and a `docker-compose.yml`:

```yaml
version: "3"
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:latest
    container_name: forgejo
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - FORGEJO__database__DB_TYPE=sqlite3
    restart: always
    volumes:
      - forgejo-data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"
      - "2222:22"

volumes:
  forgejo-data:
```

### Step 2: Start Forgejo

```bash
docker compose up -d
```

Wait 10-20 seconds for first boot, then verify:

```bash
curl -s http://localhost:3000/api/v1/version
# Should return: {"version":"1.22.0"} or similar
```

### Step 3: Initial admin setup

Open `http://localhost:3000` in a browser. The first user registered becomes the site admin.

For headless/automated setup, use the API:

```bash
# Create admin user via CLI (inside the container)
docker exec -u git forgejo forgejo admin user create \
  --username <admin-name> \
  --email <admin-email> \
  --password <password> \
  --admin \
  --must-change-password=false
```

### Step 4: Create an access token

Log in as the admin, go to Settings → Applications → Generate New Token.

Or via API:

```bash
curl -s -X POST "http://localhost:3000/api/v1/users/<admin-name>/tokens" \
  -u "<admin-name>:<password>" \
  -H "Content-Type: application/json" \
  -d '{"name":"api-access","scopes":["write:repository","write:issue","read:user"]}'
```

Store the returned `sha1` token — it won't be shown again.

### Step 5: Create your first repo

Via web UI: click "+" → New Repository.

Via API:

```bash
curl -s -X POST "http://localhost:3000/api/v1/user/repos" \
  -H "Authorization: token <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-project","description":"My project","private":false}'
```

### Step 6: Push code to Forgejo

```bash
cd my-project
git init
git add -A
git commit -m "Initial commit"

# Using HTTPS with token
git remote add forgejo http://<admin-name>:<token>@localhost:3000/<admin-name>/my-project.git
git push -u forgejo main
```

### Step 7: (Optional) Set up CI with Forgejo Actions

Forgejo Actions provides CI/CD similar to GitHub Actions.

1. **Add a runner:**

```bash
# Download the runner
docker run -d --name forgejo-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v forgejo-runner-data:/data \
  codeberg.org/forgejo/runner:latest \
  forgejo-runner register --no-interactive \
    --instance http://host.docker.internal:3000 \
    --token <runner-registration-token> \
    --name local-runner

# Start the runner
docker start forgejo-runner
```

Get the registration token from: Site Administration → Actions → Runners → Register New Runner.

2. **Add a workflow to a repo:**

Create `.forgejo/workflows/ci.yml`:

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

Forgejo exposes SSH on port 2222 by default. To use SSH instead of HTTPS:

```bash
git remote add forgejo ssh://git@localhost:2222/<admin-name>/my-project.git
```

Add to `~/.ssh/config` for cleaner URLs:

```
Host localhost
  HostName localhost
  Port 2222
  User git
```

## Backup

The Forgejo data volume contains all repos, users, and config. Back it up with:

```bash
docker run --rm -v forgejo-data:/data -v $(pwd):/backup ubuntu \
  tar czf /backup/forgejo-backup-$(date +%Y%m%d).tar.gz /data
```

## Pitfalls

- **Port 3000 in use** — If another service uses port 3000, change the port mapping in docker-compose.yml (e.g., `"3001:3000"`) and access Forgejo at `http://localhost:3001`.
- **Default branch is `main` for new repos** — Created via the web UI or API, new repos default to `main` (not `master`). Push to `main`.
- **Admin password via CLI sets must_change_password** — On some Forgejo builds, creating a user via CLI sets a "must change password" flag that locks the user out of admin APIs. If this happens, change the password once via the web UI to clear the flag.
- **Runner can't connect** — The runner needs to reach Forgejo. If running in Docker, use `http://host.docker.internal:3000` (not `localhost:3000` — that's the runner's own localhost).
- **SQLite is fine for small setups** — For single-user or small-team use, SQLite is sufficient. Switch to PostgreSQL only if you have many concurrent users.
- **HTTPS/TLS** — Forgejo serves HTTP by default. For HTTPS, put it behind a reverse proxy (Caddy, nginx, Traefik) with TLS termination.
