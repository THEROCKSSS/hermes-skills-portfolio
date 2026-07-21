# Contributing to Hermes Skills Portfolio

Thank you for your interest in contributing! This portfolio accepts new skills, improvements to existing skills, and site enhancements.

## Adding a New Skill

1. **Check existing skills** — avoid duplicates. Search `skills/` and `skills-index.json`.
2. **Create the skill directory**: `skills/<your-skill-name>/`
   - Use lowercase, hyphenated names (e.g., `log-analyzer`, not `LogAnalyzer`).
3. **Write `SKILL.md`** — the agent-facing instructions. Required frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: "One-line description of what the skill does."
   version: 1.0.0
   ---
   ```
   The body should include: When to Use, What It Does, Step-by-step instructions, Pitfalls, and Verification.
4. **Write `README.md`** — the human-facing documentation. Should explain what the skill does, why it exists, how to install it, and a quick-start example.
5. **Add to `skills-index.json`** — add an entry with: `name`, `category`, `tier`, `description`, `install_url`, `source` (`new` / `generalized` / `adapted`), `agent_use`, `user_use`, and the content fields.
6. **Sync the site** — if you changed `site/`, copy to `docs/`: `cp site/* docs/`.
7. **Test locally** — open `docs/index.html` in a browser. Verify your skill appears, the detail page opens, and all content renders.

## Skill Quality Standards

- **Empowering**: the skill should help a user or agent accomplish a real task.
- **Self-contained**: no dependencies on private infrastructure or internal tools.
- **Runnable**: instructions should produce a working result, not just describe one.
- **Honest**: no invented metrics, no fabricated testimonials, no AI-slop phrasing.
- **Attributed**: if adapted from another source, credit it in `source_attribution`.

## Categories and Tiers

| Category | Description |
|---|---|
| DevOps & Infrastructure | Deployment, hosting, networking, monitoring |
| Backend | APIs, databases, server-side logic |
| Frontend | UI, design, client-side work |
| Integrations | Third-party services, bots, webhooks |
| Utility | General-purpose tools and helpers |
| Meta | Skills about skills, portfolios, workflows |

| Tier | Meaning |
|---|---|
| Core | Broadly empowering — nearly any user benefits |
| Featured | Highly useful within a category |
| Utility | Useful for specific workflows |

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b add-my-skill`.
2. Make your changes following the steps above.
3. Verify CI passes (frontmatter validation + index sync check).
4. Open a PR with a clear title and description.
5. Link any related issues.

## Site Enhancements

The static site (`site/` + `docs/`) is plain HTML/CSS/JS — no framework, no build step. If you're adding features:
- Keep it framework-free. No React, no Vue, no npm dependencies.
- Dark mode is the default. Use OKLCH tokens from `:root`.
- Test at 320px, 768px, and desktop widths.
- Sync `site/` to `docs/` before committing.

## Code of Conduct

Be respectful, constructive, and inclusive. We're building tools that empower people.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
