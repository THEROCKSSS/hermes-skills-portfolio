#!/usr/bin/env python3
"""Generate per-skill HTML share pages from skills-index.json.

Usage:
    python scripts/generate_skill_pages.py [--base-url URL]

Outputs:
    site/skills/<name>/index.html  — per-skill page (source of truth)
    docs/skills/<name>/index.html  — deployed copy (GitHub Pages)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.portfolio_tools import generate_all_pages


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(repo_root, "skills-index.json")
    site_dir = os.path.join(repo_root, "site")
    docs_dir = os.path.join(repo_root, "docs")

    base_url = "https://therocksss.github.io/hermes-skills-portfolio"
    if "--base-url" in sys.argv:
        idx = sys.argv.index("--base-url")
        base_url = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else base_url

    result = generate_all_pages(index_path, site_dir, docs_dir, base_url)
    print(f"Generated {result['pages_generated']} skill pages")
    if result["errors"]:
        for err in result["errors"]:
            print(f"  ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    print("All pages generated successfully.")


if __name__ == "__main__":
    main()