// Hermes Skills Portfolio — site renderer
// Fetches skills-index.json, renders sortable/filterable/expanding skill cards.
// Tries multiple fetch paths to work both locally and on GitHub Pages.

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
  var SOURCE_LABELS = { new: "Newly authored", generalized: "Generalized", adapted: "Adapted" };

  // --- Data loading ---

  function loadIndex(cb) {
    // Try multiple paths: ./skills-index.json (root), ../skills-index.json (site/ subdir)
    var paths = ["./skills-index.json", "../skills-index.json", "/skills-index.json"];
    var tried = 0;

    function tryNext() {
      if (tried >= paths.length) {
        document.getElementById("skill-grid").innerHTML =
          '<p class="empty-state">Could not load skills-index.json. Make sure the file exists at the repo root.</p>';
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

  // --- Rendering ---

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderSkillCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var usage = totalUsage(skill);
    var sourceLabel = SOURCE_LABELS[skill.source] || skill.source;
    var installCmd = "hermes skills install " + skill.install_url;

    var div = document.createElement("div");
    div.className = "skill-card";
    div.setAttribute("data-skill", skill.name);

    var headerHtml =
      '<div class="skill-card-header">' +
        '<a class="skill-name" href="' + escapeHtml(skill.install_url) + '" target="_blank" rel="noopener">' + escapeHtml(skill.name) + '</a>' +
        '<span class="tier-badge ' + skill.tier + '">' + TIER_LABELS[skill.tier] + '</span>' +
      '</div>' +
      '<p class="skill-desc">' + escapeHtml(skill.description) + '</p>' +
      '<div class="skill-meta">' +
        '<span class="skill-cat">' + escapeHtml(catName) + '</span>' +
        '<span class="skill-source">' + escapeHtml(sourceLabel) + '</span>' +
        (usage > 0 ? '<span>' + usage + ' installs</span>' : '<span>new</span>') +
        (skill.recency ? '<span>updated ' + escapeHtml(skill.recency) + '</span>' : '') +
        '<a class="skill-install" href="' + escapeHtml(skill.install_url) + '" target="_blank" rel="noopener">SKILL.md ↗</a>' +
      '</div>';

    var detailHtml =
      '<div class="skill-detail">' +
        '<div class="skill-detail-grid">' +
          '<div class="skill-detail-section">' +
            '<h4>Category</h4><p>' + escapeHtml(catName) + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Tier</h4><p>' + TIER_LABELS[skill.tier] + ' — ' + tierDescription(skill.tier) + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Source</h4><p>' + escapeHtml(sourceLabel) + (skill.source_attribution ? ' (from ' + escapeHtml(skill.source_attribution) + ')' : '') + '</p>' +
          '</div>' +
          '<div class="skill-detail-section">' +
            '<h4>Version</h4><p>' + escapeHtml((skill.frontmatter && skill.frontmatter.version) || '1.0.0') + '</p>' +
          '</div>' +
        '</div>' +
        '<div class="install-block">' +
          '<h4>Install</h4>' +
          '<code>' + escapeHtml(installCmd) + '</code>' +
        '</div>' +
        '<a class="close-detail" onclick="window.__closeDetail()">Close ↑</a>' +
      '</div>';

    div.innerHTML = headerHtml + detailHtml;
    return div;
  }

  function tierDescription(tier) {
    if (tier === "core") return "Broadly empowering, nearly any user benefits";
    if (tier === "featured") return "Highly useful within a category";
    return "Useful for specific workflows";
  }

  function render() {
    if (!indexData) return;
    var skills = filterSkills(sortSkills(indexData.skills, currentSort));
    var grid = document.getElementById("skill-grid");
    grid.innerHTML = "";

    if (skills.length === 0) {
      grid.innerHTML = '<p class="empty-state">No skills match the current filters.</p>';
      document.getElementById("results-count").textContent = "0 skills match";
      return;
    }

    document.getElementById("results-count").textContent =
      skills.length + " skill" + (skills.length === 1 ? "" : "s") + " shown";

    var frag = document.createDocumentFragment();
    for (var i = 0; i < skills.length; i++) {
      frag.appendChild(renderSkillCard(skills[i], indexData.categories));
    }
    grid.appendChild(frag);

    // Re-expand if there was an expanded card
    if (expandedSkill) {
      var card = grid.querySelector('[data-skill="' + expandedSkill + '"]');
      if (card) card.classList.add("expanded");
    }
  }

  // --- Card expansion ---

  window.__closeDetail = function () {
    document.querySelectorAll(".skill-card.expanded").forEach(function (c) {
      c.classList.remove("expanded");
    });
    expandedSkill = null;
  };

  function setupCardClicks() {
    document.getElementById("skill-grid").addEventListener("click", function (e) {
      // Don't toggle when clicking a link
      if (e.target.tagName === "A" || e.target.tagName === "CODE" || e.target.classList.contains("close-detail")) return;

      var card = e.target.closest(".skill-card");
      if (!card) return;

      var skillName = card.getAttribute("data-skill");

      // Close all other expanded cards
      document.querySelectorAll(".skill-card.expanded").forEach(function (c) {
        if (c !== card) c.classList.remove("expanded");
      });

      // Toggle this card
      if (card.classList.contains("expanded")) {
        card.classList.remove("expanded");
        expandedSkill = null;
      } else {
        card.classList.add("expanded");
        expandedSkill = skillName;
        // Scroll the card into view
        setTimeout(function () {
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 50);
      }
    });
  }

  // --- Category filter population ---

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

  // --- Init ---

  function init() {
    loadIndex(function (data) {
      indexData = data;
      populateCategoryFilter(data.categories || {});
      updateCount(data.skills.length);
      render();
      setupCardClicks();
    });

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
    document.getElementById("search-input").addEventListener("input", function (e) {
      currentSearch = e.target.value;
      render();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
