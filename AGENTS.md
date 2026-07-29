# AGENTS.md

Instructions for AI agents (Claude, GPT, Hermes, Cursor, etc.) working on this repository.

## Project Overview

A public portfolio of empowering skills for the Hermes agent platform. Each skill lives in `skills/<name>/` with a `SKILL.md` (agent instructions) and `README.md` (human-facing docs). A four-page static site in `docs/` (mirrored from `site/`) renders the portfolio on GitHub Pages — Catalog, Bundles, Changelog, Submit a skill — sharing one locked design system.

**Read `design.md` before touching any page.** It is the single source of truth for the visual system (theme, tokens, nav/footer markup, per-page macrostructure) — see `design.md` § What pages MUST share. Read `ARCHITECTURE.md` for how the pieces fit together and data flows. Read `CONTEXT.md` for the project's locked scope decisions and vocabulary.

## Repository Structure

```
skills/<name>/SKILL.md      Agent instructions (YAML frontmatter + markdown body)
skills/<name>/README.md     Human-facing documentation
skills-index.json            Master index: all skills with tier, category, usage, full content
bundles.json                 Curated groupings of existing skills (Bundles page data)
pending-sources.json         External-sourcing review queue (Submit page data)
CHANGELOG.md                 Generated from real git log + skills-index.json recency — do not hand-edit, regenerate
design.md                    Locked design system — read before any site change
ARCHITECTURE.md              How the pieces fit together, data flow, generator scripts
site/                        Source static site (HTML/CSS/JS, no framework, no build step)
  index.html, bundles.html, changelog.html, submit.html
  css/tokens.css, css/base.css   — shared, do not edit per page
  css/catalog.css, css/bundles.css, css/changelog.css, css/submit.css, css/skill-page.css
  js/common.js                — shared theme/cmd-k/toast/copy/reveal utilities, do not edit per page
  js/catalog.js, js/bundles.js, js/changelog.js, js/submit.js, js/skill-page.js
  skills/<name>/index.html    — generated static per-skill pages (OG tags for link unfurling)
docs/                         Deployed copy of site/ — what GitHub Pages actually serves
scripts/portfolio_tools.py    Generator: builds skills-index.json entries + renders per-skill pages
scripts/generate_skill_pages.py  CLI entrypoint — run after any skill or template change
tests/                       pytest suite for the generator
.forgejo/workflows/           Forgejo CI
.github/workflows/            GitHub Actions CI
CONTEXT.md                    Project glossary and locked decisions
```

## Conventions

### Skills
- Every `SKILL.md` must have full frontmatter: `name`, `description` (starts with "Use when…", trigger conditions only — never a workflow summary), `version`, `author`, `license`, `metadata.hermes.tags`, `metadata.hermes.related_skills` (only reference names that exist under `skills/`).
- Body structure: `# Title` → `## Overview` → `## When to Use` → topic body → `## Common Pitfalls` (numbered, specific to that skill) → `## Verification Checklist` (checkboxes).
- Categories: `devops`, `frontend`, `backend`, `utility`, `meta`, `integrations`.
- Tiers: `core` (broadly useful), `featured` (category-strong), `utility` (specific workflows).
- Source types: `new` (originally authored), `generalized` (adapted from internal patterns), `adapted` (from external repos with attribution).
- If a skill is adapted from an external repo, set `source_attribution` in `skills-index.json`. The site links to the original source.
- `skills-index.json` caches each skill's rendered `skillmd_content`/`readme_content` — if you edit a `SKILL.md`/`README.md` by hand, you must also refresh that skill's cached copy in `skills-index.json` (the generator does this automatically; a raw file edit alone will not update what the site shows).

### External sourcing (pending-sources.json)
- A separate track from community-submitted issues: the maintainer proposing an existing skill found in another public repo.
- Every entry requires: real repo verified to exist, a permissive license noted precisely (don't call something "open source" if it's source-available/restricted), and a documented safety read (checked for prompt-injection phrasing, destructive commands, obfuscation, exfiltration) before it's added — even to the pending list.
- `review_recommendation: "recommended" | "needs_review"` is the proposer's assessment, not an approval. Nothing in this file is live in the catalog or credited until the maintainer approves it individually — never flip an entry into `skills-index.json` without that explicit approval.

