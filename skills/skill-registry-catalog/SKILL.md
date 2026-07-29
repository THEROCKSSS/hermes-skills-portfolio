---
name: skill-registry-catalog
description: Use when the user wants to survey public agent-skill registries (skills.md, skillsmp.com) for a domain and build a categorized, source-cited catalog repo with approved/pending buckets and live ingestion counters — not for organizing skills already adopted into the user's own library.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill-registry, cataloging, ci-automation, github-api, forgejo-api, skills-md]
    related_skills: [skill-publish, portfolio-upkeep, skills-portfolio-scaffold]
---

# skill-registry-catalog

## Overview

Build a categorized, source-cited catalog of third-party agent skills harvested from public
registries. Each skill is separated from your own library so it is easy to triage — approved
skills (matching your local library) and pending skills (awaiting human review) live in their
own folders, with a master `CATALOG.md` and live ingestion counters.

## When to Use

- Survey public skill registries (skills.md, skillsmp.com) for specific domains — Discord,
  security/pentest, backend, API, MCP, frontend, etc.
- Produce a repo the user can browse and approve/reject one skill at a time.
- Track ingestion volume over time (hour / day / week / month / year / all-time).
- The user asks to "look at these registries and catalog the skills" or "track external skills
  separated from my own."

## Sources

Two public registries are the defaults. Fetch structured data from their JSON APIs, not the
HTML pages.

| Registry | List page | JSON API | Notes |
|---|---|---|---|
| skills.md | `https://skills.md/skills` | `https://skills.md/api/skills` | Returns the full array in one call |
| skillsmp.com | `https://skillsmp.com/search` | `https://skillsmp.com/api/skills?page=N&limit=100` | Caps at 100/page — must paginate |

Fetch from `terminal` with `curl`/`urllib`, or from the browser console with `fetch()`. Keep
the HTML pages for visual confirmation only; the catalog data comes from the JSON.

### Response shapes (abridged)

skills.md element:
```json
{"name":"api-test-suite","displayName":"API Test Suite",
 "description":"Generate and run API test suites...","category":"Development Tools",
 "tags":["api","testing","automation","qa"],"pricing":{"tier":"free"},"source":"official"}
```

skillsmp.com element:
```json
{"id":"...","name":"openspec-apply-change","author":"Orient-Software-Development",
 "description":"...","githubUrl":"https://github.com/.../tree/main/.claude/skills/...",
 "stars":0,"updatedAt":"1783911957","path":"SKILL.md",
 "route":{"ownerSlug":"...","repoSlug":"...","routeSlug":"...","sourceSkillPath":"..."}}
```

### Parsing quirks (real, not theoretical)

- **skillsmp.com caps at 100 per response** even if you pass `limit=1000`. Paginate `page=1..N`
  until a page returns `[]` or fewer than 100 items:
  ```python
  all_sk = []
  for p in range(1, 30):
      d = json.load(urlopen(f"https://skillsmp.com/api/skills?page={p}&limit=100"))
      s = d.get("skills", [])
      if not s:
          break
      all_sk += s
  ```
- **skills.md `/api/skills`** can return the JSON array concatenated with `===` plus an HTML
  error page if multiple candidate URLs were fetched together in one console call. Slice before
  parsing:
  ```python
  raw = wrapper["result"]
  end = raw.find("}]") + 2
  skills = json.loads(raw[:end])
  ```
- **skillsmp.com `/api/search?q=` returns 404.** There is no text-search API — pull the full
  paginated `/api/skills` and filter client-side.

## Workflow

### 1. Confirm sources and categories
Agree the registries and focus categories with the user (e.g. Discord, Security/Pentest, Backend,
API, MCP). Categories are defined as regex keyword maps over each skill's
`name + description + tags + category/author` (lower-cased).

```python
CATS = {
  "Discord":         [r"discord"],
  "Security/Pentest":[r"security", r"pentest", r"penetration", r"vuln", r"\baudit\b",
                      r"exploit", r"\bcve\b", r"secure", r"threat", r"secret", r"\bauth\b",
                      r"hardening"],
  "Backend":         [r"backend", r"server", r"\bdb\b", r"database", r"orm", r"microservice",
                      r"fastapi", r"django", r"express", r"\bsql\b"],
  "API":             [r"\bapi\b", r"\brest\b", r"graphql", r"openapi", r"endpoint",
                      r"webhook", r"\bsdk\b"],
  "MCP":             [r"\bmcp\b", r"model context protocol", r"mcp server", r"mcp client"],
}
```

### 2. Extract + filter
- Pull both datasets as JSON (see quirks above).
- Run each skill through the category maps; a skill hits a category if any pattern matches.
- Cross-reference each skill name against the user's **local skill library** to decide
  approved vs pending (see Filtering).
- Dedupe by `(source, name)`.

### 3. Build the catalog repo
```
<repo>/
├── README.md            # overview + live COUNTERS block
├── CATALOG.md           # 3-bucket master list (approved / pending / other)
├── .github/workflows/   # validate.yml, counters.yml, rescan.yml
├── scripts/             # build_catalog.py, counters.py
└── skills/
    ├── approved/<name>__<source>/{README.md, SKILL.md}
    └── pending/<name>__<source>/{README.md, SKILL.md}
```
- Per-skill `SKILL.md` frontmatter: `name`, `source` (direct registry URL), `status`
  (`approved` | `pending`), `incorporated_as` (for approved).
