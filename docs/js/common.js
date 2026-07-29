// Hermes Skills Portfolio — shared foundation (theme, data loading, cmd-k, toast, copy, reveal).
// Every page includes this before its own page script. Do not duplicate this logic per page.
(function (global) {
  "use strict";

  // --- Theme ---
  function initTheme() {
    var saved = localStorage.getItem("portfolio-theme");
    document.documentElement.setAttribute("data-theme", saved || "light");
  }
  function toggleTheme() {
    var current = document.documentElement.getAttribute("data-theme");
    var next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("portfolio-theme", next);
  }
  function wireThemeToggle() {
    var btn = document.getElementById("theme-toggle");
    if (btn) btn.addEventListener("click", toggleTheme);
  }

  // --- Data loading (skills-index.json, tried from a few relative depths) ---
  function loadIndex(cb) {
    var paths = ["./skills-index.json", "../skills-index.json", "/skills-index.json"];
    var tried = 0;
    function tryNext() {
      if (tried >= paths.length) { cb(null); return; }
      fetch(paths[tried++])
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(cb)
        .catch(tryNext);
    }
    tryNext();
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function highlightText(text, q) {
    var escaped = escapeHtml(text);
    if (!q) return escaped;
    var pattern = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    try { return escaped.replace(new RegExp("(" + pattern + ")", "ig"), "<mark>$1</mark>"); }
    catch (e) { return escaped; }
  }

  function canonicalSkillUrl(name) {
    var base = global.location.origin + global.location.pathname.replace(/[^/]*$/, "");
    return base + "skills/" + encodeURIComponent(name) + "/";
  }

  // --- Toast ---
  var toastTimer = null;
  function showToast(msg) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();
    var toast = document.createElement("div");
    toast.className = "toast"; toast.textContent = msg; toast.setAttribute("role", "status"); toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add("show"); });
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove("show"); setTimeout(function () { toast.remove(); }, 200); }, 1800);
  }

  // --- Copy to clipboard ---
  function copyToClipboard(text, btn, opts) {
    opts = opts || {};
    var restoreLabel = opts.restoreLabel || (btn ? btn.textContent : "Copy");
    var toastMsg = opts.toastMsg || "Copied";
    function onSuccess() {
      if (btn) { btn.classList.add("is-success"); btn.textContent = "Copied"; setTimeout(function () { btn.classList.remove("is-success"); btn.textContent = restoreLabel; }, 1800); }
      showToast(toastMsg);
    }
    if (navigator.clipboard) { navigator.clipboard.writeText(text).then(onSuccess); }
    else {
      var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); onSuccess();
    }
  }

  // --- Reveal on scroll ---
  function initReveal(root) {
    var els = (root || document).querySelectorAll(".reveal:not(.is-in)");
    if (!els.length) return;
    if (!("IntersectionObserver" in global)) { els.forEach(function (el) { el.classList.add("is-in"); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
    }, { threshold: 0.15 });
    els.forEach(function (el) { io.observe(el); });
  }

  // --- Cmd-K palette ---
  var cmdk = { indexData: null, backdrop: null, input: null, results: null, selected: -1, filtered: [] };

  function buildCmdkDom() {
    var backdrop = document.createElement("div");
    backdrop.className = "cmdk-backdrop"; backdrop.id = "cmdk-modal";
    backdrop.innerHTML =
      '<div class="cmdk-modal" role="dialog" aria-modal="true" aria-label="Search skills">' +
        '<div class="cmdk-input-row">' +
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
          '<input class="cmdk-input" id="cmdk-input" type="text" placeholder="Search skills by name, keyword, capability…" autocomplete="off" aria-label="Search skills" />' +
          '<kbd>Esc</kbd>' +
        '</div>' +
        '<div class="cmdk-results" id="cmdk-results" role="listbox"></div>' +
      '</div>';
    document.body.appendChild(backdrop);
    cmdk.backdrop = backdrop;
    cmdk.input = backdrop.querySelector("#cmdk-input");
    cmdk.results = backdrop.querySelector("#cmdk-results");

    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeCmdk(); });
    cmdk.input.addEventListener("input", function () { renderCmdkResults(cmdk.input.value); });
    cmdk.input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { closeCmdk(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); moveSelection(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); moveSelection(-1); }
      else if (e.key === "Enter") { e.preventDefault(); goToSelected(); }
    });
  }

  function moveSelection(delta) {
    if (!cmdk.filtered.length) return;
    cmdk.selected = (cmdk.selected + delta + cmdk.filtered.length) % cmdk.filtered.length;
    Array.prototype.forEach.call(cmdk.results.children, function (row, i) {
      row.setAttribute("aria-selected", String(i === cmdk.selected));
    });
    var sel = cmdk.results.children[cmdk.selected];
    if (sel) sel.scrollIntoView({ block: "nearest" });
  }

  function goToSelected() {
    var skill = cmdk.filtered[cmdk.selected] || cmdk.filtered[0];
    if (skill) global.location.href = canonicalSkillUrl(skill.name);
  }

  function renderCmdkResults(q) {
    var skills = (cmdk.indexData && cmdk.indexData.skills) || [];
    var needle = (q || "").toLowerCase();
    var filtered = !needle ? skills.slice(0, 8) : skills.filter(function (s) {
      var hay = (s.name + " " + s.description + " " + s.category).toLowerCase();
      return hay.indexOf(needle) !== -1;
    }).slice(0, 8);
    cmdk.filtered = filtered;
    cmdk.selected = filtered.length ? 0 : -1;
    if (!filtered.length) {
      cmdk.results.innerHTML = '<div class="cmdk-empty">No skills match &ldquo;' + escapeHtml(q) + '&rdquo;.</div>';
      return;
    }
    cmdk.results.innerHTML = filtered.map(function (s, i) {
      return '<div class="cmdk-row" role="option" aria-selected="' + (i === 0 ? "true" : "false") + '" data-name="' + escapeHtml(s.name) + '">' +
        '<span class="cmdk-row-desc"><span class="cmdk-row-name">' + highlightText(s.name, q) + '</span> — ' + highlightText(s.description, q) + '</span>' +
      '</div>';
    }).join("");
    Array.prototype.forEach.call(cmdk.results.children, function (row, i) {
      row.addEventListener("click", function () { cmdk.selected = i; goToSelected(); });
    });
  }

  function openCmdk() {
    if (!cmdk.backdrop) buildCmdkDom();
    cmdk.backdrop.classList.add("is-open");
    renderCmdkResults("");
    cmdk.input.value = "";
    setTimeout(function () { cmdk.input.focus(); }, 10);
  }
  function closeCmdk() {
    if (cmdk.backdrop) cmdk.backdrop.classList.remove("is-open");
    var trigger = document.getElementById("cmdk-trigger");
    if (trigger) trigger.focus();
  }

  function initCmdk(indexData) {
    cmdk.indexData = indexData;
    var trigger = document.getElementById("cmdk-trigger");
    if (trigger) trigger.addEventListener("click", openCmdk);
    document.addEventListener("keydown", function (e) {
      var isTypingTarget = e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); return; }
      if (e.key === "/" && !isTypingTarget) { e.preventDefault(); openCmdk(); return; }
      if (e.key === "t" && !isTypingTarget) { toggleTheme(); return; }
    });
  }

  global.HermesCommon = {
    initTheme: initTheme, toggleTheme: toggleTheme, wireThemeToggle: wireThemeToggle,
    loadIndex: loadIndex, escapeHtml: escapeHtml, highlightText: highlightText, canonicalSkillUrl: canonicalSkillUrl,
    showToast: showToast, copyToClipboard: copyToClipboard, initReveal: initReveal, initCmdk: initCmdk,
  };

  initTheme();
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", wireThemeToggle); }
  else { wireThemeToggle(); }
})(window);
