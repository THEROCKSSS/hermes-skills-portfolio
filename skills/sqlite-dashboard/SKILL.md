---
name: sqlite-dashboard
description: Use when the user wants to browse a SQLite database file through a web UI or desktop app, run ad-hoc SQL queries against it, or inspect an application's .db/.sqlite/.sqlite3 file without installing a full database server.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [sqlite, database-browser, sqlite-web, docker, ad-hoc-sql]
    related_skills: [tailscale-deploy, caddy-reverse-proxy, csv-toolkit]
---

# sqlite-dashboard

## Overview

Set up a web-based UI for browsing SQLite databases. SQLite is everywhere — application databases, agent state stores, config files — but there's no built-in UI for inspecting them. This skill deploys a lightweight web dashboard for any SQLite database file.

## When to Use

- The user wants to browse a SQLite database without installing a desktop app.
- The user wants to inspect an application's database (Hermes state.db, a web app's SQLite, etc.).
- The user wants to run ad-hoc SQL queries against a database from a browser.
- The user says "let me see my database", "browse my SQLite db", or "what's in this .db file".

## Options

Three approaches, depending on the user's needs:

| Tool | Type | Best for |
|---|---|---|
| **sqlite-web** | Python web app | Quick browsing, query execution, export |
| **DB Browser for SQLite** | Desktop app | Local inspection without a server |
| **LiteQueen / sqlite-explorer** | Docker web UI | Persistent web access, multiple databases |

## Option 1: sqlite-web (recommended)

A Python-based web UI for SQLite databases.

### Install

```bash
pip install sqlite-web
```

### Run

```bash
# Start the web UI for a database file
sqlite-web /path/to/database.db

# With options
sqlite-web /path/to/database.db \
  --host 0.0.0.0 \
  --port 8080 \
  --read-only  # prevent accidental edits
```

Open `http://localhost:8080` in a browser.

### Features

- Table browser with pagination
- SQL query editor with syntax highlighting
- CSV/JSON export
- Insert/update/delete rows
- Foreign key navigation
- Index and trigger viewer

### With Docker

```yaml
version: "3"
services:
  sqlite-web:
    image: coleifer/sqlite-web:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /path/to/your/db:/data
    command: sqlite_web /data/database.db --host 0.0.0.0 --port 8080
```

## Option 2: DB Browser for SQLite (desktop)

A GUI app for local inspection. No server needed.

- **Linux**: `apt install sqlitebrowser` or download from https://sqlitebrowser.org
- **macOS**: `brew install --cask db-browser-for-sqlite`
- **Windows**: download from https://sqlitebrowser.org

Open the app, then File → Open Database → select your `.db` file.

## Option 3: Docker web UI (persistent)

For a persistent web dashboard that can browse multiple databases:

```yaml
version: "3"
services:
  sqlite-explorer:
    image: ghcr.io/coleifer/sqlite-web:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./databases:/data:ro
    command: sqlite_web /data --host 0.0.0.0 --port 8080 --read-only
```

Mount a directory of database files and browse any of them from the UI.

## Workflow

### Step 1: Identify the database

Find the SQLite database the user wants to browse:

```bash
# Find .db files in a project
find /path/to/project -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3"

# Check it's a valid SQLite database
file /path/to/database.db
# → SQLite 3.x database
```

### Step 2: Start the dashboard

```bash
sqlite-web /path/to/database.db --host 0.0.0.0 --port 8080 --read-only
```

### Step 3: Browse

Open `http://localhost:8080`:
- **Browse Data** tab → select a table → see rows with pagination
- **Execute SQL** tab → run ad-hoc queries
- **Structure** tab → see schema, indexes, triggers
- **Export** → download as CSV or JSON

### Step 4: Query examples

```sql
-- List all tables
SELECT name FROM sqlite_master WHERE type='table';

-- Count rows in each table
SELECT 'sessions' as tbl, COUNT(*) as rows FROM sessions
UNION ALL
SELECT 'logs', COUNT(*) FROM logs;

-- Recent records
SELECT * FROM sessions ORDER BY rowid DESC LIMIT 10;

-- Search across columns
SELECT * FROM logs WHERE message LIKE '%error%' ORDER BY timestamp DESC LIMIT 20;
```

## Export

```bash
# Export a table to CSV via the command line
sqlite3 /path/to/database.db ".mode csv" ".headers on" ".output export.csv" "SELECT * FROM my_table;" ".quit"

# Export to JSON
sqlite3 /path/to/database.db ".mode json" ".output export.json" "SELECT * FROM my_table;" ".quit"
```

## Common Pitfalls

1. **Opening a database that's already open for writing elsewhere.** A second writer hits
   "database is locked" errors. Use `--read-only` mode for browsing — it doesn't require write
   locks.
2. **Scrolling a multi-million-row table instead of querying it.** sqlite-web paginates, but
   rendering that many pages is slow. Use the SQL query tab with `LIMIT` instead.
3. **Copying only the `.db` file from a WAL-mode database.** Uncommitted data lives in the
   `-wal` file, not the main file. Copy both, or checkpoint first:
   `sqlite3 database.db "PRAGMA wal_checkpoint(TRUNCATE);"`.
4. **Assuming a `.db` extension means valid SQLite.** Run `file database.db` first — if it
   doesn't say "SQLite 3.x database," confirm with `sqlite3 database.db "PRAGMA integrity_check;"`
   before trusting the dashboard's output.
5. **Leaving the dashboard writable for a production database.** Without `--read-only`, a
   misclick in the UI can modify or delete rows. Default to read-only for any database that isn't
   a scratch copy.
6. **Exposing sqlite-web directly to the public internet.** It has no built-in authentication and
   grants full read/write access to the database. Put it behind Tailscale or a reverse proxy with
   auth instead of publishing the port.

## Verification Checklist

- [ ] `file <database>` confirms "SQLite 3.x database" before the dashboard is pointed at it.
- [ ] Dashboard reachable at `http://<host>:8080` and the target database's tables are visible in
      the Browse Data tab.
- [ ] Read-only mode confirmed (`--read-only` flag present) unless the user explicitly wants
      write access.
- [ ] If the source database uses WAL, the `-wal` file was copied alongside `.db` or checkpointed
      first — row counts match the live database.
- [ ] Dashboard is not reachable from the public internet without authentication (Tailscale/proxy
      auth in front, or bound to localhost only).
