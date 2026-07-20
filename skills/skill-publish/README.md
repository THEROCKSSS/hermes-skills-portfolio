# skill-publish

Publish one skill from a monorepo into its own dedicated GitHub repo with a standalone README.

## What it does

The agent extracts a single skill from a skills monorepo, generates a self-contained README, creates a new public GitHub repo for that skill, and pushes it. The monorepo stays the source of truth — the per-skill repo is a spotlight artifact for discoverability.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/skill-publish/SKILL.md
```

## How to use

```
"Publish the tailscale-deploy skill to its own GitHub repo"
```

The agent:
1. Reads the skill from `skills/tailscale-deploy/` in your monorepo
2. Generates a standalone README (rewrites relative links, adds install instructions)
3. Creates `https://github.com/<your-user>/tailscale-deploy`
4. Pushes the skill files
5. Returns the repo URL and the one-line install command

## Prerequisites

- A skills monorepo with skills in `skills/<name>/` directories
- A GitHub personal access token with `repo` scope (set as `GITHUB_TOKEN` or use `gh auth login`)
- The skill to publish must have a `SKILL.md` with `name` and `description` frontmatter

## What you get

- A public GitHub repo containing one skill, self-contained
- A standalone README with install instructions pointing to the new repo
- The skill is installable via `hermes skills install <url>` from the new repo
- The monorepo is unchanged — the per-skill repo is a derived artifact

## Example

```
User: "Give the hallmark-readme skill its own repo"

Agent:
  1. Reads skills/hallmark-readme/SKILL.md → name: hallmark-readme, description: "..."
  2. Stages the skill files to a temp directory
  3. Generates a standalone README.md (rewrites relative links)
  4. Creates repo: gh repo create hallmark-readme --public
  5. Pushes: git push -u origin main
  6. Returns: "Published at https://github.com/your-user/hallmark-readme"

The skill is now installable from its own repo:
  hermes skills install https://github.com/your-user/hallmark-readme/blob/main/SKILL.md
```
