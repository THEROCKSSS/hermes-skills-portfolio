# generate-dockerfile

Detect a project's stack and generate an optimized multi-stage Dockerfile with the supporting files for a reproducible, non-root build.

## What it does

`generate-dockerfile` reads a project's manifests (`package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `uv.lock`, …), figures out what runtime it uses, and writes a multi-stage `Dockerfile` plus the files that make the build safe and reproducible: `.dockerignore`, `.env.example`, and a `docker-compose.yml` when the service has dependencies. The agent runs the detection and writes the files; the skill supplies the rules and the templates. It covers Python (pip/poetry/uv), Node.js (npm/yarn/pnpm), Go, Rust, and static sites.

## Install

This skill ships in the Hermes skills portfolio. Install it with:

```bash
hermes skills install generate-dockerfile
```

If you are vendoring it into your own profile, copy the `skills/generate-dockerfile` directory (the `SKILL.md`) into your Hermes skills folder.

## How to use

Ask Hermes to dockerize a project, or trigger it during scaffolding:

```
dockerize this project
```

```
write a Dockerfile for ./api
```

```
containerize my Go service and add a compose file with Postgres
```

The agent will:

1. Read the project root and identify the manifest(s).
2. Detect the stack from the signals in the supported-stacks table.
3. Write `Dockerfile`, `.dockerignore`, and (when relevant) `.env.example` and `docker-compose.yml`.
4. Optionally run `docker build` to confirm it works.

A mixed project (a Node frontend and a Python API, for example) produces one Dockerfile per deployable service, not a single combined image.

## Supported stacks

| Stack           | Detected from                          | Package manager      |
|-----------------|----------------------------------------|----------------------|
| Node.js         | `package.json`                         | npm / yarn / pnpm    |
| Python (pip)    | `requirements.txt`                     | pip                  |
| Python (poetry) | `pyproject.toml` with `[tool.poetry]`  | poetry               |
| Python (uv)     | `pyproject.toml` + `uv.lock`           | uv                   |
| Go              | `go.mod`                               | go modules           |
| Rust            | `Cargo.toml` + `Cargo.lock`            | cargo                |
| Static site     | `index.html` / SPA build output        | none (nginx serves)  |

## Example

Given a FastAPI project with `requirements.txt`:

```
myapi/
  app/
    main.py
  requirements.txt
```

Running `generate-dockerfile` produces:

- A two-stage `Dockerfile` that builds wheels in a `builder` stage, installs them into a clean `python:3.12-slim` runtime stage, runs as a non-root `app` user, and exposes a `HEALTHCHECK` against `/health`.
- A `.dockerignore` that keeps `node_modules`, `.git`, `.env`, and build output out of the image.
- A `.env.example` listing `DATABASE_URL`, `PORT`, and `LOG_LEVEL` (no secrets).
- A `docker-compose.yml` wiring the API to a `postgres:16-alpine` container with a health-gated `depends_on`, so the app only starts once the database is ready.

You then build and run it:

```bash
docker compose up --build
```

The full templates for every stack live in `SKILL.md`.
