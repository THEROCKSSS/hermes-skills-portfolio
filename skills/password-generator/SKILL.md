---
name: password-generator
description: "Generate secure passwords and passphrases — agent + this skill = user gets cryptographically strong credentials."
version: 1.0.0
---

# password-generator

Generate secure passwords, passphrases, and API keys. The agent creates random passwords with configurable complexity, memorable passphrases from word lists, and API tokens with specific character sets.

## When to Use

- The user needs a strong password.
- The user wants a memorable passphrase.
- The user needs an API key or token.
- The user says "generate a password", "make me a secure password", or "create an API key".

## Secure Password

```python
import secrets
import string

def generate_password(length: int = 16, uppercase: bool = True, lowercase: bool = True, digits: bool = True, symbols: bool = True, exclude_similar: bool = False) -> str:
    """Generate a cryptographically secure random password."""
    chars = ""
    if lowercase:
        chars += string.ascii_lowercase
    if uppercase:
        chars += string.ascii_uppercase
    if digits:
        chars += string.digits
    if symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if exclude_similar:
        chars = chars.replace("0", "").replace("O", "").replace("l", "").replace("1", "").replace("I", "")

    # Ensure at least one of each requested type
    password = []
    required = []
    if lowercase:
        required.append(secrets.choice(string.ascii_lowercase))
    if uppercase:
        required.append(secrets.choice(string.ascii_uppercase))
    if digits:
        required.append(secrets.choice(string.digits))
    if symbols:
        required.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

    remaining = length - len(required)
    password = required + [secrets.choice(chars) for _ in range(remaining)]

    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)
```

## Passphrase (memorable)

```python
import secrets

WORD_LIST = [
    "apple", "brave", "cloud", "dance", "eagle", "flame", "grace", "heart",
    "ivory", "jungle", "kneel", "lemon", "maple", "noble", "ocean", "pearl",
    "quest", "river", "storm", "trust", "unity", "vivid", "whisper", "xenon",
    "yacht", "zebra", "anchor", "bloom", "creek", "dawn", "ember", "frost",
    "globe", "haven", "ideal", "jewel", "karma", "lotus", "mint", "north",
]

def generate_passphrase(words: int = 4, separator: str = "-", capitalize: bool = True, add_number: bool = True) -> str:
    """Generate a memorable passphrase from random words."""
    selected = [secrets.choice(WORD_LIST) for _ in range(words)]
    if capitalize:
        selected = [w.capitalize() for w in selected]
    if add_number:
        selected.append(str(secrets.randbelow(100)))
    return separator.join(selected)
```

## API Key / Token

```python
def generate_api_key(length: int = 32, prefix: str = "") -> str:
    """Generate a random API key."""
    chars = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(chars) for _ in range(length))
    if prefix:
        return f"{prefix}_{key}"
    return key
```

## Hex Token

```python
def generate_hex_token(bytes_len: int = 32) -> str:
    """Generate a hex token (e.g., for OAuth)."""
    return secrets.token_hex(bytes_len)
```

## URL-safe Token

```python
def generate_urlsafe_token(bytes_len: int = 32) -> str:
    """Generate a URL-safe token."""
    return secrets.token_urlsafe(bytes_len)
```

## Password Strength Check

```python
import re

def check_strength(password: str) -> dict:
    """Evaluate password strength."""
    score = 0
    checks = {
        "length_12+": len(password) >= 12,
        "length_16+": len(password) >= 16,
        "has_lowercase": bool(re.search(r'[a-z]', password)),
        "has_uppercase": bool(re.search(r'[A-Z]', password)),
        "has_digit": bool(re.search(r'\d', password)),
        "has_symbol": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)),
        "no_common_patterns": not re.search(r'(123|abc|qwe|password|admin)', password, re.IGNORECASE),
    }

    for check in checks.values():
        if check:
            score += 1

    if score >= 7:
        rating = "strong"
    elif score >= 5:
        rating = "moderate"
    else:
        rating = "weak"

    return {"score": score, "rating": rating, "checks": checks}
```

## Batch Generation

```python
def generate_batch(count: int = 10, length: int = 16) -> list:
    """Generate multiple passwords at once."""
    return [generate_password(length) for _ in range(count)]
```

## Workflow

1. Determine what the user needs: password, passphrase, or API key
2. For passwords: confirm length and character requirements
3. For passphrases: confirm word count and separator
4. For API keys: confirm length and prefix
5. Generate using `secrets` module (cryptographically secure)
6. Optionally check strength
7. Return the credential(s)

## Pitfalls

- **Never use `random` for passwords** — The `random` module is not cryptographically secure. Always use `secrets` (Python 3.6+).
- **Similar characters** — Characters like `0/O`, `l/1/I` cause confusion. Use `exclude_similar=True` for passwords that will be typed manually.
- **Short passphrases** — A 2-word passphrase is weaker than a 12-char random password. Use at least 4 words for adequate entropy.
- **Word list size** — A small word list reduces passphrase entropy. The built-in list has 40 words; for higher security, use a larger list (e.g., EFF's 7776-word list).
- **Password in process args** — Don't pass generated passwords as command-line arguments (visible in `ps`). Write to a file or stdout instead.
- **Logging** — Never log generated passwords. Print them once and let the user copy them.
