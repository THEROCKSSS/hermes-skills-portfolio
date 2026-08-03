// Hermes Skills Portfolio — shared foundation (theme, data loading, cmd-k, toast, copy, reveal).
// Every page includes this before its own page script. Do not duplicate this logic per page.
(function (global) {
  "use strict";

  // --- Theme ---
  function initTheme() {
    // Dusk is a dark-primary theme (see design.md). Light stays available
    // as an explicit opt-in for anyone who already toggled it.
    var saved = localStorage.getItem("portfolio-theme");
    document.documentElement.setAttribute("data-theme", saved || "dark");
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

  // --- Data loading ---
  // One seam for "fetch a JSON file, trying a few relative-path depths, because
  // the same page can be served from different directory depths." Previously
  // reimplemented verbatim in bundles.js and submit.js for their own data files —
  // consolidated here after an architecture review found the duplication.
  function loadJsonWithFallback(paths, cb) {
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
  function loadIndex(cb) {
    loadJsonWithFallback(["./skills-index.json", "../skills-index.json", "/skills-index.json"], cb);
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
    // threshold: 0 (not a percentage) — a percentage threshold breaks for any section taller
    // than ~1/threshold viewport heights, since that fraction of its box can never be
    // simultaneously visible (bit us with the Submit page's pending-sources section, which
    // never satisfied a 0.15 threshold once it grew past ~5000px). Firing as soon as any
    // pixel is visible is correct for a reveal-once effect regardless of element height.
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
    }, { threshold: 0 });
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
          '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
          '<input class="cmdk-input" id="cmdk-input" type="text" placeholder="Search skills by name, keyword, capability…" autocomplete="off" aria-label="Search skills" />' +
          '<kbd>Esc</kbd>' +
        '</div>' +
        '<div class="cmdk-results" id="cmdk-results" role="listbox"></div>' +
        '<p class="cmdk-hint">Scope with <code>cat:devops</code> or <code>tier:core</code> &middot; arrows to move, Enter to open</p>' +
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
    var parsed = parseQuery(q);
    var filtered = (!q ? skills.slice() : searchSkills(skills, q)).slice(0, 8);
    cmdk.filtered = filtered;
    cmdk.selected = filtered.length ? 0 : -1;

    if (!filtered.length) {
      var suggestion = didYouMean(skills, q);
      cmdk.results.innerHTML =
        '<div class="cmdk-empty">No skills match &ldquo;' + escapeHtml(q) + '&rdquo;.' +
        (suggestion ? ' Did you mean <button class="cmdk-suggest" type="button" data-suggest="' + escapeHtml(suggestion) + '">' + escapeHtml(suggestion) + '</button>?' : '') +
        '</div>';
      var sug = cmdk.results.querySelector(".cmdk-suggest");
      if (sug) sug.addEventListener("click", function () {
        cmdk.input.value = sug.getAttribute("data-suggest");
        renderCmdkResults(cmdk.input.value);
        cmdk.input.focus();
      });
      return;
    }
    // Highlight against the free-text portion only — `cat:devops` is a scope,
    // not something to mark up inside the result text.
    var mark = parsed.text;
    cmdk.results.innerHTML = filtered.map(function (s, i) {
      return '<div class="cmdk-row" role="option" aria-selected="' + (i === 0 ? "true" : "false") + '" data-name="' + escapeHtml(s.name) + '">' +
        '<span class="cmdk-row-desc"><span class="cmdk-row-name">' + highlightText(s.name, mark) + '</span> — ' + highlightText(s.description, mark) + '</span>' +
        '<span class="tier-badge ' + escapeHtml(s.tier) + '">' + (TIER_LABELS[s.tier] || s.tier) + '</span>' +
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
    // Build the dialog up front rather than lazily on first open: the trigger
    // advertises aria-controls="cmdk-modal", and that reference dangles (and is
    // announced as broken) until the element actually exists in the document.
    if (!cmdk.backdrop) buildCmdkDom();
    var trigger = document.getElementById("cmdk-trigger");
    if (trigger) trigger.addEventListener("click", openCmdk);
    document.addEventListener("keydown", function (e) {
      var isTypingTarget = e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); return; }
      if (e.key === "/" && !isTypingTarget) { e.preventDefault(); openCmdk(); return; }
      if (e.key === "t" && !isTypingTarget) { toggleTheme(); return; }
    });
  }

  // --- Nav scroll-morph (N10) ---
  // Transparent over the billboard, opaque past the threshold. Pages with no
  // billboard mark their nav .is-solid in the HTML and opt out entirely.
  function initNavMorph() {
    var nav = document.getElementById("nav");
    if (!nav || nav.classList.contains("is-solid")) return;
    var ticking = false;
    function apply() {
      nav.classList.toggle("is-stuck", global.scrollY > 80);
      ticking = false;
    }
    global.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; global.requestAnimationFrame(apply); }
    }, { passive: true });
    apply();
  }

  // --- Poster artwork ---
  // Deterministic, generated, and honest: the hue comes from the skill's own
  // name, so the same skill always looks the same and nothing is stock or
  // invented. Returns CSS custom-property values consumed by .poster-art.
  // A curated hue ring rather than the full 360°. Free-running hues land in the
  // 80–140 olive/yellow-green band often enough to look muddy as a deep wash
  // (docker-umbrella hashed to 89 and read as dirty khaki), so the ring skips it.
  var ART_HUES = [20, 5, 350, 320, 295, 270, 245, 220, 200, 178, 155, 35];

  function posterArt(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) { h = (h * 31 + name.charCodeAt(i)) >>> 0; }
    var hue = ART_HUES[h % ART_HUES.length];
    // Analogous second stop — a wide jump can cross back into the muddy band.
    var hue2 = (hue + 22) % 360;
    return {
      a: "oklch(46% 0.145 " + hue + ")",
      b: "oklch(21% 0.075 " + hue2 + ")",
      monogram: name.replace(/[^a-z0-9]+/gi, " ").trim().split(/\s+/).slice(0, 2)
        .map(function (w) { return w.charAt(0).toUpperCase(); }).join("")
    };
  }

  var TIER_LABELS = { core: "Core", featured: "Featured", utility: "Utility" };

  function renderPoster(skill) {
    var art = posterArt(skill.name);
    var installCmd = "hermes skills install " + skill.install_url;
    return '<article class="poster" tabindex="0" role="listitem" data-name="' + escapeHtml(skill.name) + '">' +
      '<div class="poster-art" style="--art-a:' + art.a + ';--art-b:' + art.b + '">' +
        '<span class="poster-mono" aria-hidden="true">' + escapeHtml(art.monogram) + '</span>' +
        '<button class="poster-quick" type="button" data-copy="' + escapeHtml(installCmd) + '" ' +
          'aria-label="Copy install command for ' + escapeHtml(skill.name) + '" title="Copy install command">' +
          '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>' +
        '</button>' +
      '</div>' +
      '<div class="poster-body">' +
        '<h3 class="poster-name">' + escapeHtml(skill.name) + '</h3>' +
        '<p class="poster-desc">' + escapeHtml(skill.description) + '</p>' +
        '<div class="poster-foot">' +
          '<span class="tier-badge ' + escapeHtml(skill.tier) + '">' + (TIER_LABELS[skill.tier] || skill.tier) + '</span>' +
        '</div>' +
      '</div>' +
    '</article>';
  }

  function skeletonPosters(n) {
    var out = "";
    for (var i = 0; i < n; i++) {
      out += '<div class="skeleton" aria-hidden="true"><div class="skeleton-art"></div><div class="skeleton-line"></div><div class="skeleton-line short"></div></div>';
    }
    return out;
  }

  // --- Visitor-local lists ---
  // There is no backend. A global "1.2k saved" would be fabricated, so these
  // are explicitly this-browser-only and labelled that way in the UI.
  function readList(key) {
    try { return JSON.parse(localStorage.getItem(key)) || []; }
    catch (e) { return []; }
  }
  function writeList(key, arr) {
    try { localStorage.setItem(key, JSON.stringify(arr.slice(0, 60))); } catch (e) { /* private mode */ }
  }
  var MYLIST_KEY = "portfolio-mylist";
  var RECENT_KEY = "portfolio-recent";

  function getMyList() { return readList(MYLIST_KEY); }
  function isInMyList(name) { return getMyList().indexOf(name) !== -1; }
  function toggleMyList(name) {
    var list = getMyList();
    var i = list.indexOf(name);
    if (i === -1) { list.unshift(name); } else { list.splice(i, 1); }
    writeList(MYLIST_KEY, list);
    return i === -1;
  }
  function getRecentlyViewed() { return readList(RECENT_KEY); }
  function pushRecentlyViewed(name) {
    var list = getRecentlyViewed().filter(function (n) { return n !== name; });
    list.unshift(name);
    writeList(RECENT_KEY, list.slice(0, 12));
  }

  // --- Search ---
  // Parses `cat:` / `tier:` scopes out of the query, then ranks by match
  // quality rather than raw substring presence, so "dockr" still finds
  // docker-umbrella and core skills win ties.
  function parseQuery(raw) {
    var scopes = { category: null, tier: null };
    var terms = [];
    String(raw || "").split(/\s+/).forEach(function (tok) {
      if (!tok) return;
      var m = /^(cat|category|tier):(.+)$/i.exec(tok);
      if (m) {
        var key = m[1].toLowerCase() === "tier" ? "tier" : "category";
        scopes[key] = m[2].toLowerCase();
      } else { terms.push(tok.toLowerCase()); }
    });
    return { scopes: scopes, text: terms.join(" "), terms: terms };
  }

  function subsequenceScore(needle, hay) {
    // Ordered-subsequence match with a gap penalty — typo/abbreviation tolerant
    // without pulling in a fuzzy-search dependency.
    var hi = 0, gaps = 0, started = -1;
    for (var ni = 0; ni < needle.length; ni++) {
      var found = hay.indexOf(needle.charAt(ni), hi);
      if (found === -1) return -1;
      if (started === -1) started = found;
      if (hi > 0 && found > hi) gaps += found - hi;
      hi = found + 1;
    }
    return Math.max(0, 60 - gaps * 2 - started);
  }

  function scoreSkill(skill, parsed) {
    var s = parsed.scopes;
    if (s.category && String(skill.category).toLowerCase() !== s.category) return -1;
    if (s.tier && String(skill.tier).toLowerCase() !== s.tier) return -1;
    if (!parsed.text) return 1 + tierWeight(skill);

    var name = String(skill.name).toLowerCase();
    var desc = String(skill.description || "").toLowerCase();
    var cat = String(skill.category || "").toLowerCase();
    var total = 0;

    for (var i = 0; i < parsed.terms.length; i++) {
      var t = parsed.terms[i];
      var best = -1;
      if (name === t) best = 1000;
      else if (name.indexOf(t) === 0) best = 500;
      else if (name.indexOf(t) !== -1) best = 300;
      else if (desc.indexOf(t) !== -1) best = 120;
      else if (cat.indexOf(t) !== -1) best = 90;
      else {
        var sub = subsequenceScore(t, name);
        if (sub >= 0) best = 60 + sub;
      }
      if (best < 0) return -1; // every term must match something
      total += best;
    }
    return total + tierWeight(skill);
  }
  function tierWeight(skill) {
    return skill.tier === "core" ? 30 : skill.tier === "featured" ? 15 : 0;
  }

  function searchSkills(skills, rawQuery) {
    var parsed = parseQuery(rawQuery);
    return skills
      .map(function (s) { return { skill: s, score: scoreSkill(s, parsed) }; })
      .filter(function (r) { return r.score >= 0; })
      .sort(function (a, b) { return b.score - a.score || a.skill.name.localeCompare(b.skill.name); })
      .map(function (r) { return r.skill; });
  }

  function editDistance(a, b) {
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i;
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
      }
      prev = cur.slice();
    }
    return prev[b.length];
  }

  // "Did you mean" — only offered when a real name is genuinely close, so it
  // never invents a suggestion for a query that simply has no match.
  function didYouMean(skills, rawQuery) {
    var parsed = parseQuery(rawQuery);
    if (!parsed.text) return null;
    var best = null, bestD = Infinity;
    skills.forEach(function (s) {
      var d = editDistance(parsed.text, String(s.name).toLowerCase());
      if (d < bestD) { bestD = d; best = s.name; }
    });
    var tolerance = Math.max(2, Math.floor(parsed.text.length / 3));
    return bestD <= tolerance ? best : null;
  }

  global.HermesCommon = {
    initTheme: initTheme, toggleTheme: toggleTheme, wireThemeToggle: wireThemeToggle,
    loadIndex: loadIndex, loadJsonWithFallback: loadJsonWithFallback, escapeHtml: escapeHtml, highlightText: highlightText, canonicalSkillUrl: canonicalSkillUrl,
    showToast: showToast, copyToClipboard: copyToClipboard, initReveal: initReveal, initCmdk: initCmdk,
    initNavMorph: initNavMorph, posterArt: posterArt, renderPoster: renderPoster, skeletonPosters: skeletonPosters,
    getMyList: getMyList, isInMyList: isInMyList, toggleMyList: toggleMyList,
    getRecentlyViewed: getRecentlyViewed, pushRecentlyViewed: pushRecentlyViewed,
    parseQuery: parseQuery, searchSkills: searchSkills, didYouMean: didYouMean,
    TIER_LABELS: TIER_LABELS,
  };

  function boot() { wireThemeToggle(); initNavMorph(); }

  initTheme();
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", boot); }
  else { boot(); }
})(window);
