# markdown-linter

Check markdown files for consistency, broken links, missing alt text, and common formatting issues.

## What it does

The agent scans a markdown file and checks for 8 common issues: heading level skips, multiple h1s, trailing whitespace, missing image alt text, empty link text, mixed list markers, code blocks without language, and lines over 120 chars. Reports a sorted punch list with line numbers. Can auto-fix trailing whitespace and normalize list markers.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/markdown-linter/SKILL.md
```

## How to use

```
"Lint my README.md"
```

The agent:
1. Runs all 8 checks
2. Reports issues sorted by line number
3. Offers to auto-fix trailing whitespace and list markers

## Checks

| Rule | What it catches |
|---|---|
| heading-skip | h1 → h3 (skipping h2) |
| multiple-h1 | More than one # heading |
| trailing-whitespace | Spaces at end of lines |
| missing-alt-text | Images without alt text |
| empty-link-text | Links with no display text |
| mixed-list-markers | Mixing - and * for lists |
| missing-code-language | Code blocks without a language |
| line-too-long | Lines over 120 characters |

## Example

```
User: "Check my docs for markdown issues"

Agent:
  1. Lints docs.md
  2. Finds:
     Line 12: trailing-whitespace
     Line 34: missing-alt-text (image)
     Line 45: mixed-list-markers (mixing - and *)
     Line 67: missing-code-language
  3. Offers: "Auto-fix 2 issues (whitespace, list markers)?"
  4. User approves → fixes applied
```
