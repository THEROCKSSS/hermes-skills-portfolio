#!/usr/bin/env python3
"""Generate the Atom feed from the SAME data the changelog page renders.

Why this exists
---------------
`site/js/changelog-data.js` holds `window.HermesChangelog.COMMITS` — the real,
dated commits that both the changelog page and the catalog's "What's new" feed
read. A hand-maintained `feed.xml` would be a second copy of that history and
would drift the moment someone adds an entry to the page and forgets the feed
(exactly how the cached skill content drifted for 46 of 51 skills once).

So the feed is *derived*: this script parses the COMMITS array straight out of
the JS module and renders it as Atom. `--check` fails when the on-disk feed
disagrees with the data, so CI can gate it the same way it gates the content
cache and the site/docs sync.

Fail loudly, never quietly
--------------------------
Every shape assumption is asserted: the module must define
`window.HermesChangelog`, `COMMITS` must be a non-empty array of objects, and
every object needs a well-formed `date`, `time`, `hash` and `text`. Anything
else raises `FeedDataError` and exits non-zero — an empty or truncated feed is
a worse failure than a red build, because it looks fine to a reader.

Timestamps
----------
The changelog data carries `date` + `time` with no timezone (it was captured
with `git log --date=format:"%Y-%m-%d %H:%M"`). Atom requires an offset, so the
feed normalizes those wall-clock stamps to UTC and labels them `Z`. Nothing
here reads the current clock: the feed's own `<updated>` is the newest entry's
timestamp, which keeps `--check` deterministic.

Usage
-----
    python scripts/generate_feed.py            # write site/feed.xml + docs/feed.xml
    python scripts/generate_feed.py --check    # exit 1 if either file is stale
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import quoteattr as xml_attr

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "site" / "js" / "changelog-data.js"
# Both copies are written from one rendered string, so they are byte-identical
# by construction — CI's "site/ and docs/ are in sync" step diffs them.
OUTPUT_PATHS = (REPO_ROOT / "site" / "feed.xml", REPO_ROOT / "docs" / "feed.xml")

BASE_URL = "https://therocksss.github.io/hermes-skills-portfolio/"
REPO_URL = "https://github.com/THEROCKSSS/hermes-skills-portfolio"
AUTHOR_NAME = "Owen"
AUTHOR_URI = "https://github.com/THEROCKSSS"
FEED_TITLE = "Hermes Skills Portfolio — Changelog"
FEED_SUBTITLE = (
    "Every change to the Hermes Skills catalog and site, newest first — "
    "real commits only, no invented history."
)

REQUIRED_FIELDS = ("date", "time", "hash", "text")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
_HASH_RE = re.compile(r"^[0-9a-f]{7,40}$")
_IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
_COMMITS_RE = re.compile(r"COMMITS\s*:\s*\[")


class FeedDataError(Exception):
    """The changelog data is missing or not the shape this generator expects."""


# --------------------------------------------------------------------------
# JS object-literal reader
# --------------------------------------------------------------------------
# changelog-data.js is a JS module, not JSON: keys are unquoted and the file is
# full of `//` comments. Rather than regex-scraping fields (which silently
# yields fewer entries when the formatting changes), this is a small recursive
# reader for the JSON subset of JS — object/array/string/number/true/false/null
# plus unquoted keys, comments and trailing commas. Anything outside that
# subset raises instead of being skipped.


def _skip_ws(src: str, i: int) -> int:
    n = len(src)
    while i < n:
        ch = src[i]
        if ch in " \t\r\n":
            i += 1
        elif src.startswith("//", i):
            nl = src.find("\n", i)
            i = n if nl == -1 else nl + 1
        elif src.startswith("/*", i):
            end = src.find("*/", i)
            if end == -1:
                raise FeedDataError("unterminated /* block comment in changelog data")
            i = end + 2
        else:
            break
    return i


_SIMPLE_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v",
    "0": "\0", "\\": "\\", "/": "/", "'": "'", '"': '"', "\n": "", "\r": "",
}


def _read_string(src: str, i: int) -> tuple[str, int]:
    quote = src[i]
    i += 1
    out: list[str] = []
    n = len(src)
    while i < n:
        ch = src[i]
        if ch == "\\":
            if i + 1 >= n:
                raise FeedDataError("unterminated escape in a changelog string")
            esc = src[i + 1]
            if esc == "u":
                hexs = src[i + 2:i + 6]
                if len(hexs) != 4 or any(c not in "0123456789abcdefABCDEF" for c in hexs):
                    raise FeedDataError(f"bad \\u escape in changelog data: {src[i:i + 6]!r}")
                out.append(chr(int(hexs, 16)))
                i += 6
                continue
            if esc in _SIMPLE_ESCAPES:
                out.append(_SIMPLE_ESCAPES[esc])
                i += 2
                continue
            raise FeedDataError(f"unsupported escape sequence \\{esc} in changelog data")
        if ch == quote:
            return "".join(out), i + 1
        if ch in "\r\n":
            raise FeedDataError("unterminated string literal in changelog data")
        out.append(ch)
        i += 1
    raise FeedDataError("unterminated string literal in changelog data")


def _read_value(src: str, i: int, out: list[str]) -> int:
    i = _skip_ws(src, i)
    if i >= len(src):
        raise FeedDataError("unexpected end of changelog data while reading a value")
    ch = src[i]
    if ch == "[":
        return _read_array(src, i, out)
    if ch == "{":
        return _read_object(src, i, out)
    if ch in "\"'":
        text, i = _read_string(src, i)
        out.append(json.dumps(text))
        return i
    num = _NUMBER_RE.match(src, i)
    if num:
        out.append(num.group(0))
        return num.end()
    ident = _IDENT_RE.match(src, i)
    if ident and ident.group(0) in ("true", "false", "null"):
        out.append(ident.group(0))
        return ident.end()
    raise FeedDataError(
        f"unsupported token in changelog data at offset {i}: {src[i:i + 40]!r}"
    )


def _read_array(src: str, i: int, out: list[str]) -> int:
    out.append("[")
    i = _skip_ws(src, i + 1)
    first = True
    while True:
        if i >= len(src):
            raise FeedDataError("unterminated array in changelog data")
        if src[i] == "]":
            out.append("]")
            return i + 1
        if not first:
            out.append(",")
        i = _read_value(src, i, out)
        first = False
        i = _skip_ws(src, i)
        if i < len(src) and src[i] == ",":
            i = _skip_ws(src, i + 1)  # trailing commas are legal JS, not JSON
        elif i < len(src) and src[i] != "]":
            raise FeedDataError(
                f"expected ',' or ']' in changelog data at offset {i}: {src[i:i + 40]!r}"
            )


def _read_object(src: str, i: int, out: list[str]) -> int:
    out.append("{")
    i = _skip_ws(src, i + 1)
    first = True
    while True:
        if i >= len(src):
            raise FeedDataError("unterminated object in changelog data")
        if src[i] == "}":
            out.append("}")
            return i + 1
        if not first:
            out.append(",")
        if src[i] in "\"'":
            key, i = _read_string(src, i)
        else:
            ident = _IDENT_RE.match(src, i)
            if not ident:
                raise FeedDataError(
                    f"expected an object key in changelog data at offset {i}: {src[i:i + 40]!r}"
                )
            key, i = ident.group(0), ident.end()
        out.append(json.dumps(key))
        i = _skip_ws(src, i)
        if i >= len(src) or src[i] != ":":
            raise FeedDataError(f"expected ':' after key {key!r} in changelog data")
        out.append(":")
        i = _read_value(src, i + 1, out)
        first = False
        i = _skip_ws(src, i)
        if i < len(src) and src[i] == ",":
            i = _skip_ws(src, i + 1)
        elif i < len(src) and src[i] != "}":
            raise FeedDataError(
                f"expected ',' or '}}' in changelog data at offset {i}: {src[i:i + 40]!r}"
            )


def extract_commits(js_text: str) -> list:
    """Pull the COMMITS array out of the changelog-data.js module."""
    if "window.HermesChangelog" not in js_text:
        raise FeedDataError(
            "changelog data does not assign window.HermesChangelog — "
            "the shared source of truth moved or was renamed"
        )
    match = _COMMITS_RE.search(js_text)
    if not match:
        raise FeedDataError(
            "no `COMMITS: [` array found in the changelog data — "
            "refusing to emit a feed from an unknown shape"
        )
    buf: list[str] = []
    _read_array(js_text, match.end() - 1, buf)
    value = json.loads("".join(buf))
    if not isinstance(value, list):
        raise FeedDataError("COMMITS is not an array")
    return value


def parse_commits(data_path: Path = DATA_PATH) -> list[dict]:
    """Read + validate every commit. Raises FeedDataError rather than degrading."""
    if not Path(data_path).exists():
        raise FeedDataError(f"changelog data file not found: {data_path}")
    commits = extract_commits(Path(data_path).read_text(encoding="utf-8"))
    if not commits:
        raise FeedDataError(
            "COMMITS is empty — refusing to write an empty feed "
            "(a silently empty feed reads as 'nothing ever shipped')"
        )
    seen: dict[str, int] = {}
    for idx, commit in enumerate(commits):
        if not isinstance(commit, dict):
            raise FeedDataError(f"COMMITS[{idx}] is {type(commit).__name__}, expected an object")
        blank = [
            field for field in REQUIRED_FIELDS
            if not isinstance(commit.get(field), str) or not commit[field].strip()
        ]
        if blank:
            raise FeedDataError(
                f"COMMITS[{idx}] has missing/blank field(s): {', '.join(blank)}"
            )
        if not _DATE_RE.match(commit["date"]):
            raise FeedDataError(f"COMMITS[{idx}].date is not YYYY-MM-DD: {commit['date']!r}")
        if not _TIME_RE.match(commit["time"]):
            raise FeedDataError(f"COMMITS[{idx}].time is not HH:MM: {commit['time']!r}")
        if not _HASH_RE.match(commit["hash"]):
            raise FeedDataError(
                f"COMMITS[{idx}].hash is not a git short hash: {commit['hash']!r}"
            )
        try:
            commit_timestamp(commit)
        except ValueError as exc:
            raise FeedDataError(
                f"COMMITS[{idx}] has an impossible date/time "
                f"({commit['date']} {commit['time']}): {exc}"
            ) from exc
        if commit["hash"] in seen:
            raise FeedDataError(
                f"COMMITS[{idx}].hash {commit['hash']!r} duplicates COMMITS[{seen[commit['hash']]}] "
                "— entry ids must be unique"
            )
        seen[commit["hash"]] = idx
    return commits


# --------------------------------------------------------------------------
# Atom rendering
# --------------------------------------------------------------------------

def commit_timestamp(commit: dict) -> datetime:
    """Wall-clock date+time from the data, normalized to UTC (see module docstring)."""
    return datetime.strptime(
        f"{commit['date']} {commit['time']}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=timezone.utc)


def iso8601(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def entry_id(commit: dict, base_url: str = BASE_URL) -> str:
    """Stable per-entry id built on the commit hash.

    Deliberately the same anchor the page gives that row (`commit-<hash>`), so
    the id both never changes and actually resolves to the entry it names.
    """
    return f"{base_url}changelog.html#commit-{commit['hash']}"


def entry_title(text: str, limit: int = 100) -> str:
    """First sentence of the real commit line, trimmed — never a new claim."""
    flat = " ".join(text.split())
    sentence_end = re.search(r"[.!?](?:\s|$)", flat)
    title = flat[:sentence_end.start()] if sentence_end else flat
    if len(title) > limit:
        title = title[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"
    return title


def render_feed(commits: list[dict], base_url: str = BASE_URL) -> str:
    """Render the Atom document. Pure function of the data — no clock reads."""
    ordered = sorted(commits, key=commit_timestamp, reverse=True)
    feed_url = base_url + "feed.xml"
    changelog_url = base_url + "changelog.html"
    updated = iso8601(commit_timestamp(ordered[0]))

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        # An XML comment may never contain a double hyphen, so the check flag is
        # described rather than spelled out here.
        "<!-- Generated by scripts/generate_feed.py from site/js/changelog-data.js.",
        "     Do not edit by hand: regenerate with `python scripts/generate_feed.py`.",
        "     CI runs that script in check mode, which fails when this file",
        "     disagrees with the changelog data. -->",
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{xml_escape(FEED_TITLE)}</title>",
        f"  <subtitle>{xml_escape(FEED_SUBTITLE)}</subtitle>",
        f"  <id>{xml_escape(feed_url)}</id>",
        f'  <link rel="self" type="application/atom+xml" href={xml_attr(feed_url)}/>',
        f'  <link rel="alternate" type="text/html" href={xml_attr(changelog_url)}/>',
        f"  <updated>{updated}</updated>",
        "  <author>",
        f"    <name>{xml_escape(AUTHOR_NAME)}</name>",
        f"    <uri>{xml_escape(AUTHOR_URI)}</uri>",
        "  </author>",
        "  <rights>MIT</rights>",
        f"  <generator uri={xml_attr(REPO_URL)}>scripts/generate_feed.py</generator>",
    ]

    for commit in ordered:
        moment = iso8601(commit_timestamp(commit))
        url = entry_id(commit, base_url)
        lines += [
            "  <entry>",
            f"    <title>{xml_escape(entry_title(commit['text']))}</title>",
            f"    <id>{xml_escape(url)}</id>",
            f'    <link rel="alternate" type="text/html" href={xml_attr(url)}/>',
            f"    <updated>{moment}</updated>",
            f"    <published>{moment}</published>",
            f'    <content type="text">{xml_escape(commit["text"])}</content>',
            "  </entry>",
        ]

    lines.append("</feed>")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Write / check
# --------------------------------------------------------------------------

def write_feed(document: str, paths=OUTPUT_PATHS) -> list[Path]:
    written = []
    for path in paths:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" so a Windows run does not write CRLF into one copy and
        # break the byte-for-byte site/docs diff CI runs on Linux.
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(document)
        written.append(path)
    return written


def check_feed(document: str, paths=OUTPUT_PATHS) -> list[str]:
    """Return a problem message per stale/missing output. Empty list == current."""
    problems = []
    expected = document.encode("utf-8")
    for path in paths:
        path = Path(path)
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        if not path.exists():
            problems.append(f"{rel} is missing")
        elif path.read_bytes() != expected:
            problems.append(f"{rel} is stale — it disagrees with site/js/changelog-data.js")
    return problems


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    unknown = [arg for arg in argv if arg != "--check"]
    if unknown:
        print(f"FAIL: unknown argument(s): {' '.join(unknown)}")
        print(__doc__.strip().splitlines()[-1])
        return 2

    try:
        commits = parse_commits()
        document = render_feed(commits)
    except FeedDataError as exc:
        print(f"FAIL: {exc}")
        return 1

    if check_only:
        problems = check_feed(document)
        for problem in problems:
            print(f"FAIL: {problem}")
        if problems:
            print("\nRun: python scripts/generate_feed.py")
            return 1
        print(f"feed.xml is current in site/ and docs/ ({len(commits)} entries).")
        return 0

    written = write_feed(document)
    print(f"Wrote {len(commits)} entries to:")
    for path in written:
        print(f"  {path.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
