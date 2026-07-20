# sqlite-dashboard

Browse SQLite databases with a web UI — inspect tables, run queries, and export data from any browser.

## What it does

The agent launches a web-based dashboard (sqlite-web) for any SQLite database file. You get a table browser, SQL query editor, schema viewer, and CSV/JSON export — all in a browser. No desktop app needed.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/sqlite-dashboard/SKILL.md
```

## How to use

```
"Let me browse my Hermes state.db"
```

The agent:
1. Finds the database file
2. Launches: `sqlite-web /path/to/state.db --port 8080 --read-only`
3. Opens `http://localhost:8080` in your browser
4. You see tables, can run queries, export data

## What you get

| Feature | Notes |
|---|---|
| Table browser | Paginated, sortable |
| SQL query editor | With syntax highlighting |
| Schema viewer | Tables, indexes, triggers |
| CSV/JSON export | Per-table or per-query |
| Read-only mode | Prevents accidental edits |

## Example

```
User: "What's in my app's database?"

Agent:
  1. Finds: /var/lib/myapp/data.db
  2. Launches: sqlite-web /var/lib/myapp/data.db --port 8080 --read-only
  3. Returns: "Dashboard at http://localhost:8080"
  4. User browses tables, runs SELECT queries, exports to CSV
```
