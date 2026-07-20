---
name: file-organizer
description: "Organize files by type, date, or pattern — agent + this skill = user gets a clean directory structure."
version: 1.0.0
---

# file-organizer

Organize files in a directory by type, date, or custom patterns. The agent scans a directory, categorizes files, and moves them into a structured layout. Supports dry-run mode to preview before moving.

## When to Use

- The user has a messy directory (Downloads, Desktop) and wants it organized.
- The user wants to sort files by type, date, or name pattern.
- The user wants to find and remove duplicate files.
- The user says "organize my downloads", "clean up this folder", or "sort these files".

## Organize by Type

```python
import os
import shutil
from pathlib import Path

CATEGORY_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf", ".pages"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
    "Presentations": [".ppt", ".pptx", ".key", ".odp"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"],
    "Code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".sh", ".html", ".css", ".json", ".xml", ".yaml", ".yml"],
    "Executables": [".exe", ".msi", ".deb", ".rpm", ".dmg", ".app", ".apk"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Data": [".db", ".sqlite", ".sql", ".json", ".csv"],
}

def organize_by_type(directory: str, dry_run: bool = True) -> dict:
    """Organize files into subdirectories by category."""
    moved = {}
    skipped = []

    for item in Path(directory).iterdir():
        if item.is_dir():
            continue

        ext = item.suffix.lower()
        category = "Misc"
        for cat, extensions in CATEGORY_MAP.items():
            if ext in extensions:
                category = cat
                break

        target_dir = Path(directory) / category
        target_path = target_dir / item.name

        if dry_run:
            moved[str(item)] = str(target_path)
        else:
            target_dir.mkdir(exist_ok=True)
            if target_path.exists():
                # Append number to avoid overwriting
                stem = item.stem
                i = 1
                while target_path.exists():
                    target_path = target_dir / f"{stem}_{i}{item.suffix}"
                    i += 1
            shutil.move(str(item), str(target_path))
            moved[str(item)] = str(target_path)

    return {"moved": moved, "count": len(moved), "dry_run": dry_run}
```

## Organize by Date

```python
import datetime

def organize_by_date(directory: str, dry_run: bool = True) -> dict:
    """Organize files into year/month subdirectories by modification date."""
    moved = {}

    for item in Path(directory).iterdir():
        if item.is_dir():
            continue

        mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
        year = str(mtime.year)
        month = mtime.strftime("%m-%B")

        target_dir = Path(directory) / year / month
        target_path = target_dir / item.name

        if dry_run:
            moved[str(item)] = str(target_path)
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(target_path))
            moved[str(item)] = str(target_path)

    return {"moved": moved, "count": len(moved), "dry_run": dry_run}
```

## Find Duplicates

```python
import hashlib

def find_duplicates(directory: str) -> dict:
    """Find duplicate files by content hash."""
    hashes = {}
    duplicates = {}

    for item in Path(directory).rglob("*"):
        if item.is_file():
            h = hashlib.sha256(item.read_bytes()).hexdigest()
            if h in hashes:
                if h not in duplicates:
                    duplicates[h] = [hashes[h]]
                duplicates[h].append(str(item))
            else:
                hashes[h] = str(item)

    return {
        "total_files": len(hashes) + sum(len(v) - 1 for v in duplicates.values()),
        "duplicate_groups": len(duplicates),
        "duplicates": duplicates,
    }
```

## Workflow

1. Identify the directory to organize
2. Run in dry-run mode first to show what would move where
3. Show the user the proposed organization
4. If approved, run without dry-run to actually move files
5. Report: files moved, categories created, any duplicates found

## Pitfalls

- **Always dry-run first** — Never move files without showing the user what will happen. A wrong category mapping could scatter files unexpectedly.
- **Name collisions** — Files with the same name in different categories will collide. The code handles this by appending `_1`, `_2`, etc.
- **Symlinks** — `Path.iterdir()` includes symlinks. Moving a symlink moves the link, not the target. Handle symlinks separately if needed.
- **Hidden files** — Files starting with `.` (`.gitignore`, `.env`) are included by default. Filter them out if the user doesn't want them moved.
- **Permission errors** — Moving files requires write permission on both the source and target. On Windows, files in use can't be moved.
- **Large directories** — `find_duplicates` reads every file to hash it. For directories with thousands of large files, this is slow. Consider hashing only files above a size threshold first.
