---
name: color-palette-generator
description: "Generate color palettes from images or keywords — agent + this skill = user gets a cohesive color scheme for any project."
version: 1.0.0
---

# color-palette-generator

Generate color palettes from images, keywords, or base colors. The agent extracts dominant colors from images, generates complementary palettes from a seed color, and produces CSS custom properties ready to use.

## When to Use

- The user wants a color palette for a web project.
- The user wants to extract colors from an image or screenshot.
- The user wants a palette based on a mood or keyword.
- The user says "generate a color palette", "extract colors from this image", or "give me a color scheme".

## Extract Colors from Image

```python
from PIL import Image
from collections import Counter

def extract_palette(image_path: str, num_colors: int = 6) -> list:
    """Extract dominant colors from an image."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    img = img.resize((150, 150))  # downsize for speed

    pixels = list(img.getdata())
    counter = Counter(pixels)

    palette = []
    for color, count in counter.most_common(num_colors * 3):
        # Skip colors too similar to already-selected ones
        too_close = False
        for existing in palette:
            if sum(abs(a - b) for a, b in zip(color, existing)) < 50:
                too_close = True
                break
        if not too_close:
            palette.append(color)
        if len(palette) >= num_colors:
            break

    return [{"hex": rgb_to_hex(c), "rgb": c} for c in palette]

def rgb_to_hex(rgb: tuple) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
```

## Generate from Base Color

```python
import colorsys

def generate_palette(base_hex: str, scheme: str = "analogous") -> list:
    """Generate a palette from a base color."""
    r, g, b = int(base_hex[1:3], 16), int(base_hex[3:5], 16), int(base_hex[5:7], 16)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

    colors = []
    if scheme == "analogous":
        offsets = [-30, -15, 0, 15, 30]
        for offset in offsets:
            new_h = (h + offset/360) % 1.0
            rgb = colorsys.hsv_to_rgb(new_h, s, v)
            colors.append(rgb_to_hex((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))))

    elif scheme == "complementary":
        new_h = (h + 0.5) % 1.0
        for sat in [s, s*0.7, s*0.5]:
            rgb = colorsys.hsv_to_rgb(h, sat, v)
            colors.append(rgb_to_hex((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))))
            rgb = colorsys.hsv_to_rgb(new_h, sat, v)
            colors.append(rgb_to_hex((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))))

    elif scheme == "triadic":
        for offset in [0, 120, 240]:
            new_h = (h + offset/360) % 1.0
            rgb = colorsys.hsv_to_rgb(new_h, s, v)
            colors.append(rgb_to_hex((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))))

    elif scheme == "monochrome":
        for val in [0.3, 0.5, 0.7, 0.85, 1.0]:
            rgb = colorsys.hsv_to_rgb(h, s, val)
            colors.append(rgb_to_hex((int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))))

    return colors
```

## CSS Custom Properties Output

```python
def palette_to_css(palette: list, name: str = "palette") -> str:
    """Generate CSS custom properties from a palette."""
    css = ":root {\n"
    for i, color in enumerate(palette, 1):
        hex_val = color["hex"] if isinstance(color, dict) else color
        css += f"  --color-{name}-{i}: {hex_val};\n"
    css += "}"
    return css
```

## Workflow

1. Determine the source: image, base color, or keyword
2. For images: extract dominant colors with deduplication
3. For base colors: generate analogous/complementary/triadic/monochrome scheme
4. Convert to hex
5. Optionally output as CSS custom properties
6. Return the palette

## Pitfalls

- **Similar colors** — Raw color extraction returns near-identical shades. The deduplication threshold (distance < 50) filters these, but may be too aggressive or too loose for some images.
- **Image too large** — Extracting from a 5000x5000 image is slow. Downsize first (the code resizes to 150x150).
- **Transparency** — RGBA images have an alpha channel. Convert to RGB first to avoid transparent pixels skewing the palette.
- **Scheme choice** — "Analogous" is safe for most projects. "Complementary" can be jarring. "Monochrome" is elegant but low contrast.
- **Hex vs OKLCH** — This skill generates hex colors. For perceptually uniform palettes, convert to OKLCH. The `hallmark-readme` and `frontend-design-toolkit` skills recommend OKLCH.
- **Dark mode** — The generated palette is for light mode. For dark mode, invert the lightness of each color while keeping the hue.
