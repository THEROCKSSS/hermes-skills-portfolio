# 0003: Two-axis skill ranking — curated usefulness tier + empirical usage

Skills in the portfolio are ranked on two axes:

1. **Usefulness Tier** (curated, set at publish time, static until re-reviewed) — three tiers: `Core` (broadly empowering, nearly any user benefits), `Featured` (highly useful within a category), `Utility` (useful for specific workflows). This is a judgment call by the author, not a metric. It is the day-one ranking.

2. **Usage** (empirical, accumulates over time) — pulled from the Hermes skills hub install count (if published there) + GitHub clone/star signals + a self-reported "I'm using this" reaction on the portfolio site. Starts at 0 for every skill. Becomes meaningful once the portfolio has real traffic.

**Default sort:** Usefulness tier (Core → Featured → Utility), then usage within tier. Users can re-sort by usage-only, recency, category, or alphabetical.

**Agent parsing:** A structured `skills-index.json` at the repo root contains per skill: name, category, usefulness tier, usage count, recency, install URL, one-line description. The portfolio README and Pages site render from the same file so users and agents see the same truth.

## Considered Options

- **A. Usage-only ranking.** Rejected: cold-start is fatal. Every skill shows 0 installs on day one and the portfolio looks dead. No credible day-one ordering.
- **B. Usefulness-only ranking (no usage axis).** Rejected: never improves with real adoption data. A skill that becomes genuinely popular stays buried below a Core skill that nobody uses. No empirical signal ever surfaces.
- **C. Star-only ranking (GitHub stars per skill).** Rejected: stars are a vanity metric at this scale, and per-skill repos don't exist by default (the monorepo is the primary repo). Stars accumulate on the shopfront, not per skill, so per-skill star counts are meaningless until a per-skill publish happens.
- **D. Alphabetical with tier badges (no ordering).** Rejected: the user explicitly said "ranked," not "labeled." Badges without ordering don't meet the requirement — a user scanning the list can't tell which Core skill is more useful than another.
- **E. Two-axis (curated usefulness + empirical usage, default sort tier-then-usage, structured skills-index.json for agents).** Accepted. Solves the cold-start problem with a credible curated day-one ranking, enriches with empirical data over time, and gives agents a single structured file to parse instead of markdown prose.

## Consequences

- The `skills-index.json` schema is now a contract: every skill directory must have its metadata harvestable into the index. A CI lint step validates that every `skills/*/SKILL.md` has the required frontmatter (name, category, tier, description) and that `skills-index.json` is in sync.
- Tier assignments are authored decisions — the grilling/refining process for each skill includes assigning a tier. Tiers are not auto-derived.
- Usage data collection is deferred until the portfolio has a real distribution surface (GitHub public + optional Hermes hub publish). On day one, `usage` is 0 for all skills in the index.
- The Pages site needs a sort/filter UI (category dropdown, tier filter, sort-by selector). This is a build-time concern for the site, not a structural change to the repo.
- If the Hermes hub is added later, its install counts feed back into `skills-index.json` via a refresh script.
