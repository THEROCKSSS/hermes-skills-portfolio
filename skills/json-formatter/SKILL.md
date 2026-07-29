---
name: json-formatter
description: Use when a user has messy or minified JSON that needs formatting, wants to validate a JSON file, extract specific fields from nested JSON, or convert a JSON array of objects to CSV.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [json, validation, jsonpath, csv-conversion]
    related_skills: [csv-toolkit, regex-tester]
---

# json-formatter

## Overview

Format, validate, minify, and transform JSON. The agent handles malformed JSON, pretty-prints messy output, extracts specific fields with dot-notation paths, and converts between JSON and other formats.

## When to Use

- The user has messy or minified JSON that needs formatting.
- The user wants to validate a JSON file.
- The user wants to extract specific fields from a large JSON.
- The user says "format this JSON", "pretty print this", or "validate my JSON".

## Pretty Print

```python
import json

def pretty_print(json_str: str, indent: int = 2) -> str:
    """Format JSON with indentation."""
    data = json.loads(json_str)
    return json.dumps(data, indent=indent, ensure_ascii=False)

def pretty_print_file(input_path: str, output_path: str = None, indent: int = 2):
    """Format a JSON file in place or to a new file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    out = output_path or input_path
    with open(out, 'w') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return out
```

## Minify

```python
def minify_json(json_str: str) -> str:
    """Remove all whitespace from JSON."""
    data = json.loads(json_str)
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
```

## Validate

```python
def validate_json(json_str: str) -> dict:
    """Validate JSON and return error details if invalid."""
    try:
        json.loads(json_str)
        return {"valid": True}
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "column": e.colno,
            "position": e.pos,
            "context": json_str[max(0, e.pos-20):e.pos+20] if e.pos else ""
        }
```

## Extract Fields

```python
def extract_fields(data, paths: list):
    """Extract specific fields from nested JSON using dot notation.
    paths = ["user.name", "user.email", "items.0.title"]
    """
    def get_nested(obj, path):
        keys = path.split('.')
        current = obj
        for key in keys:
            if isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return None
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if current is None:
                return None
        return current

    if isinstance(data, str):
        data = json.loads(data)

    return {path: get_nested(data, path) for path in paths}
```

## JSON to CSV

```python
import csv

def json_to_csv(json_path: str, csv_path: str, record_path: str = None):
    """Convert a JSON array of objects to CSV."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    if record_path:
        # Navigate to the array
        for key in record_path.split('.'):
            data = data[key]

    if not isinstance(data, list):
        raise ValueError("JSON must be an array of objects")

    # Collect all field names
    fieldnames = set()
    for record in data:
        fieldnames.update(record.keys())
    fieldnames = sorted(fieldnames)

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow({k: record.get(k, '') for k in fieldnames})
    return csv_path
```

## Fix Common JSON Errors

```python
def fix_json(json_str: str) -> str:
    """Attempt to fix common JSON formatting errors."""
    # Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    # Replace single quotes with double quotes
    json_str = json_str.replace("'", '"')
    # Remove comments (// and /* */)
    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    return json_str

import re
```

## Workflow

1. Read the JSON (string or file)
2. If validation fails, try `fix_json` to fix common errors
3. Pretty-print with 2-space indent
4. If extracting fields, use dot-notation paths
5. If converting to CSV, flatten the array
6. Return the formatted/validated/extracted result

## Common Pitfalls

1. **Trailing commas.** Standard JSON doesn't allow trailing commas. `fix_json` removes them, but validate first to know if there's an issue.
2. **Single quotes.** JSON requires double quotes. JSON5 allows single quotes, but standard parsers reject them.
3. **Comments in JSON.** Standard JSON doesn't allow comments. JSONC and JSON5 do. `fix_json` strips comments for standard compatibility.
4. **Large JSON files.** `json.load()` loads the entire file into memory. For files over 100MB, use `ijson` for streaming parsing.
5. **Unicode.** Use `ensure_ascii=False` to keep Unicode characters readable. With `ensure_ascii=True` (default), they become `\uXXXX` escapes.
6. **Nested arrays.** `json_to_csv` only flattens one level. Deeply nested objects need manual flattening before CSV conversion.

## Verification Checklist

- [ ] `validate_json` reports valid before any downstream transform (extract/CSV/minify) is trusted
- [ ] Output uses `ensure_ascii=False` when Unicode readability matters
- [ ] `fix_json` output is re-validated with `json.loads` before being treated as fixed
- [ ] CSV conversion confirms the source resolves to a flat array of objects (not nested) before running
- [ ] Files over 100MB use a streaming parser (`ijson`), not `json.load`