### Static Site
- `design.md` is the source of truth for the visual system. `site/` is the source of truth for implementation; after any change, sync to `docs/` (see Verification Checklist).
- No build step, no framework, no npm dependencies. Plain HTML/CSS/JS.
- **Light mode is the default**, dark is a toggle (localStorage-persisted) — this is a deliberate Cobalt-theme decision recorded in `design.md`, not the project's original convention.
- OKLCH color tokens in `site/css/tokens.css`. Reference tokens by name — never inline raw OKLCH/hex/rgb values, never an inline `font-family`.
- Fonts: Space Grotesk (display) + Inter (body) + JetBrains Mono (code/labels), loaded via Google Fonts.
- The nav and footer markup must stay byte-identical across all four pages (only `aria-current` differs) — the canonical copy lives in `design.md`.

### CI
- Both Forgejo and GitHub Actions validate: every `SKILL.md` has required frontmatter, `skills-index.json` is in sync with skill directories, `site/`/`docs/` are byte-identical, no forbidden internal-infrastructure references leak into public files (see the workflow file for the exact pattern list — don't quote the patterns here, or you'll trip the check that scans this very file), and every skill has a rendered per-skill page.

## How to Add a Skill

1. Create `skills/<name>/SKILL.md` with full frontmatter (see Conventions above) and the required body structure.
2. Create `skills/<name>/README.md` with human-facing docs.
3. Add an entry to `skills-index.json` with all required fields (see existing entries for schema).
4. Run `python scripts/generate_skill_pages.py` to render the new static per-skill page and refresh cached content — run it as its own command (the sandbox can terminate a single process writing ~100 files across `site/` and `docs/`).
5. Sync `site/` to `docs/` for anything you touched directly (`cp site/index.html docs/`, etc. — there is no single sync-everything script yet, see `ARCHITECTURE.md`).
6. Commit with a message like: `Add <name> skill (<tier> tier, <category>)`.

## How to Change the Site

1. Read `design.md` first — it locks genre, theme, macrostructure per page, and the shared nav/footer/tokens.
2. Never introduce a different theme "for variety" — variety lives in macrostructure/component choice, not palette.
3. Never edit `site/css/tokens.css` or `site/css/base.css` per-page — they're shared; add page-specific rules to that page's own CSS file.
4. `site/js/common.js` owns theme, cmd-k, toast, copy-to-clipboard, and reveal-on-scroll — call into it, don't reimplement.
5. Sync `site/` → `docs/` for every file you touched.
6. Regenerate `CHANGELOG.md` after committing (see `scripts/` or the changelog-regeneration steps in `ARCHITECTURE.md`) — don't hand-edit it.

## What NOT to Do

- Do not reference internal infrastructure, local paths, or private identities in any public file.
- Do not add npm dependencies, build tools, or frameworks to the static site.
- Do not change the LICENSE without explicit owner approval.
- Do not remove the `docs/` directory — it powers GitHub Pages.
- Do not push to `main` without passing CI.
- Do not invent metrics, testimonials, or usage numbers anywhere — all `usage` counts start at 0 and stay real.
- Do not merge or credit anything from `pending-sources.json` into `skills-index.json` without the maintainer's explicit per-entry approval.

## Verification Checklist

Before submitting a PR:
- [ ] `SKILL.md` has full required frontmatter (see Conventions)
- [ ] `skills-index.json` is in sync with `skills/` directories (same count)
- [ ] `site/` and `docs/` are byte-identical for every file you touched
- [ ] Nav/footer markup unchanged except `aria-current`, matches `design.md`
- [ ] No inline OKLCH/hex/rgb color or inline `font-family` in any CSS you touched
- [ ] No references to private infrastructure or identities
- [ ] `python -m pytest tests/` passes
- [ ] Site renders correctly (open `docs/index.html` in a browser, or run a local static server)
