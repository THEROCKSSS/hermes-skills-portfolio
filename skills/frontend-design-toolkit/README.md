# frontend-design-toolkit

Build frontends using curated real-world design system patterns so the result doesn't look AI-generated.

## What it does

The agent uses design patterns from real, recognizable products (Stripe, Linear, Vercel, Discord, Spotify, Notion, GitHub, Apple) combined with anti-AI-slop rules to build frontends with actual design intent. It picks a design system that matches your project type, sets up OKLCH color tokens and font pairings, and builds the UI from real component patterns — not LLM defaults.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/frontend-design-toolkit/SKILL.md
```

## How to use

```
"Build me a SaaS landing page"
```

The agent:
1. Asks what you're building (landing page, dashboard, web app, etc.)
2. Recommends 2-3 design systems from the catalog (e.g., "Stripe for pricing, Linear for the dashboard")
3. Sets up OKLCH color tokens, font pairing, and a 4pt spacing scale
4. Builds the HTML structure, then applies the design system
5. Runs the anti-AI-slop check (no gradient heroes, no emoji icons, no filler copy)
6. Tests responsive at 320/375/414/768px

## Design systems included

| System | Best for | Signature pattern |
|---|---|---|
| Stripe | SaaS pricing, payment flows, API docs | Per-feature pricing comparison rows |
| Linear | Dashboards, admin panels, project tools | Command palette (⌘K), keyboard-first nav |
| Vercel | Dev tool landing pages, deployment UIs | Deployment cards with status + commit hash |
| Discord | Chat apps, community tools | Three-column layout (server rail + sidebar + content) |
| Spotify | Media apps, content browsers | Horizontal scroll rows, large artwork cards |
| Notion | Note apps, wikis, documentation | Block-based editor, minimal chrome |
| GitHub | Code hosting, developer tools | Tabbed nav, code blocks with syntax highlighting |
| Apple | Product launches, premium consumer | Full-bleed imagery, massive whitespace |

## Anti-AI-slop rules

The skill enforces a ban list of patterns that make frontends immediately recognizable as LLM-generated:

- No purple-to-blue gradient heroes
- No three equal feature cards with emoji icons (🚀 ⚡ 🔒)
- No "powerful, seamless, comprehensive" filler copy
- No glassmorphism on everything
- No centered-everything layouts
- No Inter as the only font (must pair display + body)
- No random hex colors (must use OKLCH tokens)

## Example

```
User: "Build a dashboard for my project management tool"

Agent:
  1. Recommends: Linear-style (dark gray + purple accent, command palette, dense lists)
  2. Sets up tokens:
     --paper: oklch(15% 0.005 240)    /* dark background */
     --accent: oklch(52% 0.14 270)    /* purple accent */
     --font-display: "Inter Tight"
     --font-body: "Inter"
  3. Builds: sidebar + main content area, command palette, issue list
  4. Slop check: no gradient hero ✓, no emoji icons ✓, font pairing ✓
  5. Tests at 320px / 768px / desktop
  6. Returns: working HTML/CSS dashboard with Linear-inspired design
```
