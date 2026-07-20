# ascii-art

Generate ASCII art from text and images — banners, image conversions, and decorative text for terminals and docs.

## What it does

The agent creates ASCII art in three modes: text banners (pyfiglet, 500+ fonts), image-to-ASCII conversion (photo to text art), and decorative boxes/cowsay for terminal output. Useful for CLI tool headers, README decorations, and fun terminal output.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/ascii-art/SKILL.md
```

## How to use

**Text banner:**
```
"Make an ASCII banner that says MY TOOL"
```

**Image to ASCII:**
```
"Convert logo.png to ASCII art"
```

The agent generates the ASCII art and returns it as text.

## Example

```
User: "Make a banner for my CLI tool called DEPLOY"

Agent (using pyfiglet with 'slant' font):
    ___       __           ___     ___
   /   | ____/ /________  /   |   /   |
  / /| |/ __  / ___/ __ \/ /| |  / /| |
 / ___ / /_/ / /  / /_/ / ___ | / ___ |
/_/  |_\__,_/_/   \____/_/  |_|/_/  |_|

Returns the ASCII banner as text.
```
