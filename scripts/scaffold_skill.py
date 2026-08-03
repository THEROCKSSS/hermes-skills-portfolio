#!/usr/bin/env python3
"""Scaffold a new skill directory from an approved community submission.

What this does
--------------
Takes the fields captured by `.github/ISSUE_TEMPLATE/skill_request.yml` (as a
JSON file, as the raw rendered issue body, or as CLI flags) and:

  1. validates the proposed name (kebab-case, not already taken),
  2. writes ``skills/<name>/SKILL.md`` and ``skills/<name>/README.md`` in the
     repo's existing format,
  3. emits the ``skills-index.json`` entry as JSON on stdout or to a file.

What this deliberately does NOT do
----------------------------------
It never writes into ``skills-index.json``. The index is the catalog's source
of truth and a human (or the submission workflow's explicit merge step) decides
when an entry lands in it. This script only *proposes* the entry.

Install-URL rule (the bug this file must never reintroduce)
-----------------------------------------------------------
``install_url`` MUST be the raw host::

    https://raw.githubusercontent.com/OWNER/REPO/main/skills/<name>/SKILL.md

A ``github.com/.../blob/...`` URL serves ``text/html``, so
``hermes skills install <blob-url>`` exits 0 while writing GitHub's web page
into the skill body. The human-facing blob page is kept separately in
``source_url`` and is never used as an install target. ``build_index_entry``
asserts this split; see ``scripts/normalize_install_urls.py``.

Usage
-----
    # from a parsed submission
    python scripts/scaffold_skill.py --json submission.json

    # straight from a GitHub issue-form body
    python scripts/scaffold_skill.py --issue-body body.md --issue-number 42

    # see what would happen, write nothing
    python scripts/scaffold_skill.py --json submission.json --dry-run

    # validate only (also reports the closest existing skills)
    python scripts/scaffold_skill.py --issue-body body.md --check-only \
        --report report.json

Exit codes: 0 = ok, 2 = the submission is invalid (bad name, duplicate,
missing required field), 1 = unexpected I/O failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:  # PyYAML is used only to re-parse what we generate, as a self-check.
    import yaml
except ImportError:  # pragma: no cover - exercised only on a bare interpreter
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_OWNER = "THEROCKSSS"
DEFAULT_REPO = "hermes-skills-portfolio"
DEFAULT_REF = "main"

EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_INVALID = 2

# Skill directory names: lowercase kebab-case only. This is also the URL slug,
# the frontmatter `name`, and the site route, so it has to stay filesystem- and
# URL-safe on every platform.
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_MIN_LEN = 3
NAME_MAX_LEN = 48
# Names that would collide with a top-level repo path or confuse the site router.
RESERVED_NAMES = {"skills", "site", "docs", "scripts", "tests", "index", "new", "all"}

CATEGORIES = ("devops", "frontend", "backend", "utility", "meta", "integrations")
CATEGORY_ALIASES = {
    "devops & infrastructure": "devops",
    "devops and infrastructure": "devops",
    "infrastructure": "devops",
    "dev-ops": "devops",
    "integration": "integrations",
    "front-end": "frontend",
    "back-end": "backend",
}

TIERS = ("core", "featured", "utility")
ORIGINS = ("original", "adapted")

TAG_STOPWORDS = {
    "a", "an", "and", "any", "are", "for", "from", "into", "its", "not", "one",
    "our", "out", "over", "the", "that", "this", "with", "when", "what", "who",
    "you", "your", "user", "users", "agent", "agents", "skill", "skills", "use",
    "uses", "using", "will", "can", "has", "have", "run", "runs", "make", "makes",
    "them", "their", "they", "then", "than", "get", "gets", "set", "sets", "new",
    "without", "instead", "real", "own", "off", "all",
}

TAG_MAX = 6
RELATED_MAX = 3
FRONTMATTER_DESC_MAX = 480

# Issue-form field id -> submission key. The ids are declared in
# .github/ISSUE_TEMPLATE/skill_request.yml; keep the two in sync.
FIELD_IDS = {
    "skill_name": "name",
    "category": "category",
    "tier": "tier",
    "description": "description",
    "when_to_use": "when_to_use",
    "what_it_does": "what_it_does",
    "prerequisites": "prerequisites",
    "origin": "origin",
    "origin_url": "origin_url",
}

# The rendered issue body uses the human-readable *label*, not the id, so the
# parser matches on the label text (normalized) as well.
LABEL_TO_FIELD = {
    "proposed skill name": "name",
    "skill name": "name",
    "category": "category",
    "tier": "tier",
    "one-line description": "description",
    "description": "description",
    "when to use it": "when_to_use",
    "when to use": "when_to_use",
    "what the agent does": "what_it_does",
    "what it does": "what_it_does",
    "prerequisites": "prerequisites",
    "original or adapted": "origin",
    "origin": "origin",
    "origin url": "origin_url",
    "source url": "origin_url",
}

NO_RESPONSE = "_no response_"

REQUIRED_FIELDS = ("name", "category", "tier", "description", "when_to_use", "what_it_does")


class SubmissionError(Exception):
    """A submission is unusable. The message is shown to the maintainer verbatim."""

    def __init__(self, *errors: str):
        self.errors = [str(e) for e in errors]
        super().__init__("; ".join(self.errors))


# --------------------------------------------------------------------------
# Input parsing
# --------------------------------------------------------------------------


def _normalize_label(text: str) -> str:
    """'One-line description' / '**One line description**' -> 'one line description'."""
    lowered = re.sub(r"[-_/]+", " ", text.strip().lower())
    return " ".join(re.sub(r"[^a-z0-9 ]+", "", lowered).split())


# Built from LABEL_TO_FIELD so a label written with hyphens, bold markers or
# trailing punctuation still resolves to the same field.
_LABEL_LOOKUP = {_normalize_label(k): v for k, v in LABEL_TO_FIELD.items()}


def parse_issue_body(body: str) -> dict:
    """Parse a rendered GitHub issue-form body into submission fields.

    GitHub renders an issue form as ``### <label>`` followed by the answer.
    Unanswered optional fields render as ``_No response_``.
    """
    fields: dict[str, str] = {}
    if not body:
        return fields

    current: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current is None:
            return
        value = "\n".join(buffer).strip()
        if value.lower() == NO_RESPONSE:
            value = ""
        # Strip a markdown code fence GitHub sometimes wraps long answers in.
        fence = re.match(r"^```[a-zA-Z0-9]*\n(.*)\n```$", value, re.DOTALL)
        if fence:
            value = fence.group(1).strip()
        fields[current] = value

    for line in body.replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^#{2,4}\s+(.*\S)\s*$", line)
        if heading:
            flush()
            current = _LABEL_LOOKUP.get(_normalize_label(heading.group(1)))
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    flush()

    return {k: v for k, v in fields.items() if v}


def _choice(value: str, allowed: tuple, field: str, aliases: dict | None = None) -> str:
    """Normalize a dropdown answer to its slug.

    Dropdown options are written as ``slug — human explanation``, and people
    also paste the display name ("DevOps & Infrastructure"), so accept both.
    """
    raw = (value or "").strip()
    if not raw:
        raise SubmissionError(f"{field} is required")
    lowered = raw.lower()
    aliases = aliases or {}

    # "utility — General-purpose ..." / "utility (general purpose)" -> "utility"
    head = re.split(r"[—–\-(:]", lowered, maxsplit=1)[0].strip()
    for candidate in (lowered, head, aliases.get(lowered, ""), aliases.get(head, "")):
        if candidate in allowed:
            return candidate
    first_word = lowered.split()[0].strip(".,:;()") if lowered.split() else ""
    if first_word in allowed:
        return first_word
    raise SubmissionError(
        f"{field} must be one of {', '.join(allowed)} (got {raw!r})"
    )


def as_bullets(text: str) -> list[str]:
    """Normalize free text into a clean bullet list (markers stripped)."""
    items: list[str] = []
    for line in (text or "").replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", stripped).strip()
        if stripped:
            items.append(stripped)
    return items


def normalize_submission(raw: dict) -> dict:
    """Validate and normalize raw submission fields. Raises SubmissionError."""
    if not isinstance(raw, dict):
        raise SubmissionError("submission must be a JSON object")

    errors: list[str] = []
    sub: dict = {}

    name = str(raw.get("name", "")).strip().lower()
    sub["name"] = name

    for field in ("description", "when_to_use", "what_it_does", "prerequisites"):
        sub[field] = str(raw.get(field, "") or "").strip()

    sub["description"] = " ".join(sub["description"].split())

    for field in ("category", "tier"):
        allowed = CATEGORIES if field == "category" else TIERS
        aliases = CATEGORY_ALIASES if field == "category" else None
        try:
            sub[field] = _choice(str(raw.get(field, "")), allowed, field, aliases)
        except SubmissionError as exc:
            errors.extend(exc.errors)
            sub[field] = ""

    origin_raw = str(raw.get("origin", "") or "original")
    try:
        sub["origin"] = _choice(origin_raw, ORIGINS, "origin")
    except SubmissionError as exc:
        errors.extend(exc.errors)
        sub["origin"] = ""

    sub["origin_url"] = str(raw.get("origin_url", "") or "").strip()
    if sub["origin"] == "adapted" and not sub["origin_url"]:
        errors.append("origin_url is required when the skill is adapted from another source")
    if sub["origin_url"] and not sub["origin_url"].lower().startswith(("http://", "https://")):
        errors.append(f"origin_url must be an http(s) URL (got {sub['origin_url']!r})")

    submitter = str(raw.get("submitter", "") or "").strip().lstrip("@")
    sub["submitter"] = submitter

    issue_number = raw.get("issue_number")
    if issue_number in ("", None):
        sub["issue_number"] = None
    else:
        try:
            sub["issue_number"] = int(str(issue_number).lstrip("#"))
        except (TypeError, ValueError):
            errors.append(f"issue_number must be an integer (got {issue_number!r})")
            sub["issue_number"] = None

    for field in REQUIRED_FIELDS:
        if not sub.get(field):
            if field in ("category", "tier"):
                continue  # already reported by _choice
            errors.append(f"{field} is required and was empty")

    errors.extend(check_name(name))

    if errors:
        raise SubmissionError(*errors)
    return sub


# --------------------------------------------------------------------------
# Name validation / duplicate detection
# --------------------------------------------------------------------------


def check_name(name: str) -> list[str]:
    """Return format problems with a proposed skill name (no I/O)."""
    problems: list[str] = []
    if not name:
        problems.append("name is required and was empty")
        return problems
    if not NAME_RE.match(name):
        problems.append(
            f"name {name!r} is not lowercase kebab-case — use letters, digits and "
            "single hyphens only (e.g. 'log-analyzer', not 'LogAnalyzer' or 'log_analyzer')"
        )
    if len(name) < NAME_MIN_LEN:
        problems.append(f"name {name!r} is too short (minimum {NAME_MIN_LEN} characters)")
    if len(name) > NAME_MAX_LEN:
        problems.append(f"name {name!r} is too long (maximum {NAME_MAX_LEN} characters)")
    if name in RESERVED_NAMES:
        problems.append(f"name {name!r} is reserved and cannot be used as a skill name")
    return problems


def load_index(repo_root: Path) -> dict:
    """Read skills-index.json. A missing index is treated as empty, not fatal."""
    index_path = Path(repo_root) / "skills-index.json"
    if not index_path.exists():
        return {"skills": [], "categories": {}}
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SubmissionError(f"skills-index.json is not valid JSON: {exc}") from exc


def existing_skill_names(repo_root: Path, index: dict | None = None) -> set[str]:
    """Every name already taken — both on disk and in the index."""
    repo_root = Path(repo_root)
    names = set()
    skills_dir = repo_root / "skills"
    if skills_dir.is_dir():
        names |= {p.name.lower() for p in skills_dir.iterdir() if p.is_dir()}
    if index is None:
        index = load_index(repo_root)
    names |= {str(s.get("name", "")).lower() for s in index.get("skills", []) if s.get("name")}
    return {n for n in names if n}


def check_duplicate(name: str, repo_root: Path, index: dict | None = None) -> list[str]:
    """Return a duplicate-name problem list (empty when the name is free)."""
    repo_root = Path(repo_root)
    if index is None:
        index = load_index(repo_root)
    taken = existing_skill_names(repo_root, index)
    if name.lower() not in taken:
        return []
    where = []
    if (repo_root / "skills" / name).exists():
        where.append(f"skills/{name}/ already exists")
    if any(str(s.get("name", "")).lower() == name.lower() for s in index.get("skills", [])):
        where.append("skills-index.json already has an entry for it")
    detail = " and ".join(where) if where else "it is already taken"
    return [
        f"duplicate skill name {name!r}: {detail}. "
        "Pick a different name, or improve the existing skill instead of adding a second one."
    ]


# --------------------------------------------------------------------------
# Similar-skill lookup (used by the decline path to stay specific)
# --------------------------------------------------------------------------


def _tokens(*texts: str) -> set[str]:
    words = set()
    for text in texts:
        for word in re.split(r"[^a-z0-9]+", (text or "").lower()):
            if len(word) > 2 and word not in TAG_STOPWORDS:
                words.add(word)
    return words


def find_similar_skills(sub: dict, index: dict, limit: int = RELATED_MAX) -> list[dict]:
    """Closest existing catalog skills, by token overlap. Real names only."""
    mine = _tokens(sub.get("name", "").replace("-", " "), sub.get("description", ""))
    if not mine:
        return []
    scored = []
    for skill in index.get("skills", []):
        name = skill.get("name")
        if not name:
            continue
        theirs = _tokens(name.replace("-", " "), skill.get("description", ""))
        if not theirs:
            continue
        overlap = mine & theirs
        if not overlap:
            continue
        score = len(overlap) / len(mine | theirs)
        if sub.get("category") and skill.get("category") == sub.get("category"):
            score += 0.05
        scored.append(
            {
                "name": name,
                "category": skill.get("category", ""),
                "description": skill.get("description", ""),
                "score": round(score, 4),
            }
        )
    scored.sort(key=lambda s: (-s["score"], s["name"]))
    return scored[:limit]


# --------------------------------------------------------------------------
# URL construction
# --------------------------------------------------------------------------


def raw_install_url(name: str, owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO,
                    ref: str = DEFAULT_REF) -> str:
    """The ONLY correct install target: raw.githubusercontent.com."""
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/skills/{name}/SKILL.md"


def blob_source_url(name: str, owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO,
                    ref: str = DEFAULT_REF) -> str:
    """The human-facing page. Never an install target."""
    return f"https://github.com/{owner}/{repo}/blob/{ref}/skills/{name}/SKILL.md"


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def derive_tags(sub: dict) -> list[str]:
    """Deterministic tag list from the name, category and description."""
    tags: list[str] = []

    def add(tag: str) -> None:
        tag = re.sub(r"[^a-z0-9-]+", "", tag.lower()).strip("-")
        if tag and len(tag) > 2 and tag not in tags and tag not in TAG_STOPWORDS:
            tags.append(tag)

    for part in sub.get("name", "").split("-"):
        add(part)
    add(sub.get("category", ""))
    for word in re.split(r"[^A-Za-z0-9]+", sub.get("description", "")):
        if len(tags) >= TAG_MAX:
            break
        add(word)
    return tags[:TAG_MAX] or [sub.get("category", "utility")]


def _lower_first(text: str) -> str:
    """Lowercase a trigger's first letter so it reads inside 'Use when …'.

    Left alone when the first word is an acronym (API, CI, HTTP) or the line
    starts with punctuation such as a quoted phrase.
    """
    if not text or not text[:1].isalpha():
        return text
    first_word = text.split(maxsplit=1)[0]
    if len(first_word) > 1 and first_word.isupper():
        return text
    return text[0].lower() + text[1:]


def frontmatter_description(sub: dict) -> str:
    """Build the 'Use when …' trigger description AGENTS.md requires."""
    triggers = [t.rstrip(" .") for t in as_bullets(sub.get("when_to_use", "")) if t.strip()]
    if not triggers:
        triggers = [sub.get("description", "").rstrip(" .")]

    if triggers[0].lower().startswith("use when"):
        desc = "; ".join(triggers)
    else:
        parts = [_lower_first(t) for t in triggers]
        if len(parts) == 1:
            desc = f"Use when {parts[0]}"
        elif len(parts) == 2:
            desc = f"Use when {parts[0]}, or when {parts[1]}"
        else:
            middle = ", ".join(f"when {p}" for p in parts[1:-1])
            desc = f"Use when {parts[0]}, {middle}, or when {parts[-1]}"
    desc = " ".join(desc.split())
    if len(desc) > FRONTMATTER_DESC_MAX:
        desc = desc[: FRONTMATTER_DESC_MAX - 1].rsplit(" ", 1)[0] + "…"
    if not desc.endswith((".", "…", "!", "?")):
        desc += "."
    return desc


def yaml_double_quoted(value: str) -> str:
    """Emit a YAML double-quoted scalar that always parses back to `value`."""
    escaped = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )
    escaped = re.sub(r"[\r\n\t]+", " ", escaped)
    escaped = "".join(ch for ch in escaped if ch >= " " or ch == " ")
    return '"' + escaped + '"'


def render_frontmatter(sub: dict, related: list[str], version: str = "1.0.0") -> str:
    author = f"@{sub['submitter']}" if sub.get("submitter") else "Hermes Skills Portfolio community"
    tags = ", ".join(derive_tags(sub))
    related_str = ", ".join(related)
    return (
        "---\n"
        f"name: {sub['name']}\n"
        f"description: {yaml_double_quoted(frontmatter_description(sub))}\n"
        f"version: {version}\n"
        f"author: {yaml_double_quoted(author)}\n"
        "license: MIT\n"
        "metadata:\n"
        "  hermes:\n"
        f"    tags: [{tags}]\n"
        f"    related_skills: [{related_str}]\n"
        "---\n"
    )


def _bullet_block(text: str, fallback: str) -> str:
    items = as_bullets(text)
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


def _paragraph_block(text: str, fallback: str) -> str:
    cleaned = "\n".join(
        line.rstrip() for line in (text or "").replace("\r\n", "\n").split("\n")
    ).strip()
    return cleaned or fallback


TODO = "TODO(maintainer)"


def render_skill_md(sub: dict, related: list[str]) -> str:
    """Render SKILL.md in the repo's locked body structure (see AGENTS.md).

    Sections the submitter supplied are real content. Sections only a
    maintainer can write honestly (the runnable workflow, this skill's specific
    pitfalls, its verification checks) are explicit TODO markers — inventing
    them here would ship fabricated instructions to the catalog.
    """
    name = sub["name"]
    parts = [render_frontmatter(sub, related), "\n", f"# {name}\n\n"]

    parts.append("## Overview\n\n")
    parts.append(_paragraph_block(sub.get("what_it_does", ""), sub.get("description", "")))
    parts.append("\n\n")

    parts.append("## When to Use\n\n")
    parts.append(_bullet_block(sub.get("when_to_use", ""), f"- {sub.get('description', '')}"))
    parts.append("\n\n")

    if sub.get("prerequisites"):
        parts.append("## Prerequisites\n\n")
        parts.append(_bullet_block(sub["prerequisites"], ""))
        parts.append("\n\n")

    parts.append("## Workflow\n\n")
    parts.append(
        f"1. {TODO}: replace this list with the real, runnable steps an agent follows.\n"
        f"2. {TODO}: include the exact commands or code, not a description of them.\n"
        f"3. {TODO}: end with how the agent reports the result back to the user.\n\n"
    )

    parts.append("## Common Pitfalls\n\n")
    parts.append(
        f"1. **{TODO}** — a real failure mode specific to this skill, and how to avoid it.\n"
        f"2. **{TODO}** — a second one. Generic advice does not belong here.\n\n"
    )

    parts.append("## Verification Checklist\n\n")
    parts.append(
        f"- [ ] {TODO}: a check that proves the skill's output actually works\n"
        f"- [ ] {TODO}: a check for the failure mode listed above\n"
    )
    return "".join(parts)


def render_readme(sub: dict, install_url: str, source_url: str) -> str:
    """Render README.md in the repo's human-facing format."""
    name = sub["name"]
    parts = [f"# {name}\n\n", f"{sub.get('description', '')}\n\n"]

    parts.append("## What it does\n\n")
    parts.append(_paragraph_block(sub.get("what_it_does", ""), sub.get("description", "")))
    parts.append("\n\n")

    parts.append("## Install\n\n")
    parts.append("```bash\n")
    parts.append(f"hermes skills install {install_url}\n")
    parts.append("```\n\n")

    if sub.get("prerequisites"):
        parts.append("## Prerequisites\n\n")
        parts.append(_bullet_block(sub["prerequisites"], ""))
        parts.append("\n\n")

    parts.append("## How to use\n\n")
    parts.append("```\n")
    parts.append(f'"{TODO}: the sentence a user actually types to trigger this skill"\n')
    parts.append("```\n\n")
    parts.append("The agent:\n\n")
    parts.append(
        f"1. {TODO}: first thing the agent does\n"
        f"2. {TODO}: second thing\n"
        f"3. {TODO}: what it reports back\n\n"
    )

    parts.append("## Example\n\n")
    parts.append("```\n")
    parts.append(f"{TODO}: a real transcript — input, and the output it produced.\n")
    parts.append("```\n\n")

    parts.append("## Source\n\n")
    origin = sub.get("origin", "original")
    submitter = f"@{sub['submitter']}" if sub.get("submitter") else "a community contributor"
    issue = sub.get("issue_number")
    issue_txt = f" (issue #{issue})" if issue else ""
    if origin == "adapted":
        parts.append(
            f"Adapted by {submitter}{issue_txt} from {sub.get('origin_url', '')} — "
            "see that source for the original author and license.\n"
        )
    else:
        parts.append(f"Originally authored by {submitter} and submitted{issue_txt}.\n")
    parts.append(f"\nView on GitHub: {source_url}\n")
    return "".join(parts)


