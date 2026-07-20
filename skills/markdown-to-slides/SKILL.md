---
name: markdown-to-slides
description: Turn Markdown into polished presentation slides using reveal.js, Marp, or Slidev. Use when a user wants to author talks, decks, or lectures from plain text and export them to PDF/PPTX.
version: 1.0.0
---

# markdown-to-slides

Author beautiful presentations from plain Markdown — no drag-and-drop editors, no
locked-in proprietary formats. This skill covers three best-in-class engines
(reveal.js, Marp, Slidev), their slide-delimiter syntax, theming, live preview,
and one-command export to PDF or PowerPoint.

## When to Use

Reach for this skill whenever the user asks to:

- Build a slide deck, talk, keynote, or lecture from Markdown or notes.
- Convert an existing Markdown document into slides.
- Theme, brand, or restyle a presentation quickly.
- Export slides to PDF (for sharing/handouts) or PPTX (for collaborators).
- Set up a live-reloading preview while writing a talk.

Do **not** use it for static documents (use a doc/reports skill), posters, or
infographics where a single fixed canvas is the deliverable.

## Tools

Pick an engine based on the job. All three consume Markdown; they differ in
philosophy and export strength.

### reveal.js
- **Best for:** rich, interactive, animated decks; speaker notes; embedded code
  execution; vertical/nested slides.
- **Authoring:** raw HTML + Markdown, or the `reveal-md` CLI which wraps
  Markdown in a reveal.js scaffold.
- **Install:** `npm install -g reveal-md` (CLI) or `npm create reveal@latest`.
- **Run:** `reveal-md deck.md` → serves at `http://localhost:5655`.
- **Strengths:** largest plugin ecosystem (math, charts, audio, PDF export).

### Marp
- **Best for:** minimal, opinionated Markdown→slides with zero fuss. Great for
  docs teams that already write Markdown.
- **Authoring:** standard Markdown with a `---` slide separator and YAML front
  matter for theming.
- **Install:** `npm install -g @marp-team/marp-cli`.
- **Run:** `marp deck.md -w` (watch mode) or `marp deck.md --pdf`.
- **Strengths:** fastest path to a clean deck; first-class PDF/PPTX/HTML export;
  official VSCode extension with live preview.

### Slidev
- **Best for:** developer talks — code highlighting, live demos, Vue components
  inside slides, drawing on slides.
- **Authoring:** Markdown with `---` separators and `<style>` / `<script>`
  blocks; slide-level `<v-clicks>` for step animations.
- **Install:** `npm init slidev` then `npm install`.
- **Run:** `npm run dev` → serves at `http://localhost:3030`.
- **Strengths:** built on Vite (HMR), draws on slide, records presentations,
  exports to PDF/PPTX via `@slidev/cli` build.

## Markdown Syntax for Slides

All three use `---` on its own line as the default slide separator.

```markdown
---
# Title Slide
A subtitle here

---

## Slide Two
- Bullet one
- Bullet two

> A blockquote for emphasis

---

## Slide Three
\`\`\`js
console.log("code is highlighted");
\`\`\`
```

### reveal.js (via reveal-md)
Use `---` for horizontal slides and `--` for vertical (nested) slides:

```markdown
# Horizontal A
---

# Horizontal B
--

## Nested under B
```

Add speaker notes with HTML comments: `<!-- .slide: data-notes="Talk about X" -->`
or a `Notes:` block when using `reveal-md` note syntax.

### Marp
Front matter controls the deck globally:

```markdown
---
marp: true
theme: default
paginate: true
---

# First slide
```

- `<!-- _class: lead -->` applies a CSS class to one slide.
- `<!-- _backgroundColor: #0b3d91 -->` sets a slide background.
- `<!-- _paginate: false -->` hides the page number on that slide.

### Slidev
- `---` separates slides; `---layout: center` switches layout for the next slide.
- `<v-click>` and `<v-clicks>` reveal list items step by step.
- A slide's first comment block (`<!-- ... -->`) becomes speaker notes.

## Themes

### reveal.js
Themes are CSS files in `css/theme/` (e.g. `black`, `white`, `league`,
`beige`, `sky`, `night`). Switch via front matter or the `theme` flag:
`reveal-md deck.md --theme night`. Custom themes are plain CSS overriding
`--r-background-color`, `--r-main-font`, etc.

### Marp
Ships with `default`, `gaia`, and `uncover`. Apply via front matter
`theme: gaia`. Custom themes are defined in a CSS file and registered with
`@theme mytheme` directives (see Marp core docs). Brand decks by overriding
CSS custom properties:

```css
:root {
  --color-background: #0b3d91;
  --color-foreground: #ffffff;
  --color-primary: #ffb000;
}
```

### Slidev
Themes are npm packages (e.g. `@slidev/theme-default`, `@slidev/theme-seriph`,
`@slidev/theme-apple-basic`). Install and set in front matter:
`theme: seriph`. Unstyled local `style` blocks override per-deck.

## Export to PDF/PPTX

### Marp (simplest, recommended default)
```bash
marp deck.md --pdf deck.pdf
marp deck.md --pptx deck.pptx
marp deck.md --html deck.html
```
For pixel-perfect PDF, enable Chromium in Marp: `marp --pdf --allow-local-files`.

### reveal.js
Use the print-to-PDF query param in a headless browser, or:
```bash
reveal-md deck.md --print deck.pdf        # chromium required
```
PPTX export is not native; convert the PDF, or render HTML and use a
PDF→PPTX converter (e.g. `unoconv` / LibreOffice headless).

### Slidev
```bash
slidev build --pdf        # requires playwright/chromium
slidev build --pptx       # exports .pptx
slidev export deck.md     # interactive export wizard
```
Ensure `npx playwright install chromium` is available for PDF/PPTX builds.

## Live Preview

- **Marp:** `marp deck.md -w` plus the Marp VSCode extension (side-by-side
  preview). Or `npx @marp-team/marp-cli deck.md -w -s` for a server.
- **reveal.js:** `reveal-md deck.md` opens a live server; edits hot-reload.
- **Slidev:** `npm run dev` gives Vite HMR — edits appear instantly, plus a
  presenter mode at `/presenter/0` and a drawing layer.

Always preview before exporting; fonts, backgrounds, and code blocks often
shift between preview and print.

## Pitfalls

- **`---` ambiguity:** YAML front matter and slide separators both use `---`.
  Keep front matter at the very top and ensure a blank line around separators.
- **Chromium missing:** PDF/PPTX export in Marp and Slidev needs a headless
  browser. Install it (`npx @marp-team/marp-cli --version` then
  `npx playwright install chromium`) or exports silently fail.
- **Absolute image paths:** Use relative paths; pass `--allow-local-files`
  (Marp) or run from the deck's directory so assets resolve in export.
- **Fonts not embedded:** Some PDF converters drop web fonts. Prefer system
  fonts or bundle `@font-face` files alongside the deck.
- **Speaker notes leak:** Notes render in HTML export by default; strip them
  for public PDFs (`marp --pdf` excludes notes; reveal needs a flag).
- **Engine mismatch:** reveal.js uses `--` for vertical slides; Marp/Slidev
  treat `--` as a thematic break. Don't mix syntaxes across engines.
- **Watch-mode port clash:** If a preview server won't start, the port is
  likely busy — kill the stray process or pass an explicit port flag.
