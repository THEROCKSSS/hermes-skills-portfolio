#!/usr/bin/env python3
"""Re-read every skill's SKILL.md / README.md into skills-index.json.

Why this exists
---------------
`skills-index.json` caches each skill's `skillmd_content` and `readme_content`
so the catalog's detail overlay can render without 100+ extra fetches. The
cache has no automated refresh, so editing `skills/<name>/SKILL.md` silently
leaves the site serving the old text. ARCHITECTURE.md recorded this as a known
open decision after the cache had already drifted for 46 of 51 skills once.

This closes it: `--check` fails CI when any cached copy differs from disk, and
the default run re-syncs them. Content lives in the markdown files; the index
is a derived cache, never the source of truth.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "skills-index.json"


def _read(path: Path) -> str | None:
    if not path.exists():
        return None
    # newline="" keeps the file's own line endings, so a CRLF README doesn't
    # get silently normalized into the JSON and show up as a phantom diff.
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def collect(index: dict) -> tuple[list[str], list[str]]:
    """Return (stale_skill_names, missing_file_messages) without writing."""
    stale: list[str] = []
    missing: list[str] = []
    for skill in index.get("skills", []):
        name = skill["name"]
        skill_dir = REPO_ROOT / "skills" / name
        for filename, field in (("SKILL.md", "skillmd_content"), ("README.md", "readme_content")):
            disk = _read(skill_dir / filename)
            if disk is None:
                missing.append(f"{name}: skills/{name}/{filename} does not exist")
                continue
            if skill.get(field) != disk:
                stale.append(f"{name}:{field}")
    return stale, missing


def refresh(index: dict) -> list[str]:
    """Write disk content into the index. Returns the fields that changed."""
    changed: list[str] = []
    for skill in index.get("skills", []):
        name = skill["name"]
        skill_dir = REPO_ROOT / "skills" / name
        for filename, field in (("SKILL.md", "skillmd_content"), ("README.md", "readme_content")):
            disk = _read(skill_dir / filename)
            if disk is None:
                continue
            if skill.get(field) != disk:
                skill[field] = disk
                changed.append(f"{name}:{field}")
    return changed


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    if check_only:
        stale, missing = collect(index)
        for m in missing:
            print(f"FAIL: {m}")
        for s in stale:
            print(f"FAIL: {s} is stale — disk and skills-index.json disagree")
        if stale or missing:
            print(
                f"\n{len(stale)} stale cached field(s), {len(missing)} missing file(s). "
                "Run: python scripts/refresh_content_cache.py"
            )
            return 1
        print(f"Content cache is in sync for all {len(index['skills'])} skills.")
        return 0

    changed = refresh(index)
    INDEX_PATH.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Refreshed {len(changed)} cached field(s) across {len(index['skills'])} skills.")
    for c in changed:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
