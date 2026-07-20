---
name: csv-toolkit
description: "Process CSV files — filter, transform, merge, and analyze — agent + this skill = user gets structured data operations without Excel."
version: 1.0.0
---

# csv-toolkit

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

## Pitfalls

- **Encoding issues** — CSVs from Excel may use Windows-1252 encoding. Use `pd.read_csv(path, encoding='latin1')` if UTF-8 fails.
- **Large CSVs** — pandas loads the entire file into memory. For files over 1GB, use `chunksize` parameter or `polars` instead.
- **Delimiter detection** — Some CSVs use semicolons or tabs. Use `pd.read_csv(path, sep=';')` or `engine='python'` for auto-detection.
- **Quoting** — Fields with commas should be quoted. pandas handles this, but the `csv` module needs `quoting=csv.QUOTE_MINIMAL`.
- **Date parsing** — Date columns are read as strings by default. Use `pd.read_csv(path, parse_dates=['date_column'])`.
- **NaN vs empty** — Empty cells become NaN in pandas, not empty strings. Use `df.fillna('')` to convert back.
