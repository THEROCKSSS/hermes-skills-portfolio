// Hermes Skills Portfolio — per-skill static page script.
// Wires: cmd-k search data (via HermesCommon), the install-command copy
// button, and the Overview / SKILL.md / README tab strip. Nothing here
// re-implements theme, cmd-k, toast, or copy — those all come from
// window.HermesCommon (site/js/common.js), included before this file.
(function () {
  "use strict";
  var HC = window.HermesCommon;

  function initTabs() {
    var tabs = document.querySelectorAll(".detail-tab");
    if (!tabs.length) return;
    Array.prototype.forEach.call(tabs, function (tab) {
      tab.addEventListener("click", function () {
        Array.prototype.forEach.call(tabs, function (t) {
          t.classList.remove("active");
          t.setAttribute("aria-selected", "false");
        });
        document.querySelectorAll(".detail-tab-content").forEach(function (c) {
          c.classList.remove("active");
        });
        tab.classList.add("active");
        tab.setAttribute("aria-selected", "true");
        var panel = document.getElementById("tab-" + tab.getAttribute("data-tab"));
        if (panel) panel.classList.add("active");
      });
    });
  }

  function initCopyInstall() {
    var btn = document.getElementById("copy-btn");
    var code = document.getElementById("install-cmd");
    if (!btn || !code || !HC) return;
    btn.addEventListener("click", function () {
      HC.copyToClipboard(code.textContent, btn, { restoreLabel: "Copy", toastMsg: "Install command copied" });
    });
  }

  function initSearch() {
    if (!HC) return;
    HC.loadIndex(function (data) {
      if (data) HC.initCmdk(data);
    });
  }

  function init() {
    initTabs();
    initCopyInstall();
    initSearch();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
