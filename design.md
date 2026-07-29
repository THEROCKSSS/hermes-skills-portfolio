# Design — Hermes Skills Portfolio

A locked design system for this app. Every page redesign reads this file before
emitting code. Do not regenerate per page — extend or amend this file when the
system needs to grow.

## Genre
modern-minimal

## Theme
Cobalt — cool engineered near-white paper, one electric-cobalt signal accent,
ruler-drawn hairlines, tight 6px control radii, one dark "graphite" band per
page for a showcase moment. Reference register: GitBook / Firecrawl / Vercel /
Mintlify / Stripe docs school. Never orange, never a chromatic flood — the
accent is a signal, used at under 5% of any viewport.

**Mode.** Cobalt's native identity is light-primary with one dark band ("never
a dark theme"). This project keeps its pre-existing dark/light toggle for
users who prefer it, but **light is now the default** — a deliberate deviation
from the previous dark-default, confirmed with the project owner on
2026-07-29 (Cobalt fights a dark-default; light is what the theme actually is).
Dark mode is a careful full-palette inversion (see `site/css/tokens.css`
`[data-theme="dark"]`), not the theme's native state.

## Macrostructure family
Pages vary shape by type; all share nav, footer, theme, and type. No page may
introduce a different theme "for variety" — variety lives in macrostructure
choice, not palette.

- **Hub (Catalog / home):** Ecosystem Index — Featured/Just Added rail, by
  category, by tier, then search-first browsing. Not one flat grid.
- **Content (Changelog):** Index-First — a calm, dated, hairline-ruled log.
  Cobalt explicitly rejects prose-led "Long Document," so this stays
  list-shaped, never narrative-editorial.
- **Process (Submit a skill):** Narrative Workflow — the actual submission
  pipeline as numbered stages (Open issue → Review → Approved → PR opens →
  Merged/live), not a marketing pitch for submitting.
- **Discovery (Bundles):** Index-First — a calm list of curated bundles (real
  groupings of existing catalog skills for one job), each expandable to its
  member skills with a bulk-copy of every install command. Not a grid of
  marketing cards — bundles are reference material, same register as the
  changelog.
- **Detail (per-skill):** kept as the existing overlay + static per-skill
  pages; reskinned to the system, structure unchanged.

## Theme tokens
See `site/css/tokens.css` for the full token set (colors, type, space, motion,
z-index). Summary:
- `--color-paper` oklch(98.5% 0.004 250) · `--color-ink` oklch(24% 0.02 258)
- `--color-accent` oklch(58% 0.20 256) — the one signal
- `--color-graphite` oklch(22% 0.016 260) — the one dark band / code card
- `--color-rule` oklch(90% 0.006 250) — hairlines do the work, no boxed cards

## Typography
- Display: Space Grotesk 500/600
- Body: Inter 400/500
- Mono: JetBrains Mono 400/500 — code, eyebrows, kbd hints, status chips, all UPPERCASE with 0.06em tracking
- Google Fonts:
  `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap`

## Spacing
4-point named scale in `tokens.css` (`--space-3xs` … `--space-4xl`). Pages use
named tokens, never raw px.

## Motion
- Easings: `--ease-out` / `--ease-in` / `--ease-in-out` (see `motion.md` values, mirrored in tokens.css)
- Reveal pattern: fade + 10px rise via `.reveal` / `.reveal.is-in`, IntersectionObserver only, once
- One hero type-in on the catalog page only; everywhere else: reveal or none
- Reduced-motion: opacity-only, ≤150ms (see `tokens.css` media query)

## Microinteractions stance
- Silent success over celebratory toasts — toast only for copy actions and theme change is silent
- Hover delay: none (immediate) · focus rings: instant, never animated
- Optimistic, no confirm dialogs for non-destructive actions

## CTA voice
- Primary: solid `--color-accent` fill, `--color-accent-ink` text, 6px radius, no pill
- Secondary: outline, `--color-rule-2` border, hover → accent border + accent text
- Name the destination ("Install", "Copy link"), never "Click here" / "Learn more"

