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


# Data files whose source of truth is the repo root. They must be mirrored into
# site/ *before* site/ is copied into docs/, otherwise site/ keeps serving a
# stale copy: the local dev server reads site/, so a drifted site/skills-index.json
# means local testing shows different data than production. That is exactly how
# the cached skill content drifted for 46 of 51 skills without anyone noticing.
ROOT_OWNED_DATA = ("skills-index.json", "bundles.json", "pending-sources.json")


def sync():
    site_dir = ROOT / "site"
    docs_dir = ROOT / "docs"
    copied = []

    for name in ROOT_OWNED_DATA:
        src = ROOT / name
        if not src.exists():
            continue
        shutil.copyfile(src, site_dir / name)
        copied.append(f"{name} (root -> site/)")

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

    for name in ROOT_OWNED_DATA:
        src = ROOT / name
        if not src.exists():
            continue
        shutil.copyfile(src, docs_dir / name)
        copied.append(f"{name} (root -> docs/)")

    print(f"Synced {len(copied)} file(s) from site/ to docs/:")
    for name in sorted(copied):
        print(f"  {name}")


if __name__ == "__main__":
    sync()
    sys.exit(0)
