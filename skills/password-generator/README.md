# password-generator

Generate secure passwords, memorable passphrases, and API keys.

## What it does

The agent generates cryptographically secure credentials using Python's `secrets` module. Three modes: random passwords (configurable length and character set), memorable passphrases (random words joined by dashes), and API keys (alphanumeric tokens with optional prefix). Includes a strength checker.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/password-generator/SKILL.md
```

## How to use

```
"Generate a strong 20-character password"
```

The agent generates a password with mixed case, digits, and symbols, then checks its strength.

## Types

| Type | Example | Best for |
|---|---|---|
| Password | `K7#m@xL9!pQ4$vB2` | Accounts, databases |
| Passphrase | `Ocean-Storm-Vivid-Maple-42` | Master passwords |
| API key | `sk_aB3dE9fG2hI5jK8` | Service tokens |
| Hex token | `a3f5b8c1d2e4...` | OAuth, sessions |

## Example

```
User: "I need a memorable master password"

Agent:
  1. Generates: generate_passphrase(words=5, separator="-", add_number=True)
  2. Returns: "Haven-Globe-Ember-Noble-Creek-73"
  3. Strength: strong (7/7 checks passed)
```
