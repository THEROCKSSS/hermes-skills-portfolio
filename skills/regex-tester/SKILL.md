---
name: regex-tester
description: "Test and debug regular expressions — agent + this skill = user gets a working regex with match results."
version: 1.0.0
---

# regex-tester

Test, debug, and build regular expressions. The agent creates regex patterns from descriptions, tests them against sample text, explains what they match, and helps fix patterns that don't work as expected.

## When to Use

- The user wants to test a regex pattern against text.
- The user needs help writing a regex for a specific pattern.
- The user has a regex that isn't matching correctly.
- The user says "test this regex", "write a regex for", or "why isn't my regex working".

## Test a Regex

```python
import re

def test_regex(pattern: str, text: str, flags: list = None) -> dict:
    """Test a regex pattern against text and return detailed results."""
    flag = 0
    if flags:
        if 'i' in flags: flag |= re.IGNORECASE
        if 'm' in flags: flag |= re.MULTILINE
        if 's' in flags: flag |= re.DOTALL
        if 'x' in flags: flag |= re.VERBOSE

    try:
        compiled = re.compile(pattern, flag)
    except re.error as e:
        return {"valid": False, "error": str(e), "pattern": pattern}

    matches = list(compiled.finditer(text))

    return {
        "valid": True,
        "pattern": pattern,
        "match_count": len(matches),
        "matches": [
            {
                "match": m.group(0),
                "start": m.start(),
                "end": m.end(),
                "groups": m.groups(),
                "named_groups": m.groupdict(),
            }
            for m in matches
        ],
        "highlighted": highlight_matches(text, matches),
    }

def highlight_matches(text: str, matches) -> str:
    """Return text with matches wrapped in markers."""
    result = []
    last_end = 0
    for m in matches:
        result.append(text[last_end:m.start()])
        result.append(f"[{m.group(0)}]")
        last_end = m.end()
    result.append(text[last_end:])
    return ''.join(result)
```

## Common Patterns

```python
PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "url": r"https?://[^\s<>"']+[^\s<>"'.]",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "ipv6": r"(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}",
    "phone_us": r"\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})",
    "date_iso": r"\d{4}-\d{2}-\d{2}",
    "date_us": r"\d{1,2}/\d{1,2}/\d{2,4}",
    "time": r"\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?",
    "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "hex_color": r"#[0-9a-fA-F]{6}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "zipcode_us": r"\b\d{5}(?:-\d{4})?\b",
    "semver": r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?(?:\+[a-zA-Z0-9.]+)?",
    "mac_address": r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})",
}
```

## Build Regex from Description

The agent can construct patterns from natural language descriptions:

```python
def build_regex(description: str) -> str:
    """Build a regex from a natural language description.
    This is a guide — the agent constructs the pattern based on understanding."""
    # The agent interprets the description and constructs the pattern
    # Examples of what the agent can build:
    examples = {
        "match email addresses": PATTERNS["email"],
        "find all urls": PATTERNS["url"],
        "extract dates in YYYY-MM-DD format": PATTERNS["date_iso"],
        "match a phone number": PATTERNS["phone_us"],
        "find hex color codes": PATTERNS["hex_color"],
        "match semver versions": PATTERNS["semver"],
    }
    return examples  # The agent selects or constructs the appropriate pattern
```

## Explain a Regex

```python
def explain_regex(pattern: str) -> str:
    """Break down a regex pattern into human-readable components."""
    explanations = {
        r'\d': "any digit (0-9)",
        r'\w': "any word character (a-z, A-Z, 0-9, _)",
        r'\s': "any whitespace",
        r'.': "any character",
        r'*': "zero or more of the preceding",
        r'+': "one or more of the preceding",
        r'?': "zero or one of the preceding",
        r'{n}': "exactly n of the preceding",
        r'{n,m}': "between n and m of the preceding",
        r'^': "start of string/line",
        r'$': "end of string/line",
        r'[]': "character class",
        r'()': "capture group",
        r'(?:)': "non-capturing group",
        r'(?=)': "lookahead",
        r'(?!)': "negative lookahead",
        r'|': "alternation (OR)",
        r'\\': "literal backslash",
    }
    # The agent walks through the pattern and explains each component
    return "See pattern breakdown in the response"
```

## Replace with Regex

```python
def regex_replace(pattern: str, text: str, replacement: str, count: int = 0) -> str:
    """Replace matches with a replacement string."""
    return re.sub(pattern, replacement, text, count=count or 0)
```

## Workflow

1. Understand what the user wants to match
2. Either the user provides a pattern to test, or the agent builds one
3. Test the pattern against sample text
4. Show matches with positions and groups
5. If no matches, debug: explain the pattern and suggest fixes
6. Return the working pattern and match results

## Pitfalls

- **Greedy vs lazy** — `.*` is greedy (matches as much as possible). `.*?` is lazy (matches as little as possible). This is the most common regex bug.
- **Anchoring** — Without `^` and `$`, the pattern matches anywhere in the string. Use anchors to match the full string.
- **Escape special characters** — `.` in a pattern matches any character. To match a literal dot, use `\.`.
- **Catastrophic backtracking** — Nested quantifiers like `(a+)+` can cause exponential matching time on certain inputs. Avoid nested quantifiers.
- **Character class ranges** — `[a-z]` is lowercase only. `[A-Za-z]` includes both. `[\w]` includes digits and underscore.
- **Unicode** — `\w` in Python 3 matches Unicode word characters by default. Use `[a-zA-Z0-9_]` for ASCII-only.
