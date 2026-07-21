# Hermes Skills Portfolio

Empowering skills for the Hermes agent — install one, your agent can now do that for you.

by **Owen**

---

## What this is

A curated portfolio of ~50 skills for [Hermes Agent](https://hermes-agent.nousresearch.com). Each skill follows one pattern: **agent + this skill = you get a working capability**. Not a tutorial. Not a reference. A skill that makes your agent able to deliver an outcome — deploy a service on Tailscale, generate a non-generic frontend, build a Discord bot, self-host Forgejo, publish a skill to GitHub.

Skills are categorized, ranked by usefulness and usage, and sortable. Browse the [static site](./site/index.html) or read `skills-index.json` directly.

## Install any skill

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/<skill-name>/SKILL.md
```

Or clone the repo and install from a local path:

```bash
git clone https://github.com/THEROCKSSS/hermes-skills-portfolio
hermes skills install ./hermes-skills-portfolio/skills/<skill-name>/SKILL.md
```

## Categories

| Category | What it covers |
|---|---|
| DevOps & Infrastructure | Deploy, host, and operate services |
| Frontend | Build distinctive, non-generic UIs |
| Backend | APIs, tests, and server-side architecture |
| Utility | General-purpose capabilities for everyday workflows |
| Meta | Skills about skills — portfolios, publishing, catalogs |
| Integrations | Connect agents to external platforms and services |

## Ranking

Every skill is assigned a **usefulness tier** at publish time:

- **Core** — broadly empowering, nearly any user benefits
- **Featured** — highly useful within a category
- **Utility** — useful for specific workflows

The default sort is tier (Core → Featured → Utility), then usage within tier. Usage data (Hermes hub installs, GitHub clones, self-reported users) accumulates over time and enriches the ranking.

Agents can read `skills-index.json` in one parse to recommend skills — no markdown prose parsing required.

## Skills

_Skills are added in phases. The index is rebuilt as skills land. See `skills-index.json` for the current list._

<!-- SKILLS_TABLE_START -->
<!-- The skills table is generated from skills-index.json by a refresh script. -->
<!-- During Phase 1 (scaffold), this section is intentionally empty. -->
<!-- SKILLS_TABLE_END -->

## Repository structure

```
hermes-skills-portfolio/
├── README.md                  ← you are here
├── CONTEXT.md                 ← domain glossary (terms and definitions)
├── skills-index.json          ← single source of truth for the portfolio
├── skills-index.schema.json   ← JSON schema for the index
├── LICENSE                    ← MIT
├── docs/adr/                  ← architecture decision records
├── skills/                    ← one directory per skill
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── README.md
│       ├── references/
│       ├── scripts/
│       └── templates/
├── .forgejo/workflows/        ← CI: validate frontmatter + index sync
└── site/                      ← static sortable portfolio site
    ├── index.html
    ├── styles.css
    └── app.js
```

## Skill sources

The ~50 skills come from three sources:

1. **Generalized** (~15-20) — personal-utility skills reworked for public use, with profile-specific coupling stripped.
2. **Newly authored** (~15-20) — original skills for common capability gaps.
3. **Adapted** (~10-15) — third-party skills reworked and published with source attribution.

Adapted skills cite their original author and URL in their README and in `skills-index.json` under `source_attribution`.

## Architecture decisions

- [ADR 0001 — Skills-only, GitHub shopfront, Forgejo mirror](./docs/adr/0001-skills-only-github-shopfront-forgejo-mirror.md)
- [ADR 0002 — Three-surface repo architecture](./docs/adr/0002-three-surface-repo-architecture.md)
- [ADR 0003 — Two-axis skill ranking](./docs/adr/0003-two-axis-skill-ranking.md)
- [ADR 0004 — Five-phase build order](./docs/adr/0004-five-phase-build-order.md)

## For contributors

Each skill must have:

- `SKILL.md` with frontmatter: `name`, `description`, `version` (minimum)
- `README.md` with: what it does, how to install, how to use, one example
- An entry in `skills-index.json` with: name, category, tier, description, install_url, path, source, source_attribution (if adapted)

The CI workflow (`.forgejo/workflows/validate.yml`) lints every `SKILL.md` for required frontmatter and checks `skills-index.json` sync. Run locally:

```bash
# Validate all skills have frontmatter
for skill_md in skills/*/SKILL.md; do
  name=$(grep -m1 '^name:' "$skill_md" | sed 's/^name:[[:space:]]*//')
  [ -z "$name" ] && echo "FAIL: $skill_md missing name"
done
```

## License

MIT — see [LICENSE](./LICENSE). Adapted skills retain their original license where it differs.

## Status

Phase 1 (scaffold) complete. Skills are added in phases — Core tier first, then Featured, then Utility. See the [ADRs](./docs/adr/) for the full build plan.
