---
name: markdown-linter
description: "Lint markdown files for consistency and common issues — agent + this skill = user gets clean, consistent documentation."
version: 1.0.0
---

# markdown-linter

Check markdown files for common issues: inconsistent heading levels, broken links, missing alt text, trailing whitespace, and formatting inconsistencies. The agent scans markdown files and reports a fixable punch list.

## When to Use

- The user wants to check their markdown for issues.
- The user is preparing documentation for publication.
- The user wants consistent markdown across a project.
- The user says "check my markdown", "lint this doc", or "fix markdown issues".

## Checks

```python
import re
from pathlib import Path

def lint_markdown(filepath: str) -> list:
    """Run all markdown linting checks and return issues."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
        content = "".join(lines)

    issues = []

    # 1. Heading levels should not skip (h1 → h3 is bad)
    heading_levels = []
    for i, line in enumerate(lines, 1):
        match = re.match(r'^(#{1,6})\s', line)
        if match:
            level = len(match.group(1))
            heading_levels.append((i, level))

    for j, (line_num, level) in enumerate(heading_levels):
        if j > 0:
            prev_level = heading_levels[j-1][1]
            if level > prev_level + 1:
                issues.append({
                    "line": line_num,
                    "rule": "heading-skip",
                    "message": f"Heading level {level} skips from h{prev_level} — should be h{prev_level+1} max"
                })

    # 2. Multiple h1 headings
    h1_count = sum(1 for _, level in heading_levels if level == 1)
    if h1_count > 1:
        issues.append({
            "line": 0,
            "rule": "multiple-h1",
            "message": f"Found {h1_count} h1 headings — should have only one"
        })

    # 3. Trailing whitespace
    for i, line in enumerate(lines, 1):
        if line.rstrip() != line and line.strip():
            issues.append({
                "line": i,
                "rule": "trailing-whitespace",
                "message": "Trailing whitespace at end of line"
            })

    # 4. Images without alt text
    for i, line in enumerate(lines, 1):
        for match in re.finditer(r'!\[([^\]]*)\]\([^\)]+\)', line):
            alt = match.group(1)
            if not alt.strip():
                issues.append({
                    "line": i,
                    "rule": "missing-alt-text",
                    "message": "Image has no alt text"
                })

    # 5. Links without text
    for i, line in enumerate(lines, 1):
        for match in re.finditer(r'\[([^\]]*)\]\([^\)]+\)', line):
            text = match.group(1)
            if not text.strip() and not line.startswith('!'):
                issues.append({
                    "line": i,
                    "rule": "empty-link-text",
                    "message": "Link has no display text"
                })

    # 6. Inconsistent list markers (mixing - and *)
    dash_lists = sum(1 for line in lines if re.match(r'^\s*-\s', line))
    star_lists = sum(1 for line in lines if re.match(r'^\s*\*\s', line))
    if dash_lists > 0 and star_lists > 0:
        issues.append({
            "line": 0,
            "rule": "mixed-list-markers",
            "message": f"Mixed list markers: {dash_lists} dash, {star_lists} asterisk — pick one"
        })

    # 7. Code blocks without language
    in_code_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
            else:
                lang = stripped[3:].strip()
                if not lang:
                    issues.append({
                        "line": i,
                        "rule": "missing-code-language",
                        "message": "Code block has no language specified"
                    })
                in_code_block = True

    # 8. Lines too long (over 120 chars, excluding URLs and tables)
    for i, line in enumerate(lines, 1):
        if len(line.rstrip()) > 120 and not line.strip().startswith("|") and "http" not in line:
            issues.append({
                "line": i,
                "rule": "line-too-long",
                "message": f"Line is {len(line.rstrip())} chars (max 120 recommended)"
            })

    return sorted(issues, key=lambda x: x["line"])
```

## Auto-fix

```python
def fix_markdown(filepath: str) -> dict:
    """Auto-fix simple markdown issues."""
    with open(filepath, 'r') as f:
        content = f.read()

    fixes = 0

    # Fix trailing whitespace
    lines = content.split("\n")
    fixed_lines = []
    for line in lines:
        fixed = line.rstrip()
        if fixed != line:
            fixes += 1
        fixed_lines.append(fixed)

    # Normalize list markers (use - consistently)
    for i, line in enumerate(fixed_lines):
        if re.match(r'^(\s*)\*\s', line):
            fixed_lines[i] = re.sub(r'^(\s*)\*\s', r'\1- ', line)
            fixes += 1

    with open(filepath, 'w') as f:
        f.write("\n".join(fixed_lines))

    return {"fixes": fixes, "file": filepath}
```

## Workflow

1. Run `lint_markdown` to get all issues
2. Present issues sorted by line number
3. Offer to auto-fix trailing whitespace and list markers
4. For other issues, show the line and suggested fix
5. Let the user decide which to fix

## Pitfalls

- **Frontmatter** — YAML frontmatter (between `---` lines) is not markdown. Skip it during linting.
- **Tables** — Table rows can be long. The line-length check skips lines starting with `|`.
- **URLs** — Long URLs make lines long. The check skips lines containing `http`.
- **Nested code blocks** — Code blocks inside code blocks (quarto, mdx) can confuse the parser. The `in_code_block` toggle handles simple cases.
- **Auto-fix is conservative** — Only fixes whitespace and list markers. Heading levels, alt text, and link text require manual judgment.
