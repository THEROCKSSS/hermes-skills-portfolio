# Design — Hermes Skills Portfolio

A locked design system for this app. Every page redesign reads this file before
emitting code. Do not regenerate per page — extend or amend this file when the
system needs to grow.

## Genre
atmospheric

## Theme
**Dusk** (custom) — a soft warm-violet dark canvas with a warm amber signal and
generous radii. Quieter and more workmanlike than a cinematic register: the
catalog is a tool you filter, not a storefront you browse.

Chosen on 2026-08-02 from a 50-variation prototype (10 layouts x 5 skins, in
`prototypes/catalog/`). The owner picked **layout L4 (Sidebar filter) with skin
S5 (Dusk)**. This supersedes the short-lived Marquee/rails direction.

**Mode.** Dark-primary. This **supersedes** the 2026-07-29 decision that made
Cobalt's light palette the default; the owner asked for this direction
explicitly on 2026-08-02. The light palette is retained as a full inversion
(`[data-theme="light"]` in `site/css/tokens.css`) because the site has always
shipped a working toggle and removing it would regress anyone using it.
`initTheme()` in `site/js/common.js` defaults to `dark` and honours a saved
preference.

**The accent can be the button here.** Dusk's amber sits at 76% lightness, so
dark ink on it clears ~7:1 — unlike the previous crimson, which forced the CTA
onto a separate light fill. `--color-cta` and `--color-accent` therefore hold
the same value in this theme; they stay separate tokens so a future re-skin with
a darker accent can split them again without touching any page CSS.

## Macrostructure family
Pages vary shape by type; all share nav, footer, theme, and type. No page may
introduce a different theme "for variety" — variety lives in macrostructure
choice, not palette.

- **Hub (Catalog / home):** **Sidebar Filter** — a compact masthead, then a
  persistent left sidebar of facets (search, category, tier, personal lists)
  driving a results grid on the right. The sidebar collapses behind a real
  disclosure button below 60rem.
  **The facet counts are the distribution chart.** Each facet row draws a bar
  proportional to its share, so the sidebar answers both "filter this" and
  "how is the catalog shaped" without a second section restating the same
  numbers. A table view of the same figures sits behind a `<details>`.
- **Content (Changelog):** Index-First — a calm, dated log, reskinned to the
  dark canvas. Still list-shaped, never narrative-editorial.
- **Process (Submit a skill):** Narrative Workflow — the submission pipeline as
  numbered stages, not a marketing pitch.
- **Discovery (Bundles):** Index-First — curated bundles, each expandable to
  its member skills with a bulk copy of every install command.
- **Detail (per-skill):** overlay + static per-skill pages, reskinned to the
  system; structure unchanged so share links and crawlers keep working.

## Theme tokens
See `site/css/tokens.css` for the full set. Token *names* are unchanged across
the Cobalt → Marquee → Dusk re-themes on purpose: page CSS references them by
name, so a re-skin stays a values-only change. Summary:
- `--color-paper` oklch(19% 0.020 300) — soft warm-violet dark, never pure `#000`
- `--color-ink` oklch(94% 0.012 60) — warm, to sit against the violet ground
- `--color-accent` oklch(76% 0.130 55) — the one signal, and the CTA fill
- `--card-w`, `--poster-ratio`, `--sidebar-w`, `--gutter` — shell and card
  geometry, the structural core of this theme
- Elevation on dark goes **lighter**: `paper` canvas → `paper-2` resting card →
  `paper-3` lifted card

## Typography
- Display: Plus Jakarta Sans 600/700/800 (roman — never italic headers)
- Body: Plus Jakarta Sans 400/500
- Mono: JetBrains Mono 400/500 — code, eyebrows, kbd hints, status chips,
  UPPERCASE with 0.06em tracking
- Google Fonts:
  `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap`

## Spacing
4-point named scale in `tokens.css` (`--space-3xs` … `--space-4xl`). Pages use
named tokens, never raw px.

## Motion
- Easings: `--ease-out` / `--ease-in` / `--ease-in-out`
- Three primitives only: **card-lift** (translate + shadow on hover/focus),
  **bar-grow** (facet distribution bars animate width once), **reveal**
  (fade + 10px rise, IntersectionObserver, once)
- Nothing moves on its own. No autoplay, no carousel — a page that moves while
  you are reading it is hostile.
- Reduced-motion: durations collapse to 1ms; bar-grow and card-lift stop.

## Microinteractions stance
- Silent success over celebratory toasts — toast only for copy actions; theme
  change is silent
- Hover delay: none · focus rings instant, never animated
- Facet rows are real `<button>`s carrying `aria-pressed`, so filtering is
  keyboard- and screen-reader-operable, never a hover-only affordance
- Optimistic, no confirm dialogs for non-destructive actions

## CTA voice
- Primary: `--color-cta` fill, `--color-cta-ink` text, 6px radius, no pill
- Secondary: `--color-cta-2` translucent raise, inherits ink
- Name the destination ("Install", "Copy link", "Add to My List") — never
  "Click here" / "Learn more"

