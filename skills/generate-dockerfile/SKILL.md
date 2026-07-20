---
name: generate-dockerfile
description: "Generate an optimized multi-stage Dockerfile for a detected project stack — agent + this skill = user gets a production-ready Docker setup."
version: 1.0.0
---

# generate-dockerfile

Read a project, detect its stack, and emit a multi-stage Dockerfile plus the
supporting files (`.dockerignore`, `.env.example`, `docker-compose.yml`) needed
for a reproducible, small, non-root container build. The agent writes the files;
this skill carries the detection rules and the templates.

## When to Use
- The user says "dockerize this", "write a Dockerfile", or "containerize my app".
- You are scaffolding a new project and it will be deployed as a container.
- An existing project has no Dockerfile, or has one that copies source before
  dependencies, runs as root, or ships a single oversized stage.
- You are setting up local development with multiple services (app + database +
  cache) and need a `docker-compose.yml`.

## Workflow
1. **Inventory the project root.** List files and read the manifest(s):
   `package.json`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `go.mod`,
   `Cargo.toml`, `uv.lock`, `yarn.lock`, `pnpm-lock.yaml`, `index.html`.
2. **Detect the stack** using the signals in the table below. One project can
   mix stacks (e.g. Node frontend + Python API) — generate one Dockerfile per
   deployable service, not one mega-image.
3. **Pick the matching template** and adjust versions to the constraints you
   found (Node `engines`, Python version in `pyproject.toml`, Go toolchain).
4. **Write `Dockerfile`** to the service root. Always write `.dockerignore`
   alongside it — without it the build context leaks `.env`, `node_modules`,
   and `.git` into the image.
5. **Emit `.env.example`** if the code reads env vars (database URLs, API keys,
   ports). Never write real secrets into the image.
6. **Emit `docker-compose.yml`** when the service has dependencies (Postgres,
   Redis, a sibling API). Skip it for a standalone static site.
7. **Verify** by running `docker build` (or `docker compose build`) if Docker is
   available and the user wants validation. Otherwise hand back the files with
   the exact build command to run.

## Stack Detection

| Stack        | Primary signal(s)                                   | Package manager        |
|--------------|-----------------------------------------------------|------------------------|
| Node.js      | `package.json`                                      | npm / yarn / pnpm      |
| Python (pip) | `requirements.txt`                                  | pip                    |
| Python (poetry) | `pyproject.toml` with `[tool.poetry]`            | poetry                 |
| Python (uv)  | `pyproject.toml` + `uv.lock`                        | uv                     |
| Go           | `go.mod`                                            | go modules             |
| Rust         | `Cargo.toml` + `Cargo.lock`                         | cargo                  |
| Static site  | `index.html` / SPA build output, no backend runtime | (none — nginx serves)  |

Detection priority when multiple exist: a backend runtime manifest
(`go.mod`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`) wins over a
frontend `package.json`. A `package.json` with only a `build` script and no
server start script is a static-site build step, not a Node service.

## Dockerfile Templates

### Python — pip (primary)
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels
COPY --chown=app:app . /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Poetry / uv differ only in how the dependency set is produced before the
install. Replace the `builder` stage's copy+install with:
- **Poetry:** `RUN pip install poetry` → `COPY pyproject.toml poetry.lock ./` →
  `RUN poetry config virtualenvs.create false && poetry export -f requirements.txt --without-hashes -o requirements.txt` → then the same `pip wheel` step.
- **uv:** `RUN pip install uv` → `COPY pyproject.toml uv.lock* ./` →
  `RUN uv pip compile -o requirements.txt pyproject.toml || true` → then the same `pip wheel` step. (If you install straight into a venv target instead, drop the wheel stage.)

### Node.js — npm (primary)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S app && adduser -S app -G app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/public ./public
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O - http://127.0.0.1:3000/health || exit 1
CMD ["node", "dist/index.js"]
```
Package-manager variants change the manifest copy and the install command:

| Manager | Manifest(s) copied        | Install command (builder / runtime)                          |
|---------|---------------------------|--------------------------------------------------------------|
| npm     | `package.json package-lock.json` | `npm ci --ignore-scripts` / `npm ci --omit=dev --ignore-scripts` |
| yarn    | `package.json yarn.lock`  | `yarn install --frozen-lockfile --ignore-scripts` / `--production` |
| pnpm    | `package.json pnpm-lock.yaml` | `pnpm install --frozen-lockfile --ignore-scripts` / `--prod` (needs `corepack enable`) |

### Go (static binary)
```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /src
RUN apk add --no-cache git
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/bin ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/bin /app/bin
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app/bin"]
```
For a `HEALTHCHECK` under distroless you need a binary in the image, so either
add a small health subcommand to the server and call it from `HEALTHCHECK`, or
drop the `HEALTHCHECK` here and rely on the compose-level check.

### Rust (static binary)
```dockerfile
FROM rust:1.78 AS builder
WORKDIR /app
# Build dependencies first: the dummy crate lets Cargo cache the dep layer.
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs \
    && cargo build --release \
    && rm -rf src
COPY . .
RUN cargo build --release

FROM gcr.io/distroless/cc-debian12
COPY --from=builder /app/target/release/app /app/app
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app/app"]
```

### Static site (SPA built with Node, served by nginx)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q -O - http://127.0.0.1/ || exit 1
```
For client-side routing (React/Vue history mode) the `nginx.conf` needs an
internal fallback to `index.html`:
```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  location / { try_files $uri $uri/ /index.html; }
}
```

## Supporting Files

### `.dockerignore`
Always write this. It keeps build context small and stops `.env` from landing
in the image.
```
.git
.gitignore
node_modules
__pycache__
*.pyc
.venv
venv
dist
build
target
.env
.env.*
Dockerfile
docker-compose.yml
.dockerignore
*.md
.vscode
.idea
.DS_Store
```

### `.env.example`
Write this only if the code reads environment variables. Keep it secret-free.
```
# Copy to .env and fill in real values — never commit the filled-in .env.
DATABASE_URL=postgres://app:app@db:5432/app
REDIS_URL=redis://cache:6379
PORT=8000
LOG_LEVEL=info
```

### `docker-compose.yml`
Write this when the service has dependencies. The `depends_on` + healthcheck
pattern avoids "container started but DB not ready" races.
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "-", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
volumes:
  db_data:
```