- Per-skill `README.md`: description, metadata table, Original URL, an action checkbox for review.
- Folder names join skill and source so the same skill from two registries does not collide:
  `<name>__<source>` (e.g. `api-test-suite__skills.md`).

### 4. Cross-reference against local library
Decide `approved` vs `pending`:
- **Approved** — the skill's name or function overlaps an existing local skill, or it is a
  known upgrade of one you already use. Keep the match loose-but-verified.
- **Other** — does not fit any focus category and is not approved; still recorded so re-scans
  stay stable.
Require either exact local-skill-name containment **or** an explicit `known_upgrades` map
(e.g. `api-test-suite`, `backend-patterns`, `generate-dockerfile`, `repo-security-audit`,
`discord-suite`). Reject bare substring hits (`image`, `write`, `backend`) — they over-match.

## Catalog Structure

`CATALOG.md` is the master index with three buckets:

```markdown
# Catalog

## Approved (already in your library)
| Name | Source | Category | Local match |
|---|---|---|---|
| api-test-suite | skills.md | Backend/API | api-test-suite |

## Pending (awaiting review)
| Name | Source | Category | Original URL |
|---|---|---|---|
| some-new-skill | skillsmp.com | MCP | https://... |

## Other (out of focus, not approved)
| Name | Source | Category |
|---|---|---|
| ... | ... | ... |
```

Each per-skill folder has a self-contained `README.md` with an `[ ] reviewed` checkbox so a
human can tick skills off one at a time.

## Counters

The user wants time-window tracking. `README.md` carries a fenced block that the counter script
rewrites from git history:

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

`scripts/counters.py --patch` computes the counts from the commit timestamps of added files under
`skills/` and rewrites the block in place:

```bash
git log --diff-filter=A --name-only --pretty=%ct -- skills/ \
  | python scripts/counters.py --patch
```

## CI/Automation

Put three workflows in your git host's CI directory (GitHub: `.github/workflows/`; Forgejo:
`.forgejo/workflows/`; GitLab: `.gitlab-ci.yml`). Use `[skip ci]` in counter-commit messages to
avoid loops.

- **validate.yml** — on push/PR, lint every `SKILL.md` frontmatter (required: `name`, `source`,
  `status`; `status ∈ {approved, pending}`).
- **counters.yml** — scheduled hourly + on push; runs `counters.py --patch` and commits if the
  block changed.
- **rescan.yml** — scheduled weekly; re-fetches both APIs, diffs new names against existing
  `skills/` entries, and opens one review issue per new focus skill (labels: `pending-approval`,
  `source:*`, `cat:*`).

Issue posting uses your git host's REST API with a token. Labels usually require **numeric IDs**
(GitHub: `labels: [id,...]`), so fetch the label list first and map `name → id`. Never embed the
token in source; read it from a CI secret.

## Common Pitfalls

1. **Trusting a single `limit=1000` call on skillsmp.com.** The API caps at 100/page regardless
   of the requested limit. Loop `page=1..N` until a page returns `[]` or fewer than 100 items, or
   the catalog silently truncates.
2. **Parsing the skills.md response with a bare `json.loads`.** When multiple candidate URLs are
   fetched together in one console call, the response can be the JSON array concatenated with
   `===` plus a trailing HTML error page. Slice at the first `}]` before parsing.
3. **Calling `/api/search?q=` on skillsmp.com.** There is no text-search endpoint — it 404s. Pull
   the full paginated `/api/skills` and filter client-side instead.
4. **Approving on a bare substring match.** Matching `image`, `write`, or `backend` as a
   substring over-matches unrelated skills. Require exact local-skill-name containment or an
   explicit `known_upgrades` map before marking a skill `approved`.
5. **Declaring the catalog "done."** It's a living artifact — re-scans keep adding entries. Hand
   the live repo URL to the user for visual verification instead of self-certifying completion.
6. **Letting the counters workflow commit without `[skip ci]`.** A counter-update commit that
   doesn't skip CI retriggers the same workflow, creating a commit loop.
7. **Using a read-only token for issue/label creation.** The `rescan.yml` workflow needs write
   scope on the target repo; a read-only token fails with 403. Labels also usually require
   numeric IDs — fetch the label list first and map `name → id`.

## Verification Checklist

- [ ] Both registries pulled from their JSON APIs (not scraped HTML), with skillsmp.com paginated
      to a page returning `[]` or `< 100` items.
- [ ] Every entry deduped by `(source, name)` before it lands in `CATALOG.md`.
- [ ] Every `approved` entry has a verified local-skill-name match or an explicit upgrade-map hit
      — no bare substring approvals.
- [ ] `CATALOG.md`'s three buckets (Approved / Pending / Other) match the per-skill folders under
      `skills/approved/` and `skills/pending/`.
- [ ] The `COUNTERS_START`/`COUNTERS_END` block reflects real git history, not placeholder zeros.
- [ ] `validate.yml`, `counters.yml`, and `rescan.yml` are present and counter/rescan commits
      include `[skip ci]`.
