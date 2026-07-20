---
name: frontend-design-toolkit
description: "Build distinctive frontends using curated real-world design system patterns — agent + this skill = user gets a non-generic UI that doesn't look AI-generated."
version: 1.0.0
---

# frontend-design-toolkit

Build frontends that don't look like an LLM generated them. The agent uses curated design patterns from real, recognizable products (Stripe, Linear, Vercel, Discord, Spotify, Notion, etc.) combined with anti-AI-slop rules to produce UIs with actual design intent.

## When to Use

- The user asks for a frontend, landing page, dashboard, web app, or UI component.
- The user wants to redesign an existing UI that looks generic or AI-generated.
- The user says "build me a frontend", "design a page", "make this look better", or "I don't want it to look like AI made it".
- Any time you're about to write HTML/CSS/JSX for a user-facing interface.

## Anti-AI-Slop Rules

These are the tells that make a frontend immediately recognizable as LLM-generated. The agent must not produce them.

### Banned patterns

| Pattern | Why it's a tell | What to do instead |
|---|---|---|
| Purple-to-blue gradient hero | Every AI-generated SaaS landing page | Solid color, editorial photo, or typography-only hero |
| Three equal feature cards with icons | The most generic layout in AI output | Asymmetric grid, numbered list, or narrative section |
| Emoji as feature icons (🚀 ⚡ 🔒 ✨) | Instant AI signal | Custom SVG icons, or no icons — let typography carry it |
| "Powerful, seamless, comprehensive" copy | Filler words that mean nothing | Concrete verbs and specifics |
| Glassmorphism on everything | Overused AI aesthetic | Solid surfaces with real borders |
| Centered everything | Default LLM layout | Intentional asymmetry, left-aligned editorial layouts |
| Aurora/blob backgrounds | AI-generated background noise | Solid colors, grid lines, or real imagery |
| Inter as the only font | Default AI font choice | Pair a display face with a body face |

### Required patterns

- **Color in OKLCH** — not random hex values. Use CSS custom properties.
- **Font pairing** — a display face + a body face. Never a single font for everything.
- **4pt spacing scale** — `--space-xs: 0.25rem`, `--space-sm: 0.5rem`, `--space-md: 1rem`, `--space-lg: 2rem`, `--space-xl: 4rem`.
- **Intentional whitespace** — whitespace is a design element, not empty space to fill.
- **Real structure** — sections should have a reason to exist, not be there because "a landing page needs 8 sections".

## Design System Catalog

Real, recognizable design systems the agent can draw from. Each entry has a concrete pattern to replicate, not just a "vibe."

