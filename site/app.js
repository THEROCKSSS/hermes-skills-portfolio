// Hermes Skills Portfolio — app.js
// Dark mode default, light toggle, sort/filter/search, expandable cards,
// copy-to-clipboard, keyboard shortcuts, URL hash state, distribution bar,
// filter chips, back-to-top, toast notifications.
// Hallmark + frontend-design-craft applied: no AI-slop, OKLCH tokens, tabular-nums,
// specific transitions, instant focus rings, prefers-reduced-motion honored.

(function () {
  "use strict";

  var indexData = null;
  var currentSort = "tier-usage";
  var currentCategory = "";
  var currentTier = "";
  var currentSearch = "";
  var expandedSkill = null;

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

  // Category colors for distribution bar
  var CAT_COLORS = {
    devops: "oklch(65% 0.12 145)",
    backend: "oklch(65% 0.12 230)",
    frontend: "oklch(65% 0.12 300)",
    integrations: "oklch(65% 0.12 65)",
    meta: "oklch(65% 0.12 0)",
    utility: "oklch(65% 0.10 180)",
  };

  // --- Theme management ---

  function initTheme() {
    var saved = localStorage.getItem("portfolio-theme");
    if (saved) {
      document.documentElement.setAttribute("data-theme", saved);
    } else {
      // Dark mode default — no need to check prefers-color-scheme
      document.documentElement.setAttribute("data-theme", "dark");
    }
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
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
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
        arr.sort(function (a, b) {
          var t = TIER_ORDER[a.tier] - TIER_ORDER[b.tier];
          return t !== 0 ? t : totalUsage(b) - totalUsage(a);
        });
        break;
      case "usage":
        arr.sort(function (a, b) { return totalUsage(b) - totalUsage(a); });
        break;
      case "recency":
        arr.sort(function (a, b) { return (b.recency || "").localeCompare(a.recency || ""); });
        break;
      case "category":
        arr.sort(function (a, b) {
          var c = (a.category || "").localeCompare(b.category || "");
          return c !== 0 ? c : TIER_ORDER[a.tier] - TIER_ORDER[b.tier];
        });
        break;
      case "alpha":
        arr.sort(function (a, b) { return a.name.localeCompare(b.name); });
        break;
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
        var hay = (s.name + " " + s.description + " " + s.category + " " + s.tier).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  // --- URL hash state ---

  function readHashState() {
    var hash = window.location.hash.substring(1);
    if (!hash) return;
    var params = new URLSearchParams(hash);
    if (params.get("sort")) {
      currentSort = params.get("sort");
      document.getElementById("sort-select").value = currentSort;
    }
    if (params.get("cat")) {
      currentCategory = params.get("cat");
      document.getElementById("category-filter").value = currentCategory;
    }
    if (params.get("tier")) {
      currentTier = params.get("tier");
      document.getElementById("tier-filter").value = currentTier;
    }
    if (params.get("q")) {
      currentSearch = params.get("q");
      document.getElementById("search-input").value = currentSearch;
    }
  }

  function writeHashState() {
    var params = new URLSearchParams();
    if (currentSort !== "tier-usage") params.set("sort", currentSort);
    if (currentCategory) params.set("cat", currentCategory);
    if (currentTier) params.set("tier", currentTier);
    if (currentSearch) params.set("q", currentSearch);
    var hash = params.toString();
    if (hash) {
      window.history.replaceState(null, "", "#" + hash);
    } else {
      window.history.replaceState(null, "", window.location.pathname);
    }
  }

  // --- Rendering ---

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderDistributionBar(categories, skills) {
    var bar = document.getElementById("distribution-bar");
    bar.innerHTML = "";
    var counts = {};
    var total = skills.length;
    for (var i = 0; i < skills.length; i++) {
      var cat = skills[i].category;
      counts[cat] = (counts[cat] || 0) + 1;
    }
    var keys = Object.keys(categories).sort();
    for (var j = 0; j < keys.length; j++) {
      var key = keys[j];
      var count = counts[key] || 0;
      if (count === 0) continue;
      var seg = document.createElement("div");
      seg.className = "dist-segment";
      seg.setAttribute("data-cat", key);
      seg.style.flex = count;
      seg.title = categories[key].name + ": " + count;
      seg.setAttribute("role", "img");
      seg.setAttribute("aria-label", categories[key].name + ": " + count + " skills");
      bar.appendChild(seg);
    }
  }

  function renderFilterChips() {
    var container = document.getElementById("active-filters");
    container.innerHTML = "";
    if (currentCategory) {
      container.appendChild(makeChip("Category: " + currentCategory, function() {
        currentCategory = "";
        document.getElementById("category-filter").value = "";
        writeHashState();
        render();
      }));
    }
    if (currentTier) {
      container.appendChild(makeChip("Tier: " + TIER_LABELS[currentTier], function() {
        currentTier = "";
        document.getElementById("tier-filter").value = "";
        writeHashState();
        render();
      }));
    }
    if (currentSearch) {
      container.appendChild(makeChip('Search: "' + currentSearch + '"', function() {
        currentSearch = "";
        document.getElementById("search-input").value = "";
        writeHashState();
        render();
      }));
    }
  }

  function makeChip(label, onRemove) {
    var chip = document.createElement("span");
    chip.className = "filter-chip";
    var text = document.createElement("span");
    text.textContent = label;
    var btn = document.createElement("button");
    btn.textContent = "\u00d7";
    btn.setAttribute("aria-label", "Remove filter: " + label);
    btn.onclick = function(e) { e.stopPropagation(); onRemove(); };
    chip.appendChild(text);
    chip.appendChild(btn);
    return chip;
  }

  function renderSkillCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var usage = totalUsage(skill);
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var installCmd = "hermes skills install " + skill.install_url;
    var version = (skill.frontmatter && skill.frontmatter.version) || "1.0.0";

    var div = document.createElement("div");
    div.className = "skill-card";
    div.setAttribute("data-skill", skill.name);
    div.setAttribute("tabindex", "0");

    var headerHtml =
      '<div class="skill-card-header">' +
        '<a class="skill-name" href="' + escapeHtml(skill.install_url) + '" target="_blank" rel="noopener">' + escapeHtml(skill.name) + '</a>' +
        '<span class="tier-badge ' + skill.tier + '">' + TIER_LABELS[skill.tier] + '</span>' +
      '</div>' +
      '<p class="skill-desc">' + escapeHtml(skill.description) + '</p>' +
      '<div class="skill-meta">' +
        '<span class="skill-cat">' + escapeHtml(catName) + '</span>' +
        '<span class="skill-source">' + escapeHtml(sourceLabel) + '</span>' +
        (skill.recency ? '<span class="skill-recency">' + escapeHtml(skill.recency) + '</span>' : '') +
        '<a class="skill-install-link" href="' + escapeHtml(skill.install_url) + '" target="_blank" rel="noopener">SKILL.md \u2197</a>' +
      '</div>';

    var detailHtml =
      '<div class="skill-detail">' +
        '<div class="skill-detail-grid">' +
          '<div class="skill-detail-section">' +
            '<h4>Category</h4><p>' + escapeHtml(catName) + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Tier</h4><p>' + TIER_LABELS[skill.tier] + ' \u2014 ' + TIER_DESCS[skill.tier] + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Source</h4><p>' + escapeHtml(sourceLabel) + (skill.source_attribution ? ' (from ' + escapeHtml(skill.source_attribution) + ')' : '') + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Version</h4><p>' + escapeHtml(version) + '</p>' +
          '</div>' +
        '</div>' +
        '<div class="install-block">' +
          '<h4>Install</h4>' +
          '<code id="install-cmd-' + escapeHtml(skill.name) + '">' + escapeHtml(installCmd) + '</code>' +
          '<button class="copy-btn" data-clipboard="' + escapeHtml(installCmd) + '">Copy</button>' +
        '</div>' +
        '<button class="close-detail" type="button">Close \u2191</button>' +
      '</div>';

    div.innerHTML = headerHtml + detailHtml;
    return div;
  }

  function render() {
    if (!indexData) return;
    var skills = filterSkills(sortSkills(indexData.skills, currentSort));
    var grid = document.getElementById("skill-grid");
    var noResults = document.getElementById("no-results");
    grid.innerHTML = "";

    renderFilterChips();
    writeHashState();

    if (skills.length === 0) {
      grid.hidden = true;
      noResults.hidden = false;
      document.getElementById("results-count").textContent = "0 skills match";
      return;
    }

    grid.hidden = false;
    noResults.hidden = true;
    document.getElementById("results-count").textContent =
      skills.length + " skill" + (skills.length === 1 ? "" : "s") + " shown";

    var frag = document.createDocumentFragment();
    for (var i = 0; i < skills.length; i++) {
      frag.appendChild(renderSkillCard(skills[i], indexData.categories));
    }
    grid.appendChild(frag);

    if (expandedSkill) {
      var card = grid.querySelector('[data-skill="' + expandedSkill + '"]');
      if (card) card.classList.add("expanded");
    }
  }

  // --- Toast ---

  var toastTimer = null;
  function showToast(msg) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();
    var toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = msg;
    document.body.appendChild(toast);
    requestAnimationFrame(function() {
      toast.classList.add("show");
    });
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() {
      toast.classList.remove("show");
      setTimeout(function() { toast.remove(); }, 200);
    }, 1800);
  }

  // --- Copy to clipboard ---

  function copyToClipboard(text, btn) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function() {
        btn.classList.add("copied");
        btn.textContent = "Copied!";
        showToast("Install command copied");
        setTimeout(function() {
          btn.classList.remove("copied");
          btn.textContent = "Copy";
        }, 2000);
      });
    } else {
      // Fallback
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      btn.classList.add("copied");
      btn.textContent = "Copied!";
      showToast("Install command copied");
      setTimeout(function() {
        btn.classList.remove("copied");
        btn.textContent = "Copy";
      }, 2000);
    }
  }

  // --- Card expansion ---

  function closeAllExpanded() {
    document.querySelectorAll(".skill-card.expanded").forEach(function (c) {
      c.classList.remove("expanded");
    });
    expandedSkill = null;
  }

  function setupCardClicks() {
    document.getElementById("skill-grid").addEventListener("click", function (e) {
      // Handle copy button
      if (e.target.classList.contains("copy-btn")) {
        e.stopPropagation();
        var text = e.target.getAttribute("data-clipboard");
        copyToClipboard(text, e.target);
        return;
      }
      // Handle close button
      if (e.target.classList.contains("close-detail")) {
        e.stopPropagation();
        closeAllExpanded();
        return;
      }
      // Don't toggle when clicking a link
      if (e.target.tagName === "A") return;

      var card = e.target.closest(".skill-card");
      if (!card) return;

      var skillName = card.getAttribute("data-skill");

      document.querySelectorAll(".skill-card.expanded").forEach(function (c) {
        if (c !== card) c.classList.remove("expanded");
      });

      if (card.classList.contains("expanded")) {
        card.classList.remove("expanded");
        expandedSkill = null;
      } else {
        card.classList.add("expanded");
        expandedSkill = skillName;
        setTimeout(function () {
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 50);
      }
    });

    // Keyboard: Enter/Space to expand focused card
    document.getElementById("skill-grid").addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        var card = e.target.closest(".skill-card");
        if (card && e.target === card) {
          e.preventDefault();
          card.click();
        }
      }
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

  function updateCount(n) {
    document.getElementById("skill-count").textContent = n + " skill" + (n === 1 ? "" : "s");
  }

  // --- Back to top ---

  function setupBackToTop() {
    var btn = document.getElementById("back-to-top");
    window.addEventListener("scroll", function () {
      if (window.scrollY > 600) {
        btn.hidden = false;
      } else {
        btn.hidden = true;
      }
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // --- Keyboard shortcuts ---

  function setupKeyboard() {
    document.addEventListener("keydown", function (e) {
      // Don't intercept when typing in an input
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") {
        if (e.key === "Escape") {
          e.target.blur();
        }
        return;
      }

      if (e.key === "/") {
        e.preventDefault();
        document.getElementById("search-input").focus();
      } else if (e.key === "Escape") {
        if (expandedSkill) {
          closeAllExpanded();
        }
      } else if (e.key === "t" || e.key === "T") {
        toggleTheme();
      }
    });
  }

  // --- Clear filters ---

  function setupClearFilters() {
    document.getElementById("clear-filters-btn").addEventListener("click", function () {
      currentSort = "tier-usage";
      currentCategory = "";
      currentTier = "";
      currentSearch = "";
      document.getElementById("sort-select").value = "tier-usage";
      document.getElementById("category-filter").value = "";
      document.getElementById("tier-filter").value = "";
      document.getElementById("search-input").value = "";
      writeHashState();
      render();
    });
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
    });

    document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
    document.getElementById("sort-select").addEventListener("change", function (e) {
      currentSort = e.target.value;
      render();
    });
    document.getElementById("category-filter").addEventListener("change", function (e) {
      currentCategory = e.target.value;
      render();
    });
    document.getElementById("tier-filter").addEventListener("change", function (e) {
      currentTier = e.target.value;
      render();
    });

    var searchTimer = null;
    document.getElementById("search-input").addEventListener("input", function (e) {
      currentSearch = e.target.value;
      if (searchTimer) clearTimeout(searchTimer);
      searchTimer = setTimeout(render, 150);
    });

    setupKeyboard();
    setupBackToTop();
    setupClearFilters();

    // Listen for hash changes (back/forward buttons)
    window.addEventListener("hashchange", function () {
      readHashState();
      render();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
