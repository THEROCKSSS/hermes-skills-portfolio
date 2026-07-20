# skill-registry-catalog

Survey public AI-agent skill registries and turn them into a categorized, source-cited catalog
you can actually triage — not a bookmark dump.

## What it does

The agent pulls skill data from public registries (skills.md, skillsmp.com), filters it by the
categories you care about, and builds a repository where every third-party skill gets its own
folder. Skills are split into three buckets — **approved** (already in your local library),
**pending** (awaiting your review), and **other** (out of focus) — and a counter tracks how many
skills you add per time window. Optional CI re-scans the registries on a schedule so the catalog
stays current.

This is the "what's out there worth evaluating" skill. It deliberately keeps third-party skills
separate from your own so you can approve or reject them one at a time.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/skill-registry-catalog/SKILL.md
```

## How to use

```
"Catalog the Discord, security, and MCP skills from skills.md and skillsmp.com,
 separated from my own library, and track how many I add per week."
```

The agent will:

1. Confirm which registries and focus categories you want.
2. Fetch the structured data from each registry's JSON API.
3. Filter by your categories and cross-reference against your local skill library.
4. Build a repo with per-skill folders, a master `CATALOG.md`, and a `README.md` counter block.
5. (Optional) Wire up CI to re-scan and update counters on a schedule.

## Sources and APIs

Two registries are supported out of the box. Always pull from the JSON API, not the HTML page.

| Registry | JSON API | Behavior |
|---|---|---|
| skills.md | `https://skills.md/api/skills` | Returns the full skill array in one response |
| skillsmp.com | `https://skillsmp.com/api/skills?page=N&limit=100` | Caps at 100 items/page — paginate until empty |

Both return one JSON object per skill with at least `name`, `description`, and a source URL
(skills.md adds `tags`/`category`; skillsmp.com adds `githubUrl`/`author`/`updatedAt`).

### Fetching skillsmp.com (paginated)

```python
import json, urllib.request

def fetch_skillsmp():
    out, page = [], 1
    while True:
        url = f"https://skillsmp.com/api/skills?page={page}&limit=100"
        with urllib.request.urlopen(url) as r:
            data = json.load(r)
        batch = data.get("skills", [])
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out
```

### Fetching skills.md

```python
import json, urllib.request

def fetch_skillsmd():
    with urllib.request.urlopen("https://skills.md/api/skills") as r:
        raw = r.read().decode()
    end = raw.find("}]") + 2          # guard against concatenated error HTML
    return json.loads(raw[:end])
```

### Known parsing quirks

- **skillsmp.com** ignores `limit` above 100 — loop until a short or empty page.
- **skills.md** `/api/skills` can append `===` and an HTML error page if several candidate URLs
  were fetched in one console call. Slice at the first `}]` before parsing.
- **skillsmp.com** has no search API (`/api/search?q=` is 404). Pull all pages and filter locally.

## Catalog structure

```
<repo>/
├── README.md            # overview + live COUNTERS block
├── CATALOG.md           # approved / pending / other
├── .github/workflows/   # validate.yml, counters.yml, rescan.yml
├── scripts/
│   ├── build_catalog.py # scrape + filter + write folders
│   └── counters.py      # time-window counter + README patcher
└── skills/
    ├── approved/<name>__<source>/{README.md, SKILL.md}
    └── pending/<name>__<source>/{README.md, SKILL.md}
```

Folder names join skill and source (`api-test-suite__skills.md`) so the same skill from two
registries never collides. Each per-skill `README.md` carries an `[ ] reviewed` checkbox so a
human can tick skills off one at a time.

### Per-skill SKILL.md frontmatter

```yaml
---
name: api-test-suite
source: https://skills.md/skills/api-test-suite
status: approved          # approved | pending
incorporated_as: api-test-suite   # only for approved
---
```

## Filtering

Categories are regex keyword maps over each skill's `name + description + tags + category/author`
(lower-cased). A skill lands in a category if any pattern matches.

```python
CATS = {
    "Discord":          [r"discord"],
    "Security/Pentest": [r"security", r"pentest", r"penetration", r"vuln", r"\baudit\b",
                         r"exploit", r"\bcve\b", r"secure", r"threat", r"secret",
                         r"\bauth\b", r"hardening"],
    "Backend":          [r"backend", r"server", r"\bdb\b", r"database", r"orm",
                         r"microservice", r"fastapi", r"django", r"express", r"\bsql\b"],
    "API":              [r"\bapi\b", r"\brest\b", r"graphql", r"openapi", r"endpoint",
                         r"webhook", r"\bsdk\b"],
    "MCP":              [r"\bmcp\b", r"model context protocol", r"mcp server", r"mcp client"],
}
```

### Approved vs pending

- **Approved** — the skill name or function overlaps a skill already in your local library, or it
  is a known upgrade of one you use.
- **Pending** — everything that fits a focus category but is not yet approved.
- **Other** — does not fit any focus category and is not approved; still recorded so re-scans are
  stable.

Match loosely but verify: require exact local-skill-name containment **or** an explicit
`known_upgrades` allowlist. Reject bare substring hits (`image`, `write`, `backend`) — they
over-match unrelated skills.

## Counters

The `README.md` holds a fenced block the counter script rewrites from git history:

```
<!-- COUNTERS_START -->
| Window | Skills Added |
|---|---|
| Past hour | 0 |
| Past 24h | 0 |
| Past 7d | 0 |
| Past 30d | 0 |
| Past 6mo | 0 |
| Past 1y | 0 |
| All time | 0 |
<!-- COUNTERS_END -->
```

`scripts/counters.py --patch` derives the numbers from the timestamps of added files under
`skills/`:

```bash
git log --diff-filter=A --name-only --pretty=%ct -- skills/ \
  | python scripts/counters.py --patch
```

## CI / automation

Use your git host's CI directory (GitHub `.github/workflows/`, Forgejo `.forgejo/workflows/`,
GitLab `.gitlab-ci.yml`). Put the token in a CI secret — never inline it.

- **validate.yml** — on push/PR, lint every `SKILL.md` for required frontmatter
  (`name`, `source`, `status`; `status ∈ {approved, pending}`).
- **counters.yml** — hourly + on push; runs `counters.py --patch` and commits if the block
  changed. Use `[skip ci]` in the commit message to avoid a self-trigger loop.
- **rescan.yml** — weekly; re-fetches both APIs, diffs new names against existing `skills/`, and
  opens one review issue per new focus skill. Labels generally need **numeric IDs** — fetch the
  label list first and map `name → id`.

## Requirements

- A local skill library to cross-reference against (so "approved" is meaningful).
- Network access to the registries' JSON APIs.
- A git host account and a token with repo/issue write scope for the optional automation.

## Pitfalls

- **Page caps** — skillsmp.com returns at most 100 items per call. Loop until short or empty.
- **Concatenated responses** — slice skills.md output at the first `}]` before `json.loads`.
- **No search API** — skillsmp.com `/api/search` is 404; filter the full pull locally.
- **False-positive approvals** — bare substring matches over-approve. Use exact-name or an
  allowlist.
- **CI loops** — counter commits must carry a skip directive or they re-trigger themselves.
- **Token scope** — repo/issue creation needs write scope; a read-only token fails with 403.

## Example end state

A repo where `CATALOG.md` lists 40 approved, 120 pending, 300 other skills; `README.md` shows
23 skills added in the past 7 days; and a Monday CI job opens five new review issues for skills
that appeared in the registries since last scan.
