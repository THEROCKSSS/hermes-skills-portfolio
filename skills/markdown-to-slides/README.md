# markdown-to-slides

> Turn plain Markdown into polished presentation slides — then export to PDF or
> PowerPoint in one command.

Part of the [Hermes Skills Portfolio](https://github.com/MonicaAmano/hermes-skills-portfolio)
by **Monica Amano**.

## Why this skill exists

Most people write faster in Markdown than in Keynote or PowerPoint, but turning
notes into a real deck is usually a copy-paste chore. This skill lets an agent
(or a human) author talks, lectures, and investor updates as Markdown and render
them with the three best open-source slide engines:

| Engine | Best for | Export strength |
| --- | --- | --- |
| **reveal.js** | Rich, interactive, animated decks | PDF (HTML → PPTX via conversion) |
| **Marp** | Minimal Markdown, docs teams | PDF + PPTX + HTML (native) |
| **Slidev** | Developer talks, live code | PDF + PPTX (native) |

## Install

In Hermes, install the skill from the portfolio:

```
https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/markdown-to-slides/SKILL.md
```

Or copy `skills/markdown-to-slides/` into your Hermes skills directory.

## Quick start

Create `deck.md`:

```markdown
---
marp: true
theme: default
paginate: true
---

# Hello, slides
Authored in Markdown

---

## Slide two
- Write bullets
- Separate slides with `---`
- Export when ready
```

Render and export with Marp:

```bash
npm install -g @marp-team/marp-cli
marp deck.md -w            # live preview
marp deck.md --pdf deck.pdf
marp deck.md --pptx deck.pptx
```

Prefer reveal.js or Slidev? The SKILL.md covers their syntax, theming, and
exports in full.

## What you get

- **One source of truth** — your deck is a diffable text file, not a binary.
- **Themeable in minutes** — swap or brand a deck by overriding CSS variables.
- **Portable output** — hand out PDFs, hand decks to collaborators as PPTX.
- **Live preview** — watch mode hot-reloads as you write.

## Links

- Install URL: <https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/markdown-to-slides/SKILL.md>
- Full reference: see `SKILL.md` in this folder.

---

© Monica Amano — released for the Hermes community.
