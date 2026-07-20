# 0002: Three-surface repo architecture — Forgejo monorepo, GitHub shopfront, optional per-skill publish

The portfolio uses three distinct surfaces:

1. **Local Forgejo (localhost:3000)** — a single monorepo (`agentsoul/hermes-skills-portfolio` or similar) containing all skills, one top-level directory per skill, plus the portfolio README, CONTEXT.md, docs/adr/, and the Pages static site. This is the only local structure. Every skill change is a visible commit Owen can review, and the Pages build renders the README locally for browser verification before public push.

2. **GitHub shopfront (primary public surface)** — a single GitHub repo under Monica Amano's name that mirrors the monorepo content and serves as the portfolio shopfront with a Hallmark README. This is NOT one-repo-per-skill. Stars accumulate here.

3. **Per-skill publish (optional, on-demand)** — when the user gives a prompt naming one skill, that skill is pushed from the monorepo into its own dedicated GitHub repo with its own Hallmark README/page. Triggered only by an explicit prompt. This is a capability layered on top of the monorepo, not the default structure.

## Considered Options

- **A. One repo per skill (everywhere).** Rejected by Owen: "I do not like that." Dilutes stars, multiplies CI/Pages setup, breaks the single-shopfront README requirement.
- **B. Monorepo only (Forgejo + GitHub mirror, no per-skill).** Rejected: loses the flexibility to give a single skill its own dedicated page/repo when the user wants to spotlight it.
- **C. Three-surface (Forgejo monorepo + GitHub shopfront + optional per-skill publish).** Accepted. Monorepo leverage locally and on the primary GitHub repo; per-skill publish as an on-demand capability when the user wants to spotlight one skill. Matches Owen's explicit requirements.
- **D. Umbrella repo + git submodules.** Rejected: submodule complexity for no gain at this scale; known contributor footgun.

## Consequences

- The monorepo is the source of truth. Per-skill GitHub repos, when created, are derived artifacts — they pull from the monorepo's skill directory, not the other way around.
- Push flow: `git push forgejo` (local review) → `git push origin` (public GitHub shopfront) → optional `git push <skill-repo>` (per-skill spotlight, only when triggered).
- The per-skill publish flow needs a script or prompt-driven workflow that extracts one skill directory and pushes it to its own repo with a self-contained Hallmark README. This is a build-time concern, not a structural one.
- Stars concentrate on the GitHub shopfront, directly serving the high-star goal.
- A stranger can `git clone` the shopfront and get all skills, or `hermes skills install <url>` a single skill from within it. Both paths work.
