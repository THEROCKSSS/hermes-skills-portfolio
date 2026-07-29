---
name: csv-toolkit
description: Use when the user wants to filter or transform a CSV file, merge multiple CSVs, compute summary statistics from CSV data, or says "process this CSV", "filter this data", or "merge these CSVs".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [csv, pandas, data-transformation, data-merge, aggregation]
    related_skills: [sqlite-dashboard, json-formatter]
---

# csv-toolkit

## Overview

Process CSV files with Python. Filter rows, transform columns, merge files, compute aggregates, and export results. The agent handles CSV reading, manipulation, and writing without needing Excel or a database.

## When to Use

- The user wants to filter or transform a CSV file.
- The user wants to merge multiple CSVs.
- The user wants to compute summary statistics from CSV data.
- The user says "process this CSV", "filter this data", or "merge these CSVs".

## Prerequisites

```bash
pip install pandas
# Or for simple operations, just use the csv module (built-in)
```

## Read and Inspect

```python
import pandas as pd

def inspect_csv(path: str) -> dict:
    """Quick overview of a CSV file."""
    df = pd.read_csv(path)
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "head": df.head(5).to_dict("records"),
        "null_counts": df.isnull().sum().to_dict(),
    }
```

## Filter Rows

```python
def filter_csv(path: str, output: str, condition: str):
    """Filter rows using a pandas query expression."""
    df = pd.read_csv(path)
    filtered = df.query(condition)
    filtered.to_csv(output, index=False)
    return {"input_rows": len(df), "output_rows": len(filtered), "output": output}

# Examples:
# filter_csv("data.csv", "filtered.csv", "age > 25")
# filter_csv("data.csv", "filtered.csv", "status == 'active' and revenue > 1000")
```

## Transform Columns

```python
def transform_csv(path: str, output: str, transforms: dict):
    """Apply transformations to columns.
    transforms = {"column_name": "new_value_expression"}
    """
    df = pd.read_csv(path)
    for col, expr in transforms.items():
        df[col] = df.eval(expr)
    df.to_csv(output, index=False)
    return output

# Example:
# transform_csv("data.csv", "out.csv", {
#     "price_usd": "price_eur * 1.08",
#     "name": "name.str.upper()"
# })
```

## Merge CSVs

```python
def merge_csvs(files: list, output: str, on: str = None, how: str = "outer"):
    """Merge multiple CSV files.
    If 'on' is None, concatenate vertically (stack rows).
    If 'on' is a column name, merge on that column (join).
    """
    if on is None:
        # Vertical concatenation
        dfs = [pd.read_csv(f) for f in files]
        combined = pd.concat(dfs, ignore_index=True)
    else:
        # Horizontal join
        dfs = [pd.read_csv(f) for f in files]
        combined = dfs[0]
        for df in dfs[1:]:
            combined = combined.merge(df, on=on, how=how)
    combined.to_csv(output, index=False)
    return {"output": output, "rows": len(combined), "columns": len(combined.columns)}
```

## Aggregate / Group By

```python
def aggregate_csv(path: str, output: str, group_by: str, agg: dict):
    """Group by a column and compute aggregates.
    agg = {"column": "function", ...}
    """
    df = pd.read_csv(path)
    grouped = df.groupby(group_by).agg(agg).reset_index()
    grouped.to_csv(output, index=False)
    return grouped.to_dict("records")

# Example:
# aggregate_csv("sales.csv", "summary.csv", "region", {"revenue": "sum", "orders": "count"})
```

## Sort and Deduplicate

```python
def sort_csv(path: str, output: str, by: list, ascending: bool = True):
    df = pd.read_csv(path)
    df = df.sort_values(by=by, ascending=ascending)
    df.to_csv(output, index=False)
    return output

def deduplicate_csv(path: str, output: str, subset: list = None):
    df = pd.read_csv(path)
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    df.to_csv(output, index=False)
    return {"before": before, "after": len(df), "removed": before - len(df)}
```

## Using the csv module (no pandas)

For simple operations without pandas:

```python
import csv

def simple_filter(path: str, output: str, column: str, value: str):
    """Filter rows where a column equals a value. No pandas needed."""
    with open(path, 'r') as infile, open(output, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row[column] == value:
                writer.writerow(row)
```

## Common Pitfalls

1. **UTF-8 read fails on Excel-exported CSVs.** Files saved from Excel are often Windows-1252, not UTF-8. Use `pd.read_csv(path, encoding='latin1')` if the default UTF-8 read raises a `UnicodeDecodeError`.
2. **Loading a huge file blows up memory.** pandas reads the entire file into memory. For files over ~1GB, use the `chunksize` parameter to stream, or switch to `polars`.
3. **Wrong delimiter assumed.** Some CSVs use semicolons or tabs instead of commas. Pass `sep=';'` explicitly, or `engine='python'` with `sep=None` for auto-detection — don't assume comma.
4. **Unquoted commas inside fields break parsing.** pandas handles RFC-4180 quoting automatically, but the plain `csv` module needs `quoting=csv.QUOTE_MINIMAL` (or matching the source file's quoting) or embedded commas will split a field in two.
5. **Date columns silently stay strings.** `pd.read_csv` does not parse dates by default — a "date" column read without `parse_dates=['date_column']` stays a string, and sort/filter operations on it behave lexicographically instead of chronologically.
6. **NaN and empty string are not the same.** Empty cells become `NaN` in pandas, not `''`. Downstream string operations or JSON export may need `df.fillna('')` first, or `NaN` will show up as `null`/`nan` unexpectedly.
7. **`df.eval()` transforms silently produce NaN on a typo.** A misspelled column name in a `transforms` expression doesn't always raise — check the output column for unexpected `NaN` after `transform_csv`.

## Verification Checklist

- [ ] `inspect_csv()` (or equivalent) was run on the output file to confirm expected row/column counts
- [ ] Row counts before/after filtering or deduplication were compared and match expectations (no silent full-table drop)
- [ ] Encoding was confirmed (UTF-8 succeeded, or `latin1`/other encoding was explicitly used after a decode failure)
- [ ] Delimiter was verified against the actual file (opened a few raw lines) rather than assumed to be a comma
- [ ] Date columns intended for sorting/filtering were parsed with `parse_dates`, not left as strings
- [ ] Output CSV was opened/read back to confirm it's valid and matches the expected schema
