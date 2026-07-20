---
name: log-analyzer
description: "Analyze log files for errors, patterns, and anomalies — agent + this skill = user gets insights from raw logs."
version: 1.0.0
---

# log-analyzer

Parse and analyze log files to find errors, warnings, patterns, and anomalies. The agent handles large log files, extracts structured data, counts error types, finds time-based patterns, and summarizes findings.

## When to Use

- The user wants to find errors in a log file.
- The user wants to understand what happened in a service from its logs.
- The user wants to count error types or find the most common issues.
- The user says "check the logs", "find errors in this log", or "what went wrong".

## Basic Error Extraction

```python
import re
from collections import Counter

def find_errors(log_path: str, patterns: list = None) -> dict:
    """Find error and warning lines in a log file."""
    if patterns is None:
        patterns = [
            r'\bERROR\b',
            r'\bFATAL\b',
            r'\bCRITICAL\b',
            r'\bException\b',
            r'\bTraceback\b',
            r'\bpanic\b',
        ]

    errors = []
    with open(log_path, 'r', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append({"line": line_num, "text": line.strip(), "pattern": pattern})
                    break

    return {
        "total_errors": len(errors),
        "first_10": errors[:10],
        "last_10": errors[-10:],
    }
```

## Error Type Counting

```python
def count_error_types(log_path: str) -> dict:
    """Categorize and count errors by type."""
    error_patterns = {
        "connection_refused": r"Connection.*refused|ECONNREFUSED",
        "timeout": r"timeout|timed out|ETIMEDOUT",
        "not_found": r"not found|404|ENOENT",
        "permission_denied": r"permission denied|EACCES|403",
        "out_of_memory": r"out of memory|ENOMEM|OOM",
        "auth_failure": r"auth.*fail|unauthorized|401",
        "rate_limit": r"rate limit|429|throttl",
        "ssl_error": r"SSL|certificate|TLS",
    }

    counts = Counter()
    with open(log_path, 'r', errors='ignore') as f:
        for line in f:
            for error_type, pattern in error_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    counts[error_type] += 1

    return dict(counts.most_common())
```

## Time-based Analysis

```python
from datetime import datetime
from collections import defaultdict

def errors_by_hour(log_path: str, timestamp_pattern: str = r'\[(\d{4}-\d{2}-\d{2}T\d{2}):\d{2}:\d{2}'):
    """Count errors per hour to find spikes."""
    hourly = defaultdict(int)
    with open(log_path, 'r', errors='ignore') as f:
        for line in f:
            if re.search(r'ERROR|FATAL|Exception', line, re.IGNORECASE):
                match = re.search(timestamp_pattern, line)
                if match:
                    hourly[match.group(1)] += 1

    return dict(sorted(hourly.items()))
```

## Extract Stack Traces

```python
def extract_tracebacks(log_path: str) -> list:
    """Extract full stack traces from a log file."""
    tracebacks = []
    current_trace = []
    in_trace = False

    with open(log_path, 'r', errors='ignore') as f:
        for line in f:
            if 'Traceback' in line or 'panic:' in line:
                if current_trace:
                    tracebacks.append('\n'.join(current_trace))
                current_trace = [line]
                in_trace = True
            elif in_trace:
                if line.strip() == '' or (not line.startswith(' ') and not line.startswith('\t') and not line.startswith('File') and not line.startswith('  ')):
                    tracebacks.append('\n'.join(current_trace))
                    current_trace = []
                    in_trace = False
                else:
                    current_trace.append(line)

    if current_trace:
        tracebacks.append('\n'.join(current_trace))

    return tracebacks
```

## Tail with Filtering

```python
def tail_filter(log_path: str, keyword: str, lines: int = 50):
    """Get the last N lines matching a keyword."""
    matching = []
    with open(log_path, 'r', errors='ignore') as f:
        for line in f:
            if keyword.lower() in line.lower():
                matching.append(line.strip())
                if len(matching) > lines:
                    matching.pop(0)
    return matching
```

## Summary Report

```python
def log_summary(log_path: str) -> dict:
    """Generate a comprehensive log summary."""
    total_lines = 0
    error_count = 0
    warn_count = 0
    info_count = 0

    with open(log_path, 'r', errors='ignore') as f:
        for line in f:
            total_lines += 1
            if re.search(r'\bERROR\b|\bFATAL\b', line, re.IGNORECASE):
                error_count += 1
            elif re.search(r'\bWARN', line, re.IGNORECASE):
                warn_count += 1
            elif re.search(r'\bINFO\b', line, re.IGNORECASE):
                info_count += 1

    return {
        "file": log_path,
        "total_lines": total_lines,
        "errors": error_count,
        "warnings": warn_count,
        "info": info_count,
        "error_rate": f"{error_count / total_lines * 100:.2f}%" if total_lines > 0 else "0%",
        "error_types": count_error_types(log_path),
    }
```

## Workflow

1. Identify the log file(s) to analyze
2. Run `log_summary` for a quick overview
3. Run `count_error_types` to categorize errors
4. Run `errors_by_hour` to find time-based spikes
5. Extract specific tracebacks or filtered lines for detail
6. Report findings: what errors, how many, when, and what types

## Pitfalls

- **Large log files** — Reading a 10GB log file line by line into memory will crash. Use the line-by-line iterators (as shown above) — they're memory-efficient. For extremely large files, use `grep` first to pre-filter.
- **Timestamp format varies** — The default regex assumes ISO 8601. Adjust the pattern for your log format (e.g., `r'(\d{2}:\d{2}):\d{2}'` for `HH:MM:SS`).
- **Multi-line stack traces** — Error lines span multiple lines. The traceback extractor handles this, but simple line-by-line error counting may miss context.
- **Rotated logs** — If logs rotate (`app.log.1`, `app.log.2`), analyze all of them. Use `glob.glob("app.log*")` to find all rotation files.
- **Encoding** — Some logs use non-UTF-8 encoding. Use `errors='ignore'` to skip bad bytes, or detect encoding with `chardet`.
- **False positives** — The word "error" can appear in non-error contexts (e.g., "error handling module"). Refine patterns to match your log format.