# --------------------------------------------------------------------------
# Index entry
# --------------------------------------------------------------------------


def build_index_entry(sub: dict, owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO,
                      ref: str = DEFAULT_REF, today: str | None = None) -> dict:
    """Build the proposed skills-index.json entry. Never writes the index."""
    name = sub["name"]
    install_url = raw_install_url(name, owner, repo, ref)
    source_url = blob_source_url(name, owner, repo, ref)

    # Belt and braces: a blob URL here is the exact silent-install bug that
    # scripts/normalize_install_urls.py exists to prevent.
    if "/blob/" in install_url or not install_url.startswith("https://raw.githubusercontent.com/"):
        raise SubmissionError(f"refusing to emit a non-raw install_url: {install_url}")
    if not install_url.endswith("/SKILL.md"):
        raise SubmissionError(f"install_url must point at a SKILL.md: {install_url}")

    submitter = sub.get("submitter") or ""
    issue_number = sub.get("issue_number")
    issue_url = (
        f"https://github.com/{owner}/{repo}/issues/{issue_number}" if issue_number else ""
    )
    adapted = sub.get("origin") == "adapted"

    if adapted:
        attribution = {
            "author": f"@{submitter}" if submitter else "Community contributor",
            "origin_type": "external",
            "origin_repo": "",
            "origin_url": sub.get("origin_url", ""),
            "origin_note": (
                f"Adapted from {sub.get('origin_url', '')} and submitted through the "
                f"community skill-request process{f' (issue #{issue_number})' if issue_number else ''}."
            ),
            "license": "MIT",
            "derived": True,
        }
    else:
        attribution = {
            "author": f"@{submitter}" if submitter else "Community contributor",
            "origin_type": "community",
            "origin_repo": "",
            "origin_url": issue_url,
            "origin_note": (
                "Originally authored and submitted through the community skill-request "
                f"process{f' (issue #{issue_number})' if issue_number else ''}."
            ),
            "license": "MIT",
            "derived": False,
        }

    return {
        "name": name,
        "category": sub["category"],
        "tier": sub["tier"],
        "description": sub["description"],
        "install_url": install_url,
        "path": f"skills/{name}",
        "usage": {
            "hub_installs": 0,
            "github_clones": 0,
            "stars": 0,
            "self_reported_users": 0,
        },
        "recency": today or date.today().isoformat(),
        "source": "adapted" if adapted else "new",
        "source_attribution": attribution,
        "frontmatter": {
            "name": name,
            "description": frontmatter_description(sub),
            "version": "1.0.0",
        },
        "agent_use": _bullet_block(sub.get("when_to_use", ""), f"- {sub['description']}"),
        "user_use": _paragraph_block(sub.get("what_it_does", ""), sub["description"]),
        "source_url": source_url,
    }


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------


