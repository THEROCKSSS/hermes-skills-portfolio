# env-config-manager

Manage environment variables across projects — create .env.example, validate .env, generate docs.

## What it does

The agent scans your project for environment variable usage, creates a `.env.example` template with values stripped, validates your actual `.env` file against it (reports missing and unused vars), and generates markdown documentation listing all required env vars.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/env-config-manager/SKILL.md
```

## How to use

```
"Set up environment variables for my project"
```

The agent:
1. Scans source code for `os.getenv()` / `os.environ` references
2. Creates `.env.example` with all required vars (values stripped)
3. Checks your `.env` file for missing or unused variables
4. Generates `docs/env-vars.md` documenting each variable

## Example

```
User: "I'm deploying my app. Are all env vars set?"

Agent:
  1. Scans code: finds DATABASE_URL, SECRET_KEY, API_KEY, DEBUG
  2. Creates .env.example with those 4 vars
  3. Validates .env:
     - missing: ['API_KEY']
     - unused: ['OLD_TOKEN']
  4. Returns: "Missing API_KEY. OLD_TOKEN is set but not used in code."
```
