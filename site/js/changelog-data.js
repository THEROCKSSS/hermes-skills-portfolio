// Hermes Skills Portfolio — changelog source data (shared).
//
// Extracted from changelog.js so the catalog page's "What's new" feed and the
// full changelog page read the SAME array instead of keeping two copies that
// drift. Adding an entry here updates both surfaces at once.
//
  // Source: `git log --pretty=format:"%ad|%h|%s" --date=format:"%Y-%m-%d %H:%M" -- site/
  // skills-index.json README.md CONTRIBUTING.md`, run 2026-07-29 against this repo.
  // date/time/hash are copied verbatim from that output; "text" is a present-tense
  // rewrite of the commit subject (and, for the three tier-launch commits, of the skill
  // names already listed in that same subject line — no names added beyond what the
  // commit itself named).
window.HermesChangelog = {
  COMMITS: [
    { date: "2026-08-03", time: "16:27", hash: "fde09ae",
      text: "Re-themes the site to Dusk with a persistent sidebar-filter catalog, adds a submission and review pipeline, and makes the stale-content-cache check blocking in CI. Catalog reaches 57 skills." },
    { date: "2026-07-29", time: "17:57", hash: "649bda9",
      text: "Fixes CI to check every real file instead of 4 hardcoded ones (2 already dead), deletes the dead files, adds a real site-to-docs sync script, and consolidates a fetch-with-fallback pattern that was duplicated in three files." },
    { date: "2026-07-29", time: "17:19", hash: "21772ec",
      text: "Fixes CI: stops quoting the forbidden-reference patterns inside AGENTS.md, which had been tripping the same check it was describing." },
    { date: "2026-07-29", time: "17:18", hash: "7232b74",
      text: "Adds project foundation docs (CLAUDE.md, ARCHITECTURE.md, CHANGELOG.md) and fixes a reveal-on-scroll bug that kept the Submit page's pending-sources section permanently invisible." },
    { date: "2026-07-29", time: "16:58", hash: "3fe43b7",
      text: "Redesigns the entire site with the Cobalt design system across four pages (Catalog, Bundles, Changelog, Submit), rewrites all 51 skill docs to the real Hermes skill schema, and adds a curated-bundles page plus an external-sourcing review pipeline." },
    { date: "2026-07-20", time: "23:49", hash: "37761f6",
      text: "Reverts to a popup overlay for skill clicks, keeping standalone pages for crawlers and share links." },
    { date: "2026-07-20", time: "23:35", hash: "ddffdf5",
      text: "Skill cards now link to real /skills/<name>/ pages; old #skill/ hash links redirect." },
    { date: "2026-07-20", time: "23:27", hash: "5a5f5ec",
      text: "Adds shareable per-skill pages, a star badge, tooltip enhancements, provenance info, and CI validation." },
    { date: "2026-07-20", time: "20:02", hash: "19518fd",
      text: "Fixes CI: removes forgejo_url, fixes a trailing comma, scopes the forbidden-reference check." },
    { date: "2026-07-20", time: "19:55", hash: "87707e7",
      text: "Professionalizes the GitHub repo; adds a distribution-bar hover popup and an index." },
    { date: "2026-07-20", time: "19:15", hash: "22acd32",
      text: "Redesigns the page: merges search and controls into the masthead, adds source attribution links." },
    { date: "2026-07-20", time: "19:02", hash: "f4c3646",
      text: "Cleans up search bar spacing and changes attribution to Owen." },
    { date: "2026-07-20", time: "18:44", hash: "a28bccb",
      text: "Fixes skill cards so they actually open the detail overlay on click." },
    { date: "2026-07-20", time: "04:05", hash: "28893e9",
      text: "Fixes skill card links to use proper <a href> hash links so clicking reliably opens the detail overlay." },
    { date: "2026-07-20", time: "03:56", hash: "c664d28",
      text: "Adds a detail overlay with Overview / SKILL.md / README tabs, renders SKILL.md on-site, sets dark mode as the default with a light toggle, adds copy-to-clipboard, and adds the portfolio-upkeep skill — the catalog reaches 51 skills." },
    { date: "2026-07-20", time: "03:45", hash: "62505c9",
      text: "Adds keyboard shortcuts, URL hash state, filter chips, a distribution bar, back-to-top, and toast notifications; applies OKLCH tokens and refined motion." },
    { date: "2026-07-20", time: "03:24", hash: "915c42c",
      text: "Enhances the portfolio site with high-detail expandable skill cards, multi-path data fetch, and sort/filter/search across 50 skills." },
    { date: "2026-07-20", time: "03:02", hash: "362ab42",
      text: "Updates GitHub URLs across all 50 skill files, the README, and skills-index.json to the authenticated account." },
    { date: "2026-07-20", time: "02:54", hash: "5e654db",
      text: "Adds the Utility tier — 20 skills: pdf-extract, ocr-documents, gif-search, youtube-transcript, ascii-art, excalidraw-diagram, markdown-to-pdf, env-config-manager, http-api-tester, csv-toolkit, qr-code-generator, log-analyzer, password-generator, json-formatter, regex-tester, file-organizer, changelog-generator, color-palette-generator, snippet-manager, markdown-linter. Catalog reaches 50 skills." },
    { date: "2026-07-20", time: "02:01", hash: "42e57a9",
      text: "Adds the Featured tier — 20 skills: mcp-server-build, webhook-receiver, cron-task, discord-bot-build, telegram-bot-build, ollama-local, searxng-self-host, uptime-kuma-self-host, ntfy-notifier, git-backup, dotfiles-manage, resume-builder, invoice-generator, caddy-reverse-proxy, sqlite-dashboard, markdown-to-slides, github-actions-ci, openapi-generator, email-send, rss-monitor. Catalog reaches 30 skills." },
    { date: "2026-07-20", time: "00:48", hash: "367263e",
      text: "Adds the Core tier — 10 skills: tailscale-deploy, hallmark-readme, generate-dockerfile, forgejo-self-host, skill-publish, frontend-design-toolkit, hermes-portfolio-template, docker-umbrella, api-test-suite, skill-registry-catalog." },
    { date: "2026-07-20", time: "00:26", hash: "7f3c7f5",
      text: "Scaffolds the monorepo: skills-index.json schema, CI lint, the Pages site skeleton, the Hallmark README, four ADRs, and the CONTEXT.md glossary." }
  ]
};
