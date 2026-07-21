// Hermes Skills Portfolio — app.js
// Dark mode default, light toggle, sort/filter/search, DETAIL PAGE OVERLAY with tabs,
// copy-to-clipboard, keyboard shortcuts, URL hash state, distribution bar,
// filter chips, back-to-top, toast notifications.
// Hallmark + frontend-design-craft applied.

(function () {
  "use strict";

  var indexData = null;
  var currentSort = "tier-usage";
  var currentCategory = "";
  var currentTier = "";
  var currentSearch = "";
  var currentDetailSkill = null;

  var TIER_ORDER = { core: 0, featured: 1, utility: 2 };
  var TIER_LABELS = { core: "Core", featured: "Featured", utility: "Utility" };
  var TIER_DESCS = {
    core: "Broadly empowering, nearly any user benefits",
    featured: "Highly useful within a category",
    utility: "Useful for specific workflows",
  };
  var SOURCE_LABELS = {
    new: "Newly authored",
    generalized: "Generalized from existing",
    adapted: "Adapted with attribution",
  };

  // --- Theme management ---
  function initTheme() {
    var saved = localStorage.getItem("portfolio-theme");
    document.documentElement.setAttribute("data-theme", saved || "dark");
  }
  function toggleTheme() {
    var current = document.documentElement.getAttribute("data-theme");
    var next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("portfolio-theme", next);
    showToast(next === "dark" ? "Dark mode" : "Light mode");
  }

  // --- Data loading ---
  function loadIndex(cb) {
    var paths = ["./skills-index.json", "../skills-index.json", "/skills-index.json"];
    var tried = 0;
    function tryNext() {
      if (tried >= paths.length) {
        document.getElementById("skill-grid").innerHTML =
          '<p class="empty-state">Could not load skills-index.json.</p>';
        return;
      }
      var path = paths[tried++];
      fetch(path)
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function (data) { cb(data); })
        .catch(function () { tryNext(); });
    }
    tryNext();
  }

  // --- Sorting ---
  function totalUsage(skill) {
    var u = skill.usage || {};
    return (u.hub_installs || 0) + (u.github_clones || 0) + (u.stars || 0) + (u.self_reported_users || 0);
  }
  function sortSkills(skills, mode) {
    var arr = skills.slice();
    switch (mode) {
      case "tier-usage":
        arr.sort(function (a, b) { var t = TIER_ORDER[a.tier] - TIER_ORDER[b.tier]; return t !== 0 ? t : totalUsage(b) - totalUsage(a); }); break;
      case "usage":
        arr.sort(function (a, b) { return totalUsage(b) - totalUsage(a); }); break;
      case "recency":
        arr.sort(function (a, b) { return (b.recency || "").localeCompare(a.recency || ""); }); break;
      case "category":
        arr.sort(function (a, b) { var c = (a.category || "").localeCompare(b.category || ""); return c !== 0 ? c : TIER_ORDER[a.tier] - TIER_ORDER[b.tier]; }); break;
      case "alpha":
        arr.sort(function (a, b) { return a.name.localeCompare(b.name); }); break;
    }
    return arr;
  }

  // --- Filtering ---
  function filterSkills(skills) {
    return skills.filter(function (s) {
      if (currentCategory && s.category !== currentCategory) return false;
      if (currentTier && s.tier !== currentTier) return false;
      if (currentSearch) {
        var q = currentSearch.toLowerCase();
        var hay = (s.name + " " + s.description + " " + s.category + " " + s.tier + " " + (s.agent_use || "") + " " + (s.user_use || "")).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  // --- URL hash state ---
  function readHashState() {
    var hash = window.location.hash.substring(1);
    if (!hash) return false;
    // Old #skill/<name> hash links — redirect to the real per-skill page
    if (hash.indexOf("skill/") === 0) {
      var skillName = hash.substring(6);
      window.location.replace("skills/" + skillName + "/index.html");
      return true;
    }
    var params = new URLSearchParams(hash);
    if (params.get("sort")) { currentSort = params.get("sort"); document.getElementById("sort-select").value = currentSort; }
    if (params.get("cat")) { currentCategory = params.get("cat"); document.getElementById("category-filter").value = currentCategory; }
    if (params.get("tier")) { currentTier = params.get("tier"); document.getElementById("tier-filter").value = currentTier; }
    if (params.get("q")) { currentSearch = params.get("q"); document.getElementById("search-input").value = currentSearch; }
    return false;
  }
  function writeHashState() {
    if (currentDetailSkill) return; // Don't overwrite skill detail hash
    var params = new URLSearchParams();
    if (currentSort !== "tier-usage") params.set("sort", currentSort);
    if (currentCategory) params.set("cat", currentCategory);
    if (currentTier) params.set("tier", currentTier);
    if (currentSearch) params.set("q", currentSearch);
    var hash = params.toString();
    if (hash) { window.history.replaceState(null, "", "#" + hash); }
    else { window.history.replaceState(null, "", window.location.pathname); }
  }

  // --- Rendering ---
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderDistributionBar(categories, skills) {
    var bar = document.getElementById("distribution-bar");
    bar.innerHTML = "";
    var counts = {};
    var tierCounts = {};
    for (var i = 0; i < skills.length; i++) {
      var cat = skills[i].category;
      counts[cat] = (counts[cat] || 0) + 1;
      if (!tierCounts[cat]) tierCounts[cat] = { core: 0, featured: 0, utility: 0 };
      tierCounts[cat][skills[i].tier]++;
    }
    var keys = Object.keys(categories).sort();
    var total = skills.length;
    for (var j = 0; j < keys.length; j++) {
      var key = keys[j];
      var count = counts[key] || 0;
      if (count === 0) continue;
      var seg = document.createElement("button");
      seg.className = "dist-segment";
      seg.setAttribute("data-cat", key);
      seg.style.flex = count;
      seg.setAttribute("aria-label", categories[key].name + ": " + count + " skills");
      seg.setAttribute("title", categories[key].name + " (" + count + " skills — click to filter)");
      // Hover popup with tier breakdown
      (function(k, c, tc) {
        seg.addEventListener("mouseenter", function(e) { showDistPopupEnhanced(e, k, c, tc); });
        seg.addEventListener("mouseleave", function() { hideDistPopup(); });
        seg.addEventListener("click", function() {
          currentCategory = k;
          document.getElementById("category-filter").value = k;
          writeHashState();
          render();
        });
      })(key, count, tierCounts[key]);
      bar.appendChild(seg);
    }
    // Build index/legend
    renderDistributionIndex(categories, counts, tierCounts, total);
  }

  function renderDistributionIndex(categories, counts, tierCounts, total) {
    var index = document.getElementById("dist-index");
    if (!index) return;
    index.innerHTML = "";
    var keys = Object.keys(categories).sort();
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      var count = counts[key] || 0;
      if (count === 0) continue;
      var tc = tierCounts[key] || {};
      var item = document.createElement("button");
      item.className = "dist-index-item";
      item.setAttribute("data-cat", key);
      item.innerHTML =
        '<span class="dist-index-dot" data-cat="' + key + '"></span>' +
        '<span class="dist-index-label">' + escapeHtml(categories[key].name) + '</span>' +
        '<span class="dist-index-count">' + count + '</span>' +
        '<span class="dist-index-tiers">' +
          (tc.core ? '<span class="dist-tier-mini core">' + tc.core + 'C</span>' : '') +
          (tc.featured ? '<span class="dist-tier-mini featured">' + tc.featured + 'F</span>' : '') +
          (tc.utility ? '<span class="dist-tier-mini utility">' + tc.utility + 'U</span>' : '') +
        '</span>';
      (function(k) {
        item.addEventListener("click", function() {
          currentCategory = k;
          document.getElementById("category-filter").value = k;
          writeHashState();
          render();
        });
      })(key);
      index.appendChild(item);
    }
  }

  // --- Distribution bar hover popup ---
  var distPopup = null;
  function showDistPopup(e, catKey, count, tierCounts) {
    hideDistPopup();
    var catName = indexData.categories[catKey] ? indexData.categories[catKey].name : catKey;
    var pct = Math.round((count / indexData.skills.length) * 100);
    var popup = document.createElement("div");
    popup.className = "dist-popup";
    popup.innerHTML =
      '<div class="dist-popup-name">' + escapeHtml(catName) + '</div>' +
      '<div class="dist-popup-count">' + count + ' skills &middot; ' + pct + '%</div>' +
      '<div class="dist-popup-tiers">' +
        (tierCounts.core ? '<span class="dist-popup-tier core">Core: ' + tierCounts.core + '</span>' : '') +
        (tierCounts.featured ? '<span class="dist-popup-tier featured">Featured: ' + tierCounts.featured + '</span>' : '') +
        (tierCounts.utility ? '<span class="dist-popup-tier utility">Utility: ' + tierCounts.utility + '</span>' : '') +
      '</div>' +
      '<div class="dist-popup-hint">Click to filter</div>';
    document.body.appendChild(popup);
    distPopup = popup;
    // Position near the segment
    var rect = e.target.getBoundingClientRect();
    var popupRect = popup.getBoundingClientRect();
    var left = rect.left + rect.width / 2 - popupRect.width / 2;
    var top = rect.bottom + 6;
    // Keep within viewport
    if (left < 8) left = 8;
    if (left + popupRect.width > window.innerWidth - 8) left = window.innerWidth - popupRect.width - 8;
    popup.style.left = left + "px";
    popup.style.top = top + "px";
  }
  function hideDistPopup() {
    if (distPopup) { distPopup.remove(); distPopup = null; }
  }

  function renderFilterChips() {
    var container = document.getElementById("active-filters");
    container.innerHTML = "";
    if (currentCategory) { container.appendChild(makeChip("Category: " + currentCategory, function() { currentCategory = ""; document.getElementById("category-filter").value = ""; writeHashState(); render(); })); }
    if (currentTier) { container.appendChild(makeChip("Tier: " + TIER_LABELS[currentTier], function() { currentTier = ""; document.getElementById("tier-filter").value = ""; writeHashState(); render(); })); }
    if (currentSearch) { container.appendChild(makeChip('Search: "' + currentSearch + '"', function() { currentSearch = ""; document.getElementById("search-input").value = ""; writeHashState(); render(); })); }
  }
  function makeChip(label, onRemove) {
    var chip = document.createElement("span"); chip.className = "filter-chip";
    var text = document.createElement("span"); text.textContent = label;
    var btn = document.createElement("button"); btn.textContent = "\u00d7"; btn.setAttribute("aria-label", "Remove filter: " + label);
    btn.onclick = function(e) { e.stopPropagation(); onRemove(); };
    chip.appendChild(text); chip.appendChild(btn);
    return chip;
  }

  function renderSkillCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var a = document.createElement("a");
    a.className = "skill-card";
    a.setAttribute("data-skill", skill.name);
    a.setAttribute("href", "skills/" + skill.name + "/index.html");
    a.setAttribute("role", "button");
    a.innerHTML =
      '<div class="skill-card-header">' +
        '<span class="skill-name">' + escapeHtml(skill.name) + '</span>' +
        '<span class="tier-badge ' + skill.tier + '">' + TIER_LABELS[skill.tier] + '</span>' +
      '</div>' +
      '<p class="skill-desc">' + escapeHtml(skill.description) + '</p>' +
      '<div class="skill-meta">' +
        '<span class="skill-cat">' + escapeHtml(catName) + '</span>' +
        '<span class="skill-source">' + escapeHtml(sourceLabel) + '</span>' +
        (skill.recency ? '<span class="skill-recency">' + escapeHtml(skill.recency) + '</span>' : '') +
      '</div>' +
      '<div class="skill-card-footer-hint">Click for details \u2192</div>';
    return a;
  }

  function render() {
    if (!indexData) return;
    var skills = filterSkills(sortSkills(indexData.skills, currentSort));
    var grid = document.getElementById("skill-grid");
    var noResults = document.getElementById("no-results");
    grid.innerHTML = "";
    renderFilterChips();
    writeHashState();
    if (skills.length === 0) { grid.hidden = true; noResults.hidden = false; document.getElementById("results-count").textContent = "0 skills match"; return; }
    grid.hidden = false; noResults.hidden = true;
    document.getElementById("results-count").textContent = skills.length + " skill" + (skills.length === 1 ? "" : "s") + " shown";
    var frag = document.createDocumentFragment();
    for (var i = 0; i < skills.length; i++) { frag.appendChild(renderSkillCard(skills[i], indexData.categories)); }
    grid.appendChild(frag);
  }

  // --- Detail page overlay ---

  function findSkill(name) {
    if (!indexData) return null;
    for (var i = 0; i < indexData.skills.length; i++) {
      if (indexData.skills[i].name === name) return indexData.skills[i];
    }
    return null;
  }

  function openDetail(skillName) {
    var skill = findSkill(skillName);
    if (!skill) return;

    currentDetailSkill = skillName;
    document.body.classList.add("detail-open");
    var overlay = document.getElementById("detail-overlay");
    overlay.hidden = false;

    var catName = indexData.categories[skill.category] ? indexData.categories[skill.category].name : skill.category;
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var usage = totalUsage(skill);
    var installCmd = "hermes skills install " + skill.install_url;

    // Header
    document.getElementById("detail-name").textContent = skill.name;
    var tierBadge = document.getElementById("detail-tier");
    tierBadge.textContent = TIER_LABELS[skill.tier];
    tierBadge.className = "tier-badge " + skill.tier;
    document.getElementById("detail-desc").textContent = skill.description;

    // Meta row
    var metaHtml = '<span><strong>Category:</strong> ' + escapeHtml(catName) + '</span>' +
      '<span><strong>Tier:</strong> ' + TIER_DESCS[skill.tier] + '</span>' +
      '<span><strong>Source:</strong> ' + escapeHtml(sourceLabel) + '</span>';
    if (skill.recency) metaHtml += '<span><strong>Updated:</strong> ' + escapeHtml(skill.recency) + '</span>';
    document.getElementById("detail-meta").innerHTML = metaHtml;

    // Overview tab: user_use + agent_use
    var userUse = skill.user_use || skill.description;
    var agentUse = skill.agent_use || "See the SKILL.md tab for full usage instructions.";

    // Convert bullet lists in agent_use to HTML
    if (agentUse.indexOf("- ") === 0 || agentUse.indexOf("\n- ") !== -1) {
      var lines = agentUse.split("\n");
      var listHtml = "<ul>";
      var inList = false;
      var nonListParts = [];
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line.indexOf("- ") === 0) {
          if (!inList) { inList = true; }
          listHtml += "<li>" + escapeHtml(line.substring(2)) + "</li>";
        } else if (line) {
          if (inList) { listHtml += "</ul>"; inList = false; }
          nonListParts.push("<p>" + escapeHtml(line) + "</p>");
        }
      }
      if (inList) listHtml += "</ul>";
      agentUse = nonListParts.join("") + listHtml;
    } else {
      agentUse = "<p>" + escapeHtml(agentUse) + "</p>";
    }

    document.getElementById("detail-user-use").textContent = userUse;
    document.getElementById("detail-agent-use").innerHTML = agentUse;

    // Install command
    document.getElementById("detail-install-cmd").textContent = installCmd;
    document.getElementById("detail-copy-btn").setAttribute("data-clipboard", installCmd);

    // SKILL.md link
    document.getElementById("detail-skillmd-link").href = skill.install_url;

    // Source attribution link (for adapted/generalized skills from external repos)
    var sourceLink = document.getElementById("detail-source-link");
    if (skill.source_attribution) {
      sourceLink.href = skill.source_attribution;
      sourceLink.hidden = false;
    } else {
      sourceLink.hidden = true;
    }

    // SKILL.md content
    var skillmdEl = document.getElementById("detail-skillmd-content");
    if (skill.skillmd_content) {
      skillmdEl.textContent = skill.skillmd_content;
    } else {
      skillmdEl.textContent = "SKILL.md content not available.";
    }

    // README content
    var readmeEl = document.getElementById("detail-readme-content");
    if (skill.readme_content) {
      readmeEl.textContent = skill.readme_content;
    } else {
      readmeEl.textContent = "README.md content not available.";
    }

    // Reset to overview tab
    switchDetailTab("overview");

    // Update URL hash
    window.history.replaceState(null, "", "#skill/" + skillName);

    // Scroll overlay to top
    overlay.scrollTop = 0;

    // Focus the close button for keyboard users
    document.getElementById("detail-close").focus();
  }

  function closeDetail() {
    document.body.classList.remove("detail-open");
    document.getElementById("detail-overlay").hidden = true;
    currentDetailSkill = null;
    writeHashState();
    // Restore the filter hash
    var params = new URLSearchParams();
    if (currentSort !== "tier-usage") params.set("sort", currentSort);
    if (currentCategory) params.set("cat", currentCategory);
    if (currentTier) params.set("tier", currentTier);
    if (currentSearch) params.set("q", currentSearch);
    var hash = params.toString();
    if (hash) { window.history.replaceState(null, "", "#" + hash); }
    else { window.history.replaceState(null, "", window.location.pathname); }
  }

  function switchDetailTab(tabName) {
    document.querySelectorAll(".detail-tab").forEach(function(t) { t.classList.remove("active"); });
    document.querySelectorAll(".detail-tab-content").forEach(function(c) { c.classList.remove("active"); });
    document.querySelector('.detail-tab[data-tab="' + tabName + '"]').classList.add("active");
    document.getElementById("tab-" + tabName).classList.add("active");
  }

  // --- Toast ---
  var toastTimer = null;
  function showToast(msg) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();
    var toast = document.createElement("div");
    toast.className = "toast"; toast.textContent = msg;
    document.body.appendChild(toast);
    requestAnimationFrame(function() { toast.classList.add("show"); });
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() { toast.classList.remove("show"); setTimeout(function() { toast.remove(); }, 200); }, 1800);
  }

  // --- Copy to clipboard ---
  function copyToClipboard(text, btn) {
    function onSuccess() { btn.classList.add("copied"); btn.textContent = "Copied!"; showToast("Install command copied"); setTimeout(function() { btn.classList.remove("copied"); btn.textContent = "Copy"; }, 2000); }
    if (navigator.clipboard) { navigator.clipboard.writeText(text).then(onSuccess); }
    else {
      var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); onSuccess();
    }
  }

  // --- Card clicks → open detail via hash change ---
  function setupCardClicks() {
    // Cards are <a> tags with href="skills/<name>/index.html" — clicking navigates
    // directly to the standalone per-skill page. No hash interception needed.
    document.getElementById("skill-grid").addEventListener("click", function (e) {
      if (e.target.classList.contains("skill-install-link")) return;
    });
  }

  // --- Detail overlay events ---
  function setupDetailEvents() {
    document.getElementById("detail-close").addEventListener("click", closeDetail);
    // Click outside the detail page closes it
    document.getElementById("detail-overlay").addEventListener("click", function(e) {
      if (e.target === this) closeDetail();
    });
    // Tab switching
    document.querySelectorAll(".detail-tab").forEach(function(tab) {
      tab.addEventListener("click", function() { switchDetailTab(tab.getAttribute("data-tab")); });
    });
    // Copy button in detail
    document.getElementById("detail-copy-btn").addEventListener("click", function() {
      var text = this.getAttribute("data-clipboard");
      copyToClipboard(text, this);
    });
  }

  // --- Category filter ---
  function populateCategoryFilter(categories) {
    var sel = document.getElementById("category-filter");
    var keys = Object.keys(categories).sort();
    for (var i = 0; i < keys.length; i++) {
      var opt = document.createElement("option");
      opt.value = keys[i];
      opt.textContent = categories[keys[i]].name + " (" + categories[keys[i]].skill_count + ")";
      sel.appendChild(opt);
    }
  }
  function updateCount(n) { document.getElementById("skill-count").textContent = n + " skill" + (n === 1 ? "" : "s"); }

  // --- Back to top ---
  function setupBackToTop() {
    var btn = document.getElementById("back-to-top");
    window.addEventListener("scroll", function () { btn.hidden = window.scrollY < 600; }, { passive: true });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  // --- Keyboard shortcuts ---
  function setupKeyboard() {
    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") {
        if (e.key === "Escape") { e.target.blur(); }
        return;
      }
      if (e.key === "/") { e.preventDefault(); document.getElementById("search-input").focus(); }
      else if (e.key === "Escape") {
        if (currentDetailSkill) { closeDetail(); }
      }
      else if (e.key === "t" || e.key === "T") { toggleTheme(); }
    });
  }

  // --- Clear filters ---
  function setupClearFilters() {
    document.getElementById("clear-filters-btn").addEventListener("click", function () {
      currentSort = "tier-usage"; currentCategory = ""; currentTier = ""; currentSearch = "";
      document.getElementById("sort-select").value = "tier-usage";
      document.getElementById("category-filter").value = "";
      document.getElementById("tier-filter").value = "";
      document.getElementById("search-input").value = "";
      writeHashState(); render();
    });
  }

  // --- GitHub star count badge (issue #7) ---
  function loadStarCount() {
    var repo = "THEROCKSSS/hermes-skills-portfolio";
    var url = "https://api.github.com/repos/" + repo;
    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var stars = data.stargazers_count || 0;
        var badge = document.getElementById("star-count-badge");
        if (badge) {
          badge.textContent = "\u2605 " + stars;
          badge.style.display = "inline-flex";
        }
      })
      .catch(function() { /* silently fail — star badge is non-critical */ });
  }

  // --- Distribution bar tooltip: show top 3 skills (issue #8) ---
  function showDistPopupEnhanced(e, catKey, count, tierCounts) {
    hideDistPopup();
    var catName = indexData.categories[catKey] ? indexData.categories[catKey].name : catKey;
    var pct = Math.round((count / indexData.skills.length) * 100);
    // Get top 3 skills in this category by usage
    var catSkills = indexData.skills.filter(function(s) { return s.category === catKey; });
    catSkills.sort(function(a, b) { return totalUsage(b) - totalUsage(a); });
    var top3 = catSkills.slice(0, 3).map(function(s) { return s.name; });
    var top3Html = top3.length > 0
      ? '<div class="dist-popup-skills">' + top3.map(function(n) { return '<span class="dist-popup-skill">' + escapeHtml(n) + '</span>'; }).join('') + '</div>'
      : '';
    var popup = document.createElement("div");
    popup.className = "dist-popup";
    popup.innerHTML =
      '<div class="dist-popup-name">' + escapeHtml(catName) + '</div>' +
      '<div class="dist-popup-count">' + count + ' skills &middot; ' + pct + '%</div>' +
      '<div class="dist-popup-tiers">' +
        (tierCounts.core ? '<span class="dist-popup-tier core">Core: ' + tierCounts.core + '</span>' : '') +
        (tierCounts.featured ? '<span class="dist-popup-tier featured">Featured: ' + tierCounts.featured + '</span>' : '') +
        (tierCounts.utility ? '<span class="dist-popup-tier utility">Utility: ' + tierCounts.utility + '</span>' : '') +
      '</div>' +
      top3Html +
      '<div class="dist-popup-hint">Click to filter</div>';
    document.body.appendChild(popup);
    distPopup = popup;
    var rect = e.target.getBoundingClientRect();
    var popupRect = popup.getBoundingClientRect();
    var left = rect.left + rect.width / 2 - popupRect.width / 2;
    var top = rect.bottom + 6;
    if (left < 8) left = 8;
    if (left + popupRect.width > window.innerWidth - 8) left = window.innerWidth - popupRect.width - 8;
    popup.style.left = left + "px";
    popup.style.top = top + "px";
  }

  // --- Init ---
  function init() {
    initTheme();
    loadIndex(function (data) {
      indexData = data;
      populateCategoryFilter(data.categories || {});
      updateCount(data.skills.length);
      renderDistributionBar(data.categories || {}, data.skills);
      readHashState();
      render();
      setupCardClicks();
      setupDetailEvents();
    });
    loadStarCount();
    document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
    document.getElementById("sort-select").addEventListener("change", function (e) { currentSort = e.target.value; render(); });
    document.getElementById("category-filter").addEventListener("change", function (e) { currentCategory = e.target.value; render(); });
    document.getElementById("tier-filter").addEventListener("change", function (e) { currentTier = e.target.value; render(); });
    var searchTimer = null;
    document.getElementById("search-input").addEventListener("input", function (e) {
      currentSearch = e.target.value;
      if (searchTimer) clearTimeout(searchTimer);
      searchTimer = setTimeout(render, 150);
    });
    setupKeyboard(); setupBackToTop(); setupClearFilters();
    window.addEventListener("hashchange", function () { var isSkill = readHashState(); if (!isSkill) render(); });
  }
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); }
  else { init(); }
})();
