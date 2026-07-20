# 0004: Five-phase build order with reviewable checkpoints

The portfolio is built in five phases, each producing a reviewable checkpoint before the next begins:

1. **Phase 1 — Scaffold + meta:** monorepo structure, Forgejo remote, portfolio Hallmark README skeleton, `skills-index.json` schema, CI lint workflow, Pages static-site skeleton. No skills yet. Reviewable after Phase 1 — Owen sees the skeleton, the README, the Pages site, the CI before any skill is authored.

2. **Phase 2 — Core tier skills (~10):** the highest-usefulness skills first (tailscale-deploy, hallmark-readme, generate-dockerfile, forgejo-self-host, skill-publish, frontend-design-toolkit, hermes-portfolio-template, docker-umbrella, api-test-suite-gen, skill-registry-catalog). Each goes through the grilling/refining process. Reviewable after Phase 2.

3. **Phase 3 — Featured tier skills (~20):** category-fill skills at Featured tier. Bulk of the new-authoring and adaptation work.

4. **Phase 4 — Utility tier skills (~20):** the long tail. Includes adapted third-party skills with attribution.

5. **Phase 5 — GitHub shopfront mirror + per-skill publish dogfood:** push the monorepo to Monica Amano's GitHub, run `skill-publish` on one skill to verify the per-skill flow works end-to-end.

## Considered Options

- **A. All-at-once build.** Rejected: 50 skills with no reviewable skeleton means Owen can't course-correct until 50 skills are done. Too late to fix structural problems.
- **B. Skills-first, scaffold-later.** Rejected: without the `skills-index.json` schema and CI lint locked first, skills drift in format and the index becomes a retrofit. Schema-first is non-negotiable.
- **C. Alphabetical or category-order build.** Rejected: building alphabetically means the weakest skills get the same effort as the strongest. Building tier-order (Core first) means the portfolio's justification is solid before the long tail starts.
- **D. Single phase, no reviewable checkpoints.** Rejected: violates Owen's standing rule that deliverables must be reviewable in a runnable form, not committed unseen.
- **E. Five-phase, tier-order, reviewable checkpoints.** Accepted. Schema-first prevents drift. Core-first means the portfolio's reason-for-existing is solid before the long tail. Checkpoints respect Owen's review rule. Per-skill publish dogfood last because it depends on at least one real skill existing to publish.

## Consequences

- Phase 1 is a hard prerequisite for Phase 2 — the `skills-index.json` schema and CI lint must exist before any skill is authored, so every skill is born in compliance.
- Core tier skills (Phase 2) are the portfolio's justification. If they're not good, the portfolio isn't good — better to find out after 10 skills than after 50.
- Featured and Utility tiers (Phases 3–4) are fill. They can be built in parallel or in batches once the Core tier is locked.
- The per-skill publish dogfood (Phase 5) is the end-to-end verification of the three-surface architecture. If it fails, the architecture needs rework — but only after ~50 skills exist, so the rework cost is bounded.
- Each phase ends with a commit + push to Forgejo so Owen can review at localhost:3000 before the next phase begins, per the established commit-and-review workflow.
