// Hermes Skills Portfolio — Catalog page (Ecosystem Index macrostructure).
// Rails (Featured/core, by-category, by-tier) + quickstart + full search/sort/filter
// grid + skill detail overlay. Reads skills-index.json at render time — every count
// on this page comes from that file, never invented. Uses HermesCommon for theme,
// cmd-k, toast, copy, reveal — does not reimplement any of them.
(function () {
  "use strict";

  var HC = window.HermesCommon;

  var indexData = null;
  var currentSort = "tier-usage";
  var currentCategory = "";
  var currentTier = "";
  var currentSearch = "";
  var currentDetailSkill = null;

  var TIER_ORDER = { core: 0, featured: 1, utility: 2 };
  var TIER_LABELS = { core: "Core", featured: "Featured", utility: "Utility" };
  var TIER_DESCS = {
    core: "Broadly empowering — nearly any user benefits.",
    featured: "Highly useful within a category.",
    utility: "Useful for specific workflows.",
  };
  var SOURCE_LABELS = {
    new: "Newly authored",
    generalized: "Generalized from existing",
    adapted: "Adapted with attribution",
  };

  function el(id) { return document.getElementById(id); }
  function prefersReducedMotion() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  // --- Usage / sorting / filtering (same rules as the previous single-page site) ---
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

  function findSkill(name) {
    if (!indexData) return null;
    for (var i = 0; i < indexData.skills.length; i++) {
      if (indexData.skills[i].name === name) return indexData.skills[i];
    }
    return null;
  }

  // --- URL hash state ---
  function readHashState() {
    var hash = window.location.hash.substring(1);
    if (!hash) return false;
    if (hash.indexOf("skill/") === 0) {
      var skillName = decodeURIComponent(hash.substring(6));
      setTimeout(function () { openDetail(skillName); }, 0);
      return true;
    }
    var params = new URLSearchParams(hash);
    if (params.get("sort")) { currentSort = params.get("sort"); el("sort-select").value = currentSort; }
    if (params.get("cat")) { currentCategory = params.get("cat"); el("category-filter").value = currentCategory; }
    if (params.get("tier")) { currentTier = params.get("tier"); el("tier-filter").value = currentTier; }
    if (params.get("q")) { currentSearch = params.get("q"); el("search-input").value = currentSearch; }
    return false;
  }
  function writeHashState() {
    if (currentDetailSkill) return;
    var params = new URLSearchParams();
    if (currentSort !== "tier-usage") params.set("sort", currentSort);
    if (currentCategory) params.set("cat", currentCategory);
    if (currentTier) params.set("tier", currentTier);
    if (currentSearch) params.set("q", currentSearch);
    var hash = params.toString();
    if (hash) window.history.replaceState(null, "", "#" + hash);
    else window.history.replaceState(null, "", window.location.pathname);
  }

  function discordBlurb(skill) {
    return "**" + skill.name + "** — " + skill.category + " · " + TIER_LABELS[skill.tier] + "\n" +
      skill.description + "\n" +
      "Install: `hermes skills install " + skill.install_url + "`\n" +
      HC.canonicalSkillUrl(skill.name);
  }

  // ============ HERO STATS ============
  function renderHeroStats(data) {
    var tierCount = { core: 0, featured: 0, utility: 0 };
    data.skills.forEach(function (s) { if (tierCount[s.tier] !== undefined) tierCount[s.tier]++; });
    el("stat-total").textContent = String(data.portfolio.total_skills);
    el("stat-categories").textContent = String(Object.keys(data.categories).length);
    el("stat-core").textContent = String(tierCount.core);
  }

  // ============ RAIL — Core skills (Featured) ============
  function renderFeaturedRail(data) {
    var track = el("rail-featured-track");
    var core = data.skills.filter(function (s) { return s.tier === "core"; });
    el("rail-featured-desc").textContent = core.length + " core skill" + (core.length === 1 ? "" : "s") + " — " + TIER_DESCS.core.toLowerCase();
    track.innerHTML = "";
    if (!core.length) { track.innerHTML = '<p class="rail-loading mono">No core-tier skills yet.</p>'; return; }
    var frag = document.createDocumentFragment();
    core.forEach(function (s) { frag.appendChild(makeRailCard(s, data.categories)); });
    track.appendChild(frag);
  }
  function makeRailCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var a = document.createElement("a");
    a.className = "rail-card";
    a.href = "#skill/" + encodeURIComponent(skill.name);
    a.setAttribute("role", "listitem");
    a.innerHTML =
      '<span class="tier-badge ' + skill.tier + '">' + TIER_LABELS[skill.tier] + '</span>' +
      '<span class="rail-card-name">' + HC.escapeHtml(skill.name) + '</span>' +
      '<span class="rail-card-cat mono">' + HC.escapeHtml(catName) + '</span>' +
      '<p class="rail-card-desc">' + HC.escapeHtml(skill.description) + '</p>';
    return a;
  }

  // ============ BROWSE — by category ============
  function renderCategoryGrid(data) {
    var grid = el("category-grid");
    grid.innerHTML = "";
    var keys = Object.keys(data.categories).sort(function (a, b) {
      return data.categories[b].skill_count - data.categories[a].skill_count;
    });
    var frag = document.createDocumentFragment();
    keys.forEach(function (key) {
      var cat = data.categories[key];
      var card = document.createElement("button");
      card.type = "button";
      card.className = "browse-card";
      card.setAttribute("role", "listitem");
      card.innerHTML =
        '<span class="browse-card-count mono">' + cat.skill_count + '</span>' +
        '<span class="browse-card-name">' + HC.escapeHtml(cat.name) + '</span>' +
        '<p class="browse-card-desc">' + HC.escapeHtml(cat.description) + '</p>';
      card.addEventListener("click", function () {
        currentCategory = key;
        el("category-filter").value = key;
        writeHashState();
        renderGrid();
        scrollToGrid();
      });
      frag.appendChild(card);
    });
    grid.appendChild(frag);
  }

  // ============ BROWSE — by tier ============
  function renderTierGrid(data) {
    var grid = el("tier-grid");
    grid.innerHTML = "";
    var tierCount = { core: 0, featured: 0, utility: 0 };
    data.skills.forEach(function (s) { if (tierCount[s.tier] !== undefined) tierCount[s.tier]++; });
    var frag = document.createDocumentFragment();
    ["core", "featured", "utility"].forEach(function (tier) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "browse-card tier-card " + tier;
      card.setAttribute("role", "listitem");
      card.innerHTML =
        '<span class="browse-card-count mono">' + tierCount[tier] + '</span>' +
        '<span class="browse-card-name">' + TIER_LABELS[tier] + '</span>' +
        '<p class="browse-card-desc">' + TIER_DESCS[tier] + '</p>';
      card.addEventListener("click", function () {
        currentTier = tier;
        el("tier-filter").value = tier;
        writeHashState();
        renderGrid();
        scrollToGrid();
      });
      frag.appendChild(card);
    });
    grid.appendChild(frag);
  }

  function scrollToGrid() {
    var target = el("all-skills");
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ============ QUICKSTART (graphite band) — the page's one real hero type-in ============
  // Types a REAL skill's REAL install command (from skills-index.json) into the code
  // element character-by-character. Runs once per page load, never on re-render.
  var quickstartTypedIn = false;

  function typeInText(node, text, opts) {
    opts = opts || {};
    var minMs = opts.minMs || 30;
    var maxMs = opts.maxMs || 45;
    var onDone = opts.onDone || function () {};
    var i = 0;
    node.textContent = "";
    (function step() {
      if (i >= text.length) { onDone(); return; }
      i++;
      node.textContent = text.slice(0, i);
      setTimeout(step, minMs + Math.random() * (maxMs - minMs));
    })();
  }

  function renderQuickstart(data) {
    var example = data.skills.filter(function (s) { return s.tier === "core"; })[0] || data.skills[0];
    if (!example) return;
    var cmd = "hermes skills install " + example.install_url;
    var codeEl = el("quickstart-install-cmd");
    var btn = el("quickstart-copy-btn");

    function wireCopy() {
      btn.disabled = false;
      btn.removeAttribute("aria-disabled");
      btn.addEventListener("click", function () {
        HC.copyToClipboard(cmd, btn, { restoreLabel: "Copy", toastMsg: "Install command copied" });
      });
    }

    // Screen readers get the full, final string immediately regardless of the
    // visual typing animation — they should never be read the command character by character.
    codeEl.setAttribute("aria-label", cmd);

    if (quickstartTypedIn || prefersReducedMotion()) {
      quickstartTypedIn = true;
      codeEl.textContent = cmd;
      wireCopy();
      return;
    }
    quickstartTypedIn = true;
    typeInText(codeEl, cmd, {
      minMs: 30,
      maxMs: 45,
      onDone: function () {
        var caret = document.createElement("span");
        caret.className = "quickstart-caret";
        caret.setAttribute("aria-hidden", "true");
        codeEl.appendChild(caret);
        wireCopy();
      },
    });
  }

  // ============ FILTER CHIPS ============
  function renderFilterChips() {
    var container = el("active-filters");
    container.innerHTML = "";
    if (currentCategory) {
      var catName = (indexData.categories[currentCategory] || {}).name || currentCategory;
      container.appendChild(makeChip("Category: " + catName, function () { currentCategory = ""; el("category-filter").value = ""; writeHashState(); renderGrid(); }));
    }
    if (currentTier) {
      container.appendChild(makeChip("Tier: " + TIER_LABELS[currentTier], function () { currentTier = ""; el("tier-filter").value = ""; writeHashState(); renderGrid(); }));
    }
    if (currentSearch) {
      container.appendChild(makeChip('Search: "' + currentSearch + '"', function () { currentSearch = ""; el("search-input").value = ""; writeHashState(); renderGrid(); }));
    }
    container.appendChild(makeShareViewButton());
  }
  function makeShareViewButton() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-outline btn-sm share-view-btn";
    btn.textContent = "Share view";
    btn.addEventListener("click", function () {
      HC.copyToClipboard(window.location.href, btn, { restoreLabel: "Share view", toastMsg: "View link copied" });
    });
    return btn;
  }
  function makeChip(label, onRemove) {
    var chip = document.createElement("span"); chip.className = "filter-chip";
    var text = document.createElement("span"); text.textContent = label;
    var btn = document.createElement("button"); btn.type = "button"; btn.textContent = "×";
    btn.setAttribute("aria-label", "Remove filter: " + label);
    btn.addEventListener("click", function (e) { e.stopPropagation(); onRemove(); });
    chip.appendChild(text); chip.appendChild(btn);
    return chip;
  }

  // ============ MAIN GRID ============
  function renderSkillCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var a = document.createElement("a");
    a.className = "skill-card";
    a.href = "#skill/" + encodeURIComponent(skill.name);
    a.setAttribute("role", "listitem");
    a.innerHTML =
      '<div class="skill-card-head">' +
        '<span class="skill-card-name">' + HC.highlightText(skill.name, currentSearch) + '</span>' +
        '<span class="tier-badge ' + skill.tier + '">' + TIER_LABELS[skill.tier] + '</span>' +
      '</div>' +
      '<p class="skill-card-desc">' + HC.highlightText(skill.description, currentSearch) + '</p>' +
      '<div class="skill-card-meta">' +
        '<span class="mono">' + HC.escapeHtml(catName) + '</span>' +
        '<span class="mono">' + HC.escapeHtml(sourceLabel) + '</span>' +
      '</div>' +
      '<span class="skill-card-cta">View details <span aria-hidden="true">→</span></span>';
    return a;
  }

  function renderGrid() {
    if (!indexData) return;
    var skills = filterSkills(sortSkills(indexData.skills, currentSort));
    var grid = el("catalog-grid");
    var noResults = el("no-results");
    grid.innerHTML = "";
    renderFilterChips();
    writeHashState();
    if (skills.length === 0) {
      grid.hidden = true; noResults.hidden = false;
      el("catalog-status").textContent = "0 skills match the current filters.";
      return;
    }
    grid.hidden = false; noResults.hidden = true;
    el("catalog-status").textContent = skills.length + " skill" + (skills.length === 1 ? "" : "s") + " shown of " + indexData.skills.length + ".";
    var frag = document.createDocumentFragment();
    skills.forEach(function (s) { frag.appendChild(renderSkillCard(s, indexData.categories)); });
    grid.appendChild(frag);
  }

  function populateCategoryFilter(categories) {
    var sel = el("category-filter");
    Object.keys(categories).sort().forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = categories[key].name + " (" + categories[key].skill_count + ")";
      sel.appendChild(opt);
    });
  }

  // ============ DETAIL OVERLAY ============
  function bulletize(text) {
    if (!text) return "<p>See the SKILL.md tab for full usage instructions.</p>";
    if (text.indexOf("- ") === 0 || text.indexOf("\n- ") !== -1) {
      var lines = text.split("\n");
      var listHtml = "<ul>"; var inList = false; var parts = [];
      lines.forEach(function (line) {
        line = line.trim();
        if (line.indexOf("- ") === 0) { inList = true; listHtml += "<li>" + HC.escapeHtml(line.substring(2)) + "</li>"; }
        else if (line) { if (inList) { listHtml += "</ul>"; inList = false; } parts.push("<p>" + HC.escapeHtml(line) + "</p>"); }
      });
      if (inList) listHtml += "</ul>";
      return parts.join("") + listHtml;
    }
    return "<p>" + HC.escapeHtml(text) + "</p>";
  }

  function openDetail(skillName) {
    var skill = findSkill(skillName);
    if (!skill) return;
    currentDetailSkill = skillName;
    document.body.classList.add("detail-open");
    var overlay = el("detail-overlay");
    overlay.hidden = false;

    var catName = indexData.categories[skill.category] ? indexData.categories[skill.category].name : skill.category;
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var installCmd = "hermes skills install " + skill.install_url;

    el("detail-name").textContent = skill.name;
    var tierBadge = el("detail-tier");
    tierBadge.textContent = TIER_LABELS[skill.tier];
    tierBadge.className = "tier-badge " + skill.tier;
    el("detail-desc").textContent = skill.description;

    var metaHtml = '<span><strong>Category:</strong> ' + HC.escapeHtml(catName) + '</span>' +
      '<span><strong>Tier:</strong> ' + TIER_DESCS[skill.tier] + '</span>' +
      '<span><strong>Source:</strong> ' + HC.escapeHtml(sourceLabel) + '</span>';
    if (skill.recency) metaHtml += '<span><strong>Updated:</strong> ' + HC.escapeHtml(skill.recency) + '</span>';
    el("detail-meta").innerHTML = metaHtml;

    el("detail-user-use").textContent = skill.user_use || skill.description;
    el("detail-agent-use").innerHTML = bulletize(skill.agent_use);

    el("detail-install-cmd").textContent = installCmd;
    var installBtn = el("detail-copy-btn");
    installBtn.onclick = function () { HC.copyToClipboard(installCmd, installBtn, { restoreLabel: "Copy", toastMsg: "Install command copied" }); };

    el("detail-skillmd-link").href = skill.install_url;

    var sourceLink = el("detail-source-link");
    var originUrl = skill.source_attribution && skill.source_attribution.origin_url;
    if (originUrl) { sourceLink.href = originUrl; sourceLink.hidden = false; }
    else { sourceLink.hidden = true; }

    el("detail-skillmd-content").textContent = skill.skillmd_content || "SKILL.md content not available.";
    el("detail-readme-content").textContent = skill.readme_content || "README.md content not available.";

    var link = HC.canonicalSkillUrl(skill.name);
    var copyLinkBtn = el("detail-copy-link-btn");
    copyLinkBtn.textContent = "Copy link";
    copyLinkBtn.classList.remove("is-success");
    copyLinkBtn.onclick = function () { HC.copyToClipboard(link, copyLinkBtn, { restoreLabel: "Copy link", toastMsg: "Skill link copied" }); };

    var blurb = discordBlurb(skill);
    var copyDiscordBtn = el("detail-copy-discord-btn");
    copyDiscordBtn.textContent = "Copy Discord blurb";
    copyDiscordBtn.classList.remove("is-success");
    copyDiscordBtn.onclick = function () { HC.copyToClipboard(blurb, copyDiscordBtn, { restoreLabel: "Copy Discord blurb", toastMsg: "Discord blurb copied" }); };
    var preview = el("detail-discord-preview");
    preview.textContent = blurb;
    preview.hidden = false;

    switchDetailTab("overview");
    window.history.replaceState(null, "", "#skill/" + encodeURIComponent(skillName));
    overlay.scrollTop = 0;
    el("detail-close").focus();
  }

  function closeDetail() {
    document.body.classList.remove("detail-open");
    el("detail-overlay").hidden = true;
    currentDetailSkill = null;
    var params = new URLSearchParams();
    if (currentSort !== "tier-usage") params.set("sort", currentSort);
    if (currentCategory) params.set("cat", currentCategory);
    if (currentTier) params.set("tier", currentTier);
    if (currentSearch) params.set("q", currentSearch);
    var hash = params.toString();
    if (hash) window.history.replaceState(null, "", "#" + hash);
    else window.history.replaceState(null, "", window.location.pathname);
  }

  function switchDetailTab(tabName) {
    document.querySelectorAll(".detail-tab").forEach(function (t) {
      var active = t.getAttribute("data-tab") === tabName;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".detail-tab-content").forEach(function (c) { c.classList.remove("active"); });
    el("tab-" + tabName).classList.add("active");
  }

  function setupDetailEvents() {
    el("detail-close").addEventListener("click", closeDetail);
    el("detail-overlay").addEventListener("click", function (e) { if (e.target === this) closeDetail(); });
    document.querySelectorAll(".detail-tab").forEach(function (tab) {
      tab.addEventListener("click", function () { switchDetailTab(tab.getAttribute("data-tab")); });
    });
  }

  // ============ CONTROLS ============
  function setControlsEnabled(enabled) {
    ["sort-select", "category-filter", "tier-filter", "search-input"].forEach(function (id) {
      var node = el(id);
      node.disabled = !enabled;
      if (enabled) node.removeAttribute("aria-disabled"); else node.setAttribute("aria-disabled", "true");
    });
  }

  function setupControls() {
    el("sort-select").addEventListener("change", function (e) { currentSort = e.target.value; renderGrid(); });
    el("category-filter").addEventListener("change", function (e) { currentCategory = e.target.value; renderGrid(); });
    el("tier-filter").addEventListener("change", function (e) { currentTier = e.target.value; renderGrid(); });
    var searchTimer = null;
    el("search-input").addEventListener("input", function (e) {
      currentSearch = e.target.value;
      if (searchTimer) clearTimeout(searchTimer);
      searchTimer = setTimeout(renderGrid, 150);
    });
    el("catalog-controls").addEventListener("submit", function (e) { e.preventDefault(); });
    el("clear-filters-btn").addEventListener("click", function () {
      currentSort = "tier-usage"; currentCategory = ""; currentTier = ""; currentSearch = "";
      el("sort-select").value = "tier-usage";
      el("category-filter").value = "";
      el("tier-filter").value = "";
      el("search-input").value = "";
      renderGrid();
    });
  }

  function setupBackToTop() {
    var btn = el("back-to-top");
    window.addEventListener("scroll", function () { btn.hidden = window.scrollY < 600; }, { passive: true });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  function setupKeyboard() {
    document.addEventListener("keydown", function (e) {
      var typing = e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA";
      if (e.key === "Escape") { if (currentDetailSkill) closeDetail(); return; }
      if (typing) return;
      if (e.key === "r" || e.key === "R") {
        if (!indexData || !indexData.skills.length) return;
        var pick = indexData.skills[Math.floor(Math.random() * indexData.skills.length)];
        window.location.hash = "skill/" + encodeURIComponent(pick.name);
      }
    });
  }

  function showLoadError() {
    el("catalog-status").textContent = "Could not load skills-index.json.";
    el("hero-heading").textContent = "Skills your Hermes agent can just install.";
    el("rail-featured-track").innerHTML = '<p class="rail-loading mono">Could not load skill data.</p>';
    el("category-grid").innerHTML = '<p class="rail-loading mono">Could not load skill data.</p>';
    el("tier-grid").innerHTML = '<p class="rail-loading mono">Could not load skill data.</p>';
  }

  // ============ HERO REVEAL ============
  // The page's one hero *type-in* lives on the quickstart install command (see
  // renderQuickstart / typeInText below) — design.md allows exactly one. The H1
  // uses the shared .reveal fade+rise utility instead ("everywhere else: reveal or none").
  function initHeroReveal() {
    var heading = el("hero-heading");
    heading.classList.add("reveal");
    if (prefersReducedMotion()) { heading.classList.add("is-in"); return; }
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { heading.classList.add("is-in"); });
    });
  }

  function init() {
    setControlsEnabled(false);
    initHeroReveal();
    el("hero-search-btn").addEventListener("click", function () {
      var trigger = el("cmdk-trigger");
      if (trigger) trigger.click();
    });
    setupDetailEvents();
    setupBackToTop();
    setupKeyboard();

    HC.loadIndex(function (data) {
      if (!data) { showLoadError(); return; }
      indexData = data;
      var totalDesc = el("catalog-total-desc");
      if (totalDesc) totalDesc.textContent = "All " + data.skills.length + " skills — sort, filter, or search to narrow it down.";
      renderHeroStats(data);
      renderFeaturedRail(data);
      renderCategoryGrid(data);
      renderTierGrid(data);
      renderQuickstart(data);
      populateCategoryFilter(data.categories || {});
      setupControls();
      setControlsEnabled(true);
      var openedDetail = readHashState();
      renderGrid();
      if (!openedDetail) { /* grid already reflects hash state */ }
      window.addEventListener("hashchange", function () {
        var isSkill = readHashState();
        if (!isSkill) renderGrid();
      });
      HC.initCmdk(data);
      HC.initReveal(document);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
