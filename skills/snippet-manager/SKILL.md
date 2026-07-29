---
name: snippet-manager
description: Use when the user wants to save a reusable code snippet for later, find a snippet they saved earlier, or build a searchable personal snippet library keyed by language and tags.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [code-snippets, snippet-library, markdown-frontmatter, search, cli-tooling]
    related_skills: [dotfiles-manage, file-organizer]
---

# snippet-manager

## Overview

Store, search, and retrieve reusable code snippets. The agent saves snippets with metadata (language, tags, description), searches by keyword or tag, and inserts snippets into files on demand.

## When to Use

- The user wants to save a useful code snippet for reuse.
- The user wants to find a snippet they saved earlier.
- The user wants to build a personal snippet library.
- The user says "save this snippet", "find my snippet for", or "I had code for this".

## Storage

Snippets are stored as individual files in a snippet directory:

```
~/.snippets/
├── python_http_get.md
├── js_debounce.md
├── bash_find_large_files.md
└── sql_upsert.md
```

Each snippet file has YAML frontmatter + the code:

```markdown
---
language: python
tags: [http, requests, api]
description: HTTP GET request with error handling and timeout
created: 2026-07-20
---

```python
import requests

def http_get(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
```
```

## Save a Snippet

```python
import os
from datetime import datetime
from pathlib import Path

def save_snippet(name: str, language: str, code: str, tags: list = None, description: str = "", snippet_dir: str = None):
    """Save a code snippet to the snippet library."""
    if snippet_dir is None:
        snippet_dir = os.path.expanduser("~/.snippets")
    Path(snippet_dir).mkdir(parents=True, exist_ok=True)

    filename = f"{name}.md"
    filepath = os.path.join(snippet_dir, filename)

    frontmatter = f"""---
language: {language}
tags: [{', '.join(tags or [])}]
description: {description}
created: {datetime.now().strftime('%Y-%m-%d')}
---

```{language}
{code}
```
"""
    with open(filepath, 'w') as f:
        f.write(frontmatter)
    return filepath
```

## Search Snippets

```python
import re

def search_snippets(query: str = "", tag: str = "", language: str = "", snippet_dir: str = None) -> list:
    """Search snippets by keyword, tag, or language."""
    if snippet_dir is None:
        snippet_dir = os.path.expanduser("~/.snippets")

    results = []
    for filepath in Path(snippet_dir).glob("*.md"):
        with open(filepath, 'r') as f:
            content = f.read()

        # Parse frontmatter
        fm_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if not fm_match:
            continue

        frontmatter = fm_match.group(1)
        body = fm_match.group(2)

        # Check filters
        match = True
        if language and f"language: {language}" not in frontmatter:
            match = False
        if tag and f"tags: [{tag}" not in frontmatter and f", {tag}" not in frontmatter:
            match = False
        if query and query.lower() not in content.lower():
            match = False

        if match:
            results.append({
                "file": filepath.name,
                "content": body.strip(),
                "frontmatter": frontmatter,
            })

    return results
```

## List All Snippets

```python
def list_snippets(snippet_dir: str = None) -> list:
    """List all saved snippets with metadata."""
    if snippet_dir is None:
        snippet_dir = os.path.expanduser("~/.snippets")

    snippets = []
    for filepath in Path(snippet_dir).glob("*.md"):
        with open(filepath, 'r') as f:
            content = f.read()
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            lang = re.search(r'language:\s*(\w+)', fm)
            desc = re.search(r'description:\s*(.+)', fm)
            snippets.append({
                "name": filepath.stem,
                "language": lang.group(1) if lang else "unknown",
                "description": desc.group(1).strip() if desc else "",
            })
    return snippets
```

## Workflow

1. **Save**: The user provides code + a name → save to `~/.snippets/name.md`
2. **Search**: The user asks for a snippet → search by keyword, tag, or language
3. **Insert**: The user wants to use a snippet → retrieve it and insert into the current file
4. **List**: Show all saved snippets with metadata

## Common Pitfalls

1. **Assuming `~/.snippets/` without checking.** If the user has a preferred location (e.g.,
   inside a dotfiles repo they already version-control), set `snippet_dir` explicitly rather than
   defaulting silently.
2. **Overwriting on name collision.** `save_snippet` writes `{name}.md` unconditionally — an
   existing file with the same name is silently clobbered. Check for the file first and warn or
   append a number.
3. **Trusting stored code without testing it.** Snippets are saved as-is with no syntax
   validation; a broken snippet stays broken until someone runs it.
4. **Malformed tags breaking search.** `search_snippets` matches tags via literal substrings like
   `tags: [{tag}` or `, {tag}`. Inconsistent spacing (`[tag1,tag2]` vs `[tag1, tag2]`) in the
   frontmatter you write will cause `search_snippets(tag=...)` to miss it later.
5. **Letting one file grow past a focused snippet.** Files over a few hundred lines make the
   library hard to search and defeat the "one function or pattern per file" model — split them.

## Verification Checklist

- [ ] Saved snippet file exists at `<snippet_dir>/<name>.md` with valid YAML frontmatter
      (`language`, `tags`, `description`, `created`) followed by a fenced code block.
- [ ] `search_snippets` with the snippet's own tag/language/keyword returns the new entry.
- [ ] No pre-existing snippet was silently overwritten by the save.
- [ ] `list_snippets` shows the correct `language` and `description` parsed from frontmatter.
