#!/usr/bin/env python3
"""Content-quality and curation gates for the skills catalog.

Why this exists
---------------
`ci.yml` already guarantees the catalog is *structurally* correct: install URLs
are raw, cached content matches disk, every skill has a page, site/ and docs/
agree. None of that says anything about whether the prose is any good, whether
its links still resolve, or whether two skills quietly describe the same thing.

This script covers that second half. Six independent checks, each runnable on
its own and each exiting non-zero when it finds a real problem:

    frontmatter   required keys present, `name` matches its directory
    metrics       invented metrics / testimonials / marketing fluff (anti-slop)
    links         every http(s) URL in the corpus still resolves
    staleness     skills whose files have not been touched in N months
    duplicates    pairwise near-identical descriptions/overviews
    tiers         tier is valid, and its scope matches what the description says

Severity, and what that means for CI
------------------------------------
Findings are either FAIL or REVIEW.

  FAIL   — deterministic and unambiguous. Missing frontmatter key, a fabricated
           metric, an invalid tier value, a hard 404. Breaks the build.
  REVIEW — a heuristic said "a human should look at this". Unsourced comparative
           numbers, marketing adjectives, a stale skill, a similar-looking pair,
           a `core` skill that reads niche. Printed, never fatal, never
           auto-fixed. `--strict` promotes REVIEW to FAIL for a local audit.

Nothing here rewrites a skill. Curation judgement stays with the maintainer;
this only decides what lands on their desk.

Usage
-----
    python scripts/check_content_quality.py all
    python scripts/check_content_quality.py all --offline
    python scripts/check_content_quality.py metrics --show-suppressed
    python scripts/check_content_quality.py links --cache /tmp/links.json
    python scripts/check_content_quality.py staleness --months 9
    python scripts/check_content_quality.py duplicates --threshold 0.75
"""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "skills-index.json"
SKILLS_DIR = REPO_ROOT / "skills"

FAIL = "FAIL"
REVIEW = "REVIEW"

# Windows consoles default to cp1252 and this corpus is full of em dashes.
# Without this a clean run dies in print() instead of reporting its result.
if hasattr(sys.stdout, "reconfigure"):  # pragma: no cover - environment detail
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #


@dataclass
class Finding:
    level: str  # FAIL | REVIEW
    check: str
    subject: str  # skill name, or a pair of names
    message: str
    location: str = ""

    def render(self) -> str:
        where = f" ({self.location})" if self.location else ""
        return f"{self.level}: [{self.check}] {self.subject}{where} — {self.message}"


@dataclass
class CheckResult:
    name: str
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.level == FAIL]

    @property
    def reviews(self) -> list[Finding]:
        return [f for f in self.findings if f.level == REVIEW]


@dataclass
class Skill:
    name: str
    directory: Path
    skill_md: Path
    readme_md: Path
    frontmatter: dict
    frontmatter_error: str | None
    skill_body: str
    readme_body: str
    entry: dict  # skills-index.json entry, {} when absent


# --------------------------------------------------------------------------- #
# Frontmatter parsing (stdlib-only, with PyYAML when available)
# --------------------------------------------------------------------------- #

