---
name: ascii-art
description: Use when the user wants a text banner or logo for a CLI tool/README, wants an image converted to ASCII art, wants decorative ASCII for a terminal output or code comment, or explicitly says "make ASCII art", "generate a banner", or "convert this image to ASCII".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ascii-art, text-banner, image-to-ascii, pyfiglet, terminal-art]
    related_skills: [color-palette-generator, qr-code-generator]
---

# ascii-art

## Overview

Generate ASCII art from text (banners, logos) and images (photo-to-ASCII conversion). The agent creates text banners, converts images to ASCII, and produces decorative art for terminals, documentation, and code comments.

## When to Use

- The user wants a text banner or logo for a CLI tool or README.
- The user wants to convert an image to ASCII art.
- The user wants decorative ASCII for a terminal output or code comment.
- The user says "make ASCII art", "generate a banner", or "convert this image to ASCII".

## Prerequisites

```bash
pip install pyfiglet cowsay pillow
```

## Text Banners (pyfiglet)

```python
import pyfiglet

def banner(text: str, font: str = "standard") -> str:
    """Generate an ASCII art banner from text."""
    return pyfiglet.figlet_format(text, font=font)
```

### Popular fonts

```python
fonts = ["standard", "big", "slant", "shadow", "doom", "small", "banner3", "colossal"]

for font in fonts:
    print(f"\n=== {font} ===")
    print(pyfiglet.figlet_format("Hello", font=font))
```

### List all available fonts

```python
import pyfiglet
print(len(pyfiglet.FigletFont.getFonts()))  # 500+ fonts
```

## Image to ASCII

```python
from PIL import Image

def image_to_ascii(image_path: str, width: int = 80, ramp: str = " .:-=+*#%@") -> str:
    """Convert an image to ASCII art."""
    img = Image.open(image_path)
    img = img.convert('L')  # grayscale

    # Calculate height maintaining aspect ratio
    aspect = img.height / img.width
    # Terminal characters are taller than wide, so adjust
    height = int(aspect * width * 0.5)
    img = img.resize((width, height))

    pixels = img.getdata()
    ascii_str = ""
    for i, pixel in enumerate(pixels):
        idx = int(pixel / 255 * (len(ramp) - 1))
        ascii_str += ramp[idx]
        if (i + 1) % width == 0:
            ascii_str += "\n"

    return ascii_str
```

## Cowsay

```python
import cowsay

def say(text: str, character: str = "cow") -> str:
    """Generate a cowsay message."""
    import io, sys
    old = sys.stdout
    sys.stdout = buffer = io.StringIO()
    getattr(cowsay, character)(text)
    sys.stdout = old
    return buffer.getvalue()
```

## Boxed Text

```python
def box_text(text: str, style: str = "single") -> str:
    """Draw a box around text using Unicode box-drawing characters."""
    lines = text.split("\n")
    max_len = max(len(line) for line in lines)

    styles = {
        "single": ("│", "─", "┌", "┐", "└", "┘"),
        "double": ("║", "═", "╔", "╗", "╚", "╝"),
        "round":  ("│", "─", "╭", "╮", "╰", "╯"),
        "ascii":  ("|", "-", "+", "+", "+", "+"),
    }

    v, h, tl, tr, bl, br = styles.get(style, styles["single"])

    result = f"{tl}{h * (max_len + 2)}{tr}\n"
    for line in lines:
        result += f"{v} {line.ljust(max_len)} {v}\n"
    result += f"{bl}{h * (max_len + 2)}{br}"
    return result
```

## Workflow

1. Determine what the user wants: a text banner, image-to-ASCII, or decorative art
2. For banners: pick a font that matches the mood (big for impact, small for compact)
3. For images: resize to terminal width, convert to grayscale, map to ASCII ramp
4. Return the ASCII art as a string

## Common Pitfalls

1. **Banners too wide.** pyfiglet banners can be 100+ chars wide. Check the terminal width and pick a narrower font (small, mini, thin) for narrow terminals.
2. **Image ASCII looks squashed or stretched.** Terminal characters are ~2x taller than wide. Adjust the aspect ratio with `height = int(aspect * width * 0.5)` — skipping this factor distorts the output.
3. **Requested font not installed.** Not all pyfiglet fonts ship by default. Check `pyfiglet.FigletFont.getFonts()` for what's actually available before promising a specific font.
4. **Color codes leaking into plain-text output.** ANSI color codes (`\033[91m`) render correctly in a terminal but show as garbage escape sequences in a README or plain text file — only add color when the target is a live terminal.
5. **Converting an oversized image directly.** A 4000px image produces an unreadable wall of characters. Resize to 80-120 chars wide before mapping to the ASCII ramp, not after.

## Verification Checklist

- [ ] Text banner output was actually printed/reviewed at the target line width (not assumed to fit)
- [ ] Chosen pyfiglet font was confirmed present via `pyfiglet.FigletFont.getFonts()` before use
- [ ] Image-to-ASCII output used the aspect-ratio correction (`* 0.5`) so the result isn't vertically stretched
- [ ] Source image was resized to ≤120 chars wide before conversion
- [ ] If ANSI color was added, confirmed the output target is a terminal, not a file meant to stay plain text
