// Hermes Skills Portfolio — Catalog (Sidebar Filter macrostructure).
//
// Persistent facets drive a results grid. Every number and every string comes
// from skills-index.json or the shared changelog data at render time — nothing
// here is hardcoded or invented.
//
// The facet counts double as the distribution chart: each row draws a bar
// proportional to its share, so the sidebar is both the filter and the "how is
// this catalog shaped" view rather than restating the same numbers twice.
(function () {
  "use strict";

  var HC = window.HermesCommon;
  var TIER_LABELS = HC.TIER_LABELS;
  var TIER_DESCS = {
    core: "Broadly empowering — nearly any user benefits",
    featured: "Strong fit for a common workflow",
    utility: "Focused tool for a specific job"
  };
  var SOURCE_LABELS = { new: "Written for this catalog", generalized: "Generalized from internal use", adapted: "Adapted from an external source" };
  var REPO = "https://github.com/THEROCKSSS/hermes-skills-portfolio";
  var TIERS = ["core", "featured", "utility"];

  var indexData = null;
  var allSkills = [];
  var state = { q: "", category: "", tier: "", list: "", sort: "tier" };

  function el(id) { return document.getElementById(id); }
  function esc(s) { return HC.escapeHtml(s); }
  function catName(k) { return (indexData.categories[k] || {}).name || k; }

  // ---------- Facets ----------
  function facetRowHtml(opts) {
    var pct = opts.max ? (opts.count / opts.max) * 100 : 0;
    return '<button class="facet-row" type="button" data-facet="' + esc(opts.group) + '" data-value="' + esc(opts.value) + '" ' +
      'aria-pressed="' + (opts.active ? "true" : "false") + '" ' +
      'title="' + esc(opts.label) + ': ' + opts.count + ' of ' + allSkills.length + ' skills">' +
      '<span class="facet-bar" data-pct="' + pct.toFixed(1) + '"></span>' +
      '<span class="facet-label">' + esc(opts.label) + '</span>' +
      '<span class="facet-count">' + opts.count + '</span>' +
    '</button>';
  }

  function renderFacets() {
    var catRows = Object.keys(indexData.categories).map(function (k) {
      return { value: k, label: catName(k), count: allSkills.filter(function (s) { return s.category === k; }).length };
    }).filter(function (r) { return r.count > 0; })
      .sort(function (a, b) { return b.count - a.count; });

    var tierRows = TIERS.map(function (t) {
      return { value: t, label: TIER_LABELS[t], count: allSkills.filter(function (s) { return s.tier === t; }).length };
    }).filter(function (r) { return r.count > 0; })
      .sort(function (a, b) { return b.count - a.count; });

    var catMax = Math.max.apply(null, catRows.map(function (r) { return r.count; }));
    var tierMax = Math.max.apply(null, tierRows.map(function (r) { return r.count; }));

    el("facet-category").innerHTML = catRows.map(function (r) {
      return facetRowHtml({ group: "category", value: r.value, label: r.label, count: r.count, max: catMax, active: state.category === r.value });
    }).join("");

    el("facet-tier").innerHTML = tierRows.map(function (r) {
      return facetRowHtml({ group: "tier", value: r.value, label: r.label, count: r.count, max: tierMax, active: state.tier === r.value });
    }).join("");

    // Personal lists — only offered when they actually contain something, so
    // the sidebar never shows a filter that can only return nothing.
    var mine = HC.getMyList().filter(existsInCatalog);
    var recent = HC.getRecentlyViewed().filter(existsInCatalog);
    var listRows = "";
    if (mine.length) listRows += facetRowHtml({ group: "list", value: "mylist", label: "My List", count: mine.length, max: Math.max(mine.length, recent.length), active: state.list === "mylist" });
    if (recent.length) listRows += facetRowHtml({ group: "list", value: "recent", label: "Recently viewed", count: recent.length, max: Math.max(mine.length, recent.length), active: state.list === "recent" });
    el("facet-lists").innerHTML = listRows ||
      '<p class="facet-note">Open a skill or save one and it will show up here.</p>';

    // Table view of the same numbers, for anyone who wants them as data.
    el("facet-table").querySelector("tbody").innerHTML =
      catRows.concat(tierRows).map(function (r) {
        return "<tr><td>" + esc(r.label) + "</td><td>" + r.count + "</td></tr>";
      }).join("");

    wireFacets();
    growBars();
  }

  function existsInCatalog(name) {
    return allSkills.some(function (s) { return s.name === name; });
  }

  function growBars() {
    // Animate on reveal rather than on load so the growth is actually seen.
    var bars = document.querySelectorAll(".facet-bar[data-pct]");
    requestAnimationFrame(function () {
      bars.forEach(function (b) { b.style.width = b.getAttribute("data-pct") + "%"; });
    });
  }

  function wireFacets() {
    document.querySelectorAll(".facet-row").forEach(function (row) {
      row.addEventListener("click", function () {
        var group = row.getAttribute("data-facet");
        var value = row.getAttribute("data-value");
        state[group] = state[group] === value ? "" : value;
        applyFilters();
        renderFacets();
      });
    });
  }

  // ---------- What's new ----------
  function renderWhatsNew() {
    var commits = (window.HermesChangelog && window.HermesChangelog.COMMITS) || [];
    var list = el("whatsnew-list");
    if (!commits.length) {
      list.innerHTML = '<li class="whatsnew-empty">No changelog entries are available.</li>';
      return;
    }
    list.innerHTML = commits.slice(0, 5).map(function (c) {
      return '<li class="whatsnew-item">' +
        '<span class="whatsnew-subject">' + esc(c.text) + '</span>' +
        '<time class="whatsnew-date" datetime="' + esc(c.date) + '">' + esc(c.date) + '</time>' +
      '</li>';
    }).join("");
  }

  // ---------- Results ----------
  function currentResults() {
    var out = state.q ? HC.searchSkills(allSkills, state.q) : allSkills.slice();
    if (state.category) out = out.filter(function (s) { return s.category === state.category; });
    if (state.tier) out = out.filter(function (s) { return s.tier === state.tier; });

    if (state.list) {
      var names = state.list === "mylist" ? HC.getMyList() : HC.getRecentlyViewed();
      out = out.filter(function (s) { return names.indexOf(s.name) !== -1; });
      // Personal lists carry their own meaningful order (most recent first).
      out.sort(function (a, b) { return names.indexOf(a.name) - names.indexOf(b.name); });
      return out;
    }

    if (!state.q) {
      var order = { core: 0, featured: 1, utility: 2 };
      if (state.sort === "name") out.sort(function (a, b) { return a.name.localeCompare(b.name); });
      else if (state.sort === "category") out.sort(function (a, b) { return a.category.localeCompare(b.category) || a.name.localeCompare(b.name); });
      else out.sort(function (a, b) { return order[a.tier] - order[b.tier] || a.name.localeCompare(b.name); });
    }
    return out;
  }

  function activeCount() {
    return (state.q ? 1 : 0) + (state.category ? 1 : 0) + (state.tier ? 1 : 0) + (state.list ? 1 : 0);
  }

  function renderChips() {
    var chips = [];
    if (state.q) chips.push({ k: "q", label: 'Search: "' + state.q + '"' });
    if (state.category) chips.push({ k: "category", label: "Category: " + catName(state.category) });
    if (state.tier) chips.push({ k: "tier", label: "Tier: " + (TIER_LABELS[state.tier] || state.tier) });
    if (state.list) chips.push({ k: "list", label: state.list === "mylist" ? "My List" : "Recently viewed" });

    el("active-filters").innerHTML = chips.map(function (c) {
      return '<button class="filter-chip" type="button" data-clear="' + c.k + '">' + esc(c.label) +
        ' <span aria-hidden="true">&times;</span><span class="sr-only"> (remove filter)</span></button>';
    }).join("");

    el("active-filters").querySelectorAll(".filter-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var k = chip.getAttribute("data-clear");
        state[k] = "";
        if (k === "q") el("search-input").value = "";
        applyFilters();
        renderFacets();
      });
    });

    var count = activeCount();
    el("side-toggle-count").textContent = count ? count + " active" : "";
  }

  function applyFilters() {
    var results = currentResults();
    var grid = el("catalog-grid");
    grid.innerHTML = results.map(HC.renderPoster).join("");
    wirePosters(grid);

    el("catalog-status").textContent = results.length === allSkills.length
      ? "Showing all " + allSkills.length + " skills."
      : "Showing " + results.length + " of " + allSkills.length + " skills.";

    var none = el("no-results");
    none.hidden = results.length > 0;
    if (!results.length) {
      var suggestion = state.q ? HC.didYouMean(allSkills, state.q) : null;
      el("no-results-text").innerHTML = "No skills match those filters." +
        (suggestion ? " Did you mean <strong>" + esc(suggestion) + "</strong>?" : "");
    }
    renderChips();
    syncUrl();
  }

  function clearFilters() {
    state.q = ""; state.category = ""; state.tier = ""; state.list = "";
    el("search-input").value = "";
    applyFilters();
    renderFacets();
  }

  function syncUrl() {
    var params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.category) params.set("category", state.category);
    if (state.tier) params.set("tier", state.tier);
    if (state.list) params.set("list", state.list);
    var qs = params.toString();
    history.replaceState(null, "", qs ? "?" + qs : location.pathname);
  }

  function readUrl() {
    var params = new URLSearchParams(location.search);
    state.q = params.get("q") || "";
    state.category = params.get("category") || "";
    state.tier = params.get("tier") || "";
    state.list = params.get("list") || "";
    el("search-input").value = state.q;
  }

  function wirePosters(root) {
    root.querySelectorAll(".poster").forEach(function (card) {
      var name = card.getAttribute("data-name");
      card.addEventListener("click", function (e) {
        if (e.target.closest(".poster-quick")) return;
        openDetail(name);
      });
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDetail(name); }
      });
    });
    root.querySelectorAll(".poster-quick").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        HC.copyToClipboard(btn.getAttribute("data-copy"), null, { toastMsg: "Install command copied" });
      });
    });
  }

  // ---------- Markdown ----------
  // A deliberately small renderer: headings, lists, tables, code fences, links,
  // inline code, blockquotes, rules. Everything is escaped BEFORE any markup is
  // introduced, so skill content can never inject HTML into the page.
  function renderMarkdown(src) {
    var text = String(src == null ? "" : src).replace(/\r\n/g, "\n");
    var blocks = [];
    // The token must survive the line.trim() below — a space-delimited marker
    // gets its delimiters stripped and then never matches, which silently drops
    // every code block and leaks the raw placeholder into the page.
    text = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, function (m, lang, code) {
      blocks.push('<div class="md-pre-wrap"><pre><code>' + HC.escapeHtml(code.replace(/\n$/, "")) + "</code></pre>" +
        '<button class="md-copy" type="button">Copy</button></div>');
      return "\n%%MDBLOCK" + (blocks.length - 1) + "%%\n";
    });

    var lines = text.split("\n");
    var html = "";
    var listType = null;
    var inTable = false;

    function closeList() { if (listType) { html += "</" + listType + ">"; listType = null; } }
    function closeTable() { if (inTable) { html += "</tbody></table></div>"; inTable = false; } }

    function inline(s) {
      var out = HC.escapeHtml(s);
      out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
      out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      // Links: http(s) only — never javascript: URLs.
      out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>');
      return out;
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var placeholder = /^%%MDBLOCK(\d+)%%$/.exec(line.trim());
      if (placeholder) { closeList(); closeTable(); html += blocks[Number(placeholder[1])]; continue; }
      if (!line.trim()) { closeList(); closeTable(); continue; }

      var h = /^(#{1,6})\s+(.*)$/.exec(line);
      if (h) {
        closeList(); closeTable();
        var lvl = Math.min(h[1].length, 4);
        html += "<h" + lvl + ">" + inline(h[2]) + "</h" + lvl + ">";
        continue;
      }
      if (/^\s*([-*_])\s*\1\s*\1[\s-*_]*$/.test(line)) { closeList(); closeTable(); html += "<hr>"; continue; }

      if (line.indexOf("|") !== -1 && /^\s*\|?[-:\s|]+\|[-:\s|]*$/.test(lines[i + 1] || "")) {
        closeList();
        var headers = line.split("|").map(function (c) { return c.trim(); })
          .filter(function (c, idx, arr) { return !(c === "" && (idx === 0 || idx === arr.length - 1)); });
        html += '<div class="md-table-scroll"><table><thead><tr>' +
          headers.map(function (c) { return "<th>" + inline(c) + "</th>"; }).join("") + "</tr></thead><tbody>";
        inTable = true; i++;
        continue;
      }
      if (inTable) {
        if (line.indexOf("|") === -1) { closeTable(); }
        else {
          var cells = line.split("|").map(function (c) { return c.trim(); })
            .filter(function (c, idx, arr) { return !(c === "" && (idx === 0 || idx === arr.length - 1)); });
          html += "<tr>" + cells.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>";
          continue;
        }
      }

      var ul = /^\s*[-*]\s+(.*)$/.exec(line);
      var ol = /^\s*\d+[.)]\s+(.*)$/.exec(line);
      if (ul || ol) {
        var want = ul ? "ul" : "ol";
        if (listType !== want) { closeList(); html += "<" + want + ">"; listType = want; }
        html += "<li>" + inline((ul || ol)[1]) + "</li>";
        continue;
      }
      closeList();

      var bq = /^\s*>\s?(.*)$/.exec(line);
      if (bq) { html += "<blockquote>" + inline(bq[1]) + "</blockquote>"; continue; }

      html += "<p>" + inline(line) + "</p>";
    }
    closeList(); closeTable();
    return html;
  }

  function mountMarkdown(container, src) {
    container.innerHTML = renderMarkdown(src);
    container.querySelectorAll(".md-copy").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var code = btn.parentElement.querySelector("code");
        HC.copyToClipboard(code ? code.textContent : "", btn, { restoreLabel: "Copy", toastMsg: "Code copied" });
      });
    });
  }

  // ---------- Detail overlay ----------
  var lastFocused = null;

  function relatedTo(skill) {
    // Real relationships only: the skill's own declared related_skills when the
    // target exists in this catalog, then same-category siblings to fill out.
    var declared = [];
    var fm = skill.frontmatter || {};
    var meta = (fm.metadata && fm.metadata.hermes) || {};
    (meta.related_skills || []).forEach(function (n) {
      if (existsInCatalog(n)) declared.push(n);
    });
    var siblings = allSkills
      .filter(function (s) { return s.category === skill.category && s.name !== skill.name && declared.indexOf(s.name) === -1; })
      .slice(0, 4).map(function (s) { return s.name; });
    return declared.concat(siblings).slice(0, 6);
  }

  function openDetail(name) {
    var skill = allSkills.filter(function (s) { return s.name === name; })[0];
    if (!skill) return;
    lastFocused = document.activeElement;
    HC.pushRecentlyViewed(name);

    var overlay = el("detail-overlay");
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    setBackgroundInert(true);
    overlay.addEventListener("keydown", trapTab);

    var installCmd = "hermes skills install " + skill.install_url;

    el("detail-name").textContent = skill.name;
    var tierBadge = el("detail-tier");
    tierBadge.textContent = TIER_LABELS[skill.tier] || skill.tier;
    tierBadge.className = "tier-badge " + skill.tier;
    el("detail-desc").textContent = skill.description;

    var metaHtml = "<span><strong>Category:</strong> " + esc(catName(skill.category)) + "</span>" +
      "<span><strong>Tier:</strong> " + esc(TIER_DESCS[skill.tier] || skill.tier) + "</span>" +
      "<span><strong>Source:</strong> " + esc(SOURCE_LABELS[skill.source] || skill.source) + "</span>";
    if (skill.recency) metaHtml += "<span><strong>Updated:</strong> " + esc(skill.recency) + "</span>";
    el("detail-meta").innerHTML = metaHtml;

    el("detail-user-use").textContent = skill.user_use || skill.description;
    el("detail-agent-use").innerHTML = bulletize(skill.agent_use);

    el("detail-install-cmd").textContent = installCmd;
    var installBtn = el("detail-copy-btn");
    installBtn.onclick = function () { HC.copyToClipboard(installCmd, installBtn, { restoreLabel: "Copy", toastMsg: "Install command copied" }); };

    // install_url is the raw URL the CLI fetches; source_url is the GitHub blob
    // page a human should land on. Never point this link at install_url.
    el("detail-skillmd-link").href = skill.source_url || skill.install_url;

    var sourceLink = el("detail-source-link");
    var originUrl = skill.source_attribution && skill.source_attribution.origin_url;
    if (originUrl) { sourceLink.href = originUrl; sourceLink.hidden = false; }
    else { sourceLink.hidden = true; }

    el("detail-report-link").href = REPO + "/issues/new?title=" +
      encodeURIComponent("[" + skill.name + "] ") +
      "&body=" + encodeURIComponent("Skill: " + skill.name + "\nPage: " + HC.canonicalSkillUrl(skill.name) + "\n\nWhat went wrong:\n");

    var related = relatedTo(skill);
    var relSection = el("detail-related-section");
    if (related.length) {
      relSection.hidden = false;
      el("detail-related").innerHTML = related.map(function (n) {
        return '<button class="related-chip" type="button" data-name="' + esc(n) + '">' + esc(n) + "</button>";
      }).join("");
      el("detail-related").querySelectorAll(".related-chip").forEach(function (chip) {
        chip.addEventListener("click", function () { openDetail(chip.getAttribute("data-name")); });
      });
    } else { relSection.hidden = true; }

    syncMyListBtn(skill.name);
    mountMarkdown(el("detail-skillmd-content"), skill.skillmd_content || "SKILL.md content is not available.");
    mountMarkdown(el("detail-readme-content"), skill.readme_content || "README.md content is not available.");

    wireShare(skill);
    switchTab("overview");
    location.hash = "skill/" + encodeURIComponent(skill.name);
    el("detail-close").focus();
    renderFacets(); // "Recently viewed" may have just gained its first entry
  }

  function syncMyListBtn(name) {
    var btn = el("detail-mylist-btn");
    var saved = HC.isInMyList(name);
    btn.setAttribute("aria-pressed", String(saved));
    el("detail-mylist-label").textContent = saved ? "In My List" : "Add to My List";
    btn.onclick = function () {
      var nowSaved = HC.toggleMyList(name);
      syncMyListBtn(name);
      HC.showToast(nowSaved ? "Saved to My List (this browser)" : "Removed from My List");
      renderFacets();
      if (state.list) applyFilters();
    };
  }

  function wireShare(skill) {
    var url = HC.canonicalSkillUrl(skill.name);
    el("detail-copy-link-btn").onclick = function () {
      HC.copyToClipboard(url, el("detail-copy-link-btn"), { restoreLabel: "Copy link", toastMsg: "Link copied" });
    };
    var blurb = "**" + skill.name + "** — " + skill.description + "\n" +
      "Install: `hermes skills install " + skill.install_url + "`\n" + url;
    el("detail-copy-discord-btn").onclick = function () {
      var pre = el("detail-discord-preview");
      pre.hidden = false; pre.textContent = blurb;
      HC.copyToClipboard(blurb, el("detail-copy-discord-btn"), { restoreLabel: "Copy Discord blurb", toastMsg: "Discord blurb copied" });
    };
  }

  function bulletize(text) {
    if (!text) return "&mdash;";
    var items = String(text).split("\n").map(function (l) { return l.replace(/^-\s*/, "").trim(); }).filter(Boolean);
    if (!items.length) return "&mdash;";
    return "<ul>" + items.map(function (i) { return "<li>" + esc(i) + "</li>"; }).join("") + "</ul>";
  }

  function switchTab(tab) {
    document.querySelectorAll(".detail-tab").forEach(function (b) {
      var on = b.getAttribute("data-tab") === tab;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", String(on));
    });
    document.querySelectorAll(".detail-tab-content").forEach(function (c) {
      c.classList.toggle("active", c.id === "tab-" + tab);
    });
  }

  // The overlay is a modal dialog, so everything behind it must leave the tab
  // order — otherwise focus walks out of the dialog and lands on the footer
  // while the dialog is still open. `inert` also hides the background from
  // assistive tech, which aria-modal alone does not guarantee.
  // #cmdk-modal is included because the palette is now built at init (so its
  // aria-controls target exists), which puts its focusable input in the tab
  // order behind the dialog unless it is inerted too.
  var INERT_SELECTORS = ["#nav", "#main", ".footer", "#back-to-top", "#cmdk-modal"];
  function setBackgroundInert(on) {
    INERT_SELECTORS.forEach(function (sel) {
      var node = document.querySelector(sel);
      if (!node) return;
      if (on) { node.setAttribute("inert", ""); }
      else { node.removeAttribute("inert"); }
    });
  }

  // inert alone stops focus reaching the background, but past the dialog's last
  // control Tab still walks out into the browser chrome and wraps to <body>.
  // Cycling explicitly keeps focus inside for as long as the dialog is open.
  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),' +
    'select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

  function trapTab(e) {
    if (e.key !== "Tab") return;
    var overlay = el("detail-overlay");
    var items = Array.prototype.filter.call(
      overlay.querySelectorAll(FOCUSABLE),
      function (n) { return n.offsetParent !== null || n === document.activeElement; }
    );
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  function closeDetail() {
    el("detail-overlay").removeEventListener("keydown", trapTab);
    el("detail-overlay").hidden = true;
    document.body.style.overflow = "";
    setBackgroundInert(false);
    if (location.hash.indexOf("#skill/") === 0) {
      history.replaceState(null, "", location.pathname + location.search);
    }
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  // ---------- Boot ----------
  function init() {
    el("catalog-grid").innerHTML = HC.skeletonPosters(8);

    HC.loadIndex(function (data) {
      if (!data || !data.skills) {
        el("catalog-status").textContent = "Could not load skills-index.json.";
        el("catalog-grid").innerHTML = "";
        return;
      }
      indexData = data;
      allSkills = data.skills;

      HC.initCmdk(data);
      readUrl();

      // Viewport-agnostic wording: the facets are a left rail on desktop but sit
      // behind a disclosure on phones, so "on the left" would be wrong there.
      el("masthead-sub").textContent =
        allSkills.length + " skills across " + Object.keys(data.categories).length +
        " categories. Filter by category or tier, or press ⌘K to search.";
      // The masthead shows the generic shape, not one skill's URL: the label
      // says every skill installs the same way, and a full raw URL only ever
      // renders clipped here. The real per-skill command lives on every card
      // and in the detail overlay, where it can be copied.

      renderFacets();
      renderWhatsNew();
      applyFilters();
      HC.initReveal(document);

      if (location.hash.indexOf("#skill/") === 0) {
        openDetail(decodeURIComponent(location.hash.slice("#skill/".length)));
      }
    });

    var searchInput = el("search-input");
    var debounce = null;
    searchInput.addEventListener("input", function () {
      clearTimeout(debounce);
      debounce = setTimeout(function () { state.q = searchInput.value.trim(); applyFilters(); }, 140);
    });
    el("sort-select").addEventListener("change", function (e) { state.sort = e.target.value; applyFilters(); });
    el("clear-filters-btn").addEventListener("click", clearFilters);
    el("clear-filters-btn-2").addEventListener("click", clearFilters);

    // Sidebar disclosure (mobile only — the button is display:none above 60rem)
    var toggle = el("side-toggle");
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      el("side-body").classList.toggle("is-open", !open);
    });

    el("detail-close").addEventListener("click", closeDetail);
    el("detail-overlay").addEventListener("click", function (e) {
      if (e.target === el("detail-overlay")) closeDetail();
    });
    document.querySelectorAll(".detail-tab").forEach(function (b) {
      b.addEventListener("click", function () { switchTab(b.getAttribute("data-tab")); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !el("detail-overlay").hidden) closeDetail();
    });

    var btt = el("back-to-top");
    window.addEventListener("scroll", function () { btt.hidden = window.scrollY < 600; }, { passive: true });
    btt.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
