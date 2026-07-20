# regex-tester

Test, build, and debug regular expressions — with match highlighting and pattern explanations.

## What it does

The agent tests regex patterns against sample text and shows exactly what matches (with positions, groups, and highlighted output). Can also build patterns from natural language descriptions, explain what a pattern does component-by-component, and replace text using regex.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/regex-tester/SKILL.md
```

## How to use

```
"Test the regex \d{3}-\d{4} against this text: Call 555-1234 or 987-6543"
```

The agent:
1. Compiles the pattern
2. Finds all matches
3. Returns: "2 matches: [555-1234] at pos 5, [987-6543] at pos 18"

## Common patterns included

| Pattern | Matches |
|---|---|
| email | Email addresses |
| url | HTTP/HTTPS URLs |
| ipv4 | IPv4 addresses |
| date_iso | YYYY-MM-DD dates |
| phone_us | US phone numbers |
| uuid | UUIDs |
| hex_color | #RRGGBB colors |
| semver | Semantic versions |

## Example

```
User: "Extract all email addresses from this text"

Agent:
  1. Uses pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
  2. Tests against the text
  3. Returns: ["alice@example.com", "bob@work.org"]
```
