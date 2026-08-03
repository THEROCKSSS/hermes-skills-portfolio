#!/usr/bin/env python3
"""Fetch every skill's install_url and prove it serves a real SKILL.md.

This is the check that would have caught the blob-URL bug. A blob URL returns
HTTP 200 with `text/html`, so "did the request succeed?" is not a useful test —
the only meaningful question is whether the bytes at the other end are a skill.

For each entry this asserts:
  - the response is 200
  - the content type is not HTML
  - the body opens with a `---` frontmatter fence
  - the frontmatter carries `name:` and `description:`
  - the frontmatter `name:` matches the catalog entry's name

Usage:
    python scripts/verify_installs.py            # all skills
    python scripts/verify_installs.py --limit 5  # first 5, for a quick smoke
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "skills-index.json"
TIMEOUT = 30


def check(skill: dict) -> tuple[str, bool, str]:
    """Return (name, ok, message)."""
    name = skill.get("name", "<unnamed>")
    url = skill.get("install_url", "")
    if not url:
        return name, False, "no install_url"

    req = urllib.request.Request(url, headers={"User-Agent": "hermes-skills-portfolio-verify"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return name, False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - report any transport failure verbatim
        return name, False, f"request failed: {exc}"

    if status != 200:
        return name, False, f"HTTP {status}"
    if "text/html" in ctype.lower():
        return name, False, f"serves HTML, not markdown (Content-Type: {ctype})"
    if not body.lstrip().startswith("---"):
        return name, False, f"no frontmatter fence (body starts: {body.lstrip()[:40]!r})"

    fence_end = body.find("\n---", body.find("---") + 3)
    frontmatter = body[:fence_end] if fence_end != -1 else body[:2000]
    if "name:" not in frontmatter:
        return name, False, "frontmatter has no name:"
    if "description:" not in frontmatter:
        return name, False, "frontmatter has no description:"

    declared = ""
    for line in frontmatter.splitlines():
        if line.startswith("name:"):
            declared = line.split(":", 1)[1].strip()
            break
    if declared != name:
        return name, False, f"frontmatter name is {declared!r}, catalog says {name!r}"

    return name, True, f"{len(body)} bytes"


def main(argv: list[str]) -> int:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    skills = index["skills"]

    if "--limit" in argv:
        skills = skills[: int(argv[argv.index("--limit") + 1])]

    print(f"Verifying {len(skills)} install URLs...\n")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, skills))

    failures = [(n, m) for n, ok, m in results if not ok]
    for name, ok, msg in results:
        if not ok:
            print(f"  FAIL  {name}: {msg}")

    print()
    if failures:
        print(f"{len(failures)} of {len(results)} install URLs are broken.")
        return 1
    print(f"All {len(results)} install URLs serve a valid SKILL.md with matching frontmatter.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
