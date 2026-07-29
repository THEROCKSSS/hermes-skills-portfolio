// Submit a skill — page script. Mostly static content; wires the shared
// cmd-k search and the live catalog count into HermesCommon. Does not
// reimplement theme, cmd-k, toast, or reveal — see js/common.js.
(function () {
  "use strict";

  function renderCatalogCount(indexData) {
    var el = document.getElementById("catalog-count");
    if (!el) return;
    if (indexData && Array.isArray(indexData.skills) && indexData.skills.length) {
      el.textContent = String(indexData.skills.length);
    } else {
      el.textContent = "—";
    }
  }

  // --- Pending external sources (Owen's personal review queue — not the
  // catalog). Uses HermesCommon's shared fetch-with-fallback-paths helper
  // (consolidated there after an architecture review found this same ~10
  // lines duplicated verbatim in bundles.js and here). ---
  function loadPendingSources(cb) {
    window.HermesCommon.loadJsonWithFallback(["./pending-sources.json", "../pending-sources.json", "/pending-sources.json"], cb);
  }

  function renderPendingSource(escapeHtml, source) {
    var name = escapeHtml(source.proposed_name || "Untitled proposal");
    var category = escapeHtml(source.proposed_category || "uncategorized");
    var oneLiner = escapeHtml(source.one_liner || "");
    var repoUrl = escapeHtml(source.source_repo_url || "");
    var license = escapeHtml(source.source_license || "Unknown license");
    var dateProposed = escapeHtml(source.date_proposed || "");
    var isRecommended = source.review_recommendation === "recommended";
    var statusClass = isRecommended ? "source-status is-recommended" : "source-status is-needs-review";
    var statusLabel = isRecommended ? "Recommended" : "Needs your review";
    var reviewNote = source.safety_scan && source.safety_scan.notes ? escapeHtml(source.safety_scan.notes) : "";

    return (
      '<li class="pending-item">' +
        '<div class="pending-head">' +
          '<h3 class="pending-name">' + name + "</h3>" +
          '<span class="pending-category mono">' + category + "</span>" +
          '<span class="' + statusClass + ' mono">' + statusLabel + "</span>" +
        "</div>" +
        (oneLiner ? '<p class="pending-desc">' + oneLiner + "</p>" : "") +
        '<div class="pending-meta mono">' +
          (repoUrl ? '<a href="' + repoUrl + '" target="_blank" rel="noopener">' + repoUrl + "</a>" : "") +
          (repoUrl ? '<span class="pending-sep">&middot;</span>' : "") +
          "<span>" + license + "</span>" +
          (dateProposed ? '<span class="pending-sep">&middot;</span><span>Proposed ' + dateProposed + "</span>" : "") +
        "</div>" +
        (reviewNote ? '<p class="pending-note">' + reviewNote + "</p>" : "") +
      "</li>"
    );
  }

  function renderPendingSources(pendingData) {
    var list = document.getElementById("pending-list");
    var summary = document.getElementById("pending-summary");
    if (!list) return;

    // escapeHtml lives on HermesCommon — reuse it rather than reimplementing.
    var escapeHtml = (window.HermesCommon && window.HermesCommon.escapeHtml) || function (s) { return String(s); };

    if (!pendingData) {
      list.innerHTML = '<li class="pending-error">Pending sources couldn&rsquo;t be loaded right now.</li>';
      return;
    }
    var sources = Array.isArray(pendingData.sources) ? pendingData.sources : [];
    if (!sources.length) {
      list.innerHTML = '<li class="pending-empty">Nothing pending review right now.</li>';
      return;
    }
    // Recommended first, then needs-review — both still require Owen's click before anything goes live.
    var sorted = sources.slice().sort(function (a, b) {
      var aRec = a.review_recommendation === "recommended" ? 0 : 1;
      var bRec = b.review_recommendation === "recommended" ? 0 : 1;
      return aRec - bRec;
    });
    var recCount = sources.filter(function (s) { return s.review_recommendation === "recommended"; }).length;
    var needsCount = sources.length - recCount;
    if (summary) {
      summary.textContent = sources.length + " proposed — " + recCount + " recommended, " + needsCount + " need a closer look. Nothing here is live or credited until Owen approves it individually.";
    }
    list.innerHTML = sorted.map(function (source) { return renderPendingSource(escapeHtml, source); }).join("");
  }

  function init() {
    if (!window.HermesCommon) return;

    window.HermesCommon.loadIndex(function (indexData) {
      renderCatalogCount(indexData);
      window.HermesCommon.initCmdk(indexData);
    });

    loadPendingSources(renderPendingSources);

    window.HermesCommon.initReveal(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
