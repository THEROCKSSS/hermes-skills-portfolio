// Hermes Skills Portfolio — Bundles page. Renders curated bundles from bundles.json,
// resolving each member skill's real name/description/install_url from skills-index.json.
// Never invents skill content — a bundle is a grouping of existing catalog entries only.
(function () {
  "use strict";
  var HC = window.HermesCommon;

  function loadBundles(cb) {
    HC.loadJsonWithFallback(["./bundles.json", "../bundles.json", "/bundles.json"], cb);
  }

  function skillInstallCmd(skill) {
    return "hermes skills install " + skill.install_url;
  }

  function renderBundle(bundle, skillsByName) {
    var members = bundle.skills
      .map(function (name) { return skillsByName[name]; })
      .filter(Boolean);

    var item = document.createElement("div");
    item.className = "bundle-item";

    var head = document.createElement("button");
    head.type = "button";
    head.className = "bundle-head";
    head.setAttribute("aria-expanded", "false");
    head.innerHTML =
      '<div class="bundle-heading-text">' +
        '<div class="bundle-name">' + HC.escapeHtml(bundle.name) + '</div>' +
        '<p class="bundle-oneliner">' + HC.escapeHtml(bundle.one_liner) + '</p>' +
        '<div class="bundle-count">' + members.length + ' skill' + (members.length === 1 ? "" : "s") + '</div>' +
      '</div>' +
      '<svg class="bundle-chevron" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';

    var body = document.createElement("div");
    body.className = "bundle-body";
    var bodyInner = document.createElement("div");
    bodyInner.className = "bundle-body-inner";

    var list = document.createElement("ul");
    list.className = "bundle-skills";
    members.forEach(function (skill) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.className = "bundle-skill-row";
      a.href = HC.canonicalSkillUrl(skill.name);
      a.innerHTML =
        '<span class="bundle-skill-name">' + HC.escapeHtml(skill.name) + '</span>' +
        '<span class="bundle-skill-desc">' + HC.escapeHtml(skill.description) + '</span>';
      li.appendChild(a);
      list.appendChild(li);
    });

    var actions = document.createElement("div");
    actions.className = "bundle-actions";
    var copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "btn btn-outline";
    copyBtn.textContent = "Copy all install commands";
    copyBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var text = members.map(skillInstallCmd).join("\n");
      HC.copyToClipboard(text, copyBtn, { restoreLabel: "Copy all install commands", toastMsg: members.length + " install commands copied" });
    });
    actions.appendChild(copyBtn);

    bodyInner.appendChild(list);
    bodyInner.appendChild(actions);
    body.appendChild(bodyInner);

    head.addEventListener("click", function () {
      var isOpen = item.classList.toggle("is-open");
      head.setAttribute("aria-expanded", String(isOpen));
    });

    item.appendChild(head);
    item.appendChild(body);
    return item;
  }

  function init() {
    var list = document.getElementById("bundles-list");
    HC.loadIndex(function (indexData) {
      if (!indexData) { list.innerHTML = '<p class="bundles-loading">Could not load the skill index.</p>'; return; }
      var skillsByName = {};
      indexData.skills.forEach(function (s) { skillsByName[s.name] = s; });

      loadBundles(function (bundleData) {
        if (!bundleData || !bundleData.bundles || !bundleData.bundles.length) {
          list.innerHTML = '<p class="bundles-loading">No bundles yet.</p>';
          return;
        }
        list.innerHTML = "";
        var frag = document.createDocumentFragment();
        bundleData.bundles.forEach(function (b) { frag.appendChild(renderBundle(b, skillsByName)); });
        list.appendChild(frag);
        HC.initReveal();
      });

      HC.initCmdk(indexData);
    });
  }

  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); }
  else { init(); }
})();