## Health Checks
- Point the `HEALTHCHECK` at a real endpoint the app actually serves
  (`/health`, `/ready`). A `wget` against `/` that returns 200 for any HTML page
  hides a broken backend.
- `wget` and `curl` are not present in `distroless` or `slim` Python by default.
  The Python template uses `python -c` for the check; the Node/alpine and nginx
  templates use `wget` (present in `-alpine`).

## Non-root User
- Alpine: `addgroup -S app && adduser -S app -G app` then `USER app`.
- Debian-slim: `groupadd --system app && useradd --system --gid app --home /app app`.
- distroless: the `nonroot` user already exists — just `USER nonroot:nonroot`.
- When you `COPY` source after creating the user, pass `--chown=app:app` (or the
  distroless `nonroot`) so the runtime user can read it.

## Pitfalls
- **`npm install` instead of `npm ci`.** `npm ci` requires a lockfile and
  installs exactly what it pins — reproducible. `npm install` can drift. Use
  `npm ci`, `yarn install --frozen-lockfile`, or `pnpm install --frozen-lockfile`.
- **Lifecycle scripts.** Plain `npm ci` runs `postinstall` scripts from
  dependencies. Default to `--ignore-scripts` and only enable it for a specific
  package you have inspected.
- **Copying source before dependencies.** If `COPY . .` comes before the dep
  install, every source edit invalidates the dependency layer and re-downloads
  everything. Copy the manifest, install, then copy source.
- **Missing `.dockerignore`.** Without it, `node_modules`, `.git`, and `.env`
  get sent as build context and can be baked into the image.
- **Running as root.** The default container user is root; add a non-root user
  in the runtime stage.
- **`--latest` base tags.** Pin (`python:3.12-slim`, `node:20-alpine`). Unpinned
  builds break unpredictably when upstream moves.
- **SPA `__dirname` layout mismatch.** A Node server that resolves a sibling
  `frontend/` via `path.join(__dirname, '..', 'frontend')` breaks when the
  Dockerfile copies the backend to `/app` and the frontend elsewhere — every
  static asset 404s while `/api/*` still works. Copy the frontend into the same
  directory the server expects and have the resolver try both candidate paths.
- **Host loopback on some setups.** When testing from the host, prefer
  `http://127.0.0.1:<port>` over `localhost` — on some systems `localhost`
  resolves to IPv6 `::1` first and the request hangs even though the container
  is healthy. Confirm the app is alive from inside the container
  (`docker compose exec app wget -q -O - http://127.0.0.1:8000/health`) before
  blaming the code.

## Verification
- Run `docker build -t <svc> .` (or `docker compose build`) and confirm it
  succeeds and the final image is small.
- Run the container and hit the health endpoint from inside it.
- Confirm it does not run as root: `docker run --rm <svc> id` should report a
  non-zero uid.
- Confirm no `.env` is in the image: `docker run --rm <svc> ls -la` and inspect
  the build context.
