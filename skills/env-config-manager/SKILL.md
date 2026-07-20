---
name: env-config-manager
description: "Manage environment variables across projects — agent + this skill = user gets organized, validated, documented env config."
version: 1.0.0
---

# env-config-manager

Manage environment variables across projects. The agent creates `.env.example` files, validates `.env` files against the example, detects missing or unused variables, and generates documentation.

## When to Use

- The user is setting up a new project and needs an `.env.example`.
- The user has a `.env` file and wants to validate it.
- The user is deploying and wants to check all required env vars are set.
- The user says "set up env vars", "create .env.example", or "check my environment".

## Create .env.example

```python
import os
import re

def create_env_example(env_path: str = ".env", output_path: str = ".env.example"):
    """Generate .env.example from .env with values stripped."""
    if not os.path.exists(env_path):
        # Try to find env vars referenced in code
        return create_env_example_from_code(".", output_path)

    with open(env_path, 'r') as f:
        lines = f.readlines()

    example_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            example_lines.append(line)
            continue
        if '=' in line:
            key = line.split('=')[0]
            example_lines.append(f"{key}=  # TODO: set value")
        else:
            example_lines.append(line)

    with open(output_path, 'w') as f:
        f.write('\n'.join(example_lines))
    return output_path
```

## Find env vars from code

```python
def create_env_example_from_code(src_dir: str, output_path: str = ".env.example"):
    """Scan source code for os.environ/os.getenv references and generate .env.example."""
    env_vars = set()
    patterns = [
        r"os\.environ\.get\(['\"](\w+)['\"]",
        r"os\.getenv\(['\"](\w+)['\"]",
        r"os\.environ\[['\"](\w+)['\"]\]",
    ]

    for root, dirs, files in os.walk(src_dir):
        # Skip common ignore dirs
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
        for filename in files:
            if filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    env_vars.update(matches)

    with open(output_path, 'w') as f:
        for var in sorted(env_vars):
            f.write(f"{var}=  # TODO: set value\n")
    return output_path
```

## Validate .env

```python
def validate_env(env_path: str = ".env", example_path: str = ".env.example") -> dict:
    """Check .env against .env.example for missing/unused variables."""
    def parse_env(path):
        if not os.path.exists(path):
            return {}
        env = {}
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=')[0].strip()
                    env[key] = True
        return env

    actual = parse_env(env_path)
    expected = parse_env(example_path)

    missing = set(expected.keys()) - set(actual.keys())
    unused = set(actual.keys()) - set(expected.keys())

    return {
        "missing": sorted(missing),
        "unused": sorted(unused),
        "valid": len(missing) == 0
    }
```

## Generate env documentation

```python
def generate_env_docs(example_path: str = ".env.example", output: str = "docs/env-vars.md"):
    """Generate markdown documentation from .env.example."""
    with open(example_path, 'r') as f:
        lines = f.readlines()

    doc = "# Environment Variables\n\n"
    doc += "| Variable | Description | Required |\n"
    doc += "|---|---|---|\n"

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, comment = line.partition('#')
            key = key.split('=')[0].strip()
            desc = comment.strip() or "—"
            doc += f"| `{key}` | {desc} | Yes |\n"

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        f.write(doc)
    return output
```

## Workflow

1. If `.env` exists, generate `.env.example` from it (strip values)
2. If no `.env`, scan source code for `os.getenv` / `os.environ` references
3. Validate the actual `.env` against `.env.example` — report missing and unused vars
4. Generate markdown documentation listing all env vars

## Pitfalls

- **Secrets in .env.example** — Never commit real values. The `create_env_example` function strips values, but double-check before committing.
- **Comment-based parsing** — Comments after values (`KEY=value  # description`) may be split incorrectly. The parser handles this by splitting on `=` first.
- **Multi-line values** — Values with `export KEY="multi\nline"` are not handled. Use single-line values or parse quoted strings.
- **Code scanning misses** — `create_env_example_from_code` only finds `os.getenv` and `os.environ` patterns. Values loaded from config files or env-loading libraries (python-dotenv) won't be detected.
- **Unused variables** — Variables in `.env` but not in `.env.example` might be intentionally unlisted. Review before removing.
- **Deployed environments** — On deploy, check with `validate_env()` before starting the app. Missing required vars cause confusing runtime errors.
