# color-palette-generator

Generate color palettes from images, base colors, or keywords — output as hex or CSS custom properties.

## What it does

The agent creates cohesive color palettes in three modes: extract dominant colors from an image, generate a scheme (analogous, complementary, triadic, monochrome) from a base color, or produce a palette from a mood keyword. Output as hex values or ready-to-use CSS custom properties.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/color-palette-generator/SKILL.md
```

## How to use

```
"Extract a color palette from this screenshot"
```

The agent extracts the 6 most dominant colors and returns them as hex values plus CSS custom properties.

## Palette types

| Type | How it works |
|---|---|
| Image extraction | Finds dominant colors in an image |
| Analogous | Colors adjacent on the color wheel |
| Complementary | Base color + its opposite |
| Triadic | Three evenly-spaced colors |
| Monochrome | Variations of a single hue |

## Example

```
User: "Generate a palette from #3b82f6"

Agent:
  1. Generates analogous palette:
     #1d4ed8, #2563eb, #3b82f6, #60a5fa, #93c5fd
  2. As CSS:
     :root {
       --color-palette-1: #1d4ed8;
       --color-palette-2: #2563eb;
       --color-palette-3: #3b82f6;
       --color-palette-4: #60a5fa;
       --color-palette-5: #93c5fd;
     }
```