## Nav (shared, identical on every page)
**N10 scroll-morph** — 60px, sticky, starts transparent over the catalog's
masthead and morphs to an opaque blurred bar with a bottom hairline once
scrolled past ~80px. Every other page marks its nav `.is-solid` and starts
opaque. Wordmark + section links left; right: the working **⌘K search pill**,
theme toggle, GitHub link (desktop only).

Shared DOM/CSS/JS: `site/css/base.css` `.nav*` + `site/js/common.js`
`initCmdk` / `initNavMorph`. **Do not rebuild the nav or cmd-k per page** —
include the shared markup block below and call `HermesCommon.initCmdk(indexData)`
once data loads. Mark the current page's link with `aria-current="page"`.

```html
<a class="skip-link" href="#main">Skip to content</a>
<header class="nav" id="nav" data-nav-morph="true">
  <div class="nav-inner">
    <a class="nav-brand" href="./index.html">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 14l4-4 4 4 8-8"/><path d="M4 20h16"/></svg>
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
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span class="cmdk-trigger-label">Search skills…</span>
        <kbd class="cmdk-trigger-kbd">&#8984;K</kbd>
      </button>
      <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="Toggle theme (t)">
        <svg class="icon-sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        <svg class="icon-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <a class="github-link" href="https://github.com/THEROCKSSS/hermes-skills-portfolio" target="_blank" rel="noopener">GitHub</a>
    </div>
  </div>
</header>
```

## Footer (shared, identical on every page)
**Ft4 Dense colophon** — a compact mono block: what this is, how to install,
license, and the repo link. Replaces Cobalt's Ft2 inline line; the colophon's
technical register suits the dark canvas and gives the install command one
last, honest placement. Ft3 index-columns remains banned.

```html
<footer class="footer">
  <div class="footer-inner">
    <div class="footer-col">
      <span class="footer-word">Hermes Skills</span>
      <p class="footer-note">Install one, your agent can now do that for you.</p>
    </div>
    <div class="footer-col">
      <span class="footer-label mono">Install any skill</span>
      <code class="footer-code mono">hermes skills install &lt;url&gt;</code>
    </div>
    <div class="footer-col">
      <span class="footer-label mono">Colophon</span>
      <p class="footer-meta">By Owen &middot; MIT licensed &middot;
        <a href="https://github.com/THEROCKSSS/hermes-skills-portfolio" target="_blank" rel="noopener">Source on GitHub</a>
      </p>
    </div>
  </div>
</footer>
```

## Per-page allowances
- Catalog carries the sidebar and the results grid; no other page does.
- Changelog and Submit: typography + hairlines only, no sidebar.
- No page uses stock photography, invented metrics, or fabricated
  testimonials. Every count on the page comes from `skills-index.json` at
  render time. **Poster tiles carry generated typographic artwork** (a
  deterministic per-skill gradient + monogram derived from the skill name),
  never stock imagery and never an invented screenshot.
- Reaction / My List counts are **local to the visitor** (`localStorage`) and
  labelled as such. The site has no backend, so a global "1.2k people liked
  this" would be fabricated — it is never shown.

## What pages MUST share
- The nav and footer blocks above, byte-identical, with only `aria-current` differing.
- `site/css/tokens.css` and `site/css/base.css`, imported unmodified.
- `site/js/common.js`, imported unmodified — `HermesCommon.*` is the only way
  to touch theme, cmd-k, toast, copy, reveal, or My List.
- The accent hue, the two fonts + one mono, the CTA voice, the 6px/10px radii.

## What pages MAY differ on
- Macrostructure (per the family table above).
- Section/component archetypes within that macrostructure.
- Page-specific CSS in `site/css/<page>.css` and JS in `site/js/<page>.js` —
  new files, additive only.

## Files
```
site/css/tokens.css   locked tokens — do not edit without amending this file first
site/css/base.css     shared nav/footer/buttons/toast/cmd-k/reveal/cards/reset
site/js/common.js     shared theme/data/cmd-k/toast/copy/reveal/mylist utilities
site/index.html       Catalog (Sidebar Filter)       + css/catalog.css   + js/catalog.js
site/changelog.html   Changelog (Index-First)        + css/changelog.css + js/changelog.js
site/submit.html      Submit a skill (Narrative Workflow) + css/submit.css + js/submit.js
site/bundles.html     Bundles (Index-First)          + css/bundles.css   + js/bundles.js
site/skills/<name>/   per-skill static pages (generated, reskinned)
```

## Slop-test gates that matter most here
Gate 54 (no eyebrow-left/heading-right hanging headers), gate 46 (no invented
metrics — every number comes from `skills-index.json`; no fabricated reaction
counts), gate 34 (no horizontal scroll at 320/375/414/768 — verify all four),
gate 2 (no gradient text — the masthead title is solid ink), gate 49 (no
two-line clickable text — the nav collapses to fewer links rather than
wrapping), gate 47 (no re-drawn browser or device chrome around code blocks),
and the atmospheric ban on glassmorphism.

## Exports
`site/css/tokens.css` is the portable export. Every `--color-*`, `--font-*`,
`--space-*`, `--text-*`, `--ease-*`, `--dur-*`, `--radius-*`, and the shell
geometry tokens live there and are referenced by name downstream.
