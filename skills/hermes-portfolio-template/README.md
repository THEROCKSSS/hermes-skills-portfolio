# hermes-portfolio-template

Scaffold a publishable skills portfolio with categorized, ranked, sortable skills and a static site.

## What it does

The agent creates a portfolio repo structure for your skills: a monorepo with one directory per skill, a `skills-index.json` that serves as the single source of truth (for both humans and agents), a sortable static site, CI validation, and a Hallmark-quality README. This is the meta-skill that reproduces the portfolio structure so anyone can publish their own skills the same way.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/hermes-portfolio-template/SKILL.md
```

## How to use

```
"Set up a skills portfolio for my Hermes skills"
```

The agent:
1. Creates the repo structure (README, skills-index.json, site/, docs/adr/, skills/, CI workflow)
2. Sets up the JSON schema for the index
3. Generates the sortable static site (HTML/CSS/JS)
4. Creates the CI validation workflow
5. Shows you how to add skills incrementally

## What you get

| Component | Purpose |
|---|---|
| `skills-index.json` | Single source of truth — agents parse this, the site renders from it |
| `site/` | Sortable, filterable static site (sort by tier, usage, category, recency) |
| `skills/<name>/` | One directory per skill, each with SKILL.md + README.md |
| CI workflow | Validates every SKILL.md has required frontmatter |
| README.md | The shopfront — install instructions, categories, ranking explanation |

## The ranking model

Every skill gets a usefulness tier at publish time:

- **Core** — broadly empowering, nearly any user benefits
- **Featured** — highly useful within a category
- **Utility** — useful for specific workflows

Default sort: tier (Core → Featured → Utility), then usage within tier. Usage data accumulates over time from hub installs and GitHub clones.

## Example

```
User: "I have 15 Hermes skills I want to publish as a portfolio."

Agent:
  1. Creates the repo structure with skills-index.json schema
  2. Generates the sortable static site
  3. For each of the 15 skills: creates skills/<name>/ with SKILL.md + README.md
  4. Adds each skill to skills-index.json with category + tier
  5. Creates the CI workflow
  6. Returns: "Portfolio scaffolded. Push to GitHub when ready."

User pushes to GitHub → strangers can browse the site, install individual skills,
and agents can read skills-index.json to recommend skills.
```
