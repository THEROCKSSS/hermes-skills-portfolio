# json-formatter

Format, validate, minify, and transform JSON — pretty-print, fix errors, extract fields, convert to CSV.

## What it does

The agent takes messy or minified JSON and makes it clean: pretty-prints with indentation, validates and reports errors with line/column numbers, fixes common issues (trailing commas, single quotes, comments), extracts specific fields using dot notation, and converts JSON arrays to CSV.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/json-formatter/SKILL.md
```

## How to use

```
"Format this JSON file"
```

The agent:
1. Reads the JSON
2. Validates it — reports any errors with position
3. Pretty-prints with 2-space indentation
4. Writes the formatted output

## Example

```
User: "This API response is minified. Make it readable."

Agent:
  1. Reads the minified JSON
  2. Pretty-prints: json.dumps(data, indent=2)
  3. Returns formatted JSON with proper indentation and line breaks
```
