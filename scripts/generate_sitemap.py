#!/usr/bin/env python3
"""Generate sitemap.xml (and robots.txt) for the Hermes Skills Portfolio.

Roadmap Phase 16 — SEO & Discoverability.

The skill list is read from skills-index.json at generation time and never
hardcoded, for the same reason every count on the site is read from it: a
hand-maintained second list is a list that silently goes stale. Adding a skill
directory + index entry is enough — re-run this script and the sitemap grows.

Both output trees get identical bytes: `site/` is the working copy and `docs/`
is what GitHub Pages serves, and CI fails the build when they diverge.

Usage:
    python scripts/generate_sitemap.py            # write site/ and docs/
    python scripts/generate_sitemap.py --check    # CI: non-zero if stale
    python scripts/generate_sitemap.py --stdout   # print, write nothing
"""

import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "skills-index.json"
OUTPUT_DIRS = (ROOT / "site", ROOT / "docs")

BASE_URL = "https://therocksss.github.io/hermes-skills-portfolio/"

# The four top-level pages, with the priority/changefreq that honestly reflects
# how each one moves. The catalog is the entry point and changes whenever a
# skill lands; submit.html is a process description that rarely changes at all.
TOP_LEVEL_PAGES = (
    # (path relative to BASE_URL, changefreq, priority)
    ("", "weekly", "1.0"),
    ("bundles.html", "monthly", "0.8"),
    ("changelog.html", "weekly", "0.6"),
    ("submit.html", "monthly", "0.5"),
)

SKILL_CHANGEFREQ = "monthly"
SKILL_PRIORITY = "0.7"

ROBOTS_TXT = f"""# Hermes Skills Portfolio — https://github.com/THEROCKSSS/hermes-skills-portfolio
# The whole site is a public catalog; there is nothing here to keep out of an index.
User-agent: *
Allow: /

Sitemap: {BASE_URL}sitemap.xml
"""


def load_index(index_path=INDEX_PATH):
    """Read skills-index.json."""
    with open(index_path, encoding="utf-8") as handle:
        return json.load(handle)


def _lastmod(value):
    """Return a W3C-datetime lastmod, or None when there is no real date.

    Never invents 'today' — an unknown lastmod is simply omitted, which is
    valid sitemap XML, rather than telling a crawler the page changed when
    nothing is known to have changed.
    """
    if not value:
        return None
    text = str(value).strip()
    # skills-index.json carries plain YYYY-MM-DD per skill and an ISO timestamp
    # for the index as a whole. Both are valid W3C datetimes; pass them through
    # rather than reformatting and risking a timezone shift.
    return text or None


def build_urls(index, base_url=BASE_URL):
    """Build the ordered list of sitemap entries from the real index.

    Returns a list of dicts: {loc, lastmod, changefreq, priority}.
    """
    base = base_url if base_url.endswith("/") else base_url + "/"
    generated_at = _lastmod(index.get("generated_at"))

    urls = []
    for path, changefreq, priority in TOP_LEVEL_PAGES:
        urls.append(
            {
                "loc": base + path,
                "lastmod": generated_at,
                "changefreq": changefreq,
                "priority": priority,
            }
        )

    # Sorted by name so the file is stable across runs regardless of the order
    # skills happen to sit in the index — otherwise --check reports a false
    # "stale" every time the index is regenerated.
    for skill in sorted(index.get("skills", []), key=lambda s: s["name"]):
        urls.append(
            {
                "loc": f"{base}skills/{skill['name']}/",
                "lastmod": _lastmod(skill.get("recency")),
                "changefreq": SKILL_CHANGEFREQ,
                "priority": SKILL_PRIORITY,
            }
        )
    return urls


def render_sitemap(urls):
    """Render the urlset XML. Trailing newline included."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for entry in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(entry['loc'])}</loc>")
        if entry.get("lastmod"):
            lines.append(f"    <lastmod>{escape(entry['lastmod'])}</lastmod>")
        if entry.get("changefreq"):
            lines.append(f"    <changefreq>{escape(entry['changefreq'])}</changefreq>")
        if entry.get("priority"):
            lines.append(f"    <priority>{escape(entry['priority'])}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def render_robots(base_url=BASE_URL):
    base = base_url if base_url.endswith("/") else base_url + "/"
    return ROBOTS_TXT.replace(f"{BASE_URL}sitemap.xml", f"{base}sitemap.xml")


def _artifacts(index):
    return {
        "sitemap.xml": render_sitemap(build_urls(index)),
        "robots.txt": render_robots(),
    }


def write(output_dirs=OUTPUT_DIRS, index=None):
    """Write sitemap.xml + robots.txt into every output dir. Returns paths."""
    index = index if index is not None else load_index()
    files = _artifacts(index)
    written = []
    for directory in output_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            path = directory / name
            # newline="\n" so site/ and docs/ stay byte-identical on Windows,
            # where the default translation would emit CRLF and break CI's
            # site/docs diff.
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            written.append(path)
    return written


def _label(path):
    """Repo-relative path when possible, absolute otherwise (temp dirs in tests)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def check(output_dirs=OUTPUT_DIRS, index=None):
    """Return a list of human-readable problems. Empty list means fresh."""
    index = index if index is not None else load_index()
    files = _artifacts(index)
    problems = []
    for directory in output_dirs:
        for name, expected in files.items():
            path = directory / name
            if not path.exists():
                problems.append(f"{_label(path)} is missing")
                continue
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                problems.append(
                    f"{_label(path)} is stale — re-run scripts/generate_sitemap.py"
                )
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed files match what would be generated; exit 1 if not",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the sitemap instead of writing any file",
    )
    args = parser.parse_args(argv)

    index = load_index()

    if args.stdout:
        sys.stdout.write(render_sitemap(build_urls(index)))
        return 0

    if args.check:
        problems = check(index=index)
        if problems:
            print("FAIL: sitemap/robots are out of date:")
            for problem in problems:
                print(f"  {problem}")
            return 1
        count = len(build_urls(index))
        print(f"sitemap.xml and robots.txt are up to date ({count} URLs) in site/ and docs/.")
        return 0

    written = write(index=index)
    urls = build_urls(index)
    skills = len(index.get("skills", []))
    print(
        f"Wrote {len(written)} file(s): {len(urls)} URLs "
        f"({len(TOP_LEVEL_PAGES)} top-level pages + {skills} skill pages)"
    )
    for path in written:
        print(f"  {_label(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
