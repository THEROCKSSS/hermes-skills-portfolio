# Hermes Skills Portfolio — Handoff Document

## Session
- Session date: 2026-08-03 (commit + browser verification; work performed 2026-08-02)
- Agent: Claude Opus 5 (Claude Code)
- Prior sessions: 2026-07-29 → 07-30 (Cobalt redesign, Claude Sonnet 5, session `01JN2cT8SN8UKoPwsqYrunjL`)
- Repo: https://github.com/THEROCKSSS/hermes-skills-portfolio
- Live URL: https://therocksss.github.io/hermes-skills-portfolio/
- Canonical checkout: `repos/hermes-skills-portfolio-canonical` — **not** `projects/hermes-skills-portfolio`, which was an unconnected stale duplicate and is now archived (see below)

## Current state

**Pushed and live.** `main` is at `7dd1a33`, CI is green, Pages rebuilt, and https://therocksss.github.io/hermes-skills-portfolio/ now serves the Dusk build. The full 41-check UI suite was re-run **against the live URL**, not just localhost: all pass, no console errors.

Verified before and after the push: 193 tests, every blocking CI gate (frontmatter YAML parse, install-URL installability, sitemap/feed currency, invented-metric lint, content-cache staleness, index/directory sync, forbidden references, site↔docs parity, per-skill pages, provenance).

- 57 skills, all schema-compliant, content cache verified in sync
- Site themed **Dusk** with a persistent sidebar-filter catalog; `design.md` is the locked source of truth
- Submission/review pipeline defined in `REVIEW.md` and three workflows
- 24 entries still pending in the external-sourcing queue, none live-credited

## What was done

**2026-08-02 (the work), committed 2026-08-03 as `fde09ae`:**

1. **Dusk re-theme.** A prototype put 10 layouts × 5 skins = 50 combinations on one route against the real `skills-index.json`, so density and copy length stayed honest. Owen picked **L4 sidebar filter + S5 Dusk**. Rewritten for production rather than promoted as-is; `design.md` records it. The separate distribution charts were dropped — sidebar facet counts are the same numbers, so each facet row now draws a proportional bar and one surface answers both "filter this" and "how is the catalog shaped". Prototype preserved at `.backups/hermes-skills-portfolio-catalog-prototype-2026-08-02` with its `VERDICT.md`.
2. **Stale duplicate archived.** `projects/hermes-skills-portfolio` held 301 generated skill dirs against this repo's 51 real ones, had no git remote, used a pre-Cobalt design, and documented broken `blob/` install URLs. Verified unreferenced by `docker/`, `config/`, `scripts/`, `cron-jobs/`, `links.json`, `snapshot.json`, then moved to `.backups/hermes-skills-portfolio-STALE-DUPLICATE-2026-08-02` with restore instructions in its `ARCHIVED.md`.
3. **Submission pipeline.** `REVIEW.md` (5 states, 6 `decline:<reason>` labels, each saying what would change the answer), a `skill_request.yml` issue form, and `quality.yml` / `skill-review.yml` / `skill-submission.yml`.
4. **Architecture candidate C closed.** CI now runs `refresh_content_cache.py --check` — the drift that once hit 46/51 skills now fails the build. Frontmatter is now a real YAML parse (the old grep passed a file with an unquoted colon in its description), install URLs are proven raw rather than blob, sitemap/feed are proven current, and invented metrics are linted.
5. **Catalog 51 → 57**, media domain: `tmdb-metadata`, `media-id-mapping`, `movie-catalogue-site`, `movie-night-calendar`, `streaming-provider-embeds`, `watchlist-sync`.
6. **Changelog deduplicated** into `changelog-data.js`, read by both the catalog's "What's new" and the changelog page.
7. **Generated discovery surface**: `feed.xml`, `sitemap.xml`, `robots.txt`. **Docker**: `Dockerfile`, `docker-compose.yml`, `deploy/`. **Ten scripts** with six test files.

**2026-08-03 (browser verification + push), commits `03de143`, `af1e3e0`, `7dd1a33`:**