## Nav (shared, identical on every page)
Bordered flush bar — 60px, sticky, blur-on-scroll, 1px bottom hairline.
Wordmark + 2–3 text links left (`Catalog` / `Changelog` / `Submit a skill`).
Right: a working **⌘K search pill** (opens a real command palette — type to
filter the live `skills-index.json`, arrow keys + Enter to navigate), theme
toggle, GitHub link (desktop only). This is Cobalt's actual signature move,
not a generic pick — see `references/themes/cobalt.md` signature 5.
Shared DOM/CSS/JS: `site/css/base.css` `.nav*` + `site/js/common.js`
`initCmdk`. **Do not rebuild the nav or cmd-k per page** — include the exact
markup block below and call `HermesCommon.initCmdk(indexData)` once data
loads.

```html
<a class="skip-link" href="#main">Skip to content</a>
<header class="nav">
  <div class="nav-inner">
    <a class="nav-brand" href="./index.html">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 14l4-4 4 4 8-8"/><path d="M4 20h16"/></svg>
      Hermes Skills
    </a>
    <nav class="nav-links" aria-label="Sections">
      <a href="./index.html" data-nav="catalog">Catalog</a>
      <a href="./bundles.html" data-nav="bundles">Bundles</a>
      <a href="./changelog.html" data-nav="changelog">Changelog</a>
      <a href="./submit.html" data-nav="submit">Submit a skill</a>
    </nav>
    <div class="nav-actions">
      <button class="cmdk-trigger" id="cmdk-trigger" aria-haspopup="dialog" aria-controls="cmdk-modal">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span class="cmdk-trigger-label">Search skills…</span>
        <kbd class="cmdk-trigger-kbd">&#8984;K</kbd>
      </button>
      <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="Toggle theme (t)">
        <svg class="icon-sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        <svg class="icon-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <a class="github-link" href="https://github.com/THEROCKSSS/hermes-skills-portfolio" target="_blank" rel="noopener">GitHub</a>
    </div>
  </div>
</header>
```

Mark the current page's link with `aria-current="page"` in that page's copy
of this block.

## Footer (shared, identical on every page)
Ft2 Inline single line — wordmark + tagline + credit, hairline rule above, no
column sitemap (modern-minimal's default; Ft3 index-columns is banned for
this genre except a genuine docs root, which this isn't).

```html
<footer class="footer">
  <div class="footer-inner">
    <span class="footer-word">Hermes Skills — by Owen</span>
    <span class="footer-sep">&middot;</span>
    <span>Install one, your agent can now do that for you.</span>
    <span class="footer-sep">&middot;</span>
    <span>MIT licensed</span>
  </div>
</footer>
```

## Per-page allowances
- Catalog MAY use the dark graphite band (e.g. a "how it works" or stat strip).
- Changelog and Submit pages: typography + hairlines only, no enrichment.
- No page uses stock photography, invented metrics, or fabricated
  testimonials — every count on the page must come from `skills-index.json`
  at render time.

## What pages MUST share
- The nav and footer blocks above, byte-identical, with only `aria-current` differing.
- `site/css/tokens.css` and `site/css/base.css`, imported unmodified.
- `site/js/common.js`, imported unmodified — `HermesCommon.*` is the only way
  to touch theme, cmd-k, toast, copy, or reveal. Do not re-implement any of
  these per page.
- The accent hue, the two fonts + one mono, the CTA voice, the 6px/10px radii.

## What pages MAY differ on
- Macrostructure (per the family table above).
- Section/component archetypes within that macrostructure.
- Page-specific CSS in `site/css/<page>.css` and page-specific JS in
  `site/js/<page>.js` — new files, additive only.

## Files
```
site/css/tokens.css   locked tokens — do not edit without amending this file first
site/css/base.css     shared nav/footer/buttons/toast/cmd-k/reveal/reset — do not edit per page
site/js/common.js     shared theme/data/cmd-k/toast/copy/reveal utilities — do not edit per page
site/index.html       Catalog (Ecosystem Index)      + site/css/catalog.css   + site/js/catalog.js
site/changelog.html   Changelog (Index-First)        + site/css/changelog.css + site/js/changelog.js
site/submit.html      Submit a skill (Narrative Workflow) + site/css/submit.css + site/js/submit.js
site/bundles.html     Bundles (Index-First)               + site/css/bundles.css + site/js/bundles.js
site/skills/<name>/   per-skill static pages (existing generator, reskinned)
```

## Slop-test gates that matter most here
Gate 54 (no eyebrow-left/heading-right hanging headers), gate 46 (no invented
metrics — every number comes from `skills-index.json`), gate 6 (no
centred-everything hero on the catalog page — Cobalt is left-biased), gate 34
(no horizontal scroll at 320/375/414/768 — verify all four).
