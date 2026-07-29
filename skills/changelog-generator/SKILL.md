---
name: changelog-generator
description: Use when the user wants a changelog for their project, wants release notes generated from git history, or asks "make a changelog", "generate release notes", or "what changed since v1.0" — requires a git repo with conventional commit messages (feat:, fix:, refactor:, docs:).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [changelog, git-log, conventional-commits, release-notes]
    related_skills: [github-actions-ci, git-backup]
---

# changelog-generator

## Overview

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

    return changelog
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

## Common Pitfalls

1. **Non-conventional commits fall into "Other".** Commits without `feat:`/`fix:` prefixes get dumped in the catch-all bucket. Encourage the team to use conventional commits for better categorization, or the changelog will be mostly "Other".
2. **Merge commits clutter the output.** Merge commit messages (e.g. "Merge branch 'main'") add noise. Filter them with `--no-merges` in the `git log` command before categorizing.
3. **Squashed commits lose their history.** A squash-merged PR collapses many commits into one message; the changelog reflects only the squash message, not the individual changes.
4. **`since` must be a valid git ref.** Pass a tag name (`v1.0.0`), a commit hash, or a date — an arbitrary string that isn't a real ref makes `git log` silently return the full history instead of erroring.
5. **Cherry-picked commits appear twice.** If the same commit is cherry-picked across branches, it has a different hash on each branch and shows up as a duplicate entry. Deduplicate by commit message text, not hash, when merging changelogs across branches.

## Verification Checklist

- [ ] `generate_changelog()` was actually run against the target repo and returned non-empty output (not just defined)
- [ ] The `since` argument, if provided, is a real tag/commit/date confirmed to exist in the repo
- [ ] Merge commits were excluded (`--no-merges`) unless the user wants them included
- [ ] Output was spot-checked against `git log --oneline` for the same range to confirm no commits were silently dropped
- [ ] Written output file (if any) matches Keep a Changelog section ordering: Added, Fixed, Changed, Performance, Documentation, Testing, Maintenance, Other
