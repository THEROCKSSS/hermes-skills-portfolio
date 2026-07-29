// Hermes Skills Portfolio — Changelog (Index-First macrostructure)
// Renders a dated, hairline-ruled log from two REAL sources only:
//   1. COMMITS below — real, dated commits from `git log` on site/, skills-index.json,
//      README.md, CONTRIBUTING.md, rewritten from the terse commit subject into a clean
//      present-tense line. No fact is added that the commit message did not already state.
//   2. Skill-addition entries — computed at render time from the live skills-index.json
//      `recency` field (never hardcoded), so the count and names always match the real data.
//
// Also wires a session-only selection feature: a checkbox per entry + a sticky toolbar
// that copies the selected entries' real text + real date as a Discord-friendly plain-text
// block via HermesCommon.copyToClipboard. No entry text is invented — only the exact
// strings already rendered on the page are read back for the copy payload.
(function () {
  "use strict";

  // Source: `git log --pretty=format:"%ad|%h|%s" --date=format:"%Y-%m-%d %H:%M" -- site/
  // skills-index.json README.md CONTRIBUTING.md`, run 2026-07-29 against this repo.
  // date/time/hash are copied verbatim from that output; "text" is a present-tense
  // rewrite of the commit subject (and, for the three tier-launch commits, of the skill
  // names already listed in that same subject line — no names added beyond what the
  // commit itself named).
  var COMMITS = [
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
  ];

  function escapeHtml(s) {
    return window.HermesCommon ? window.HermesCommon.escapeHtml(s) : String(s);
  }

  // Group entries (commits + recency-derived skill-addition rows) by date, newest first.
  // Each entry carries a stable id (commit hash / recency date — both already unique in
  // this dataset) plus its exact display text and date, so the selection/copy feature
  // reads back real page content rather than re-deriving it.
  function buildGroups(indexData) {
    var byDate = {};

    function ensureDate(d) {
      if (!byDate[d]) byDate[d] = [];
      return byDate[d];
    }

    COMMITS.forEach(function (c) {
      ensureDate(c.date).push({
        kind: "commit",
        id: "commit-" + c.hash,
        sortKey: c.date + " " + c.time,
        tag: c.hash,
        text: c.text,
        date: c.date,
        html: escapeHtml(c.text)
      });
    });

    // Skills-added entries: computed live from skills-index.json `recency`, never hardcoded.
    var skills = (indexData && indexData.skills) || [];
    var byRecency = {};
    skills.forEach(function (s) {
      if (!s || !s.recency) return;
      if (!byRecency[s.recency]) byRecency[s.recency] = [];
      byRecency[s.recency].push(s.name);
    });
    Object.keys(byRecency).forEach(function (date) {
      var names = byRecency[date].slice().sort();
      var count = names.length;
      var label = count + " new skill" + (count === 1 ? "" : "s") + " added: " + names.join(", ") + ".";
      ensureDate(date).push({
        kind: "skills",
        id: "skills-" + date,
        sortKey: date + " 99:99", // recency has no time-of-day; place last within its date
        tag: "skills-index.json",
        text: label,
        date: date,
        html: escapeHtml(label)
      });
    });

    var dates = Object.keys(byDate).sort(function (a, b) { return a < b ? 1 : a > b ? -1 : 0; });
    return dates.map(function (date) {
      var entries = byDate[date].slice().sort(function (a, b) {
        return a.sortKey < b.sortKey ? 1 : a.sortKey > b.sortKey ? -1 : 0;
      });
      return { date: date, entries: entries };
    });
  }

  function renderGroups(groups) {
    var root = document.getElementById("changelog-groups");
    if (!groups.length) {
      root.innerHTML = '<p class="changelog-empty">No dated history is available yet.</p>';
      return;
    }
    root.innerHTML = groups.map(function (g) {
      var rows = g.entries.map(function (e) {
        var tagClass = e.kind === "skills" ? "changelog-entry-tag is-skills" : "changelog-entry-tag";
        var checkLabel = "Select entry for " + e.date + ": " + e.text;
        return (
          '<div class="changelog-entry reveal">' +
            '<label class="changelog-entry-select">' +
              '<input type="checkbox" class="changelog-checkbox" ' +
                'data-entry-id="' + escapeHtml(e.id) + '" ' +
                'data-entry-text="' + escapeHtml(e.text) + '" ' +
                'data-entry-date="' + escapeHtml(e.date) + '" ' +
                'aria-label="' + escapeHtml(checkLabel) + '" />' +
            '</label>' +
            '<div class="changelog-entry-content">' +
              '<div class="' + tagClass + ' mono">' + escapeHtml(e.tag) + '</div>' +
              '<div class="changelog-entry-body"><p class="changelog-entry-text">' + e.html + '</p></div>' +
            '</div>' +
          '</div>'
        );
      }).join("");
      return (
        '<section class="changelog-group">' +
          '<div class="changelog-date">' +
            '<span class="changelog-date-label mono">' + escapeHtml(g.date) + '</span>' +
            '<span class="changelog-date-count">' + g.entries.length + ' change' + (g.entries.length === 1 ? "" : "s") + '</span>' +
          '</div>' +
          rows +
        '</section>'
      );
    }).join("");
  }

  // ---- Selection + "copy selected as Discord text" toolbar ----
  // Session-only: a plain in-memory Set, no persistence across reloads (matches spec).
  var selected = {}; // entryId -> true

  function allCheckboxes() {
    return Array.prototype.slice.call(document.querySelectorAll(".changelog-checkbox"));
  }

  function selectedCount() {
    return Object.keys(selected).length;
  }

  function updateToolbar() {
    var countEl = document.getElementById("changelog-toolbar-count");
    var copyBtn = document.getElementById("changelog-copy-btn");
    var toggleBtn = document.getElementById("changelog-toggle-btn");
    if (!countEl || !copyBtn || !toggleBtn) return;

    var boxes = allCheckboxes();
    var n = selectedCount();
    countEl.textContent = n + " selected";

    var isDisabled = n === 0;
    copyBtn.disabled = isDisabled;
    copyBtn.setAttribute("aria-disabled", String(isDisabled));

    var allSelected = boxes.length > 0 && n === boxes.length;
    toggleBtn.textContent = allSelected ? "Clear" : "Select all";
  }

  function wireSelection() {
    var root = document.getElementById("changelog-groups");
    if (!root) return;
    root.addEventListener("change", function (e) {
      var cb = e.target.closest ? e.target.closest(".changelog-checkbox") : null;
      if (!cb) return;
      var id = cb.getAttribute("data-entry-id");
      if (cb.checked) selected[id] = true;
      else delete selected[id];
      updateToolbar();
    });
  }

  function wireToolbar() {
    var toggleBtn = document.getElementById("changelog-toggle-btn");
    var copyBtn = document.getElementById("changelog-copy-btn");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        var boxes = allCheckboxes();
        var allSelected = boxes.length > 0 && selectedCount() === boxes.length;
        boxes.forEach(function (cb) {
          cb.checked = !allSelected;
          var id = cb.getAttribute("data-entry-id");
          if (!allSelected) selected[id] = true;
          else delete selected[id];
        });
        updateToolbar();
      });
    }
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var n = selectedCount();
        if (!n || !window.HermesCommon) return;
        var lines = allCheckboxes()
          .filter(function (cb) { return !!selected[cb.getAttribute("data-entry-id")]; })
          .map(function (cb) {
            return "- " + cb.getAttribute("data-entry-text") + " (" + cb.getAttribute("data-entry-date") + ")";
          });
        var text = "**Hermes Skills Portfolio — updates**\n" + lines.join("\n");
        var toastMsg = n + " entr" + (n === 1 ? "y" : "ies") + " copied";
        window.HermesCommon.copyToClipboard(text, copyBtn, {
          restoreLabel: "Copy selected",
          toastMsg: toastMsg
        });
      });
    }
  }

  function init() {
    if (!window.HermesCommon) return;
    window.HermesCommon.loadIndex(function (data) {
      var groups = buildGroups(data);
      renderGroups(groups);
      window.HermesCommon.initCmdk(data || { skills: [] });
      window.HermesCommon.initReveal(document);
      wireSelection();
      wireToolbar();
      updateToolbar();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
