# forgejo-self-host

Set up a self-hosted Forgejo Git server with Docker — repos, issues, pull requests, and CI in minutes.

## What it does

The agent deploys a Forgejo instance using Docker Compose, creates an admin account, sets up an access token, and shows you how to push code. Forgejo is a lightweight self-hosted Git server (soft fork of Gitea) with a web UI, issues, pull requests, wiki, and Actions CI. It runs on your machine and holds your repos privately.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/forgejo-self-host/SKILL.md
```

## How to use

```
"Set up Forgejo on my machine"
```

The agent:
1. Generates a `docker-compose.yml` for Forgejo + SQLite
2. Runs `docker compose up -d`
3. Verifies the instance is reachable at `http://localhost:3000`
4. Creates an admin user and access token
5. Shows you how to create repos and push code

## Prerequisites

- Docker and Docker Compose
- A free port (default: 3000 for web, 2222 for SSH git)

## What you get

| Component | Default | Notes |
|---|---|---|
| Web UI | `http://localhost:3000` | Repos, issues, PRs, wiki, settings |
| SSH git | `localhost:2222` | Clone/push via SSH |
| API | `http://localhost:3000/api/v1` | REST API, token-authenticated |
| CI | Forgejo Actions | Optional, needs a runner container |
| Storage | Docker volume `forgejo-data` | SQLite by default, PostgreSQL for scale |

## Example

```
User: "I want a local Git server for my projects."

Agent:
  1. Creates docker-compose.yml with Forgejo + SQLite
  2. docker compose up -d → Forgejo starts on port 3000
  3. Creates admin user via CLI
  4. Generates access token via API
  5. Creates first repo: curl POST /api/v1/user/repos
  6. Returns: "Forgejo is running at http://localhost:3000. Your first repo is at http://localhost:3000/your-user/my-project"

User pushes code:
  git remote add forgejo http://your-user:token@localhost:3000/your-user/my-project.git
  git push -u forgejo main
```
