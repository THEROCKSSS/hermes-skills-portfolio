// Hermes Skills Portfolio — site renderer
// Reads skills-index.json, renders sortable/filterable skill cards.

(function () {
  "use strict";

  var indexData = null;
  var currentSort = "tier-usage";
  var currentCategory = "";
  var currentTier = "";
  var currentSearch = "";

  // Tier order for default sort
  var TIER_ORDER = { core: 0, featured: 1, utility: 2 };

  function loadIndex(cb) {
    fetch("../skills-index.json")
      .then(function (r) { return r.json(); })
      .then(function (data) { cb(data); })
      .catch(function (err) {
        document.getElementById("skill-grid").innerHTML =
          '<p class="empty-state">Could not load skills-index.json: ' + err.message + "</p>";
      });
  }

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

  function filterSkills(skills) {
    return skills.filter(function (s) {
      if (currentCategory && s.category !== currentCategory) return false;
      if (currentTier && s.tier !== currentTier) return false;
      if (currentSearch) {
        var q = currentSearch.toLowerCase();
        var hay = (s.name + " " + s.description + " " + s.category).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  function renderSkillCard(skill, categories) {
    var catName = categories[skill.category] ? categories[skill.category].name : skill.category;
    var installCmd = "hermes skills install " + skill.install_url;
    var div = document.createElement("div");
    div.className = "skill-card";
    div.innerHTML =
      '<div class="skill-card-header">' +
        '<a class="skill-name" href="' + skill.path + "/SKILL.md" + '">' + escapeHtml(skill.name) + "</a>" +
        '<span class="tier-badge ' + skill.tier + '">' + skill.tier + "</span>" +
      "</div>" +
      '<p class="skill-desc">' + escapeHtml(skill.description) + "</p>" +
      '<div class="skill-meta">' +
        '<span class="skill-cat">' + escapeHtml(catName) + "</span>" +
        (skill.usage ? '<span>' + totalUsage(skill) + " installs</span>" : "") +
        (skill.recency ? '<span>updated ' + escapeHtml(skill.recency) + "</span>" : "") +
        '<a class="skill-install" href="' + skill.install_url + '" title="' + escapeHtml(installCmd) + '">install →</a>' +
      "</div>";
    return div;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function render() {
    if (!indexData) return;
    var skills = filterSkills(sortSkills(indexData.skills, currentSort));
    var grid = document.getElementById("skill-grid");
    grid.innerHTML = "";
    if (skills.length === 0) {
      grid.innerHTML = '<p class="empty-state">No skills match the current filters.</p>';
      return;
    }
    var frag = document.createDocumentFragment();
    for (var i = 0; i < skills.length; i++) {
      frag.appendChild(renderSkillCard(skills[i], indexData.categories));
    }
    grid.appendChild(frag);
  }

  function populateCategoryFilter(categories) {
    var sel = document.getElementById("category-filter");
    var keys = Object.keys(categories).sort();
    for (var i = 0; i < keys.length; i++) {
      var opt = document.createElement("option");
      opt.value = keys[i];
      opt.textContent = categories[keys[i]].name;
      sel.appendChild(opt);
    }
  }

  function updateCount(n) {
    document.getElementById("skill-count").textContent = n + " skill" + (n === 1 ? "" : "s");
  }

  function init() {
    loadIndex(function (data) {
      indexData = data;
      populateCategoryFilter(data.categories || {});
      updateCount(data.skills.length);
      render();
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
