# snippet-manager

Save, search, and retrieve reusable code snippets — a personal searchable snippet library.

## What it does

The agent stores code snippets as markdown files with metadata (language, tags, description) in a snippet directory. You can save snippets by giving the code + a name, search by keyword/tag/language, and retrieve snippets to insert into your code. Snippets persist across sessions.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/snippet-manager/SKILL.md
```

## How to use

**Save a snippet:**
```
"Save this Python HTTP client as 'http_get'"
```

**Find a snippet:**
```
"Find my snippet for debouncing"
```

The agent searches the library and returns the matching snippet.

## Example

```
User: "Save this as a snippet: const debounce = (fn, ms) => { ... }"

Agent:
  1. Saves to ~/.snippets/js_debounce.md
  2. Tags: [javascript, utility, performance]
  3. Returns: "Saved. Find it with: search 'debounce'"

Later:
User: "Find my debounce snippet"
Agent: Returns the snippet code from ~/.snippets/js_debounce.md
```
