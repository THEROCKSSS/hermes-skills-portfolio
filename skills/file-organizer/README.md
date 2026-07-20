# file-organizer

Organize files by type, date, or content — clean up messy directories automatically.

## What it does

The agent scans a directory and organizes files into subdirectories by category (Images, Videos, Documents, Code, etc.) or by modification date (Year/Month). Includes dry-run mode to preview before moving, and a duplicate finder that identifies files with identical content by hash.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/file-organizer/SKILL.md
```

## How to use

```
"Organize my Downloads folder by file type"
```

The agent:
1. Scans the directory
2. Runs in dry-run mode first — shows you what would move where
3. If approved, creates category folders and moves files
4. Reports: "Moved 47 files into 8 categories"

## Organize modes

| Mode | How it sorts |
|---|---|
| By type | Images/, Videos/, Documents/, Code/, etc. |
| By date | 2026/07-July/, 2026/08-August/, etc. |
| Duplicates | Finds files with identical content by SHA-256 |

## Example

```
User: "Clean up my Desktop, but show me what you'll do first"

Agent:
  1. Dry run on ~/Desktop
  2. Shows: "Would move 23 files:
     screenshot.png → Images/
     report.pdf → Documents/
     app.py → Code/
     vacation.mp4 → Videos/"
  3. User approves
  4. Moves files, creates category folders
  5. Returns: "Done. 23 files organized into 6 categories."
```
