# Hermes Portfolio

A public portfolio of Hermes-related projects and shareable skills, with refinement as the publishing process.

## Language

**Portfolio**:
A curated, bounded set of public deliverables — shareable skills plus reference projects — with a defined finish line.
_Avoid_: "all my skills", "everything good", unbounded dump.

**Skills Track**:
One of two portfolio tracks. General-purpose skills polished and published via `hermes skills publish` and/or a public repo. Each skill must be self-contained, useful to someone who is not Owen, and free of personal-utility coupling.
_Avoid_: personal-utility skills, profile-specific workflows.

**Projects Track** (out of scope):
Originally one of two portfolio tracks — small reference apps showcasing a Hermes capability. Dropped on 2026-07-20: the portfolio is skills-only. Term retained to record the decision and the rejected alternative.
_Avoid_: full production apps, personal dashboards.

**Refining**:
The process of bringing a near-publishable skill up to public quality. Not a separate deliverable — it is the workflow _for_ the Skills Track. Publishing forces the refinement.
_Avoid_: "polishing", "cleanup" (too vague — refining is bounded by a publishable bar).

**Audience**:
General users who want their agent to do useful work for them. Not niche framework devs, not abstract "agent-framework users." The pitch is "install this skill, your agent can now do X for you."
_Avoid_: "the Hermes community", "agent developers", "contributors" (too narrow or too abstract).

**Empowering Skill**:
The pattern the Skills Track targets: agent + this skill = user gets a working capability. The skill is a means, not the subject. Archetype: a Tailscale skill that lets a user's agent deploy something on Tailscale so the user can privately access it — not a skill *about* Tailscale.
_Avoid_: tutorial skills, reference skills, "how-to" skills that describe a tool without making the agent able to deliver an outcome.

**De-prioritized**:
The Spectrum/iMessage project. Explicitly not the prize in this portfolio. May exist separately; not part of this scope.

**Distribution Surface**:
How a published skill reaches the audience. For this portfolio: a dedicated public GitHub repo with a highly-detailed README (the primary shopfront), mirrored to and deployed locally through the user's Forgejo instance at localhost:3000 (the local review/staging surface). `hermes skills publish` to the Hermes hub is a possible add-on, not the primary channel.
_Avoid_: "just put it on the hub", "just push to GitHub" (both undersell the dedicated-shopfront requirement).

**Hallmark README**:
A README authored using the Hallmark skill's anti-AI-slop design discipline — opinionated typography, real structure (not generic AI headings), no LLM filler, human-voice prose. The portfolio README and each skill's README must pass Hallmark's quality bar.
_Avoid_: auto-generated READMEs, templated READMEs, "summarize the skill in 3 bullets" READMEs.

**Forgejo Role**:
The local Forgejo instance (localhost:3000) serves two purposes for the portfolio: (1) a Git remote for the same commit-and-review workflow used for agentsoul/dashboard, agentsoul/battlebit-stats, agentsoul/agent-memory — every skill change is a visible commit Owen can review; (2) a Forgejo Pages-style static site that renders the README content as a browseable HTML page locally, so the Hallmark README can be verified in a browser before pushing to public GitHub. Forgejo is the review/staging surface; GitHub is the public shopfront.
_Avoid_: "just a git remote" (undersells the Pages rendering), "the host" (Forgejo is local review, not public hosting).

**Local Monorepo**:
The Forgejo repo is a single monorepo containing all skills, one top-level directory per skill, plus the portfolio README, CONTEXT.md, docs/adr/, and the Pages static site. This is the only local structure — there is no per-skill repo on Forgejo.
_Avoid_: one-repo-per-skill on Forgejo, submodule umbrellas.

**GitHub Shopfront**:
The primary public surface: a single GitHub repo under the user's actual name (Monica Amano) that mirrors the monorepo's content and serves as the portfolio shopfront with a Hallmark README. This is NOT one-repo-per-skill — the default public structure is one repo.
_Avoid_: "GitHub org", per-skill repos as the default structure.

**Per-Skill Publish**:
An optional, on-demand publishing flow implemented AS A SKILL (not a script) that lives inside the portfolio at `skills/skill-publish/`. When the user gives a prompt naming one skill, the agent loads `skill-publish` and uses it to push that skill from the monorepo into its own dedicated GitHub repo with its own Hallmark README/page. The skill is self-contained: a user can also read it and run the publish flow themselves manually. Triggered only by an explicit prompt — never automatic. The skill is itself one of the portfolio's empowering skills (self-referential by design).
_Avoid_: a standalone script, an auto-firing GitHub Actions workflow, making per-skill repos the default structure.

**Portfolio Size**:
The portfolio contains approximately 50 empowering skills (not 10). This is a 5× expansion from the initial proposal and is non-negotiable per the user's decision on 2026-07-20.
_Avoid_: "a small curated set", "7–10 skills", unbounded growth past ~50.

