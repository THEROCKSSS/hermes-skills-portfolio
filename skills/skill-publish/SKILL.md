---
name: skill-publish
description: Use when the user wants a single skill from a skills monorepo published to its own dedicated GitHub repo with a standalone README, separate from the monorepo — triggers include "publish this skill", "give this skill its own repo", or "spotlight this skill".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [publishing, github, monorepo, skill-distribution, readme-generation]
    related_skills: [portfolio-upkeep, skills-portfolio-scaffold, skill-registry-catalog]
---

# skill-publish

## Overview

Extract one skill from a skills monorepo and publish it into its own dedicated GitHub repository with a self-contained README. This is the per-skill spotlight flow — the monorepo stays the source of truth, the per-skill repo is a derived artifact for discoverability.

## When to Use

- The user wants to give one skill its own GitHub repo with its own page, separate from the monorepo.
- The user says "publish this skill", "give this skill its own repo", or "spotlight this skill".
- The user wants a single skill to be more discoverable than it would be inside a monorepo.

## Prerequisites

1. **A skills monorepo** with skills in `skills/<skill-name>/` directories.
2. **GitHub authentication** — a GitHub personal access token with `repo` scope. Set as `GITHUB_TOKEN` or `GH_TOKEN` environment variable, or use `gh auth login`.
3. **The skill to publish** must have a valid `SKILL.md` with frontmatter (`name`, `description` minimum).

## Workflow

### Step 1: Identify the skill to publish

Confirm the skill name with the user. The skill must exist in the monorepo at `skills/<skill-name>/`.

```bash
# Verify the skill exists
ls skills/<skill-name>/SKILL.md
```

Read the SKILL.md frontmatter to get the skill name and description.

### Step 2: Create a temporary staging directory

```bash
STAGING_DIR="/tmp/skill-publish-<skill-name>"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy the skill directory
cp -r skills/<skill-name>/* "$STAGING_DIR/"
```

### Step 3: Generate a standalone README

If the skill already has a `README.md`, polish it for standalone context. If not, generate one from the SKILL.md content:

```markdown
# <skill-name>

<description from frontmatter>

## What it does
<2-3 sentences from the SKILL.md body>

## Install
\`\`\`bash
hermes skills install https://github.com/<user>/<skill-name>/blob/main/SKILL.md
\`\`\`

## How to use
<from the SKILL.md workflow section>
```

The README must be self-contained — no references to a parent monorepo, no relative links that assume the reader is inside a larger repo.

### Step 4: Create the GitHub repository

Use the GitHub CLI or API:

```bash
# Using gh CLI
gh repo create <skill-name> --public --description "<description from frontmatter>" --source "$STAGING_DIR" --push

# Or using the API
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"<skill-name>\",\"description\":\"<description>\",\"public\":true}"
```

### Step 5: Initialize git and push

```bash
cd "$STAGING_DIR"
git init
git checkout -b main
git add -A
git commit -m "Publish <skill-name> — standalone skill repo"
git remote add origin https://github.com/<user>/<skill-name>.git
git push -u origin main
```

### Step 6: Verify

```bash
# Check the repo is public and the SKILL.md is accessible
curl -s -o /dev/null -w "%{http_code}" https://github.com/<user>/<skill-name>/blob/main/SKILL.md
# Should return 200
```

### Step 7: Return the URL to the user

```
Published: https://github.com/<user>/<skill-name>
Install: hermes skills install https://github.com/<user>/<skill-name>/blob/main/SKILL.md
```

### Step 8: Clean up

```bash
rm -rf "$STAGING_DIR"
```

## Configuration

The skill reads these from the user's environment or asks interactively:

| Setting | Env var | Default | Notes |
|---|---|---|---|
| GitHub username | `GITHUB_USER` | asks user | The repo will be created under this user/org |
| GitHub token | `GITHUB_TOKEN` or `GH_TOKEN` | asks user | Needs `repo` scope |
| Repo visibility | — | public | Can be set to private if the user asks |

## Common Pitfalls

1. **Token lacks `repo` scope.** A read-only GitHub token fails repo creation with 403 — generate one with `repo` scope at https://github.com/settings/tokens.
2. **Repo name collision.** Creation fails with 422 if a repo with the same name already exists — pick a different name or delete the existing repo first.
3. **Relative links surviving extraction.** Links like `../other-skill/` work inside the monorepo but break in a standalone repo — rewrite the README with absolute URLs or self-contained paths.
4. **Missing frontmatter blocking README generation.** If SKILL.md lacks `name` or `description`, the publish fails at the README-generation step — validate frontmatter before starting.
5. **Large files slowing or failing the push.** Binaries or datasets in the skill directory can make the push slow or fail — add a `.gitignore` to the staging dir for large/generated files.
6. **Editing the spotlight repo directly.** The monorepo is the source of truth — changes made only in the per-skill repo get lost on the next publish; always edit the monorepo first, then re-publish.

## Verification Checklist

- [ ] `skills/<skill-name>/SKILL.md` frontmatter has both `name` and `description` before starting
- [ ] Staging directory copy matches the monorepo skill directory (no missing files)
- [ ] README rewritten with no relative links back into the monorepo
- [ ] New GitHub repo created and push succeeded (`git push -u origin main` returned no errors)
- [ ] `curl -o /dev/null -w "%{http_code}"` against the published SKILL.md URL returns 200
- [ ] Staging directory cleaned up (`rm -rf "$STAGING_DIR"`) after a successful publish
