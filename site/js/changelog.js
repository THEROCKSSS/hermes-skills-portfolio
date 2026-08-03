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
//
// Phase 6 additions, all reading that same selection:
//   - "Copy as Markdown" — a dated Markdown block for docs/issues.
//   - "Copy release body" — a GitHub-release-shaped body for the selection.
//   - a date-range picker that selects every entry between two dates, alongside
//     the per-entry checkboxes (union with whatever is already ticked).
//   - a link to feed.xml, the Atom feed scripts/generate_feed.py derives from
//     the SAME changelog-data.js array this page renders.
// The toolbar markup for these is created here rather than in changelog.html so
// the page keeps one owner for the feature; every control is a real <button>
// (or a labelled native <input type="date">), never a hover-only affordance.
(function () {
  "use strict";

  // The Atom feed names each entry `<changelog.html>#commit-<hash>`, which only
  // resolves if the rendered row carries that id — so entry ids are emitted as
  // real DOM ids below and reused verbatim by the feed generator.
  var FEED_HREF = "./feed.xml";
  var MD_LABEL = "Copy as Markdown";
  var RELEASE_LABEL = "Copy release body";

  // Source: `git log --pretty=format:"%ad|%h|%s" --date=format:"%Y-%m-%d %H:%M" -- site/
  // skills-index.json README.md CONTRIBUTING.md`, run 2026-07-29 against this repo.
  // date/time/hash are copied verbatim from that output; "text" is a present-tense
  // rewrite of the commit subject (and, for the three tier-launch commits, of the skill
  // names already listed in that same subject line — no names added beyond what the
  // commit itself named).
  var COMMITS = (window.HermesChangelog && window.HermesChangelog.COMMITS) || [];

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
          '<div class="changelog-entry reveal" id="' + escapeHtml(e.id) + '">' +
            '<label class="changelog-entry-select">' +
              '<input type="checkbox" class="changelog-checkbox" ' +
                'data-entry-id="' + escapeHtml(e.id) + '" ' +
                'data-entry-text="' + escapeHtml(e.text) + '" ' +
                'data-entry-date="' + escapeHtml(e.date) + '" ' +
                'data-entry-tag="' + escapeHtml(e.tag) + '" ' +
                'data-entry-kind="' + escapeHtml(e.kind) + '" ' +
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

  // Selected rows in page order (newest first), carrying only strings already
  // rendered on the page — never re-derived or embellished.
  function selectedEntries() {
    return allCheckboxes()
      .filter(function (cb) { return !!selected[cb.getAttribute("data-entry-id")]; })
      .map(function (cb) {
        return {
          id: cb.getAttribute("data-entry-id"),
          text: cb.getAttribute("data-entry-text"),
          date: cb.getAttribute("data-entry-date"),
          tag: cb.getAttribute("data-entry-tag"),
          kind: cb.getAttribute("data-entry-kind")
        };
      });
  }

  function setDisabled(btn, isDisabled) {
    if (!btn) return;
    btn.disabled = isDisabled;
    btn.setAttribute("aria-disabled", String(isDisabled));
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
    setDisabled(copyBtn, isDisabled);
    setDisabled(document.getElementById("changelog-md-btn"), isDisabled);
    setDisabled(document.getElementById("changelog-release-btn"), isDisabled);

    var allSelected = boxes.length > 0 && n === boxes.length;
    toggleBtn.textContent = allSelected ? "Clear" : "Select all";

    updateRangeButton();
  }

  // ---- Export formats ----
  // Each format is built from the selected rows' own text/date/tag. The tag is a
  // real commit hash for commit rows and "skills-index.json" for the computed
  // skill-addition rows, so only commit rows get a hash in the output.
  function entryTag(entry) {
    return entry.kind === "commit" ? " (`" + entry.tag + "`)" : "";
  }

  function toMarkdown(entries) {
    var out = ["## Hermes Skills Portfolio — updates", ""];
    var lastDate = null;
    entries.forEach(function (e) {
      if (e.date !== lastDate) {
        if (lastDate !== null) out.push("");
        out.push("### " + e.date);
        lastDate = e.date;
      }
      out.push("- " + e.text + entryTag(e));
    });
    return out.join("\n");
  }

  function toReleaseBody(entries) {
    var out = ["## What's changed", ""];
    entries.forEach(function (e) {
      out.push("- " + e.text + entryTag(e) + " — " + e.date);
    });
    out.push("");
    out.push("**Full changelog:** " + location.href.split("#")[0]);
    return out.join("\n");
  }

  function copySelection(btn, build, label, noun) {
    var entries = selectedEntries();
    if (!entries.length || !window.HermesCommon) return;
    window.HermesCommon.copyToClipboard(build(entries), btn, {
      restoreLabel: label,
      toastMsg: entries.length + " entr" + (entries.length === 1 ? "y" : "ies") + " copied as " + noun
    });
  }

  // ---- Date-range selection ----
  function rangeInputs() {
    return {
      from: document.getElementById("changelog-range-from"),
      to: document.getElementById("changelog-range-to"),
      btn: document.getElementById("changelog-range-btn")
    };
  }

  function updateRangeButton() {
    var els = rangeInputs();
    if (!els.btn) return;
    var hasBound = !!((els.from && els.from.value) || (els.to && els.to.value));
    setDisabled(els.btn, !hasBound);
  }

  // Selects every entry whose date falls inside the range, in addition to
  // whatever is already ticked (a union, so it never silently drops a manual
  // pick). ISO dates compare correctly as plain strings.
  function applyRange() {
    var els = rangeInputs();
    if (!els.from || !els.to) return;
    var from = els.from.value;
    var to = els.to.value;
    if (!from && !to) return;
    if (from && to && from > to) { var swap = from; from = to; to = swap; }

    var matched = 0;
    allCheckboxes().forEach(function (cb) {
      var date = cb.getAttribute("data-entry-date");
      if (from && date < from) return;
      if (to && date > to) return;
      matched++;
      cb.checked = true;
      selected[cb.getAttribute("data-entry-id")] = true;
    });
    updateToolbar();

    if (window.HermesCommon) {
      var span = (from || "the start") + " to " + (to || "the latest entry");
      window.HermesCommon.showToast(
        matched
          ? matched + " entr" + (matched === 1 ? "y" : "ies") + " selected — " + span
          : "No entries between " + span
      );
    }
  }

  // ---- Toolbar controls created here (changelog.html owns only the base bar) ----
  function buildExtraControls(groups) {
    var toolbar = document.getElementById("changelog-toolbar");
    if (!toolbar || document.getElementById("changelog-toolbar-more")) return;
    var actions = toolbar.querySelector(".changelog-toolbar-actions");
    if (!actions) return;

    function makeButton(id, label, title) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.id = id;
      btn.className = "btn btn-outline changelog-export-btn";
      btn.textContent = label;
      btn.title = title;
      btn.disabled = true;
      btn.setAttribute("aria-disabled", "true");
      actions.appendChild(btn);
      return btn;
    }
    makeButton("changelog-md-btn", MD_LABEL, "Copy the selected entries as Markdown");
    makeButton("changelog-release-btn", RELEASE_LABEL, "Copy the selected entries as a GitHub release body");

    // Real dates from the rendered rows bound the pickers, so the control can
    // never offer a range the log does not cover.
    var dates = groups.map(function (g) { return g.date; }).sort();
    var earliest = dates[0] || "";
    var latest = dates[dates.length - 1] || "";

    var more = document.createElement("div");
    more.className = "changelog-toolbar-more";
    more.id = "changelog-toolbar-more";
    more.innerHTML =
      '<div class="changelog-range" role="group" aria-labelledby="changelog-range-legend">' +
        '<span class="changelog-range-legend mono" id="changelog-range-legend">Date range</span>' +
        '<label class="changelog-range-field" for="changelog-range-from">' +
          '<span class="changelog-range-label">From</span>' +
          '<input class="changelog-range-input" type="date" id="changelog-range-from" />' +
        '</label>' +
        '<label class="changelog-range-field" for="changelog-range-to">' +
          '<span class="changelog-range-label">To</span>' +
          '<input class="changelog-range-input" type="date" id="changelog-range-to" />' +
        '</label>' +
        '<button type="button" class="btn btn-outline changelog-range-btn" id="changelog-range-btn" ' +
          'disabled aria-disabled="true" title="Select every entry between these two dates">Select range</button>' +
      '</div>' +
      '<a class="changelog-feed-link" id="changelog-feed-link" href="' + FEED_HREF + '" ' +
        'type="application/atom+xml" rel="alternate">' +
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
          '<path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1.6"/>' +
        '</svg>' +
        'Atom feed' +
      '</a>';
    toolbar.appendChild(more);

    var els = rangeInputs();
    [els.from, els.to].forEach(function (input) {
      if (!input || !earliest || !latest) return;
      input.min = earliest;
      input.max = latest;
    });
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
        var lines = selectedEntries().map(function (e) {
          return "- " + e.text + " (" + e.date + ")";
        });
        var text = "**Hermes Skills Portfolio — updates**\n" + lines.join("\n");
        var toastMsg = n + " entr" + (n === 1 ? "y" : "ies") + " copied";
        window.HermesCommon.copyToClipboard(text, copyBtn, {
          restoreLabel: "Copy selected",
          toastMsg: toastMsg
        });
      });
    }

    var mdBtn = document.getElementById("changelog-md-btn");
    if (mdBtn) {
      mdBtn.addEventListener("click", function () {
        copySelection(mdBtn, toMarkdown, MD_LABEL, "Markdown");
      });
    }
    var releaseBtn = document.getElementById("changelog-release-btn");
    if (releaseBtn) {
      releaseBtn.addEventListener("click", function () {
        copySelection(releaseBtn, toReleaseBody, RELEASE_LABEL, "a release body");
      });
    }

    var els = rangeInputs();
    if (els.btn) els.btn.addEventListener("click", applyRange);
    [els.from, els.to].forEach(function (input) {
      if (input) input.addEventListener("change", updateRangeButton);
    });
  }

  function init() {
    if (!window.HermesCommon) return;
    window.HermesCommon.loadIndex(function (data) {
      var groups = buildGroups(data);
      renderGroups(groups);
      buildExtraControls(groups);
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
