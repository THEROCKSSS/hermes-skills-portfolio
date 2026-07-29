# Architecture

How the Hermes Skills Portfolio actually fits together. Read `design.md` for the visual system and `AGENTS.md` for contribution conventions — this file is about data flow and code structure.

## The shape of the system

A static site with **no backend and no build step**. Everything is plain HTML/CSS/JS plus two data files, generated and validated by a small Python toolchain, deployed by GitHub Pages serving `/docs`.

```
                    ┌─────────────────────┐
   skills/<name>/   │  skills-index.json  │   pending-sources.json
   SKILL.md +   ───▶│  (single source of  │   bundles.json
   README.md        │   truth for the     │   (independent data files,
        ▲           │   live catalog)     │    read directly by their
        │           └──────────┬──────────┘    own pages)
        │                      │
   scripts/portfolio_tools.py  │  fetched at runtime by every page's JS
   (validates + renders,       ▼
    caches SKILL.md/README.md  site/*.html + site/css/* + site/js/*
    content INTO the index)    (source of truth for the site)
                               │
                               │  manual sync (cp), see AGENTS.md
                               ▼
                          docs/*  (what GitHub Pages actually serves)
```

## Data files — three, deliberately separate

- **`skills-index.json`** — the live, approved catalog. 51 skills, each with tier/category/description/install_url/usage/`skillmd_content`/`readme_content`. This is the only file the Catalog, Changelog (recency), and Bundles pages treat as ground truth for *what skills exist*.
- **`bundles.json`** — curated groupings. Each bundle just lists real skill *names*; the Bundles page resolves those names against `skills-index.json` at render time, so a bundle can never show a description that drifts from the real catalog entry.
- **`pending-sources.json`** — the external-sourcing review queue. Deliberately **not** merged into `skills-index.json` — nothing here is live or credited until the maintainer approves an individual entry and someone manually promotes it (adds the real `skills/<name>/` files, adds the index entry, sets `source: "adapted"` + `source_attribution`, removes the pending entry).

## The generator (`scripts/`)

- **`portfolio_tools.py`** — the actual logic:
  - `render_skill_page(skill, categories, base_url)` — builds one static `skills/<name>/index.html` (the crawler-friendly page with baked Open Graph tags, used for Discord/Slack/Twitter unfurls). Also owns the shared nav/footer markup for this page type — keep it matching `design.md` if the nav ever changes.
  - `validate_portfolio_data(index, skill_dirs)` — the same frontmatter/count checks CI runs, callable locally before you push.
  - `generate_all_pages(index_path, site_dir, docs_dir, base_url)` — the orchestrator: renders every skill's page into both `site/skills/` and `docs/skills/`.
  - `_agent_use_to_html`, `build_meta_description`, `_escape` — rendering helpers.
- **`generate_skill_pages.py`** — the CLI entrypoint (`python scripts/generate_skill_pages.py`). Run this after adding/editing any skill or after changing the page template in `portfolio_tools.py`. It regenerates all 51 pages in both `site/skills/` and `docs/skills/` in one pass.
- **`enrich_provenance.py`** — a separate, narrower script for backfilling `source_attribution` fields; not part of the main add-a-skill flow.
- **`tests/test_portfolio_tools.py`** — pytest suite covering `portfolio_tools.py` (escaping, OG/Twitter metadata correctness, provenance fixture handling). Run `python -m pytest tests/` before pushing.

**What the generator does NOT do:** it doesn't touch `bundles.json`, `pending-sources.json`, or any of the four main page HTML/CSS/JS files. Those are hand-maintained.

## The site (`site/`, mirrored to `docs/`)

Four pages, one shared foundation, per `design.md`:

| File | Macrostructure | Owns |
|---|---|---|
| `index.html` + `css/catalog.css` + `js/catalog.js` | Ecosystem Index | Hero, featured/core rail, category+tier browse, quickstart band, full search/sort/filter grid, skill detail overlay |
| `bundles.html` + `css/bundles.css` + `js/bundles.js` | Index-First | Curated bundle list, expand/collapse, bulk install-command copy |
| `changelog.html` + `css/changelog.css` + `js/changelog.js` | Index-First | Real git-log-derived dated entries + recency-derived "N new skills," selection checkboxes, Discord-formatted copy |
| `submit.html` + `css/submit.css` + `js/submit.js` | Narrative Workflow | The real (partly manual) submission pipeline explained honestly, plus the pending-sources review queue |

