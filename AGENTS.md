# AGENTS.md

Instructions for AI agents (Claude, GPT, Hermes, Cursor, etc.) working on this repository.

## Project Overview

This is a public portfolio of empowering skills for the Hermes agent platform. Each skill lives in `skills/<name>/` with a `SKILL.md` (agent instructions) and `README.md` (human-facing docs). A static site in `docs/` (mirrored from `site/`) renders the portfolio on GitHub Pages with sorting, filtering, search, and detail pages.

## Repository Structure

```
skills/<name>/SKILL.md    — Agent instructions (YAML frontmatter + markdown body)
skills/<name>/README.md   — Human-facing documentation
skills-index.json          — Master index: all skills with tier, category, usage, content
site/                      — Source static site (HTML/CSS/JS, no framework)
docs/                      — Deployed copy of site/ (served by GitHub Pages)
.forgejo/workflows/        — Forgejo CI
.github/workflows/         — GitHub Actions CI
CONTEXT.md                 — Project glossary and locked decisions
```

## Conventions

### Skills
- Every `SKILL.md` must have YAML frontmatter with `name` and `description` (required by CI).
- Skills are categorized into: DevOps & Infrastructure, Backend, Frontend, Integrations, Utility, Meta.
- Tiers: `core` (broadly useful), `featured` (category-strong), `utility` (specific workflows).
- Source types: `new` (originally authored), `generalized` (adapted from internal patterns), `adapted` (from external repos with attribution).
- If a skill is adapted from an external repo, set `source_attribution` in `skills-index.json` to the original repo URL. The site will display a "View original source" link.

### Static Site
- `site/` is the source of truth. After changes, sync to `docs/`: `cp site/* docs/`.
- No build step, no framework, no npm dependencies. Plain HTML/CSS/JS.
- Dark mode is the default. Light mode is a toggle.
- OKLCH color tokens defined in `:root` in `styles.css`. Reference tokens by name, never inline raw values.
- Fonts: Inter (body) + JetBrains Mono (code). Loaded via Google Fonts.

### CI
- Both Forgejo and GitHub Actions run the same validation: every `SKILL.md` must have required frontmatter, and `skills-index.json` must be in sync with skill directories.

## How to Add a Skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, `version`).
2. Create `skills/<name>/README.md` with human-facing docs.
3. Add an entry to `skills-index.json` with all required fields (see existing entries for schema).
4. Sync `site/` to `docs/` if the site needs updating.
5. Commit with a message like: `Add <name> skill (<tier> tier, <category>)`.

## What NOT to Do

- Do not reference internal infrastructure, local paths, or private identities in any public file.
- Do not add npm dependencies, build tools, or frameworks to the static site.
- Do not change the LICENSE without explicit owner approval.
- Do not remove the `docs/` directory — it powers GitHub Pages.
- Do not push to `main` without passing CI.

## Verification Checklist

Before submitting a PR:
- [ ] `SKILL.md` has `name` and `description` in frontmatter
- [ ] `skills-index.json` is in sync with `skills/` directories
- [ ] `site/` and `docs/` are in sync
- [ ] No references to private infrastructure or identities
- [ ] Site renders correctly (open `docs/index.html` in a browser)