_FENCE_RE = re.compile(r"^---\s*$", re.M)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_block, body). frontmatter_block is None if absent."""
    stripped = text.lstrip("﻿")
    if not stripped.startswith("---"):
        return None, text
    # Find the closing fence after the opening one.
    rest = stripped[3:]
    m = _FENCE_RE.search(rest)
    if not m:
        return None, text
    return rest[: m.start()], rest[m.end():]


def _coerce_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(p) for p in inner.split(",")]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    return raw


_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?$")


def _mini_yaml(block: str) -> dict:
    """A deliberately small YAML subset parser.

    Handles exactly what a SKILL.md frontmatter uses: nested mappings by
    indentation, `key: value` scalars, inline flow lists, `- item` block lists,
    and folded/literal block scalars (`description: >-`, which several skills
    use for their long trigger sentence). Exists so the workflow needs no pip
    install — ci.yml installs nothing either, and a quality gate that needs a
    dependency to run is a quality gate that gets skipped.
    """
    root: dict = {}
    # (indent, container) stack
    stack: list[tuple[int, dict]] = [(-1, root)]
    pending_list: tuple[dict, str] | None = None

    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        if content.startswith("- "):
            if pending_list is not None:
                container, key = pending_list
                container.setdefault(key, [])
                if isinstance(container[key], list):
                    container[key].append(_coerce_scalar(content[2:]))
            continue

        pending_list = None
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        container = stack[-1][1]

        if ":" not in content:
            continue
        key, _, raw = content.partition(":")
        key = key.strip()
        raw = raw.strip()

        if _BLOCK_SCALAR_RE.match(raw):
            folded = raw[0] == ">"
            chunk: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip(" "))) <= indent:
                    break
                chunk.append(nxt.strip())
                i += 1
            container[key] = (" ".join(c for c in chunk if c) if folded else "\n".join(chunk)).strip()
            continue

        # PyYAML rejects an unquoted scalar containing ": " ("mapping values are
        # not allowed here"). The fallback parser must reject it too, or CI
        # (no PyYAML installed) would pass a file that every real YAML loader
        # refuses to read.
        if raw and raw[0] not in "\"'[" and ": " in raw:
            raise ValueError(
                f"mapping values are not allowed here: `{key}` has an unquoted value "
                f"containing ': ' — quote the value"
            )
        if raw == "":
            child: dict = {}
            container[key] = child
            stack.append((indent, child))
            pending_list = (container, key)
        else:
            container[key] = _coerce_scalar(raw)
    return root


def parse_frontmatter(text: str) -> tuple[dict, str | None]:
    """Return (frontmatter_dict, error_message)."""
    block, _ = split_frontmatter(text)
    if block is None:
        return {}, "no YAML frontmatter fence"
    try:  # pragma: no cover - depends on environment
        import yaml  # type: ignore

        data = yaml.safe_load(block)
        if data is None:
            return {}, "frontmatter is empty"
        if not isinstance(data, dict):
            return {}, f"frontmatter is a {type(data).__name__}, expected a mapping"
        return data, None
    except ImportError:
        try:
            data = _mini_yaml(block)
        except ValueError as exc:
            return {}, f"frontmatter does not parse: {exc}"
        if not data:
            return {}, "frontmatter is empty"
        return data, None
    except Exception as exc:  # pragma: no cover - malformed YAML
        return {}, f"frontmatter does not parse: {exc}"


# --------------------------------------------------------------------------- #
# Corpus loading
# --------------------------------------------------------------------------- #


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_index(root: Path = REPO_ROOT) -> dict:
    path = root / "skills-index.json"
    if not path.exists():
        return {"skills": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_skills(root: Path = REPO_ROOT) -> list[Skill]:
    """Read every skills/<name>/ directory off disk. Disk is the source of truth."""
    index = load_index(root)
    by_name = {s.get("name"): s for s in index.get("skills", [])}
    skills_dir = root / "skills"
    out: list[Skill] = []
    if not skills_dir.is_dir():
        return out
    for directory in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_md = directory / "SKILL.md"
        readme_md = directory / "README.md"
        raw = _read(skill_md)
        fm, err = parse_frontmatter(raw) if raw else ({}, "SKILL.md does not exist")
        _, body = split_frontmatter(raw)
        out.append(
            Skill(
                name=directory.name,
                directory=directory,
                skill_md=skill_md,
                readme_md=readme_md,
                frontmatter=fm,
                frontmatter_error=err,
                skill_body=body,
                readme_body=_read(readme_md),
                entry=by_name.get(directory.name, {}),
            )
        )
    return out


# --------------------------------------------------------------------------- #
# 1. Frontmatter revalidation
# --------------------------------------------------------------------------- #

REQUIRED_KEYS = ("name", "description", "version", "author", "license")


def check_frontmatter(skills: list[Skill]) -> CheckResult:
    """Every SKILL.md carries the required keys and declares its own directory name.

    Reports every offender, never short-circuits on the first one.
    """
    result = CheckResult("frontmatter")
    known = {s.name for s in skills}

    for skill in skills:
        loc = f"skills/{skill.name}/SKILL.md"
        if not skill.skill_md.exists():
            result.findings.append(
                Finding(FAIL, "frontmatter", skill.name, "SKILL.md does not exist", loc)
            )
            continue
        if skill.frontmatter_error:
            result.findings.append(
                Finding(FAIL, "frontmatter", skill.name, skill.frontmatter_error, loc)
            )
            continue

        for key in REQUIRED_KEYS:
            value = skill.frontmatter.get(key)
            if value is None:
                result.findings.append(
                    Finding(FAIL, "frontmatter", skill.name, f"missing required key `{key}`", loc)
                )
            elif isinstance(value, str) and not value.strip():
                result.findings.append(
                    Finding(FAIL, "frontmatter", skill.name, f"`{key}` is empty", loc)
                )

        declared = skill.frontmatter.get("name")
        if isinstance(declared, str) and declared.strip() and declared.strip() != skill.name:
            result.findings.append(
                Finding(
                    FAIL,
                    "frontmatter",
                    skill.name,
                    f"frontmatter name is `{declared.strip()}` but the directory is `{skill.name}`",
                    loc,
                )
            )

        # AGENTS.md conventions — real rules, but not the five hard keys, so
        # they surface for review instead of breaking the build.
        desc = skill.frontmatter.get("description")
        if isinstance(desc, str) and desc.strip() and not desc.strip().lower().startswith("use when"):
            result.findings.append(
                Finding(
                    REVIEW,
                    "frontmatter",
                    skill.name,
                    'description does not start with "Use when" (AGENTS.md: trigger conditions only)',
                    loc,
                )
            )
        hermes = (skill.frontmatter.get("metadata") or {}).get("hermes") or {}
        if not hermes.get("tags"):
            result.findings.append(
                Finding(REVIEW, "frontmatter", skill.name, "no metadata.hermes.tags", loc)
            )
        for related in hermes.get("related_skills") or []:
            if isinstance(related, str) and related and related not in known:
                result.findings.append(
                    Finding(
                        REVIEW,
                        "frontmatter",
                        skill.name,
                        f"related_skills references `{related}`, which is not a skill directory",
                        loc,
                    )
                )

    result.stats = {"skills_checked": len(skills), "required_keys": list(REQUIRED_KEYS)}
    return result


# --------------------------------------------------------------------------- #
# 2. Invented-metric lint
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class MetricPattern:
    id: str
    level: str
    regex: re.Pattern
    why: str
    # When set, the phrase only counts if this also matches inside the same
    # sentence/table-cell. "in minutes" is marketing in "gets it running in
    # minutes" and a threat model in "10,000 PINs fall in minutes".
    context: re.Pattern | None = None


VALUE_VERB_RE = re.compile(
    r"\b(?:set\s*up|setup|deploy\w*|install\w*|running|runs|ready|build|built|create[sd]?"
    r"|generate[sd]?|launch\w*|configur\w*|start\w*|ship\w*|theme\w*|scaffold\w*|onboard\w*"
    r"|up\s+and\s+running|get(?:s)?\s+(?:it|you)\b)",
    re.I,
)

#
# The FAIL/REVIEW line follows AGENTS.md's actual rule — "Do not invent metrics,
# testimonials, or usage numbers". A fabricated *data point* (a count, a
# percentage, an attributed endorsement, a ranking) is objectively checkable and
# breaks the build. A hype *adjective* ("best-in-class", "seamless", "in
# minutes") is a style judgement that depends on context, so it is reported for
# a human and never auto-fixed — a linter that fails the build on adjectives
# gets muted within a week.
_RAW_METRIC_PATTERNS: list[tuple] = [
    (
        "social-proof",
        FAIL,
        re.compile(
            r"\b(?:trusted|loved|used|relied on)\s+by\s+(?:\d|over|more than|thousands|millions|teams at|companies like)",
            re.I,
        ),
        "testimonial-shaped social proof",
    ),
    (
        "join-n",
        FAIL,
        re.compile(r"\bjoin\s+(?:over\s+)?[\d,.]+\s*[kKmM]?\+?\s*(?:developers?|users?|teams?)", re.I),
        "invented community size",
    ),
    (
        "invented-count",
        FAIL,
        re.compile(
            r"\b(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?\s*[kKmM])\+?\s*"
            r"(?:\+\s*)?(?:developers?|users?|teams?|companies|customers|downloads?|installs?|stars?)\b",
            re.I,
        ),
        "large round user/download count",
    ),
    (
        "plus-count",
        FAIL,
        re.compile(r"\b\d+\+\s*(?:developers?|users?|teams?|companies|downloads?|installs?|stars?)\b", re.I),
        "N+ headcount claim",
    ),
    (
        # `[\d,.]+` alone matches a bare comma, so "downloads, stars, license"
        # in a list of badge types read as a star count. Anchor on a digit.
        "star-count",
        FAIL,
        re.compile(r"\b\d[\d,.]*\s*[kKmM]?\+?\s*(?:github\s+)?stars\b", re.I),
        "star count",
    ),
    (
        # A bare `#1` is ordinary prose ("the #1 complaint"). Only a #1 attached
        # to a product noun is a ranking claim.
        "rank-claim",
        FAIL,
        re.compile(
            r"(?:#1|\bnumber\s+one\b)\s+(?:\w+\s+){0,2}"
            r"(?:choice|tool|solution|platform|library|framework|product|app|option|generator|server)\b"
            r"|\brated\s+#1\b|\branked\s+#1\b",
            re.I,
        ),
        "ranking claim with nothing behind it",
    ),
    (
        "superlative",
        REVIEW,
        re.compile(
            r"\b(?:industry[-\s]leading|best[-\s]in[-\s]class|market[-\s]leading"
            r"|world'?s\s+(?:best|leading|fastest|most)|the\s+best\s+(?:tool|way|solution)\s+for)\b",
            re.I,
        ),
        "unearned ranking superlative — name the property instead",
    ),
    (
        "speed-hype",
        REVIEW,
        re.compile(r"\b(?:blazing(?:ly)?\s+fast|lightning[-\s]fast|insanely\s+fast|super[-\s]fast)\b", re.I),
        "performance adjective with no benchmark",
    ),
    (
        "percent-claim",
        FAIL,
        re.compile(
            r"(?:(?:increase|improve|boost|reduce|cut|save|speed\s*up|grow)\w*[^.\n]{0,40}\bby\s+\d+(?:\.\d+)?\s*%)"
            r"|(?:\b\d+(?:\.\d+)?\s*%\s+(?:faster|slower|better|more\s+\w+|improvement|increase|boost|reduction|productivity))",
            re.I,
        ),
        "percentage improvement with no cited source",
    ),
    (
        "multiplier",
        REVIEW,
        re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?\s*)?x\b[^.\n]{0,25}"
            r"\b(?:faster|slower|better|quicker|performance|speedup|improvement|throughput)\b",
            re.I,
        ),
        "unsourced multiplier claim — cite a benchmark or drop the number",
    ),
    (
        "time-promise",
        REVIEW,
        re.compile(
            r"\bin\s+(?:just\s+)?(?:minutes|seconds|under\s+a\s+minute|less\s+than\s+\d+\s+(?:minutes?|seconds?))\b",
            re.I,
        ),
        "time-to-value promise reads like marketing copy",
        VALUE_VERB_RE,
    ),
    (
        "fluff",
        REVIEW,
        re.compile(
            r"\b(?:seamless(?:ly)?|effortless(?:ly)?|cutting[-\s]edge|state[-\s]of[-\s]the[-\s]art"
            r"|game[-\s]chang(?:er|ing)|revolutionary|world[-\s]class|supercharges?"
            r"|built\s+with\s+love|unlock\s+the\s+power|next[-\s]generation)\b",
            re.I,
        ),
        "marketing filler",
    ),
]

METRIC_PATTERNS: list[MetricPattern] = [MetricPattern(*p) for p in _RAW_METRIC_PATTERNS]

# A match sitting on a line that also disowns it is a *citation* of the
# anti-pattern, not the anti-pattern. hallmark-readme is an entire skill about
# not writing this way and its tables are full of quoted bad examples.
NEGATIVE_CONTEXT_RE = re.compile(
    r"\b(?:never|don'?t|do not|avoid|omit(?:ted)?|delete[ds]?|banned|forbidden|wrong|bad"
    r"|instead|anti[-\s]?pattern|slop|fabricat\w*|invent\w*|ai\s+tell)\b",
    re.I,
)
# Weaker markers ("no", "not", "without", "filler") only suppress when the match
# is *also* inside quotes — i.e. the sentence is holding the phrase up as an
# example rather than using it. "No 'powerful, seamless' filler copy" is a rule,
# not a violation of one.
WEAK_NEGATION_RE = re.compile(r"\b(?:no|not|without|filler|rather\s+than|over)\b", re.I)
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
FENCE_LINE_RE = re.compile(r"^\s*(?:```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code spans, preserving line numbers.

    Almost every naive false positive in this corpus lives in code: `{:02x}`
    hex formatting reads as "02x", `oklch(20% ...)` reads as a percentage claim,
    `"stars": 0` reads as a star count. None of it is prose, so none of it is
    a content-quality problem.
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else INLINE_CODE_RE.sub("", line))
    return "\n".join(out)


@dataclass
class MetricHit:
    pattern_id: str
    level: str
    matched: str
    line_no: int
    line: str
    why: str
    suppressed_by: str | None = None


def lint_metrics_text(text: str, treat_as_prose: bool = True) -> list[MetricHit]:
    """Scan one document. Returns every candidate hit, suppressed ones included.

    `suppressed_by` is set (rather than the hit being dropped) so a run can show
    its own false-positive filtering instead of asking to be trusted.
    """
    scan = strip_code(text) if treat_as_prose else text
    hits: list[MetricHit] = []
    lines = scan.splitlines()
    for pattern in METRIC_PATTERNS:
        for i, line in enumerate(lines, start=1):
            for m in pattern.regex.finditer(line):
                hit = MetricHit(pattern.id, pattern.level, m.group(0).strip(), i, line.strip(), pattern.why)
                if pattern.context and not pattern.context.search(_segment_of(line, m.start())):
                    hit.suppressed_by = "no value claim in the same sentence — reads as plain fact"
                else:
                    hit.suppressed_by = _suppression_reason(line, m)
                hits.append(hit)
    return hits


_SEGMENT_SPLIT_RE = re.compile(r"[.;|]")


def _segment_of(line: str, position: int) -> str:
    """The sentence / table cell the match sits in."""
    start = 0
    for m in _SEGMENT_SPLIT_RE.finditer(line):
        if m.start() >= position:
            return line[start:m.start()]
        start = m.end()
    return line[start:]


def _suppression_reason(line: str, match: re.Match) -> str | None:
    if NEGATIVE_CONTEXT_RE.search(line):
        return "cited as an anti-pattern on the same line"
    if _is_quoted(line, match):
        if TABLE_ROW_RE.match(line):
            return "quoted example inside a comparison table"
        if WEAK_NEGATION_RE.search(line):
            return "quoted example inside a negative statement"
    return None


def _is_quoted(line: str, match: re.Match) -> bool:
    before = line[: match.start()]
    return (before.count('"') % 2 == 1) or (before.count("“") > before.count("”"))


def check_metrics(skills: list[Skill], show_suppressed: bool = False) -> CheckResult:
    result = CheckResult("metrics")
    candidates = 0
    suppressed = 0
    suppressed_detail: list[str] = []

    for skill in skills:
        docs = [
            (f"skills/{skill.name}/SKILL.md", _read(skill.skill_md)),
            (f"skills/{skill.name}/README.md", _read(skill.readme_md)),
        ]
        # The index description is what the catalog page actually renders, so it
        # gets linted even though it is not a file on disk.
        desc = (skill.entry.get("description") or "").strip()
        if desc:
            docs.append((f"skills-index.json:{skill.name}.description", desc))
        fm_desc = skill.frontmatter.get("description")
        if isinstance(fm_desc, str) and fm_desc.strip():
            docs.append((f"skills/{skill.name}/SKILL.md:frontmatter.description", fm_desc.strip()))

        for location, text in docs:
            if not text:
                continue
            for hit in lint_metrics_text(text):
                candidates += 1
                if hit.suppressed_by:
                    suppressed += 1
                    if show_suppressed:
                        suppressed_detail.append(
                            f"  suppressed [{hit.pattern_id}] {location}:{hit.line_no} "
                            f"{hit.matched!r} — {hit.suppressed_by}"
                        )
                    continue
                result.findings.append(
                    Finding(
                        hit.level,
                        "metrics",
                        skill.name,
                        f"{hit.why}: {hit.matched!r} — “{_clip(hit.line)}”",
                        f"{location}:{hit.line_no}",
                    )
                )

    surviving = candidates - suppressed
    result.stats = {
        "candidate_matches": candidates,
        "suppressed_by_context": suppressed,
        "reported": surviving,
        "suppression_rate": round(suppressed / candidates, 3) if candidates else 0.0,
    }
    result.notes.append(
        f"{candidates} raw pattern match(es); {suppressed} suppressed as cited anti-patterns; "
        f"{surviving} reported."
    )
    result.notes.extend(suppressed_detail)
    return result


def _clip(text: str, width: int = 110) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


# --------------------------------------------------------------------------- #
# 3. Broken-link checker
# --------------------------------------------------------------------------- #

# The trailing `(?:[<{]...[>}])?` deliberately swallows a template suffix, so
# `https://api.telegram.org/bot<TOKEN>/setWebhook` comes back whole instead of
# being truncated to `https://api.telegram.org/bot` — which is a live host and a
# hard 404, i.e. the worst kind of false positive.
URL_RE = re.compile(r"https?://[^\s<>\"'`\\|)\]}]+(?:[<{][^\s>}]*[>}][^\s<>\"'`\\|)\]}]*)*", re.I)
TRAILING_JUNK = ".,;:!?—–*_'\""

# Docs are full of stand-ins. Checking them is noise at best and a red build at
# worst, so they are classified, never fetched. Each alternative below is a real
# convention found in this corpus:
PLACEHOLDER_RE = re.compile(
    r"[<>{}]"                                   # https://<your-domain>/hook
    r"|\.\.\."                                  # https://github.com/.../tree/main
    r"|YOUR[-_.]|MY[-_]"                        # your-domain.com, my-alerts-abc123
    r"|example\.(?:com|org|net)"                # RFC 2606 documentation names
    r"|localhost|127\.0\.0\.1|0\.0\.0\.0"       # loopback
    r"|github\.com/(?:user|users|me|you|owner|username|your[-\w]*|my[-\w]*|org|example)/",
    re.I,
)

UNVERIFIABLE_CODES = {401, 403, 405, 406, 429, 999}
# Endpoints that answer 404 by design when called without params or auth. A 404
# from one of these says nothing about whether the documentation is stale.
API_ENDPOINT_RE = re.compile(r"//api\.|googleapis\.com|/api/|/v\d+/", re.I)
USER_AGENT = "hermes-skills-portfolio-quality-check/1.0 (+https://github.com/)"


@dataclass
class LinkResult:
    url: str
    status: str  # ok | broken | unverifiable | placeholder | malformed
    detail: str
    checked_at: str = ""


def extract_urls(text: str) -> list[str]:
    # Code blocks are NOT stripped here: the install command lives in a fenced
    # block, and a dead install URL is the single worst link in the corpus.
    urls: list[str] = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(TRAILING_JUNK)
        # Markdown often wraps a URL in parentheses; only strip an unbalanced one.
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        if url:
            urls.append(url)
    return urls


def collect_urls(skills: list[Skill]) -> dict[str, list[str]]:
    """url -> list of locations that mention it."""
    found: dict[str, list[str]] = {}
    for skill in skills:
        for location, text in (
            (f"skills/{skill.name}/SKILL.md", _read(skill.skill_md)),
            (f"skills/{skill.name}/README.md", _read(skill.readme_md)),
        ):
            for url in extract_urls(text):
                found.setdefault(url, []).append(location)
    return found


def validate_url_shape(url: str) -> LinkResult:
    """Offline validation: is this even a well-formed, checkable URL?"""
    if PLACEHOLDER_RE.search(url):
        return LinkResult(url, "placeholder", "documentation placeholder, not a real target")
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        return LinkResult(url, "malformed", f"unparsable: {exc}")
    if parts.scheme not in ("http", "https"):
        return LinkResult(url, "malformed", f"unsupported scheme {parts.scheme!r}")
    if " " in url:
        return LinkResult(url, "malformed", "contains a space")
    if not parts.netloc:
        # `https://...` in a table cell — an ellipsis, not a link. The trailing
        # dots are stripped as punctuation before we ever see it.
        return LinkResult(url, "placeholder", "truncated template (no host)")
    if "." not in parts.netloc.split(":")[0]:
        # `http://dashboard:8080` (compose service), `http://my-service`
        # (tailnet MagicDNS). Single-label hosts are valid on those networks and
        # deliberately unresolvable from anywhere else — not a broken link.
        return LinkResult(
            url, "placeholder", f"single-label host {parts.netloc!r} (container/tailnet name)"
        )
    return LinkResult(url, "ok", "shape is valid (offline mode: not fetched)")


def _fetch_once(url: str, timeout: float, method: str) -> tuple[int | None, str]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, ""
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc.reason)
    except urllib.error.URLError as exc:
        return None, str(exc.reason)
    except Exception as exc:  # socket/ssl/decoding oddities
        return None, f"{type(exc).__name__}: {exc}"


def check_url(url: str, timeout: float = 10.0) -> LinkResult:
    """HEAD, fall back to GET, retry once. 403/429 is 'unverifiable', not broken.

    CI runners get blocked by a lot of hosts (Cloudflare, docs sites, npm).
    Treating that as a broken link would make the check cry wolf every week and
    train everyone to ignore it.
    """
    shape = validate_url_shape(url)
    if shape.status != "ok":
        return shape

    last_detail = ""
    for attempt in range(2):  # one retry
        for method in ("HEAD", "GET"):
            code, detail = _fetch_once(url, timeout, method)
            if code is None:
                last_detail = detail
                continue
            if code < 400:
                return LinkResult(url, "ok", f"{method} {code}")
            if code in UNVERIFIABLE_CODES:
                return LinkResult(url, "unverifiable", f"{method} {code} (host blocks automated checks)")
            if code in (404, 410):
                # Some hosts 404 a HEAD they would have answered for a GET, so a
                # 404 is only conclusive once GET agrees.
                if method == "HEAD":
                    last_detail = f"HEAD {code}"
                    continue
                if API_ENDPOINT_RE.search(url):
                    return LinkResult(
                        url, "unverifiable", f"GET {code} on an API endpoint (needs auth/params)"
                    )
                if urlsplit(url).path in ("", "/"):
                    return LinkResult(
                        url, "unverifiable", f"GET {code} on a bare host root (not a content page)"
                    )
                return LinkResult(url, "broken", f"GET {code} {detail}".strip())
            last_detail = f"{method} {code} {detail}".strip()
        if attempt == 0:
            time.sleep(0.5)
    if last_detail:
        return LinkResult(url, "unverifiable", f"no conclusive response ({last_detail})")
    return LinkResult(url, "unverifiable", "no conclusive response")


def default_cache_path() -> Path:
    """Deliberately outside the repo — a cache file is not a source artifact.

    CI passes an explicit --cache under the runner temp dir and restores it with
    actions/cache, so reruns stay fast without ever dirtying `git status`.
    """
    return Path(tempfile.gettempdir()) / "hermes-skills-quality" / "link-cache.json"


def _load_cache(path: Path, ttl_days: float) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    cutoff = time.time() - ttl_days * 86400
    return {
        url: rec
        for url, rec in raw.items()
        if isinstance(rec, dict) and rec.get("ts", 0) >= cutoff
    }


def _save_cache(path: Path, cache: dict[str, dict]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    except OSError:
        pass  # a cache that cannot be written is a slow run, not a failure


def check_links(
    skills: list[Skill],
    offline: bool = False,
    workers: int = 8,
    timeout: float = 10.0,
    cache_path: Path | None = None,
    ttl_days: float = 7.0,
) -> CheckResult:
    result = CheckResult("links")
    urls = collect_urls(skills)
    result.stats["unique_urls"] = len(urls)

    if offline:
        results = {url: validate_url_shape(url) for url in urls}
        result.notes.append(f"--offline: validated the shape of {len(urls)} unique URL(s), fetched none.")
    else:
        cache_path = cache_path or default_cache_path()
        cache = _load_cache(cache_path, ttl_days)
        results = {}
        todo = []
        for url in urls:
            hit = cache.get(url)
            if hit:
                results[url] = LinkResult(url, hit["status"], hit["detail"] + " (cached)", hit.get("iso", ""))
            else:
                todo.append(url)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for res in pool.map(lambda u: check_url(u, timeout), todo):
                results[res.url] = res
                cache[res.url] = {
                    "status": res.status,
                    "detail": res.detail,
                    "ts": time.time(),
                    "iso": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
        _save_cache(cache_path, cache)
        result.notes.append(
            f"Checked {len(todo)} URL(s) over the network, {len(urls) - len(todo)} served from "
            f"cache at {cache_path}."
        )

    tally: dict[str, int] = {}
    for url, res in sorted(results.items()):
        tally[res.status] = tally.get(res.status, 0) + 1
        where = ", ".join(sorted(set(urls[url])))
        if res.status == "broken":
            result.findings.append(Finding(FAIL, "links", url, f"broken — {res.detail}", where))
        elif res.status == "malformed":
            result.findings.append(Finding(FAIL, "links", url, f"malformed URL — {res.detail}", where))
        elif res.status == "unverifiable":
            result.findings.append(
                Finding(REVIEW, "links", url, f"unverifiable — {res.detail}", where)
            )
    result.stats.update(tally)
    return result


# --------------------------------------------------------------------------- #
# 4. Staleness report
# --------------------------------------------------------------------------- #


def git_last_commit_iso(path: Path, root: Path = REPO_ROOT) -> str | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(root)).replace("\\", "/")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def months_since(iso: str, now: datetime | None = None) -> float:
    when = datetime.fromisoformat(iso)
    now = now or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (now - when).days / 30.44


def check_staleness(skills: list[Skill], months: float = 6.0, root: Path = REPO_ROOT) -> CheckResult:
    """Surface skills nobody has touched in a while. Never fails the build.

    Age is not a defect — a correct skill can sit untouched for a year. This is
    a review queue, so every finding is REVIEW by construction.
    """
    result = CheckResult("staleness")
    unknown = 0
    ages: list[tuple[float, str, str]] = []
    for skill in skills:
        iso = git_last_commit_iso(skill.directory, root)
        if not iso:
            unknown += 1
            continue
        age = months_since(iso)
        ages.append((age, skill.name, iso[:10]))
    for age, name, day in sorted(ages, reverse=True):
        if age >= months:
            result.findings.append(
                Finding(
                    REVIEW,
                    "staleness",
                    name,
                    f"last touched {day} ({age:.1f} months ago, threshold {months:g})",
                    f"skills/{name}",
                )
            )
    result.stats = {
        "threshold_months": months,
        "skills_with_history": len(ages),
        "skills_without_history": unknown,
        "oldest_months": round(max((a for a, _, _ in ages), default=0.0), 1),
        "newest_months": round(min((a for a, _, _ in ages), default=0.0), 1),
    }
    if unknown:
        result.notes.append(f"{unknown} skill(s) had no git history (new, untracked, or shallow clone).")
    if ages and max(a for a, _, _ in ages) < months:
        result.notes.append(
            f"Nothing is stale: the oldest skill was last touched "
            f"{max(a for a, _, _ in ages):.1f} months ago, under the {months:g}-month threshold. "
            "A freshly-squashed history makes every skill look new — read this alongside the real commit dates."
        )
    return result


# --------------------------------------------------------------------------- #
# 5. Duplicate-content detector
# --------------------------------------------------------------------------- #

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "into", "is", "it", "its", "of", "on", "or", "our", "that", "the", "their", "them",
    "then", "there", "these", "this", "to", "use", "used", "user", "uses", "when", "with",
    "you", "your", "want", "wants", "says", "agent",
}


def normalize_text(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def token_set(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def extract_section(body: str, heading: str) -> str:
    """Pull one `## Heading` section out of a markdown body."""
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    m = pattern.search(body)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def skill_profile(skill: Skill) -> str:
    """The text a duplicate would actually duplicate: what it claims to do."""
    parts = [
        (skill.entry.get("description") or "").strip(),
        str(skill.frontmatter.get("description") or "").strip(),
        extract_section(skill.skill_body, "Overview").strip(),
    ]
    return normalize_text(" ".join(p for p in parts if p))


def score_all_pairs(profiles: dict[str, str]) -> list[tuple[str, str, float, float]]:
    """Every pair, scored. Returns (a, b, difflib_ratio, jaccard), most similar first."""
    names = sorted(profiles)
    tokens = {n: token_set(profiles[n]) for n in names}
    out: list[tuple[str, str, float, float]] = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not profiles[a] or not profiles[b]:
                continue
            j = jaccard(tokens[a], tokens[b])
            ratio = difflib.SequenceMatcher(None, profiles[a], profiles[b]).ratio()
            out.append((a, b, round(ratio, 3), round(j, 3)))
    return sorted(out, key=lambda r: -max(r[2], r[3]))


def find_duplicate_pairs(
    profiles: dict[str, str], threshold: float = 0.80, token_threshold: float = 0.70
) -> list[tuple[str, str, float, float]]:
    """Pairs whose similarity clears either threshold."""
    return [
        p for p in score_all_pairs(profiles) if p[2] >= threshold or p[3] >= token_threshold
    ]


def check_duplicates(
    skills: list[Skill], threshold: float = 0.80, token_threshold: float = 0.70
) -> CheckResult:
    result = CheckResult("duplicates")
    profiles = {s.name: skill_profile(s) for s in skills}
    empty = [n for n, p in profiles.items() if not p]
    scored = score_all_pairs(profiles)
    pairs = [p for p in scored if p[2] >= threshold or p[3] >= token_threshold]
    # Print the closest pairs even when none cross the bar, so a clean run is
    # visibly calibrated rather than just silent.
    if scored:
        top = "; ".join(f"{a}~{b} {max(r, j):.0%}" for a, b, r, j in scored[:3])
        result.notes.append(f"Closest pairs in the corpus: {top}")
    for a, b, ratio, j in pairs:
        result.findings.append(
            Finding(
                REVIEW,
                "duplicates",
                f"{a} <-> {b}",
                f"descriptions/overviews are {ratio:.0%} similar (token overlap {j:.0%}) — "
                "confirm these are genuinely different skills",
            )
        )
    result.stats = {
        "pairs_compared": len(scored),
        "threshold": threshold,
        "token_threshold": token_threshold,
        "flagged_pairs": len(pairs),
        "max_similarity": max((max(r, j) for _, _, r, j in scored), default=0.0),
        "skills_without_profile": len(empty),
    }
    if empty:
        result.notes.append(f"No comparable text for: {', '.join(sorted(empty))}")
    return result


# --------------------------------------------------------------------------- #
# 6. Tier-consistency check
# --------------------------------------------------------------------------- #

VALID_TIERS = ("core", "featured", "utility")
# Categories are DERIVED from skills-index.json's own `categories` block, never
# hardcoded: the index defines the vocabulary, so adding a legitimate new
# category would otherwise fail every skill that uses it. This tuple is only the
# fallback for a malformed index with no categories block at all.
FALLBACK_CATEGORIES = ("devops", "frontend", "backend", "utility", "meta", "integrations")


def valid_categories(index):
    """The category vocabulary declared by the index itself."""
    declared = tuple((index or {}).get("categories", {}).keys())
    return declared or FALLBACK_CATEGORIES

# A skill is "narrow" when its description only makes sense if you already run
# one particular product or handle one particular file format.
NARROW_SIGNALS = re.compile(
    r"\b(?:tailscale|forgejo|caddy|searxng|ollama|uptime[-\s]kuma|discord|telegram|ntfy|excalidraw"
    r"|sqlite|tenor|youtube|postman|keynote|powerpoint|openapi|qr|vcard|wifi|ocr|rss|atom|csv|pdf"
    r"|gif|json|yaml|markdown|ascii|regex|cron|dotfiles|smtp)\b",
    re.I,
)
# ...and "broad" when it names no vendor and applies to any project.
BROAD_SIGNALS = re.compile(
    r"\b(?:any\s+project|any\s+repo|every\s+project|your\s+project|any\s+codebase|your\s+codebase"
    r"|any\s+stack|detected\s+project|for\s+any\b|regardless\s+of|meta[-\s]skill)\b",
    re.I,
)


def tier_scope_findings(entries: list[dict]) -> list[Finding]:
    """Heuristic only. Flags a mismatch between declared tier and described scope.

    Deliberately never rewrites `tier`. Tier is an editorial judgement about how
    much of the audience a skill serves; a regex cannot make that call, it can
    only notice when the prose and the label point in different directions.
    """
    findings: list[Finding] = []
    for entry in entries:
        name = entry.get("name", "<unnamed>")
        tier = entry.get("tier")
        desc = entry.get("description") or ""
        narrow = len(set(m.group(0).lower() for m in NARROW_SIGNALS.finditer(desc)))
        broad = len(set(m.group(0).lower() for m in BROAD_SIGNALS.finditer(desc)))

        if tier == "core" and narrow >= 1 and broad == 0:
            findings.append(
                Finding(
                    REVIEW,
                    "tiers",
                    name,
                    f"tier=core but the description is scoped to a specific tool/format "
                    f"({narrow} narrow signal(s), 0 broad): “{_clip(desc, 90)}”",
                )
            )
        elif tier == "utility" and broad >= 1 and narrow == 0:
            findings.append(
                Finding(
                    REVIEW,
                    "tiers",
                    name,
                    f"tier=utility but the description reads broadly applicable "
                    f"({broad} broad signal(s), 0 narrow): “{_clip(desc, 90)}”",
                )
            )
    return findings


def check_tiers(skills: list[Skill], root: Path = REPO_ROOT) -> CheckResult:
    result = CheckResult("tiers")
    index = load_index(root)
    entries = index.get("skills", [])
    by_name = {e.get("name"): e for e in entries}
    categories = valid_categories(index)

    for skill in skills:
        entry = by_name.get(skill.name)
        if entry is None:
            result.findings.append(
                Finding(FAIL, "tiers", skill.name, "skill directory has no skills-index.json entry")
            )
            continue
        tier = entry.get("tier")
        if not tier:
            result.findings.append(Finding(FAIL, "tiers", skill.name, "no `tier` in skills-index.json"))
        elif tier not in VALID_TIERS:
            result.findings.append(
                Finding(FAIL, "tiers", skill.name, f"tier {tier!r} is not one of {VALID_TIERS}")
            )
        category = entry.get("category")
        if not category:
            result.findings.append(Finding(FAIL, "tiers", skill.name, "no `category` in skills-index.json"))
        elif category not in categories:
            result.findings.append(
                Finding(FAIL, "tiers", skill.name, f"category {category!r} is not one of {categories}")
            )

    result.findings.extend(tier_scope_findings([e for e in entries if e.get("name") in by_name]))

    counts: dict[str, int] = {}
    for e in entries:
        counts[str(e.get("tier"))] = counts.get(str(e.get("tier")), 0) + 1
    result.stats = {"tier_counts": counts, "skills": len(entries)}
    return result


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def print_result(result: CheckResult, quiet: bool = False) -> None:
    print(f"\n=== {result.name} ===")
    for note in result.notes:
        print(note)
    fails = result.failures
    reviews = result.reviews
    for finding in fails:
        print(finding.render())
    if not quiet:
        for finding in reviews:
            print(finding.render())
    if result.stats:
        print(f"stats: {json.dumps(result.stats, sort_keys=True, default=str)}")
    print(f"-> {len(fails)} failure(s), {len(reviews)} item(s) for review")


def markdown_summary(results: list[CheckResult]) -> str:
    lines = ["# Content quality report", ""]
    lines.append("| Check | Failures | For review | Notes |")
    lines.append("|---|---:|---:|---|")
    for r in results:
        note = r.notes[0].replace("|", "\\|") if r.notes else ""
        lines.append(f"| `{r.name}` | {len(r.failures)} | {len(r.reviews)} | {_clip(note, 80)} |")
    for r in results:
        if not r.findings:
            continue
        lines += ["", f"## {r.name}", ""]
        for f in r.failures:
            lines.append(f"- **FAIL** `{f.subject}` — {f.message} {'`' + f.location + '`' if f.location else ''}")
        for f in r.reviews[:40]:
            lines.append(f"- _review_ `{f.subject}` — {f.message} {'`' + f.location + '`' if f.location else ''}")
        if len(r.reviews) > 40:
            lines.append(f"- _… {len(r.reviews) - 40} more review item(s)_")
    lines += ["", "FAIL items break the build. Review items are for a human to judge —",
              "nothing here is auto-fixed or auto-committed."]
    return "\n".join(lines) + "\n"


def write_summary(results: list[CheckResult], path: str | None) -> None:
    target = path or os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(markdown_summary(results))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

ALL_CHECKS = ("frontmatter", "metrics", "links", "staleness", "duplicates", "tiers")


def run_checks(names: list[str], args: argparse.Namespace) -> list[CheckResult]:
    skills = load_skills(args.root)
    results: list[CheckResult] = []
    for name in names:
        if name == "frontmatter":
            results.append(check_frontmatter(skills))
        elif name == "metrics":
            results.append(check_metrics(skills, show_suppressed=args.show_suppressed))
        elif name == "links":
            results.append(
                check_links(
                    skills,
                    offline=args.offline,
                    workers=args.workers,
                    timeout=args.timeout,
                    cache_path=Path(args.cache) if args.cache else None,
                    ttl_days=args.cache_ttl_days,
                )
            )
        elif name == "staleness":
            results.append(check_staleness(skills, months=args.months, root=args.root))
        elif name == "duplicates":
            results.append(
                check_duplicates(skills, threshold=args.threshold, token_threshold=args.token_threshold)
            )
        elif name == "tiers":
            results.append(check_tiers(skills, root=args.root))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_content_quality.py",
        description="Content-quality and curation gates for the skills catalog.",
    )
    parser.add_argument(
        "checks",
        nargs="*",
        default=["all"],
        help=f"one or more of: all, {', '.join(ALL_CHECKS)} (default: all)",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root (default: this repo)")
    parser.add_argument("--strict", action="store_true", help="treat REVIEW findings as failures")
    parser.add_argument("--quiet", action="store_true", help="print failures only")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit findings as JSON")
    parser.add_argument("--summary-file", help="append a markdown report here (default: $GITHUB_STEP_SUMMARY)")

    parser.add_argument("--show-suppressed", action="store_true", help="metrics: show context-suppressed matches")

    parser.add_argument("--offline", action="store_true", help="links: validate URL shape only, no network")
    parser.add_argument("--workers", type=int, default=8, help="links: concurrent fetches (default: 8)")
    parser.add_argument("--timeout", type=float, default=10.0, help="links: per-request timeout seconds")
    parser.add_argument("--cache", help="links: cache file path (default: OS temp dir, never the repo)")
    parser.add_argument("--cache-ttl-days", type=float, default=7.0, help="links: cache entry lifetime")

    parser.add_argument("--months", type=float, default=6.0, help="staleness: months before a skill is stale")

    parser.add_argument("--threshold", type=float, default=0.80, help="duplicates: difflib ratio threshold")
    parser.add_argument("--token-threshold", type=float, default=0.70, help="duplicates: token-overlap threshold")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    requested = args.checks or ["all"]
    names = list(ALL_CHECKS) if "all" in requested else requested
    unknown = [n for n in names if n not in ALL_CHECKS]
    if unknown:
        print(f"FAIL: unknown check(s): {', '.join(unknown)}")
        return 2

    results = run_checks(names, args)

    if args.as_json:
        print(
            json.dumps(
                {
                    r.name: {
                        "stats": r.stats,
                        "notes": r.notes,
                        "findings": [vars(f) for f in r.findings],
                    }
                    for r in results
                },
                indent=2,
                default=str,
            )
        )
    else:
        for result in results:
            print_result(result, quiet=args.quiet)

    write_summary(results, args.summary_file)

    total_fail = sum(len(r.failures) for r in results)
    total_review = sum(len(r.reviews) for r in results)
    print(
        f"\nTOTAL: {total_fail} failure(s), {total_review} review item(s) "
        f"across {len(results)} check(s)."
    )
    if total_fail:
        return 1
    if args.strict and total_review:
        print("--strict: review items treated as failures.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
