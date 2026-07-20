# searxng-self-host

Self-host a private SearXNG meta-search engine that queries Google, Bing, and DuckDuckGo without tracking you.

## What it does

The agent deploys SearXNG with Docker Compose, configures the search engines, and exposes a web UI plus a JSON API. Searches are proxied — the search engines see the server's IP, not yours. No tracking, no ads, no query logging.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/searxng-self-host/SKILL.md
```

## How to use

```
"Set up a private search engine on my server"
```

The agent:
1. Creates a docker-compose.yml with SearXNG
2. Generates a settings.yml with Google, Bing, DuckDuckGo, Wikipedia enabled
3. Starts the container
4. Verifies the JSON API works
5. Returns: "Search UI at http://localhost:8080, API at http://localhost:8080/search?q=...&format=json"

## Prerequisites

- Docker and Docker Compose
- A free port (default: 8080)

## What you get

| Component | URL | Notes |
|---|---|---|
| Web UI | `http://localhost:8080` | Search interface |
| JSON API | `http://localhost:8080/search?q=...&format=json` | For programmatic use |
| Settings | `searxng/settings.yml` | Configure engines, privacy, proxy |

## Example

```
User: "I want my agent to search the web privately"

Agent:
  1. Deploys SearXNG with Docker
  2. Enables JSON API in settings
  3. Tests: curl http://localhost:8080/search?q=test&format=json → results
  4. Returns: "Your agent can now search via http://localhost:8080/search?q=...&format=json"
```
