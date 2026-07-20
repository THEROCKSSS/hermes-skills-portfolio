# portfolio-upkeep

Maintain and update a Hermes skills portfolio — sync site files, enrich the index, validate skills, and push.

## What it does

The agent syncs site files from `site/` to `docs/` for GitHub Pages, enriches `skills-index.json` with `agent_use`, `user_use`, `skillmd_content`, and `readme_content` fields extracted from each skill's files, validates that all skill directories have proper frontmatter and index entries, and pushes updates to both Forgejo and GitHub. Run this after adding, updating, or removing skills.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/portfolio-upkeep/SKILL.md
```

## How to use

```
"Update the portfolio — I added a new skill"
```

The agent:
1. Validates all skill directories (SKILL.md, README.md, frontmatter)
2. Enriches skills-index.json with agent_use, user_use, skillmd_content, readme_content
3. Syncs site files to docs/
4. Commits and pushes to Forgejo + GitHub
5. Waits for GitHub Pages to rebuild
6. Verifies the live site

## Example

```
User: "I updated the tailscale-deploy skill. Sync the portfolio."

Agent:
  1. Validates: all 50 skills OK
  2. Enriches: updates tailscale-deploy's skillmd_content + agent_use
  3. Syncs: copies index.html, styles.css, app.js, skills-index.json to docs/
  4. Commits: "Upkeep: sync site, enrich index after tailscale-deploy update"
  5. Pushes to Forgejo + GitHub
  6. Verifies: https://therocksss.github.io/hermes-skills-portfolio/ returns 200
```
