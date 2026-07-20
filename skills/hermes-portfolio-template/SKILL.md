---
name: hermes-portfolio-template
description: "Set up a skills portfolio repo with categorized, ranked, sortable skills — agent + this skill = user gets their own publishable skill portfolio structure."
version: 1.0.0
---

# hermes-portfolio-template

Scaffold a skills portfolio repository with the three-surface architecture: a monorepo of skills, a `skills-index.json` for agent-parseable metadata, a sortable static site, and CI validation. This is the meta-skill that reproduces the portfolio structure for anyone who wants to publish their own skills.

## When to Use

- The user wants to publish their own Hermes skills as a portfolio.
- The user wants a structured, categorized, ranked collection of skills (not just a flat directory).
- The user wants their skills to be discoverable by both humans (sortable site) and agents (structured index).
- The user says "set up a skills portfolio", "I want to publish my skills", or "make my skills installable".

## Prerequisites

- Git installed and configured
- A GitHub account (for the public shopfront)
- Hermes Agent installed (for `hermes skills install` to work for end users)
- Skills to publish — at least one `SKILL.md` with frontmatter

## Workflow

### Step 1: Create the repo structure

```
<portfolio-name>/
├── README.md                    ← the shopfront (Hallmark quality)
├── skills-index.json            ← single source of truth
├── skills-index.schema.json     ← schema for the index
├── LICENSE                      ← MIT recommended
├── .gitignore
├── docs/adr/                    ← architecture decisions
├── skills/                      ← one directory per skill
│   └── <skill-name>/
│       ├── SKILL.md
│       └── README.md
└── site/                        ← sortable static site
    ├── index.html
    ├── styles.css
    └── app.js
```

### Step 2: Create skills-index.json

The index is the single source of truth. Both the README and the static site render from it. Schema:

```json
{
  "version": "1.0.0",
  "generated_at": "ISO-8601 timestamp",
  "portfolio": {
    "name": "Your Portfolio Name",
    "owner": "Your Name",
    "tagline": "One sentence. No filler.",
    "total_skills": 0,
    "github_url": "https://github.com/your-user/your-portfolio"
  },
  "categories": {
    "devops": { "name": "DevOps", "description": "...", "skill_count": 0 },
    "frontend": { "name": "Frontend", "description": "...", "skill_count": 0 }
  },
  "skills": [
    {
      "name": "skill-name",
      "category": "devops",
      "tier": "core",
      "description": "One line. What agent + skill delivers.",
      "install_url": "https://github.com/your-user/your-portfolio/blob/main/skills/skill-name/SKILL.md",
      "path": "skills/skill-name",
      "usage": { "hub_installs": 0, "github_clones": 0, "stars": 0 },
      "recency": "2026-01-01",
      "source": "new",
      "source_attribution": ""
    }
  ]
}
```

### Step 3: Assign usefulness tiers

Every skill gets one of three tiers at publish time:

| Tier | Meaning |
|---|---|
| `core` | Broadly empowering, nearly any user benefits |
| `featured` | Highly useful within a category |
| `utility` | Useful for specific workflows |

This is a curated judgment, not a metric. It's the day-one ranking — usage data enriches it later but never replaces it.

### Step 4: Create the static site

The `site/` directory contains a self-contained HTML/CSS/JS app that:
- Fetches `skills-index.json` on page load
- Renders skill cards in a responsive grid
- Supports sorting (tier-then-usage default, plus usage/recency/category/alphabetical)
- Supports filtering (category, tier) and search
- Uses OKLCH colors, a real font pairing, no AI-slop patterns

See the portfolio's own `site/` directory for a working reference implementation.

### Step 5: Add CI validation

Create `.github/workflows/validate.yml` (or `.forgejo/workflows/validate.yml` for Forgejo):

```yaml
name: validate
on: push
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate SKILL.md frontmatter
        run: |
          for skill_md in skills/*/SKILL.md; do
            name=$(grep -m1 '^name:' "$skill_md" | sed 's/^name:[[:space:]]*//')
            [ -z "$name" ] && echo "FAIL: $skill_md missing name" && exit 1
          done
```

### Step 6: Write the README

The portfolio README is the shopfront. It should include:
- A one-sentence tagline (no filler)
- Install instructions for individual skills
- A categories table
- The ranking explanation (tiers + usage)
- The repo structure
- Links to ADRs (if any)
- License info

### Step 7: Publish

```bash
git init
git add -A
git commit -m "Initial portfolio scaffold"
git remote add origin https://github.com/<user>/<portfolio-name>.git
git push -u origin main
```

### Step 8: Add skills incrementally

Each new skill:
1. Create `skills/<skill-name>/SKILL.md` with frontmatter
2. Create `skills/<skill-name>/README.md` (Hallmark quality)
3. Add an entry to `skills-index.json`
4. Commit and push
5. The CI validates the frontmatter

## Skill Entry Requirements

Every skill in the portfolio must have:

| Requirement | Where | Notes |
|---|---|---|
| `SKILL.md` with frontmatter | `skills/<name>/SKILL.md` | `name`, `description`, `version` minimum |
| `README.md` | `skills/<name>/README.md` | What it does, install, how to use, example |
| Index entry | `skills-index.json` | name, category, tier, description, install_url, path, source |

## Pitfalls

- **Index drift** — If you add a skill directory but forget to add an entry to `skills-index.json`, the site won't show it and the CI should warn. Keep them in sync.
- **Relative links in README** — Links like `../other-skill/` break when a skill is published to its own repo via `skill-publish`. Use absolute URLs for cross-skill references.
- **Tier inflation** — Don't mark everything `core`. If all skills are core, the tier is meaningless. Reserve `core` for skills that nearly any user benefits from.
- **No categories** — Every skill must belong to a category. Uncategorized skills break the filter UI and the agent-parseable index.
- **Invented usage data** — Start all usage counts at 0. Don't fabricate install numbers — they'll be overwritten by real data once the portfolio has traffic, and fake numbers erode trust.