### Stripe — payment SaaS
- **Colors:** Indigo (#635BFF) on white, with soft gray surfaces
- **Typography:** Sohne (sans) + Cambridge (serif for display)
- **Pattern:** Pricing tables with per-feature comparison rows, clean alignment, subtle hover states
- **Layout:** Generous whitespace, centered max-width content, subtle shadows
- **Replicate for:** SaaS pricing pages, payment flows, API documentation

### Linear — project management
- **Colors:** Dark gray (#0D1117) with purple accent (#5E6AD2)
- **Typography:** Inter Tight (display) + Inter (body)
- **Pattern:** Command palette (⌘K), dense list views, keyboard-first navigation
- **Layout:** Sidebar + main content, minimal chrome, fast transitions
- **Replicate for:** Dashboards, admin panels, project management tools

### Vercel — deployment platform
- **Colors:** Black, white, with subtle gray accents
- **Typography:** Geist Sans + Geist Mono
- **Pattern:** Deployment cards with status indicators, clean monospace metadata
- **Layout:** Centered hero, grid of feature cards (but not the generic 3-card pattern — use varied spans)
- **Replicate for:** Dev tool landing pages, deployment dashboards, status pages

### Discord — community platform
- **Colors:** Dark gray (#36393F) with blurple (#5865F2)
- **Typography:** Whitney (custom) or Inter as substitute
- **Pattern:** Sidebar-heavy navigation, channel list, member list, chat area
- **Layout:** Three-column (server rail + channel sidebar + main content)
- **Replicate for:** Chat apps, community tools, real-time dashboards

### Spotify — media platform
- **Colors:** Black (#121212) with green accent (#1DB954)
- **Typography:** Circular (custom) or Inter as substitute
- **Pattern:** Large artwork cards, horizontal scroll rows, sticky player bar
- **Layout:** Sidebar + content area with horizontal scroll rows
- **Replicate for:** Media apps, content browsers, music/video players

### Notion — productivity tool
- **Colors:** White (or dark mode #191919) with subtle gray
- **Typography:** Avenir Next / Inter
- **Pattern:** Block-based editor, toggle accordions, clean tables
- **Layout:** Full-width content, minimal chrome, document-first
- **Replicate for:** Note apps, wikis, documentation, content management

### GitHub — developer platform
- **Colors:** White (or dark mode #0D1117) with blue accent
- **Typography:** -apple-system / Segoe UI / Inter
- **Pattern:** Tabbed navigation, code blocks with syntax highlighting, pull request diff view
- **Layout:** Sidebar + main content, dense information display
- **Replicate for:** Code hosting, developer tools, repository browsers

### Apple — product marketing
- **Colors:** White with product-specific accents
- **Typography:** SF Pro Display + SF Pro Text
- **Pattern:** Full-bleed product imagery, scroll-triggered animations, large typography
- **Layout:** Full-width sections, massive whitespace, centered product shots
- **Replicate for:** Product launches, hardware showcases, premium consumer apps

## Color Discipline

Use OKLCH for all colors. Define them as CSS custom properties at `:root`:

```css
:root {
  --paper: oklch(98% 0.002 240);      /* main background */
  --paper-2: oklch(95% 0.004 240);    /* elevated surface */
  --ink: oklch(20% 0.010 240);        /* primary text */
  --ink-2: oklch(45% 0.008 240);      /* secondary text */
  --ink-3: oklch(65% 0.006 240);      /* tertiary text / borders */
  --accent: oklch(48% 0.12 250);      /* brand accent */
  --accent-soft: oklch(92% 0.03 250); /* accent background */
  --rule: oklch(88% 0.004 240);       /* borders and dividers */
}
```

Why OKLCH: perceptually uniform, predictable lightness adjustments, better contrast control than HSL or hex.

## Typography

Always pair two fonts. A display face for headings and a body face for text.

| Genre | Display | Body | Mood |
|---|---|---|---|
| Editorial / news | Serif (e.g., Source Serif) | Sans (e.g., Inter) | Authoritative, readable |
| SaaS / dev tool | Geometric sans (e.g., Geist) | Grotesk sans (e.g., Inter) | Modern, technical |
| Creative / agency | Display sans (e.g., Space Grotesk) | Humanist sans (e.g., Söhne) | Distinctive, brand-forward |
| Terminal / data | Monospace (e.g., JetBrains Mono) | Monospace | Dense, technical |
| Playful / consumer | Rounded sans (e.g., Plus Jakarta) | Humanist sans (e.g., Inter) | Friendly, approachable |

Use Google Fonts or self-host. Never use a system font as the only font — that's an AI tell.

## Layout

- **4pt spacing scale**: all spacing values are multiples of 4px (0.25rem). Define as custom properties.
- **Asymmetric grids**: not everything is a centered 3-column grid. Use `grid-template-columns: 2fr 1fr` or varied spans.
- **Intentional whitespace**: a section with one sentence and lots of whitespace is stronger than a section crammed with 5 features.
- **Responsive**: mobile-first. Test at 320px, 375px, 414px, 768px. No horizontal scroll.

## Component Patterns (from real products)

### Command palette (Linear-style)
```
⌘K opens a centered search box
- Filtered list of actions
- Keyboard navigation (arrow keys + enter)
- Recent items at top
```

### Pricing table (Stripe-style)
```
Three tiers side by side
- Feature comparison rows
- "Most popular" badge on middle tier
- Per-month / per-year toggle
- Clear CTA buttons
```

### Deployment card (Vercel-style)
```
Card with:
- Project name + framework icon
- Status indicator (ready/building/error)
- Timestamp + commit hash in monospace
- Visit button
```

### Sidebar navigation (Discord-style)
```
Server rail (narrow, icon-only)
  → Channel sidebar (wider, text labels)
    → Main content area
```

## Workflow

### Step 1: Ask what they're building
"What are you building? A landing page, dashboard, web app, or something else?"

### Step 2: Recommend a design system
Based on the project type, recommend 2-3 design systems from the catalog. Let the user pick.

### Step 3: Set up tokens
Define OKLCH color tokens, font pairing, and spacing scale as CSS custom properties.

### Step 4: Build the structure
HTML structure first — no styling. Verify the layout makes sense before adding visual design.

### Step 5: Apply the design system
Colors, typography, spacing, component patterns from the chosen design system.

### Step 6: Run the slop check
Re-read the anti-AI-slop rules. Check every section against the banned patterns table. Fix any violations.

### Step 7: Test responsive
Test at 320px, 375px, 414px, 768px. Fix any horizontal scroll or broken layouts.

## Pitfalls

- **Defaulting to the same style every time** — Don't always reach for Stripe-style. Match the design system to the project type.
- **Copying a design system too literally** — Use the patterns and principles, not the exact colors. Stripe's indigo doesn't work for every SaaS.
- **Skipping the font pairing** — A single-font page is an AI tell. Always pair a display face with a body face.
- **Forgetting mobile** — Test at 320px. If the layout breaks, fix it before shipping.
- **Too many animations** — Animate `transform` and `opacity` only. Most pages have too much motion, not too little.
- **Ignoring the slop check** — The anti-AI-slop rules are not optional. Run the check before shipping.