**Categorized**:
Every skill in the portfolio belongs to a named category (e.g., DevOps, Frontend, Backend, Utility, Meta). Categories are part of the portfolio's structure and are visible to both users and agents.
_Avoid_: a flat un-categorized list, ad-hoc tagging with no categories.

**Ranked**:
Skills are ranked by usefulness and usage, surfaced to users as a sortable view. Usefulness is a curated quality judgment; usage is actual install/adoption data. The ranking mechanism is TBD pending Q8–Q10.
_Avoid_: alphabetical-only ordering, random ordering, "all skills are equal".

**Sortable**:
The portfolio README and/or Pages site supports user-driven sorting (by category, by usefulness tier, by usage count, by recency) and agent-driven browsing (structured metadata an agent can parse to recommend skills). Implies more than a flat markdown list — needs a filterable/sortable view.
_Avoid_: a single static ordered list with no sort controls, unstructured prose an agent can't parse.

**Skill Sources**:
The ~50 portfolio skills come from three blended sources: (1) ~15-20 generalized from existing personal-utility skills (strip the Owen/profile coupling, rework for public use), (2) ~15-20 newly authored for common capability gaps matching the "agent + skill = working capability" pattern, (3) ~10-15 adapted from third-party skills (skills.md, skillsmp.com) with rework + source attribution per Owen's standing rule. Locked 2026-07-20.
_Avoid_: source 1 only (stretches low-quality generalizations), source 2 only (months of work, momentum loss), source 3 only (a mirror, not a portfolio).

**Usefulness Tier**:
A curated quality judgment assigned to each skill at publish time by the author. Three tiers: `Core` (broadly empowering, nearly any user benefits), `Featured` (highly useful within a category), `Utility` (useful for specific workflows). Static until re-reviewed — does not change with adoption. This is the day-one ranking and solves the cold-start problem (a new portfolio has no usage data).
_Avoid_: usage-derived tiers, star-count tiers, alphabetical-with-badges (badges without ordering don't meet the "ranked" requirement).

**Usage**:
Empirical adoption data that accumulates over time, pulled from the Hermes skills hub install count (if published there) + GitHub clone/star signals + a self-reported "I'm using this" reaction on the portfolio site. Starts at 0 for every skill on day one. Becomes meaningful once the portfolio has real traffic. The second axis of ranking — enriches but never replaces the Usefulness Tier.
_Avoid_: stars-only (vanity metric at this scale, and per-skill repos don't exist by default), self-reported-only (gamable).

**Skills Index**:
A structured `skills-index.json` file at the repo root that an agent can parse in one read to recommend skills — no markdown prose parsing required. Contains, per skill: name, category, usefulness tier, usage count, recency, install URL, one-line description. This is what makes the "agents can look through" requirement real. The portfolio README/site renders from the same file so users and agents see the same truth.
_Avoid_: a markdown-only index (agents must parse prose), a separate hand-maintained index that drifts from the actual skill directories.

**Finish Line**:
The portfolio is "done" when all seven are true: (1) the monorepo exists on Forgejo with ~50 skill directories, each with a passing Hallmark README + SKILL.md with required frontmatter; (2) `skills-index.json` exists at the repo root, in sync with all skill directories, with tier assignments and categories filled in; (3) the portfolio-level Hallmark README exists at the repo root, rendering from `skills-index.json` with sort/filter guidance; (4) the Forgejo Pages-style static site renders the README content as browseable HTML at a localhost URL; (5) the GitHub shopfront repo (under Monica Amano) mirrors the monorepo and is public; (6) the `skill-publish` skill exists in the portfolio and has been used at least once successfully (dogfooded); (7) a CI workflow lints every SKILL.md frontmatter and validates `skills-index.json` sync. Locked 2026-07-20.
_Avoid_: "done when all 50 skills are written" (skips index/site/CI/dogfood), "done when GitHub repo is public" (skips Forgejo review surface + dogfood).

**Build Order**:
Five phases, each producing a reviewable checkpoint before the next begins. Phase 1: scaffold + meta (monorepo structure, Forgejo remote, portfolio Hallmark README skeleton, `skills-index.json` schema, CI lint workflow, Pages static-site skeleton — no skills yet). Phase 2: Core tier skills (~10, highest usefulness first). Phase 3: Featured tier skills (~20, category-fill). Phase 4: Utility tier skills (~20, long tail including adapted third-party with attribution). Phase 5: GitHub shopfront mirror + per-skill publish dogfood (push monorepo to Monica Amano's GitHub, run `skill-publish` on one skill to verify the per-skill flow end-to-end). Locked 2026-07-20.
_Avoid_: all-at-once (no course-correction until 50 skills are done), skills-first-then-scaffold (skills drift in format, index becomes a retrofit), alphabetical/category-order build (weakest skills get same effort as strongest), single-phase with no checkpoints (violates Owen's standing review-in-runnable-form rule).
