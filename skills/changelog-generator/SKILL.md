---
name: changelog-generator
description: "Generate a changelog from git commits — agent + this skill = user gets a formatted changelog from project history."
version: 1.0.0
---

# changelog-generator

Generate a formatted changelog from git commit history. The agent reads commits, categorizes them by type (feat, fix, refactor, docs), and produces a Keep a Changelog-format document.

## When to Use

- The user wants a changelog for their project.
- The user wants to generate release notes from commits.
- The user says "make a changelog", "generate release notes", or "what changed since v1.0".

## Prerequisites

The project must be a git repository with conventional commit messages (feat:, fix:, refactor:, docs:, chore:).

## Generate from Commits

```python
import subprocess
import re
from collections import defaultdict

def get_commits(since: str = "", repo_path: str = ".") -> list:
    """Get commits with hash, date, and message."""
    cmd = ["git", "log", "--pretty=format:%H|%ai|%s"]
    if since:
        cmd.insert(2, f"{since}..HEAD")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    commits = []
    for line in result.stdout.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 2)
            commits.append({
                "hash": parts[0][:8],
                "date": parts[1][:10],
                "message": parts[2]
            })
    return commits

def categorize_commits(commits: list) -> dict:
    """Categorize commits by conventional commit type."""
    categories = defaultdict(list)
    for commit in commits:
        msg = commit["message"]
        match = re.match(r'(\w+)(\([^)]+\))?:\s*(.+)', msg)
        if match:
            cat = match.group(1)
            scope = match.group(2) or ""
            desc = match.group(3)
            categories[cat].append({
                "hash": commit["hash"],
                "scope": scope.strip("()"),
                "description": desc,
            })
        else:
            categories["other"].append({
                "hash": commit["hash"],
                "scope": "",
                "description": msg,
            })
    return dict(categories)

def generate_changelog(since: str = "", repo_path: str = ".") -> str:
    """Generate a Keep a Changelog formatted document."""
    commits = get_commits(since, repo_path)
    categorized = categorize_commits(commits)

    # Category display names and order
    category_map = {
        "feat": "Added",
        "fix": "Fixed",
        "refactor": "Changed",
        "docs": "Documentation",
        "chore": "Maintenance",
        "test": "Testing",
        "perf": "Performance",
        "other": "Other",
    }

    changelog = "# Changelog\n\n"
    for cat_key in ["feat", "fix", "refactor", "perf", "docs", "test", "chore", "other"]:
        if cat_key in categorized:
            display = category_map.get(cat_key, cat_key)
            changelog += f"## {display}\n\n"
            for item in categorized[cat_key]:
                scope = f"**{item['scope']}**: " if item["scope"] else ""
                changelog += f"- {scope}{item['description']} ({item['hash']})\n"
            changelog += "\n"

    return changangelog
```

## Conventional Commit Types

| Type | Maps to | Description |
|---|---|---|
| `feat:` | Added | New features |
| `fix:` | Fixed | Bug fixes |
| `refactor:` | Changed | Code restructuring |
| `perf:` | Performance | Performance improvements |
| `docs:` | Documentation | Documentation changes |
| `test:` | Testing | Test additions/changes |
| `chore:` | Maintenance | Build, deps, config |

## Workflow

1. Determine the range (since last tag, since a date, or all history)
2. Get commits with `git log`
3. Categorize by conventional commit prefix
4. Format as a Keep a Changelog document
5. Write to `CHANGELOG.md` or return as string

## Pitfalls

- **Non-conventional commits** — Commits without `feat:`/`fix:` prefixes go into "Other". Encourage the team to use conventional commits for better categorization.
- **Merge commits** — Merge commits clutter the changelog. Filter them with `--no-merges` in the git log command.
- **Squashed commits** — Squash commits lose individual messages. The changelog reflects the squash message, not the original commits.
- **Date range** — `since` should be a tag name (`v1.0.0`), a commit hash, or a date. Using a tag is most common for release notes.
- **Duplicate entries** — If commits are cherry-picked between branches, they may appear twice. Deduplicate by commit message.