8. **Two `[hidden]` elements were rendering anyway.** `[hidden]` is `display:none` by UA stylesheet only, so any component rule setting `display` outranks it — the element stays on screen while the script and the a11y tree both believe it's hidden. `#no-results` printed "No skills match those filters." in a 210px block under a full 57-card grid on every load; `#back-to-top` sat on screen at scroll 0. Neither showed up in the JS, and CI passed both. Fixed with one `[hidden] { display: none !important }` in the base layer, which also closes it for the four other elements that toggle the same way. `verify_ui.js` now asserts on computed style, not the attribute.
9. **CI had never actually run the test suite.** The step added in `fde09ae` had no dependency install beside it and died on "No module named pytest" — it passed locally only because the dev venv has pytest. `ci.yml` now pins Python 3.11 and installs pyyaml + pytest; `quality.yml` installs pytest and still deliberately omits PyYAML so the checker's stdlib fallback is genuinely exercised (verified: the fallback passes all 57 with the yaml import blocked).
10. **The content-cache check meant different things on different platforms.** It passed on Windows and failed on CI with 20 stale fields that had no content difference behind them. `refresh_content_cache.py` read with `newline=""`, so a Windows checkout (`core.autocrlf=true`) baked CRLF into `skills-index.json`, which then disagreed with every Linux checkout. `_read` now folds CRLF/CR to LF; cache regenerated (70 fields, zero CR left). It had never run on a Linux checkout before this push, which is why it was never caught.
11. **Bundles copy fix** — the intro said every listed skill "already exists above", left from the single-page era. Bundles has its own route now.

## What's NOT done (the gap)

- **24 pending-sources entries await individual approval.** Promoting one means: add real `skills/<name>/SKILL.md`+`README.md`, add the `skills-index.json` entry with `source: "adapted"` + `source_attribution`, remove from `pending-sources.json`, regenerate. Specific open questions: `docx-authoring` has a real licensing question (Anthropic's terms are more restrictive than "source-available" implies); `webapp-testing` and `frontend-aesthetic-direction` may duplicate `api-test-suite` and `frontend-design-toolkit`.
- **Architecture candidate D — nav/footer hand-copied in 5 places** (design.md, 4 pages, `portfolio_tools.py`), still no mechanical enforcement, still undecided. The real tension: any fix, even a verification-only CI check, is a step toward a build step this project deliberately doesn't have. Needs an explicit decision, not a silent call.
- **3 advisory tier-consistency items** (`tailscale-deploy`, `forgejo-self-host`, `api-test-suite` are `tier=core` with tool-scoped descriptions). Pre-existing, non-blocking, judgment call not yet made.
- **`docker-umbrella` label wraps awkwardly** on Bundles at some widths — minor, uninvestigated.
- **`actions/checkout@v4` and `setup-python@v5` raise a Node 20 deprecation warning** on every run. Not failing yet; the bump wasn't made because it's unrelated to the fixes it would have ridden in with.
- **A `.gitattributes` enforcing LF was considered and not added.** Normalizing inside `refresh_content_cache.py` makes the cache platform-independent on its own; forcing checkout line endings repo-wide is a bigger change than the bug required. Worth revisiting if another derived artifact shows the same Windows/Linux split.

## How to resume

1. `cd "C:\Users\User\Documents\Hermes stuff\hermes workspace\repos\hermes-skills-portfolio-canonical"` — it's a live checkout.
2. Local server: `python -m http.server 8092 --directory site --bind 0.0.0.0`. Bind `0.0.0.0`, not `127.0.0.1`, and report the Tailscale URL (`tailscale status` for the hostname) alongside localhost — Owen tests from his phone.
3. Regenerate per-skill pages after any skill/template change: `python scripts/generate_skill_pages.py`. Use the venv interpreter (`C:\Users\User\AppData\Local\hermes\hermes-agent\venv\Scripts\python`), not plain `python`.
4. After changing skills or changelog data, regenerate derived files: `generate_feed.py`, `generate_sitemap.py`, then `sync_site.py`.
5. Before pushing: `python -m pytest tests/`, then push only on explicit go-ahead, then poll `gh api repos/THEROCKSSS/hermes-skills-portfolio/pages --jq '.status'` until `built`.

## Credentials / config

- GitHub: `gh` authenticated as `THEROCKSSS`; repo-local git identity already matches. No separate token needed.
- No secrets in this repo. The staged diff was scanned for token/key patterns before committing — clean.

## Known issues / blockers

- Inline `python -c "... open(...)"` one-liners fail on this Windows box with `UnicodeDecodeError: 'charmap' codec` against `skills-index.json` — Python defaults to cp1252 locally. CI runs on ubuntu-latest where the default is UTF-8, so `ci.yml`'s inline steps are fine as written; pass `encoding='utf-8'` when reproducing those checks locally.
- Background Bash-tool processes (`run_in_background: true`) were observed dying unexpectedly in the July session, unrelated to disk space. Workaround that held: PowerShell `Start-Process -WindowStyle Hidden`.
- `page.screenshot({ fullPage: true })` does not trigger real scroll events, so `IntersectionObserver` reveals can look broken in a screenshot that works fine for a real visitor. Scroll incrementally with `window.scrollTo` before asserting. `deviceScaleFactor: 2` inflates PNG pixel height, not real CSS height — divide before treating it as scroll height.
- No Camoufox/browser MCP tool is registered here. Playwright + Chromium (`npm install playwright && npx playwright install chromium`) works.