REQUIRED_BODY_HEADINGS = ("## Overview", "## When to Use", "## Common Pitfalls",
                          "## Verification Checklist")


def verify_generated(skill_md: str, readme: str, entry: dict) -> list[str]:
    """Re-read what we just generated. Returns problems; empty means good."""
    problems: list[str] = []

    if not skill_md.startswith("---\n"):
        problems.append("SKILL.md does not start with YAML frontmatter")
    else:
        _, _, rest = skill_md.partition("---\n")
        block, sep, _body = rest.partition("\n---\n")
        if not sep:
            problems.append("SKILL.md frontmatter block is not terminated")
        elif yaml is not None:
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError as exc:
                data = None
                problems.append(f"SKILL.md frontmatter is not valid YAML: {exc}")
            if isinstance(data, dict):
                for key in ("name", "description", "version", "author", "license"):
                    if not data.get(key):
                        problems.append(f"SKILL.md frontmatter is missing {key}")
                desc = str(data.get("description", ""))
                if not desc.lower().startswith("use when"):
                    problems.append("SKILL.md description must start with 'Use when'")
                if data.get("name") != entry["name"]:
                    problems.append("SKILL.md frontmatter name does not match the entry name")
            elif data is not None:
                problems.append("SKILL.md frontmatter did not parse to a mapping")

    for heading in REQUIRED_BODY_HEADINGS:
        if heading not in skill_md:
            problems.append(f"SKILL.md is missing the required section '{heading}'")

    # Same rule scripts/normalize_install_urls.py enforces: a bare blob link in
    # prose ("view the source") is fine, a blob URL used as an install command
    # is the silent-HTML-install bug.
    for text, label in ((skill_md, "SKILL.md"), (readme, "README.md")):
        for line in text.splitlines():
            if "hermes skills install" in line and "/blob/" in line:
                problems.append(
                    f"{label} documents a blob URL as the install command: {line.strip()}"
                )
    if entry["install_url"] not in readme:
        problems.append("README.md does not document the raw install URL")

    return problems


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def scaffold(raw_submission: dict, repo_root: Path = REPO_ROOT, *, dry_run: bool = False,
             owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO, ref: str = DEFAULT_REF,
             today: str | None = None) -> dict:
    """Validate a submission and write the skill directory.

    Returns ``{"name", "entry", "files", "similar_skills", "written"}``.
    Raises ``SubmissionError`` on any validation failure — the caller should
    surface the message and exit non-zero.
    """
    repo_root = Path(repo_root)
    sub = normalize_submission(raw_submission)

    index = load_index(repo_root)
    duplicate = check_duplicate(sub["name"], repo_root, index)
    if duplicate:
        raise SubmissionError(*duplicate)

    similar = find_similar_skills(sub, index)
    related = [s["name"] for s in similar]

    skill_md = render_skill_md(sub, related)
    readme = render_readme(
        sub, raw_install_url(sub["name"], owner, repo, ref),
        blob_source_url(sub["name"], owner, repo, ref),
    )
    entry = build_index_entry(sub, owner, repo, ref, today)

    problems = verify_generated(skill_md, readme, entry)
    if problems:
        raise SubmissionError(*problems)

    skill_dir = repo_root / "skills" / sub["name"]
    # POSIX-style keys on every platform — these are repo-relative paths that
    # end up in git, PR bodies and the index `path` field, never OS paths.
    files = {
        f"skills/{sub['name']}/SKILL.md": skill_md,
        f"skills/{sub['name']}/README.md": readme,
    }

    written: list[str] = []
    if not dry_run:
        if skill_dir.exists():
            raise SubmissionError(f"{skill_dir} already exists — refusing to overwrite")
        skill_dir.mkdir(parents=True)
        for rel, content in files.items():
            path = repo_root / rel
            # newline="\n": the catalog's markdown is LF on disk and
            # skills-index.json caches it byte-for-byte, so a CRLF write here
            # would show up as a permanent phantom diff in the cache check.
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            written.append(rel)

    return {
        "name": sub["name"],
        "submission": sub,
        "entry": entry,
        "files": files,
        "similar_skills": similar,
        "written": written,
        "dry_run": dry_run,
    }


