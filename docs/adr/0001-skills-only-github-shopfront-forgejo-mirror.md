# 0001: Skills-only portfolio, GitHub as shopfront, Forgejo as local mirror

The portfolio is skills-only (no reference projects). The primary shopfront is a dedicated public GitHub repo with highly-detailed Hallmark-quality READMEs. The same content is deployed locally through the user's Forgejo instance at localhost:3000 as a review/staging surface. `hermes skills publish` to the Hermes hub is an optional add-on, not the primary channel.

## Considered Options

- **A. Dual track (skills + reference projects), hub publish.** Rejected: Owen dropped the projects track; reference apps are a second job and dilute the pitch.
- **B. Skills-only, hub publish only.** Rejected: the hub alone undersells the dedicated-shopfront requirement and limits discoverability — most people browse GitHub, not the Hermes hub.
- **C. Skills-only, GitHub shopfront + Forgejo local mirror, Hallmark READMEs.** Accepted. GitHub is the primary surface for the public; Forgejo is the local review/staging surface Owen already uses for every other project; Hallmark enforces a non-generic README quality bar.
- **D. Skills-only, GitHub only.** Rejected: loses the local review/staging surface Owen works through, and breaks the established commit-and-review-on-Forgejo workflow.

## Consequences

- Each skill gets two remotes: `origin` (public GitHub) and `forgejo` (localhost:3000). Push flow is `git push origin && git push forgejo`.
- READMEs are a first-class deliverable, not an afterthought — Hallmark is in the critical path for every skill.
- The Hermes hub is not a blocker for publishing; a skill is "published" when its GitHub repo is public and the README passes Hallmark.
- If the Hermes hub later becomes a desired channel, `hermes skills publish <path>` works without restructuring — it reads SKILL.md from the repo.
