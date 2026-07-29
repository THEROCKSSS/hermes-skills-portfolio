#!/usr/bin/env python3
"""Sync site/ into docs/ — every real file, not a hand-picked list.

Mirrors exactly what .github/workflows/ci.yml's "Check site/ and docs/ are
in sync" step validates: every file under site/ (excluding site/skills/,
which scripts/generate_skill_pages.py owns) plus the root skills-index.json.

Run this after any change under site/ instead of a manual `cp` per file.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sync():
    site_dir = ROOT / "site"
    docs_dir = ROOT / "docs"
    copied = []

    for src in site_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(site_dir)
        if rel.parts and rel.parts[0] == "skills":
            continue  # owned by scripts/generate_skill_pages.py
        dest = docs_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        copied.append(str(rel))

    index_src = ROOT / "skills-index.json"
    index_dest = docs_dir / "skills-index.json"
    shutil.copyfile(index_src, index_dest)
    copied.append("skills-index.json (root -> docs/)")

    print(f"Synced {len(copied)} file(s) from site/ to docs/:")
    for name in sorted(copied):
        print(f"  {name}")


if __name__ == "__main__":
    sync()
    sys.exit(0)