def load_raw_submission(args: argparse.Namespace) -> dict:
    """Assemble the raw submission dict from whichever input mode was used."""
    raw: dict = {}

    def read(path: str) -> str:
        if path == "-":
            return sys.stdin.read()
        return Path(path).read_text(encoding="utf-8")

    if args.json:
        text = read(args.json)
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SubmissionError(f"--json input is not valid JSON: {exc}") from exc
        if not isinstance(loaded, dict):
            raise SubmissionError("--json input must be a JSON object")
        raw.update(loaded)
    elif args.issue_body:
        raw.update(parse_issue_body(read(args.issue_body)))

    for key in FIELD_IDS.values():
        value = getattr(args, key, None)
        if value:
            raw[key] = value
    if args.submitter:
        raw["submitter"] = args.submitter
    if args.issue_number:
        raw["issue_number"] = args.issue_number
    return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scaffold_skill.py",
        description="Scaffold skills/<name>/ from an approved skill-request submission.",
    )
    source = parser.add_argument_group("input (pick one; CLI flags override file values)")
    source.add_argument("--json", metavar="FILE", help="parsed submission JSON ('-' for stdin)")
    source.add_argument("--issue-body", metavar="FILE",
                        help="rendered GitHub issue-form body ('-' for stdin)")
    source.add_argument("--name")
    source.add_argument("--category", help=f"one of: {', '.join(CATEGORIES)}")
    source.add_argument("--tier", help=f"one of: {', '.join(TIERS)}")
    source.add_argument("--description", help="one-line description")
    source.add_argument("--when-to-use", dest="when_to_use", help="trigger conditions")
    source.add_argument("--what-it-does", dest="what_it_does", help="what the agent does")
    source.add_argument("--prerequisites", default=None)
    source.add_argument("--origin", help=f"one of: {', '.join(ORIGINS)}")
    source.add_argument("--origin-url", dest="origin_url", help="required when origin=adapted")
    source.add_argument("--submitter", help="GitHub handle of the submitter")
    source.add_argument("--issue-number", help="issue number this came from")

    out = parser.add_argument_group("output")
    out.add_argument("--repo-root", default=str(REPO_ROOT),
                     help="repo root to scaffold into (default: this repo)")
    out.add_argument("--out-entry", metavar="FILE",
                     help="write the skills-index.json entry here (default: stdout)")
    out.add_argument("--report", metavar="FILE",
                     help="write the full JSON report (validation, similar skills) here")
    out.add_argument("--dry-run", action="store_true",
                     help="print what would be created, write nothing")
    out.add_argument("--check-only", action="store_true",
                     help="validate only; render and write nothing")
    out.add_argument("--owner", default=DEFAULT_OWNER)
    out.add_argument("--repo", default=DEFAULT_REPO)
    out.add_argument("--ref", default=DEFAULT_REF)
    return parser


