# Changelog

All notable changes to the Hermes Skills Portfolio. Generated from real git history and skills-index.json — no invented entries. The live, browsable version is at /changelog.html.

## 2026-07-29

- `3fe43b7` Redesigns the entire site with the Cobalt design system across four pages (Catalog, Bundles, Changelog, Submit), rewrites all 51 skill docs to the real Hermes skill schema, and adds a curated-bundles page plus an external-sourcing review pipeline.

## 2026-07-20

- `37761f6` Reverts to a popup overlay for skill clicks, keeping standalone pages for crawlers and share links.
- `ddffdf5` Skill cards now link to real /skills/<name>/ pages; old #skill/ hash links redirect.
- `5a5f5ec` Adds shareable per-skill pages, a star badge, tooltip enhancements, provenance info, and CI validation.
- `19518fd` Fixes CI: removes forgejo_url, fixes a trailing comma, scopes the forbidden-reference check.
- `87707e7` Professionalizes the GitHub repo; adds a distribution-bar hover popup and an index.
- `22acd32` Redesigns the page: merges search and controls into the masthead, adds source attribution links.
- `f4c3646` Cleans up search bar spacing and changes attribution to Owen.
- `a28bccb` Fixes skill cards so they actually open the detail overlay on click.
- `28893e9` Fixes skill card links to use proper <a href> hash links so clicking reliably opens the detail overlay.
- `c664d28` Adds a detail overlay with Overview / SKILL.md / README tabs, renders SKILL.md on-site, sets dark mode as the default with a light toggle, adds copy-to-clipboard, and adds the portfolio-upkeep skill — the catalog reaches 51 skills.
- `62505c9` Adds keyboard shortcuts, URL hash state, filter chips, a distribution bar, back-to-top, and toast notifications; applies OKLCH tokens and refined motion.
- `915c42c` Enhances the portfolio site with high-detail expandable skill cards, multi-path data fetch, and sort/filter/search across 50 skills.
- `362ab42` Updates GitHub URLs across all 50 skill files, the README, and skills-index.json to the authenticated account.
- `5e654db` Adds the Utility tier — 20 skills: pdf-extract, ocr-documents, gif-search, youtube-transcript, ascii-art, excalidraw-diagram, markdown-to-pdf, env-config-manager, http-api-tester, csv-toolkit, qr-code-generator, log-analyzer, password-generator, json-formatter, regex-tester, file-organizer, changelog-generator, color-palette-generator, snippet-manager, markdown-linter. Catalog reaches 50 skills.
- `42e57a9` Adds the Featured tier — 20 skills: mcp-server-build, webhook-receiver, cron-task, discord-bot-build, telegram-bot-build, ollama-local, searxng-self-host, uptime-kuma-self-host, ntfy-notifier, git-backup, dotfiles-manage, resume-builder, invoice-generator, caddy-reverse-proxy, sqlite-dashboard, markdown-to-slides, github-actions-ci, openapi-generator, email-send, rss-monitor. Catalog reaches 30 skills.
- `367263e` Adds the Core tier — 10 skills: tailscale-deploy, hallmark-readme, generate-dockerfile, forgejo-self-host, skill-publish, frontend-design-toolkit, hermes-portfolio-template, docker-umbrella, api-test-suite, skill-registry-catalog.
- `7f3c7f5` Scaffolds the monorepo: skills-index.json schema, CI lint, the Pages site skeleton, the Hallmark README, four ADRs, and the CONTEXT.md glossary.
- 51 new skill(s) added: api-test-suite, ascii-art, caddy-reverse-proxy, changelog-generator, color-palette-generator, cron-task, csv-toolkit, discord-bot-build, docker-umbrella, dotfiles-manage, email-send, env-config-manager, excalidraw-diagram, file-organizer, forgejo-self-host, frontend-design-toolkit, generate-dockerfile, gif-search, git-backup, github-actions-ci, hallmark-readme, http-api-tester, invoice-generator, json-formatter, log-analyzer, markdown-linter, markdown-to-pdf, markdown-to-slides, mcp-server-build, ntfy-notifier, ocr-documents, ollama-local, openapi-generator, password-generator, pdf-extract, portfolio-upkeep, qr-code-generator, regex-tester, resume-builder, rss-monitor, searxng-self-host, skill-publish, skill-registry-catalog, skills-portfolio-scaffold, snippet-manager, sqlite-dashboard, tailscale-deploy, telegram-bot-build, uptime-kuma-self-host, webhook-receiver, youtube-transcript

