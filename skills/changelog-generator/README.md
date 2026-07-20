# changelog-generator

Generate a formatted changelog from git commit history.

## What it does

The agent reads git commits, categorizes them by conventional commit type (feat → Added, fix → Fixed, refactor → Changed), and produces a Keep a Changelog formatted document. Useful for release notes, project documentation, or seeing what changed between versions.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/changelog-generator/SKILL.md
```

## How to use

```
"Generate a changelog from v1.0.0 to now"
```

The agent:
1. Runs `git log v1.0.0..HEAD`
2. Categorizes commits: feat → Added, fix → Fixed, etc.
3. Formats as a changelog document
4. Writes to CHANGELOG.md

## Example

```
User: "What changed since the last release?"

Agent:
  1. Gets commits since last tag: git describe --tags
  2. Categorizes: 3 feat, 5 fix, 2 refactor
  3. Generates:

  ## Added
  - User profile page (a1b2c3d)
  - Dark mode toggle (e4f5g6h)
  - Export to CSV (i7j8k9l)

  ## Fixed
  - Login redirect loop (m1n2o3p)
  - Date picker timezone bug (q4r5s6t)
```
