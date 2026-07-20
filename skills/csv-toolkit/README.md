# csv-toolkit

Process CSV files — filter, transform, merge, and analyze without Excel.

## What it does

The agent reads CSV files and performs data operations: filtering rows, transforming columns, merging multiple files, computing group-by aggregates, sorting, and deduplicating. Uses pandas for heavy operations and the built-in csv module for simple ones. You get structured data processing without opening Excel.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/csv-toolkit/SKILL.md
```

## How to use

```
"Filter sales.csv to only show rows where revenue > 1000"
```

The agent:
1. Reads the CSV with pandas
2. Applies the filter: `df.query("revenue > 1000")`
3. Writes the result to a new CSV
4. Returns the row counts

## Example

```
User: "Merge customer.csv and orders.csv on customer_id"

Agent:
  1. Reads both CSVs
  2. Merges: pd.merge(customers, orders, on="customer_id")
  3. Writes merged.csv (2,500 rows, 12 columns)
  4. Returns: "Merged to merged.csv — 2,500 rows"
```
