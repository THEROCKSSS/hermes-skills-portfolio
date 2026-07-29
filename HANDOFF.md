# Hermes Skills Portfolio — Handoff Document

## Session
- Session date: 2026-07-29 → 2026-07-30
- Agent: Claude Sonnet 5 (Claude Code), session `01JN2cT8SN8UKoPwsqYrunjL`
- Prior sessions: none — this was the first full session on the Cobalt redesign
- Repo: https://github.com/THEROCKSSS/hermes-skills-portfolio
- Live URL: https://therocksss.github.io/hermes-skills-portfolio/
- Local dev URL: `http://127.0.0.1:8092/` (serving `site/`), also reachable at `http://owens-pc-vpn.tailff2683.ts.net:8092/` over Tailscale — a detached `python -m http.server` process (started via PowerShell `Start-Process`, not a harness-tracked background task, since those kept dying unexpectedly in this session)

## Current state

`main` is pushed through the architecture-fix commit. CI green, GitHub Pages built and serving from `/docs`. Confirmed live:
- 51 skills, all schema-compliant (author/license/metadata/Common Pitfalls/Verification Checklist), content cache refreshed and matching the real files
- Four pages sharing one Cobalt design system: Catalog, Bundles, Changelog, Submit
- `hermes-portfolio-template` renamed to `skills-portfolio-scaffold`, confirmed via live search and old-URL-404 check
- 24 entries in the external-sourcing pending queue (16 recommended, 8 needs-review), all independently safety-vetted
- CI's site/docs parity check now globs every real file (was 4 hardcoded names, 2 already dead); `scripts/sync_site.py` replaces the manual per-file `cp`; the fetch-with-fallback pattern that was duplicated in `common.js`/`bundles.js`/`submit.js` is now one function (`HermesCommon.loadJsonWithFallback`)

## What was done (this session)

