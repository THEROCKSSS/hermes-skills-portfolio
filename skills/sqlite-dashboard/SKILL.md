---
name: sqlite-dashboard
description: "Browse SQLite databases with a web UI — agent + this skill = user gets a visual interface for inspecting any SQLite database."
version: 1.0.0
---

# sqlite-dashboard

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

## Pitfalls

- **Database locked** — If another process has the database open for writing, the web UI may get "database is locked" errors. Use `--read-only` mode for browsing (doesn't require write locks).
- **Large databases** — sqlite-web paginates results, but loading a table with millions of rows can be slow. Use the SQL query tab with `LIMIT` for large tables.
- **WAL mode** — If the database uses WAL (Write-Ahead Logging), the `.db` file alone doesn't contain all data — the `-wal` file is also needed. Copy both files, or checkpoint the WAL first: `sqlite3 database.db "PRAGMA wal_checkpoint(TRUNCATE);"`.
- **Corrupt databases** — If `file database.db` doesn't say "SQLite 3.x database", the file may be corrupt or not SQLite. Run `sqlite3 database.db "PRAGMA integrity_check;"` to verify.
- **Accidental writes** — If the dashboard is writable, a user could accidentally modify or delete data. Use `--read-only` for inspection. For production databases, always use read-only mode.
- **Exposing the dashboard** — Don't expose sqlite-web to the public internet without authentication. It gives full access to the database. Use Tailscale or a reverse proxy with auth for remote access.