Shared, never duplicated per page:
- **`css/tokens.css`** — every color/font/space/motion/z-index token. Light-default, dark-toggle (Cobalt inverts fully for dark mode; see the `[data-theme="dark"]` block).
- **`css/base.css`** — reset, nav (bordered bar + working ⌘K palette), footer, buttons (8-state), toast, reveal-on-scroll base rules.
- **`js/common.js`** — `window.HermesCommon`: `loadIndex`, `escapeHtml`, `highlightText`, `canonicalSkillUrl`, `showToast`, `copyToClipboard`, `initReveal`, `initCmdk`. Every page script calls into this rather than reimplementing theme/search/copy/reveal logic.

**A real pitfall already hit once:** `initReveal`'s `IntersectionObserver` threshold must stay `0` (fire on any visibility), not a percentage — a percentage threshold silently never fires for any section taller than roughly `1/threshold` viewport heights, since that fraction of a very tall element's box can never be simultaneously visible. This broke the Submit page's `pending-sources` section once it grew past ~5000px tall (fixed 2026-07-29).

## Skill detail: two renderings of the same content, one source

A skill's full write-up appears in two places that must never drift apart:
1. **The catalog's detail overlay** (`index.html` / `catalog.js`) — fetched client-side from `skills-index.json`'s cached `skillmd_content`/`readme_content`.
2. **The dedicated static page** (`skills/<name>/index.html`) — pre-rendered at generation time from the same fields, for crawlers that don't run JS.

Both read from `skills-index.json`. If you hand-edit a `skills/<name>/SKILL.md`, its cached copy in `skills-index.json` is now stale until you either re-run the generator or manually refresh the two cached fields — the site will keep showing the old text otherwise.

## CI (`.github/workflows/ci.yml`, mirrored in `.forgejo/workflows/`)

Validates on every push: SKILL.md frontmatter presence, `skills-index.json` count matches `skills/` directory count, `site/`↔`docs/` byte parity, no forbidden internal-reference strings, every skill has a rendered per-skill page.

## Deliberately not automated yet

- **`CHANGELOG.md` / `changelog.js`'s `COMMITS` array** are a point-in-time snapshot of `git log` output, manually appended after each meaningful commit — not regenerated automatically on every push. (This already drifted once — two real commits went briefly missing from `changelog.js` until caught by an architecture review, not CI.)
- **Promoting a `pending-sources.json` entry into the live catalog** is a manual, human-reviewed action — by design, not an oversight (see `design.md`'s honesty rules and `AGENTS.md`'s external-sourcing conventions).

## Automated as of the 2026-07-30 architecture review

An Explore-agent survey (via `/improve-codebase-architecture`) found real friction, not theoretical: CI's site/docs parity check only diffed 4 hardcoded filenames — 2 of them (`app.js`, `styles.css`) dead and unreferenced since the Cobalt redesign — while the real site had grown to 4 pages plus 7 CSS files and 6 JS files CI never touched. Fixed:

- **`scripts/sync_site.py`** — syncs every real file under `site/` into `docs/` (excluding `site/skills/`, which `generate_skill_pages.py` owns), plus the root `skills-index.json`. Run this instead of a manual `cp` per file.
- **CI's parity check** (`.github/workflows/ci.yml`) now globs every file under `site/` against its `docs/` counterpart, rather than checking a fixed list that silently stops covering new files.
- The two dead files (`site/app.js`, `site/styles.css` and their `docs/` copies) were deleted — confirmed zero references first.
- **`HermesCommon.loadJsonWithFallback(paths, cb)`** — the "try `./x.json`, then `../x.json`, then `/x.json`" fetch pattern was duplicated verbatim in `common.js`'s `loadIndex`, `bundles.js`'s `loadBundles`, and `submit.js`'s `loadPendingSources`. Consolidated into one function in `common.js`; the three named functions are now one-line callers.

Two further candidates from that review were **not** implemented — they need a design decision first, not just code: whether `skills-index.json`'s cached skill content should have an automated staleness check (it drifted for 46/51 skills once already), and whether the nav/footer markup hand-copied across 5 places (this file, `design.md`, 4 pages, `portfolio_tools.py`) should get a verification check, given the project's own "no build step" value is in some tension with adding one.