def _write_report(path: str | None, payload: dict) -> None:
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # Skill prose contains em dashes and curly quotes; a cp1252 Windows console
    # would raise UnicodeEncodeError mid-print without this.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - stream type dependent
            pass

    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root)

    try:
        raw = load_raw_submission(args)
    except (SubmissionError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INVALID if isinstance(exc, SubmissionError) else EXIT_RUNTIME

    if args.check_only:
        report: dict = {
            "ok": False,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "errors": [],
            "raw_fields": raw,
            "submission": None,
            "similar_skills": [],
        }
        try:
            index = load_index(repo_root)
            sub = normalize_submission(raw)
            errors = check_duplicate(sub["name"], repo_root, index)
            report["submission"] = sub
            report["similar_skills"] = find_similar_skills(sub, index)
            report["errors"] = errors
            report["ok"] = not errors
        except SubmissionError as exc:
            report["errors"] = exc.errors
            # Still surface neighbours when we at least know a name/description.
            partial = {
                "name": str(raw.get("name", "")).strip().lower(),
                "description": str(raw.get("description", "")),
                "category": str(raw.get("category", "")).lower(),
            }
            try:
                report["similar_skills"] = find_similar_skills(partial, load_index(repo_root))
            except SubmissionError:
                pass
        _write_report(args.report, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        for err in report["errors"]:
            print(f"ERROR: {err}", file=sys.stderr)
        return EXIT_OK if report["ok"] else EXIT_INVALID

    try:
        result = scaffold(
            raw, repo_root, dry_run=args.dry_run,
            owner=args.owner, repo=args.repo, ref=args.ref,
        )
    except SubmissionError as exc:
        for err in exc.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        _write_report(args.report, {"ok": False, "errors": exc.errors, "raw_fields": raw})
        return EXIT_INVALID
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_RUNTIME

    entry_json = json.dumps(result["entry"], indent=2, ensure_ascii=False)

    if args.dry_run:
        print(f"DRY RUN — nothing written. Would create for skill '{result['name']}':")
        for rel, content in result["files"].items():
            print(f"\n----- {rel} ({len(content.splitlines())} lines) -----")
            print(content.rstrip("\n"))
        print("\n----- proposed skills-index.json entry -----")
        print(entry_json)
        if result["similar_skills"]:
            print("\n----- closest existing skills (review for overlap) -----")
            for s in result["similar_skills"]:
                print(f"  {s['name']} ({s['category']}) score={s['score']}")
    else:
        for rel in result["written"]:
            print(f"wrote {rel}", file=sys.stderr)
        if args.out_entry:
            Path(args.out_entry).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out_entry).write_text(entry_json + "\n", encoding="utf-8")
            print(f"wrote {args.out_entry}", file=sys.stderr)
        else:
            print(entry_json)

    _write_report(args.report, {
        "ok": True,
        "name": result["name"],
        "written": result["written"],
        "dry_run": result["dry_run"],
        "entry": result["entry"],
        "similar_skills": result["similar_skills"],
    })
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
