---
name: portfolio-upkeep
description: Use when a skill has been added or updated in a Hermes skills portfolio and the site/index need to catch up — syncing site/ to docs/, enriching skills-index.json, validating frontmatter, or pushing to Forgejo and GitHub Pages. Triggers include "update the portfolio", "sync the site", "refresh the index", or "publish changes".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [portfolio, skills-index, github-pages, forgejo, sync, validation]
    related_skills: [skills-portfolio-scaffold, skill-publish, skill-registry-catalog]
---

# portfolio-upkeep

## Overview

Maintain and update a Hermes skills portfolio. The agent syncs site files to the docs/ directory, enriches skills-index.json with agent_use/user_use/skillmd_content/readme_content fields, validates skill frontmatter, and pushes updates to Forgejo and GitHub Pages.

## When to Use

- The user added or updated a skill and wants the portfolio site updated.
- The user wants to sync site/ files to docs/ for GitHub Pages.
- The user wants to validate all skills have correct frontmatter and index entries.
- The user says "update the portfolio", "sync the site", "refresh the index", or "publish changes".

## Prerequisites

- A portfolio repo with the structure described in `skills-portfolio-scaffold`
- Git remotes for both Forgejo and GitHub
- GitHub Pages enabled on the GitHub repo (serving from /docs)

## Sync Site Files to docs/

The site files live in `site/` but GitHub Pages serves from `docs/`. Sync them:

```python
import shutil, os

REPO_PATH = "path/to/hermes-skills-portfolio"

# Files to sync
site_files = ["index.html", "styles.css", "app.js"]
for filename in site_files:
    src = os.path.join(REPO_PATH, "site", filename)
    dst = os.path.join(REPO_PATH, "docs", filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Synced {filename}")

# Also copy skills-index.json to docs/
shutil.copy2(
    os.path.join(REPO_PATH, "skills-index.json"),
    os.path.join(REPO_PATH, "docs", "skills-index.json")
)
print("Synced skills-index.json")
```

## Enrich skills-index.json

When skills are added or updated, the index needs enrichment fields:

```python
import json, os, re

INDEX_PATH = os.path.join(REPO_PATH, "skills-index.json")
SKILLS_DIR = os.path.join(REPO_PATH, "skills")

with open(INDEX_PATH, 'r') as f:
    index = json.load(f)

for skill in index["skills"]:
    skill_path = os.path.join(SKILLS_DIR, skill["name"], "SKILL.md")
    readme_path = os.path.join(SKILLS_DIR, skill["name"], "README.md")

    # Read SKILL.md
    skillmd_content = ""
    if os.path.exists(skill_path):
        with open(skill_path, 'r', encoding='utf-8') as f:
            skillmd_content = f.read()

    # Read README.md
    readme_content = ""
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()

    # Extract "When to Use" from SKILL.md as agent_use
    agent_use = ""
    when_match = re.search(r'## When to Use\s*\n(.*?)(?=\n## |\Z)', skillmd_content, re.DOTALL)
    if when_match:
        agent_use = when_match.group(1).strip()

    # Extract "What it does" from README.md as user_use
    user_use = ""
    what_match = re.search(r'## What it does\s*\n(.*?)(?=\n## |\Z)', readme_content, re.DOTALL)
    if what_match:
        user_use = what_match.group(1).strip()

    # Update fields
    skill["agent_use"] = agent_use
    skill["user_use"] = user_use
    skill["skillmd_content"] = skillmd_content
    skill["readme_content"] = readme_content

# Write enriched index
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

# Also write to docs/
shutil.copy2(INDEX_PATH, os.path.join(REPO_PATH, "docs", "skills-index.json"))
```

## Validate Skills

Check that every skill directory has the required files and the index is in sync:

```python
def validate_portfolio(repo_path):
    skills_dir = os.path.join(repo_path, "skills")
    index_path = os.path.join(repo_path, "skills-index.json")

    with open(index_path, 'r') as f:
        index = json.load(f)

    index_names = {s["name"] for s in index["skills"]}
    dir_names = {d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))}

    issues = []

    # Skills in directories but not in index
    for name in dir_names - index_names:
        issues.append(f"Directory skills/{name}/ exists but not in skills-index.json")

    # Skills in index but no directory
    for name in index_names - dir_names:
        issues.append(f"skills-index.json has '{name}' but no directory exists")

    # Check each skill has SKILL.md and README.md
    for name in dir_names:
        skill_path = os.path.join(skills_dir, name)
        if not os.path.exists(os.path.join(skill_path, "SKILL.md")):
            issues.append(f"skills/{name}/SKILL.md missing")
        if not os.path.exists(os.path.join(skill_path, "README.md")):
            issues.append(f"skills/{name}/README.md missing")

    # Check frontmatter
    for name in dir_names:
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.exists(skill_md):
            with open(skill_md, 'r') as f:
                content = f.read(200)
            if not re.search(r'^name:\s*' + re.escape(name), content, re.MULTILINE):
                issues.append(f"skills/{name}/SKILL.md frontmatter name doesn't match directory name")

    return issues
```

## Full Upkeep Workflow

1. **Validate** — run `validate_portfolio()` to check for missing files, index drift, or frontmatter issues
2. **Enrich** — run the enrichment script to update agent_use, user_use, skillmd_content, readme_content in the index
3. **Sync** — copy site files and skills-index.json to docs/
4. **Commit** — `git add -A && git commit -m "Upkeep: sync site, enrich index, validate skills"`
5. **Push** — push to both Forgejo and GitHub:
   ```bash
   git push forgejo main
   git push origin main
   ```
6. **Verify** — wait 60-90 seconds for GitHub Pages to rebuild, then check the live URL

## Adding a New Skill

When adding a new skill to the portfolio:

1. Create `skills/<skill-name>/SKILL.md` with proper frontmatter (name, description, version)
2. Create `skills/<skill-name>/README.md` with "What it does" section
3. Add an entry to `skills-index.json` with: name, category, tier, description, install_url, path, source, usage (zeros), recency, source_attribution, frontmatter
4. Run the enrichment script to add agent_use, user_use, skillmd_content, readme_content
5. Sync to docs/
6. Commit and push

## Updating an Existing Skill

1. Edit the SKILL.md and/or README.md in the skill directory
2. Update the entry in `skills-index.json` if the description, tier, or category changed
3. Run the enrichment script (it overwrites agent_use, user_use, skillmd_content, readme_content from the files)
4. Sync to docs/
5. Commit and push

## Common Pitfalls

1. **docs/ drift.** The most common upkeep issue — you update site/ files but forget to copy them to docs/. GitHub Pages serves from docs/, so the live site shows stale content. Always run the sync step.
2. **Index bloat.** skills-index.json with embedded content can reach 500KB+ for 50 skills. Fine for a static site (loads once, cached by the browser), but be aware of it when committing.
3. **Frontmatter mismatch.** The `name` field in SKILL.md frontmatter must match the directory name — easy to forget when renaming a skill; the validation script catches it.
4. **GitHub Pages build time.** After pushing, GitHub Pages takes 60-90 seconds to rebuild — don't verify the live URL immediately.
5. **Forgejo and GitHub out of sync.** Always push to both remotes. Pushing only one leaves the review surface (Forgejo) and the public site (GitHub) diverged.
6. **Missing user_use field.** If a README lacks a "What it does" section, user_use stays empty and the site falls back to the raw description — add the section instead.

## Verification Checklist

- [ ] `validate_portfolio()` returns zero issues (no missing files, no index drift, no frontmatter mismatch)
- [ ] docs/ files match site/ files after the sync step
- [ ] docs/skills-index.json matches the root skills-index.json
- [ ] Pushed to both `forgejo main` and `origin main`
- [ ] Waited 60+ seconds and confirmed the live GitHub Pages URL reflects the change
- [ ] Every skill directory has both SKILL.md and README.md, and each README has a "What it does" section
