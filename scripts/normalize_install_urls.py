#!/usr/bin/env python3
"""Normalize every skill's install_url so `hermes skills install <url>` actually works.

The bug this fixes
------------------
`install_url` used to point at a GitHub *blob* URL:

    https://github.com/OWNER/REPO/blob/main/skills/<name>/SKILL.md

That URL serves `text/html` — GitHub's file *viewer*, not the file. The hermes
CLI accepts "a direct HTTP(S) URL to a SKILL.md file" and dutifully fetches it,
so the install appears to succeed while writing GitHub's page markup into the
skill body. Verified with `hermes skills inspect`: the description comes back
empty and the SKILL.md preview starts `<!DOCTYPE html>`.

The fix is the raw host, which serves the actual bytes:

    https://raw.githubusercontent.com/OWNER/REPO/main/skills/<name>/SKILL.md

Because `install_url` was doing double duty — install target *and* the
human-facing "View SKILL.md on GitHub" link — this also splits the two apart:

    install_url  raw.githubusercontent.com  (machine: what the CLI fetches)
    source_url   github.com/.../blob/...    (human: what a person clicks)

Idempotent: running it twice is a no-op.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "skills-index.json"

BLOB_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<ref>[^/]+)/(?P<path>.+)$"
)
RAW_RE = re.compile(
    r"^https://raw\.githubusercontent\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?P<ref>[^/]+)/(?P<path>.+)$"
)


def blob_to_raw(url: str) -> str:
    """github.com/O/R/blob/REF/PATH -> raw.githubusercontent.com/O/R/REF/PATH."""
    m = BLOB_RE.match(url)
    if not m:
        return url
    g = m.groupdict()
    return (
        f"https://raw.githubusercontent.com/{g['owner']}/{g['repo']}/{g['ref']}/{g['path']}"
    )


def raw_to_blob(url: str) -> str:
    """The inverse, for reconstructing the human-facing link."""
    m = RAW_RE.match(url)
    if not m:
        return url
    g = m.groupdict()
    return f"https://github.com/{g['owner']}/{g['repo']}/blob/{g['ref']}/{g['path']}"


def normalize(index: dict) -> tuple[dict, list[str]]:
    """Return (index, changed_skill_names). Mutates entries in place."""
    changed: list[str] = []
    for skill in index.get("skills", []):
        install = skill.get("install_url", "")
        if not install:
            continue

        # The human link: whatever blob URL we already have, else derive one.
        source_url = skill.get("source_url") or (
            install if BLOB_RE.match(install) else raw_to_blob(install)
        )
        raw = blob_to_raw(install)

        if skill.get("install_url") != raw or skill.get("source_url") != source_url:
            changed.append(skill["name"])

        skill["install_url"] = raw
        skill["source_url"] = source_url
    return index, changed


def verify(index: dict) -> list[str]:
    """Return a list of problems. Empty list means every entry is install-safe."""
    problems: list[str] = []
    for skill in index.get("skills", []):
        name = skill.get("name", "<unnamed>")
        install = skill.get("install_url", "")
        if not install:
            problems.append(f"{name}: install_url is empty")
            continue
        if "/blob/" in install:
            problems.append(f"{name}: install_url still points at a blob URL ({install})")
        if not install.startswith("https://raw.githubusercontent.com/"):
            problems.append(f"{name}: install_url is not a raw.githubusercontent.com URL")
        if not install.endswith("/SKILL.md"):
            problems.append(f"{name}: install_url does not end in /SKILL.md")
    return problems


# A blob URL sitting immediately after `hermes skills install` in prose is the
# same bug as the index field — a reader copies it and installs GitHub's HTML.
# Bare blob links in prose ("View the source") are legitimate and left alone.
INSTALL_CMD_RE = re.compile(
    r"(hermes skills install\s+)(https://github\.com/[^/]+/[^/]+/blob/[^\s`)\"']+)"
)

MARKDOWN_GLOBS = ("skills/*/README.md", "skills/*/SKILL.md")
EXTRA_MARKDOWN = ("README.md", "CONTRIBUTING.md", "AGENTS.md")


def _iter_markdown() -> list[Path]:
    paths: list[Path] = []
    for pattern in MARKDOWN_GLOBS:
        paths.extend(sorted(REPO_ROOT.glob(pattern)))
    for rel in EXTRA_MARKDOWN:
        p = REPO_ROOT / rel
        if p.exists():
            paths.append(p)
    return paths


def fix_markdown(check_only: bool = False) -> tuple[list[str], int]:
    """Rewrite `hermes skills install <blob-url>` to the raw URL in markdown.

    Returns (changed_relative_paths, total_occurrences).
    """
    changed: list[str] = []
    total = 0
    for path in _iter_markdown():
        # newline="" preserves each file's existing CRLF/LF endings; rewriting
        # them would produce a diff on every line of all 51 files.
        with open(path, "r", encoding="utf-8", newline="") as fh:
            original = fh.read()
        updated, n = INSTALL_CMD_RE.subn(
            lambda m: m.group(1) + blob_to_raw(m.group(2)), original
        )
        if n:
            total += n
            changed.append(str(path.relative_to(REPO_ROOT)).replace("\\", "/"))
            if not check_only:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(updated)
    return changed, total


def main(argv: list[str]) -> int:
    check_only = "--check" in argv

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    if check_only:
        problems = verify(index)
        md_changed, md_total = fix_markdown(check_only=True)
        for p in problems:
            print(f"FAIL: {p}")
        for rel in md_changed:
            print(f"FAIL: {rel} still documents a blob URL as the install command")
        if problems or md_changed:
            print(
                f"\n{len(problems)} index problem(s), "
                f"{md_total} markdown occurrence(s) across {len(md_changed)} file(s)."
            )
            return 1
        print(
            f"All {len(index['skills'])} install_urls are raw SKILL.md URLs, "
            "and no markdown documents a blob install command."
        )
        return 0

    index, changed = normalize(index)
    problems = verify(index)
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        return 1

    INDEX_PATH.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md_changed, md_total = fix_markdown()

    print(f"Normalized {len(changed)} of {len(index['skills'])} index entries.")
    print(f"Rewrote {md_total} install command(s) across {len(md_changed)} markdown file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