1. **Full Cobalt/Hallmark redesign** — locked a `design.md` design system, built four pages (Catalog = Ecosystem Index, Bundles = Index-First, Changelog = Index-First, Submit = Narrative Workflow) sharing `tokens.css`/`base.css`/`common.js`. Verified via real Playwright screenshots (no Camoufox tool available in this environment — used Playwright + Chromium instead, confirmed working).
2. **All 51 `SKILL.md` files rewritten** to the real Hermes agent skill schema (`author`/`license`/`metadata.hermes.{tags,related_skills}`, "Use when…" descriptions, `Common Pitfalls`, `Verification Checklist`) — done via 6 parallel subagents in disjoint batches, independently re-verified.
3. **Renamed** `hermes-portfolio-template` → `skills-portfolio-scaffold`, added an explicit "ask the user to name their own portfolio" step, updated all 4 cross-referencing skills and cached index content.
4. **Bundles page** — 6 real curated groupings of existing skills, each expandable with bulk install-command copy.
5. **External-sourcing pipeline** — researched 6 categories (frontend, backend, security, token-efficiency, testing/QA, productivity) via parallel research agents; added 22 vetted candidates to `pending-sources.json` (16 recommended, 8 needs-review with specific reasons) — **nothing here is merged into the live catalog; each entry needs your individual approval before it's credited/added.**
6. **Real mobile fixes** found via actual scroll-simulated screenshots: a permanently-stuck "Loading the full index…" placeholder, an unreadable/overflowing install command, tightened category-card spacing.
7. **Project docs added**: `CLAUDE.md`, `ARCHITECTURE.md`, rewrote `AGENTS.md` (was describing the old dark-default single-page site), `CHANGELOG.md` generated programmatically from real `git log` + `skills-index.json`.
8. **Live browser-tested** (subagent, Playwright) — found and fixed two real bugs: a stuck-invisible `IntersectionObserver` reveal (threshold `0.15` can never be satisfied by a section taller than ~6-7 viewport heights — now `threshold: 0`), and a self-inflicted CI failure (AGENTS.md quoted the exact strings its own forbidden-reference check scans for).
9. **New Claude Code skill**: `~/.claude/skills/project-foundation-docs/SKILL.md` — generates/refreshes this same five-doc set for any project, reuses `codebase-onboarding`'s reconnaissance rather than duplicating it.
10. **Architecture review** (`/improve-codebase-architecture`, run manually since it's user-invoke-only) — an Explore-agent survey found 6 real friction points. Two were live, currently-wrong bugs, fixed immediately (not deepening opportunities, just drift): `skills-index.json`'s cached skill content was stale for 46/51 skills; `changelog.js` was missing its two newest real commits. Presented the other four as an HTML report (sent to you, and opened locally).
11. **Implemented candidates A and B** from that report: fixed CI to glob-diff every real file instead of 4 hardcoded ones (2 already dead — deleted them), added `scripts/sync_site.py`, and consolidated the triplicated fetch-with-fallback pattern into `HermesCommon.loadJsonWithFallback`. **Candidates C and D deliberately not touched** — both need a design decision, not just code (see below).

## What's NOT done (the gap)

- **24 pending-sources entries await your individual approval.** None are live-credited. Promoting one means: add real `skills/<name>/SKILL.md`+`README.md`, add the `skills-index.json` entry with `source: "adapted"` + `source_attribution`, remove it from `pending-sources.json`, regenerate pages.
- **Architecture candidates C and D, not implemented — need your input first:**
  - **C — SKILL.md→site cache has no automated staleness check** (the exact bug that already hit 46/51 skills once this session). Open question: how strict should the check be — fail CI on any drift, or just warn? See `ARCHITECTURE.md`'s "Deliberately not automated yet" section.
  - **D — nav/footer hand-copied in 5 places** (design.md, 4 pages, `portfolio_tools.py`), no mechanical enforcement. Hasn't drifted yet. Real tension: any fix (even a verification-only CI check) is a small step away from this project's own stated "no build step" value — worth an explicit decision, not a silent call.
- **`docker-umbrella` label wraps awkwardly** on the Bundles page at some widths — minor, not investigated further.
- Two Anthropic-sourced pending candidates (`webapp-testing`, `frontend-aesthetic-direction`) are flagged needs-review specifically because they might duplicate existing catalog skills (`api-test-suite`, `frontend-design-toolkit`) — that overlap call hasn't been made.
- The `docx-authoring` pending candidate has a real license question (Anthropic's actual terms are more restrictive than "source-available" implies) that needs resolving before any approval.

## How to resume

1. Clone/pull: `git -C "C:\Users\User\Documents\Hermes stuff\hermes workspace\repos\hermes-skills-portfolio-canonical" pull` (or just `cd` there — it's a live checkout).
2. Local server, if not already running: check `curl http://127.0.0.1:8092/`; if dead, restart with:
   ```
   powershell -Command "Start-Process 'C:\Users\User\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe' -ArgumentList '-m http.server 8092 --directory \"C:\Users\User\Documents\Hermes stuff\hermes workspace\repos\hermes-skills-portfolio-canonical\site\" --bind 0.0.0.0' -WindowStyle Hidden"
   ```
3. Regenerate per-skill pages after any skill/template change: `python scripts/generate_skill_pages.py` (uses the hermes-agent venv Python, not plain `python`).
4. Run tests before pushing: `python -m pytest tests/`.
5. Push only after explicit go-ahead: `git push origin main`, then poll `gh api repos/THEROCKSSS/hermes-skills-portfolio/pages --jq '.status'` until `built`.

## Credentials / config

- GitHub: `gh` CLI already authenticated as `THEROCKSSS` (Owen's own account) — no separate token needed.
- No secrets live in this repo; nothing to configure beyond the venv Python path above.

## Known issues / blockers

- Background Bash-tool processes (`run_in_background: true`) were observed dying unexpectedly multiple times this session, unrelated to disk space (confirmed — disk had 49GB free when it happened). Workaround that held: launch via PowerShell `Start-Process -WindowStyle Hidden` instead — a real OS process, not tracked by the harness's background-task bookkeeping.
- No Camoufox or other browser-automation MCP tool is registered in this environment. Playwright + Chromium (`npm install playwright && npx playwright install chromium`) worked reliably all session and is the fallback.
- `page.screenshot({ fullPage: true })` does not trigger real scroll events — any `IntersectionObserver`-gated reveal can look broken in the screenshot even when it works for a real visitor. Verify with real incremental `window.scrollTo` simulation before trusting a "blank section" finding.

## Build order (if picking up the architecture candidates)

1. Candidate A (CI file-check fix) — cheapest, protects B/C/D from going unnoticed later.
2. Candidate B (fetch-with-fallback consolidation) — mechanical, low risk.
3. Candidate C (cache-staleness invariant) — needs a short design conversation (grilling) on how strict the check should be.
4. Candidate D (nav/footer enforcement) — needs the "no build step" tension resolved first; don't implement without that conversation.
