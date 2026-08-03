#!/usr/bin/env node
/**
 * Accessibility audit for the Hermes Skills Portfolio (Roadmap Phase 13).
 *
 * Drives a real Chromium via Playwright against a running static server and
 * checks the things this site can actually get wrong. Deliberately has NO
 * external dependency beyond `playwright` — nothing is injected from a CDN,
 * so the audit runs on an offline machine.
 *
 * Every rule below is evaluated against the live accessibility-relevant DOM
 * (computed styles, real focus order driven by real Tab presses, real colours
 * resolved through a canvas), not by reading the HTML source.
 *
 * Usage:
 *   node scripts/audit_a11y.js                     # audit http://127.0.0.1:8231
 *   node scripts/audit_a11y.js --base http://host:port
 *   node scripts/audit_a11y.js --contrast-only
 *   node scripts/audit_a11y.js --json report.json
 *
 * Exit code: 0 when there are no FAILs, 1 otherwise. WARNs never fail the run
 * (they mirror axe's "needs review" band) but are always printed.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');

// --------------------------------------------------------------------------
// CLI
// --------------------------------------------------------------------------
function parseArgs(argv) {
  const opts = { base: 'http://127.0.0.1:8231', contrastOnly: false, json: null, maxTabs: 400 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--base') opts.base = argv[++i];
    else if (a === '--contrast-only') opts.contrastOnly = true;
    else if (a === '--json') opts.json = argv[++i];
    else if (a === '--max-tabs') opts.maxTabs = Number(argv[++i]);
    else if (a === '--help' || a === '-h') { opts.help = true; }
  }
  return opts;
}

function firstSkillSlug() {
  const idx = JSON.parse(fs.readFileSync(path.join(ROOT, 'skills-index.json'), 'utf8'));
  const skills = (idx.skills || []).map((s) => s.name).sort();
  if (!skills.length) throw new Error('skills-index.json has no skills');
  return skills[0];
}

// --------------------------------------------------------------------------
// In-page audit library. Serialised into the page by page.evaluate, so it may
// not close over anything from this module.
// --------------------------------------------------------------------------
const PAGE_LIB = function () {
  const W = window;
  if (W.__a11y) return;

  function describe(el) {
    if (!el || el.nodeType !== 1) return String(el);
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    const cls = (el.getAttribute('class') || '').trim().split(/\s+/).filter(Boolean).slice(0, 3);
    if (cls.length) s += '.' + cls.join('.');
    const txt = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    if (txt) s += ' "' + txt + '"';
    return s;
  }

  function hiddenFromAT(el) {
    let n = el;
    while (n && n.nodeType === 1) {
      if (n.hasAttribute('hidden')) return true;
      if (n.getAttribute('aria-hidden') === 'true') return true;
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return true;
      n = n.parentElement;
    }
    return false;
  }

  function isRendered(el) {
    if (!el || el.nodeType !== 1) return false;
    if (el.getClientRects().length === 0) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none';
  }

  // Text a screen reader would read from a subtree: skips aria-hidden and
  // display:none descendants, keeps visually-hidden (.sr-only) text.
  function subtreeText(root) {
    let out = '';
    (function walk(n) {
      if (n.nodeType === 3) { out += n.nodeValue; return; }
      if (n.nodeType !== 1) return;
      if (n.getAttribute('aria-hidden') === 'true' || n.hasAttribute('hidden')) return;
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      for (const c of n.childNodes) walk(c);
    })(root);
    return out.replace(/\s+/g, ' ').trim();
  }

  // Pragmatic accessible-name computation covering the cases this site uses:
  // aria-labelledby -> aria-label -> native <label> -> content -> title -> alt.
  function accName(el) {
    const lb = el.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\s+/).map((id) => {
        const n = document.getElementById(id);
        return n ? subtreeText(n) : '';
      }).join(' ').trim();
      if (t) return t;
    }
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    if (/^(input|select|textarea)$/i.test(el.tagName)) {
      if (el.labels && el.labels.length) {
        const t = Array.from(el.labels).map((l) => subtreeText(l)).join(' ').trim();
        if (t) return t;
      }
      const ttl = el.getAttribute('title');
      if (ttl && ttl.trim()) return ttl.trim();
      return '';
    }
    if (el.tagName === 'IMG') {
      const alt = el.getAttribute('alt');
      if (alt && alt.trim()) return alt.trim();
    }
    const t = subtreeText(el);
    if (t) return t;
    const ttl = el.getAttribute('title');
    if (ttl && ttl.trim()) return ttl.trim();
    return '';
  }

  // ---- colour ------------------------------------------------------------
  // Resolve any CSS colour (including oklch(), which Chromium keeps in the
  // computed value) to sRGB bytes by painting it on a canvas over a known
  // opaque base. Painting also does the alpha compositing for us, so a
  // translucent token like --color-cta-2 is measured as it really renders.
  let _ctx = null;
  function ctx() {
    if (!_ctx) {
      const c = document.createElement('canvas');
      c.width = 1; c.height = 1;
      _ctx = c.getContext('2d', { willReadFrequently: true });
    }
    return _ctx;
  }
  function composite(baseRGB, cssColor) {
    const g = ctx();
    g.globalCompositeOperation = 'source-over';
    g.clearRect(0, 0, 1, 1);
    g.fillStyle = 'rgb(' + baseRGB[0] + ',' + baseRGB[1] + ',' + baseRGB[2] + ')';
    g.fillRect(0, 0, 1, 1);
    // An unparseable value leaves fillStyle untouched; guard by re-setting a
    // sentinel first so a bad value is detectable rather than silently black.
    g.fillStyle = '#010203';
    g.fillStyle = cssColor;
    if (g.fillStyle === '#010203' && String(cssColor).replace(/\s/g, '') !== '#010203') {
      return { rgb: baseRGB.slice(), ok: false };
    }
    g.fillRect(0, 0, 1, 1);
    const d = g.getImageData(0, 0, 1, 1).data;
    return { rgb: [d[0], d[1], d[2]], ok: true };
  }
  function effectiveBackground(el) {
    const chain = [];
    let n = el;
    while (n && n.nodeType === 1) { chain.push(n); n = n.parentElement; }
    chain.reverse();
    let base = [255, 255, 255];
    for (const node of chain) {
      const bg = getComputedStyle(node).backgroundColor;
      if (!bg || bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)') continue;
      base = composite(base, bg).rgb;
    }
    return base;
  }
  function lum(rgb) {
    const f = rgb.map((v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  }
  function ratio(a, b) {
    const la = lum(a), lb = lum(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }
  function hex(rgb) {
    return '#' + rgb.map((v) => v.toString(16).padStart(2, '0')).join('');
  }

  W.__a11y = {
    describe, hiddenFromAT, isRendered, subtreeText, accName,
    composite, effectiveBackground, ratio, hex,
  };
};

// --------------------------------------------------------------------------
// Static (single-pass) rules, run inside the page.
// --------------------------------------------------------------------------
const STATIC_RULES = function () {
  const A = window.__a11y;
  const issues = [];
  const add = (rule, level, el, detail) => issues.push({
    rule, level, target: typeof el === 'string' ? el : A.describe(el), detail,
  });

  // ---- 1. images / decorative graphics ----------------------------------
  document.querySelectorAll('img').forEach((img) => {
    if (A.hiddenFromAT(img)) return;
    if (!img.hasAttribute('alt') && img.getAttribute('role') !== 'presentation' && img.getAttribute('role') !== 'none') {
      add('img-alt', 'fail', img, 'img has no alt attribute and is not hidden from assistive tech');
    }
  });
  document.querySelectorAll('svg').forEach((svg) => {
    if (svg.getAttribute('aria-hidden') === 'true') return;
    if (A.hiddenFromAT(svg)) return;
    const titled = svg.querySelector(':scope > title');
    const named = svg.getAttribute('aria-label') || svg.getAttribute('aria-labelledby') || titled;
    if (!named) {
      add('svg-hidden-or-named', 'fail', svg,
        'inline <svg> is exposed to assistive tech but has no name — decorative icons need aria-hidden="true"');
    }
  });

  // ---- 2. accessible names on controls ----------------------------------
  const CONTROLS = 'button, [role="button"], a[href], [role="tab"], [role="option"], summary';
  document.querySelectorAll(CONTROLS).forEach((el) => {
    if (A.hiddenFromAT(el)) return;
    if (!A.isRendered(el)) return;
    if (!A.accName(el)) {
      add('control-name', 'fail', el, 'interactive control has no accessible name');
    }
  });

  // ---- 3. form controls have labels -------------------------------------
  document.querySelectorAll('input, select, textarea').forEach((el) => {
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (type === 'hidden' || type === 'submit' || type === 'button' || type === 'reset' || type === 'image') return;
    if (A.hiddenFromAT(el)) return;
    if (!A.accName(el)) {
      const ph = el.getAttribute('placeholder');
      add('form-label', 'fail', el,
        ph ? 'form control is named only by its placeholder ("' + ph + '") — needs a <label>, aria-label, or aria-labelledby'
           : 'form control has no associated label');
    }
  });

  // ---- 4. heading order --------------------------------------------------
  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .filter((h) => !A.hiddenFromAT(h));
  const levels = headings.map((h) => Number(h.tagName[1]));
  const h1s = headings.filter((h) => h.tagName === 'H1');
  if (h1s.length === 0) add('heading-h1', 'fail', 'document', 'page has no visible <h1>');
  if (h1s.length > 1) add('heading-h1', 'fail', 'document', 'page has ' + h1s.length + ' <h1> elements');
  for (let i = 1; i < levels.length; i++) {
    if (levels[i] > levels[i - 1] + 1) {
      add('heading-order', 'fail', headings[i],
        'heading level jumps h' + levels[i - 1] + ' -> h' + levels[i] + ' (previous: "' +
        A.subtreeText(headings[i - 1]).slice(0, 40) + '")');
    }
  }
  if (levels.length && levels[0] !== 1) {
    add('heading-order', 'fail', headings[0], 'first heading on the page is h' + levels[0] + ', not h1');
  }

  // ---- 5. landmarks ------------------------------------------------------
  const landmarkOf = (el) => {
    const explicit = (el.getAttribute('role') || '').toLowerCase();
    if (explicit) return explicit;
    const tag = el.tagName.toLowerCase();
    if (tag === 'main') return 'main';
    if (tag === 'nav') return 'navigation';
    if (tag === 'aside') return 'complementary';
    if (tag === 'form') return el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') ? 'form' : '';
    if (tag === 'section') return el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') ? 'region' : '';
    if (tag === 'header' || tag === 'footer') {
      // Only a top-level header/footer is banner/contentinfo.
      let p = el.parentElement;
      while (p && p !== document.body) {
        const pt = p.tagName.toLowerCase();
        if (['article', 'aside', 'main', 'nav', 'section'].includes(pt)) return '';
        p = p.parentElement;
      }
      return tag === 'header' ? 'banner' : 'contentinfo';
    }
    return '';
  };
  const landmarks = [];
  document.querySelectorAll('main, nav, aside, header, footer, section, form, [role]').forEach((el) => {
    if (A.hiddenFromAT(el)) return;
    const role = landmarkOf(el);
    if (!['main', 'navigation', 'complementary', 'banner', 'contentinfo', 'region', 'search', 'form'].includes(role)) return;
    landmarks.push({ el, role, name: A.accName(el) || (el.getAttribute('aria-label') || '') });
  });
  const mains = landmarks.filter((l) => l.role === 'main');
  if (mains.length !== 1) {
    add('landmark-main', 'fail', 'document', 'expected exactly 1 main landmark, found ' + mains.length);
  }
  ['banner', 'contentinfo'].forEach((role) => {
    const found = landmarks.filter((l) => l.role === role);
    if (found.length === 0) add('landmark-' + role, 'fail', 'document', 'no ' + role + ' landmark on the page');
    if (found.length > 1) add('landmark-' + role, 'fail', 'document', role + ' landmark appears ' + found.length + ' times');
  });
  // Same-role landmarks must be distinguishable by name.
  const byRole = {};
  landmarks.forEach((l) => { (byRole[l.role] = byRole[l.role] || []).push(l); });
  Object.keys(byRole).forEach((role) => {
    const group = byRole[role];
    if (group.length < 2) return;
    const seen = {};
    group.forEach((l) => {
      const key = (l.name || '').toLowerCase();
      if (seen[key]) {
        add('landmark-unique', 'fail', l.el,
          'two ' + role + ' landmarks share the accessible name "' + (l.name || '(none)') + '"');
      }
      seen[key] = true;
    });
  });

  // ---- 6. ARIA IDREFs resolve -------------------------------------------
  ['aria-controls', 'aria-labelledby', 'aria-describedby', 'aria-owns'].forEach((attr) => {
    document.querySelectorAll('[' + attr + ']').forEach((el) => {
      const ids = (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean);
      ids.forEach((id) => {
        if (!document.getElementById(id)) {
          // aria-controls targets may legitimately be created on demand, which
          // is exactly axe's "needs review" band rather than a violation.
          const level = attr === 'aria-controls' ? 'warn' : 'fail';
          add('aria-idref', level, el, attr + '="' + id + '" points at an element that does not exist in the DOM');
        }
      });
    });
  });

  // ---- 7. tab / tabpanel wiring -----------------------------------------
  document.querySelectorAll('[role="tablist"]').forEach((list) => {
    if (A.hiddenFromAT(list)) return;
    if (!A.accName(list)) add('tablist-name', 'warn', list, 'tablist has no accessible name');
    list.querySelectorAll('[role="tab"]').forEach((tab) => {
      if (!tab.getAttribute('aria-controls')) {
        add('tab-controls', 'fail', tab, 'role="tab" has no aria-controls pointing at its tabpanel');
      }
    });
  });
  document.querySelectorAll('[role="tabpanel"]').forEach((panel) => {
    if (!panel.getAttribute('aria-labelledby') && !panel.getAttribute('aria-label')) {
      add('tabpanel-name', 'fail', panel, 'role="tabpanel" is not labelled by its tab');
    }
  });

  // ---- 8. lists ----------------------------------------------------------
  document.querySelectorAll('ul, ol, [role="list"]').forEach((list) => {
    if (A.hiddenFromAT(list)) return;
    const bad = Array.from(list.children).filter((c) => {
      const role = (c.getAttribute('role') || '').toLowerCase();
      if (role === 'listitem') return false;
      if (c.tagName === 'LI' && !role) return false;
      if (c.tagName === 'SCRIPT' || c.tagName === 'TEMPLATE') return false;
      return true;
    });
    if (bad.length) {
      add('list-children', 'fail', list,
        'list has ' + bad.length + ' child element(s) that are not listitems (first: ' + A.describe(bad[0]) + ')');
    }
  });

  // ---- 9. language & title ----------------------------------------------
  if (!document.documentElement.getAttribute('lang')) {
    add('html-lang', 'fail', 'html', '<html> has no lang attribute');
  }
  if (!document.title || !document.title.trim()) {
    add('document-title', 'fail', 'document', 'page has no <title>');
  }

  // ---- 10. skip link -----------------------------------------------------
  const skip = document.querySelector('.skip-link, a[href^="#"][class*="skip"]');
  if (!skip) {
    add('skip-link', 'fail', 'document', 'no skip link found');
  } else {
    const target = document.querySelector(skip.getAttribute('href'));
    if (!target) {
      add('skip-link', 'fail', skip, 'skip link target ' + skip.getAttribute('href') + ' does not exist');
    } else {
      const focusable = target.matches('a[href], button, input, select, textarea, [tabindex]') ||
        target.hasAttribute('tabindex');
      if (!focusable) {
        // WARN, not FAIL: browsers move the sequential-focus starting point to a
        // non-focusable fragment target, so Tab does continue from there. Adding
        // tabindex="-1" is still the reliable cross-screen-reader form.
        add('skip-link-target', 'warn', target,
          'skip link target is not focusable — add tabindex="-1" so focus really lands there in every AT');
      }
    }
  }

  return issues;
};

// --------------------------------------------------------------------------
// Contrast sampling, run inside the page.
// --------------------------------------------------------------------------
const CONTRAST_SCAN = function () {
  const A = window.__a11y;
  const combos = new Map();

  function hasOwnText(el) {
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.nodeValue.trim()) return true;
    }
    return false;
  }

  document.querySelectorAll('body *').forEach((el) => {
    if (!hasOwnText(el)) return;
    if (A.hiddenFromAT(el)) return;
    if (!A.isRendered(el)) return;
    const cs = getComputedStyle(el);
    if (parseFloat(cs.opacity) === 0) return;

    const bgRGB = A.effectiveBackground(el.parentElement || document.body);
    const ownBG = cs.backgroundColor;
    const bg = (ownBG && ownBG !== 'transparent' && ownBG !== 'rgba(0, 0, 0, 0)')
      ? A.composite(bgRGB, ownBG).rgb : bgRGB;
    const fgRes = A.composite(bg, cs.color);
    if (!fgRes.ok) return;
    const fg = fgRes.rgb;

    const size = parseFloat(cs.fontSize);
    const weight = Number(cs.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const r = A.ratio(fg, bg);

    const key = [A.hex(fg), A.hex(bg), size, weight].join('|');
    if (!combos.has(key)) {
      combos.set(key, {
        fg: A.hex(fg), bg: A.hex(bg), size, weight, large,
        ratio: Math.round(r * 100) / 100,
        required: large ? 3.0 : 4.5,
        pass: r >= (large ? 3.0 : 4.5),
        count: 0,
        sample: A.describe(el),
      });
    }
    combos.get(key).count++;
  });

  return Array.from(combos.values()).sort((a, b) => a.ratio - b.ratio);
};

// --------------------------------------------------------------------------
// Keyboard / focus checks — these need real key presses, so they live here.
// --------------------------------------------------------------------------
async function keyboardChecks(page, opts) {
  const issues = [];
  const push = (rule, level, target, detail) => issues.push({ rule, level, target, detail });

  await page.evaluate(() => { window.scrollTo(0, 0); document.body.focus(); });

  // Baseline: every element that should be reachable.
  const expected = await page.evaluate(() => {
    const A = window.__a11y;
    const SEL = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, [tabindex]';
    const out = [];
    document.querySelectorAll(SEL).forEach((el) => {
      if (el.disabled) return;
      if (el.getAttribute('tabindex') === '-1') return;
      if (A.hiddenFromAT(el)) return;
      if (!A.isRendered(el)) return;
      el.setAttribute('data-a11y-expect', String(out.length));
      out.push(A.describe(el));
    });
    return out;
  });

  const reached = new Set();
  const noFocusRing = [];
  let steps = 0;
  let sawBodyTwice = 0;
  let firstIdx = null;

  while (steps < opts.maxTabs) {
    await page.keyboard.press('Tab');
    steps++;
    const info = await page.evaluate(() => {
      const A = window.__a11y;
      const el = document.activeElement;
      if (!el || el === document.body || el === document.documentElement) return { body: true };
      const cs = getComputedStyle(el);
      const outlineVisible = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 1;
      const shadowVisible = cs.boxShadow && cs.boxShadow !== 'none';
      return {
        body: false,
        idx: el.getAttribute('data-a11y-expect'),
        desc: A.describe(el),
        outline: cs.outlineStyle + ' ' + cs.outlineWidth + ' ' + cs.outlineColor,
        outlineVisible,
        shadowVisible,
        matchesFocusVisible: (() => { try { return el.matches(':focus-visible'); } catch (e) { return null; } })(),
      };
    });
    if (info.body) {
      sawBodyTwice++;
      if (sawBodyTwice >= 2) break;
      continue;
    }
    let firstArrival = true;
    if (info.idx !== null && info.idx !== undefined) {
      // Only a return to the FIRST stop means the ring wrapped. A repeat of some
      // other stop is normal — a date input eats several Tab presses moving
      // between its own day/month/year segments without changing activeElement.
      if (firstIdx === null) firstIdx = info.idx;
      else if (info.idx === firstIdx) break;
      firstArrival = !reached.has(info.idx);
      reached.add(info.idx);
    }
    // Measure the ring only as focus ARRIVES. Re-measuring a host that Tab has
    // not actually left reports Chromium UA quirks, not site defects: an
    // input[type=date] keeps document.activeElement on the host while focus
    // walks its shadow segments, and the internal calendar-picker button drops
    // :focus-visible from the host on the way past.
    if (firstArrival && !info.outlineVisible && !info.shadowVisible) {
      noFocusRing.push({ desc: info.desc, outline: info.outline, focusVisible: info.matchesFocusVisible });
    }
  }

  const missed = [];
  expected.forEach((desc, i) => { if (!reached.has(String(i))) missed.push(desc); });
  if (missed.length) {
    push('keyboard-reachable', 'fail', 'document',
      missed.length + ' of ' + expected.length + ' interactive element(s) were never focused in ' + steps +
      ' Tab presses. First: ' + missed.slice(0, 3).join(' | '));
  }
  noFocusRing.forEach((n) => {
    push('focus-visible', 'fail', n.desc,
      'no visible focus indicator when reached by Tab (outline: ' + n.outline + ')');
  });

  await page.evaluate(() => {
    document.querySelectorAll('[data-a11y-expect]').forEach((el) => el.removeAttribute('data-a11y-expect'));
  });

  return { issues, tabStops: reached.size, tabPresses: steps, expected: expected.length };
}

async function dialogChecks(page) {
  const issues = [];
  const push = (rule, level, target, detail) => issues.push({ rule, level, target, detail });

  const hasOverlay = await page.locator('#detail-overlay').count();
  if (!hasOverlay) return { issues, skipped: true };

  await page.waitForSelector('.card-grid .poster', { timeout: 15000 });
  await page.evaluate(() => {
    const p = document.querySelector('.card-grid .poster');
    p.id = p.id || 'a11y-opener';
    p.focus();
  });
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => {
    const o = document.getElementById('detail-overlay');
    return o && !o.hidden;
  }, null, { timeout: 5000 });

  const openFocus = await page.evaluate(() => {
    const o = document.getElementById('detail-overlay');
    return { inside: o.contains(document.activeElement), desc: window.__a11y.describe(document.activeElement) };
  });
  if (!openFocus.inside) {
    push('dialog-initial-focus', 'fail', '#detail-overlay',
      'focus is not moved into the dialog on open (landed on ' + openFocus.desc + ')');
  }

  // Focus trap: Tab around; focus must never escape the dialog.
  const escapes = [];
  for (let i = 0; i < 45; i++) {
    await page.keyboard.press('Tab');
    const out = await page.evaluate(() => {
      const o = document.getElementById('detail-overlay');
      const a = document.activeElement;
      const inside = o.contains(a);
      return inside ? null : window.__a11y.describe(a);
    });
    if (out) { escapes.push({ step: i + 1, desc: out }); if (escapes.length >= 3) break; }
  }
  if (escapes.length) {
    push('dialog-focus-trap', 'fail', '#detail-overlay',
      'focus leaves the open dialog after ' + escapes[0].step + ' Tab press(es) — reached ' + escapes[0].desc +
      ' (aria-modal="true" hides background content from AT but does not stop the Tab key)');
  }

  // Escape closes, and focus is restored to the opener.
  await page.keyboard.press('Escape');
  const afterEsc = await page.evaluate(() => {
    const o = document.getElementById('detail-overlay');
    return {
      closed: !!o.hidden,
      active: window.__a11y.describe(document.activeElement),
      restored: document.activeElement === document.getElementById('a11y-opener'),
    };
  });
  if (!afterEsc.closed) push('dialog-escape', 'fail', '#detail-overlay', 'Escape did not close the dialog');
  if (!afterEsc.restored) {
    push('dialog-focus-restore', 'fail', '#detail-overlay',
      'focus was not restored to the element that opened the dialog (went to ' + afterEsc.active + ')');
  }

  // Background inertness (reported, not a hard fail — aria-modal covers AT).
  const inert = await page.evaluate(() => {
    const o = document.getElementById('detail-overlay');
    const main = document.getElementById('main');
    return { mainInert: !!(main && (main.inert || main.hasAttribute('inert'))), ariaModal: o.querySelector('[role="dialog"]').getAttribute('aria-modal') };
  });
  if (!inert.mainInert) {
    push('dialog-background-inert', 'warn', '#main',
      'background content is not inert while the dialog is open (aria-modal="' + inert.ariaModal + '" only hides it from AT)');
  }

  return { issues, skipped: false };
}

// --------------------------------------------------------------------------
// Runner
// --------------------------------------------------------------------------
async function auditPage(browser, url, opts, o) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  await page.addScriptTag({ content: '(' + PAGE_LIB.toString() + ')()' });
  // Let client-rendered content (catalog grid, bundles, pending sources) land.
  await page.waitForTimeout(700);
  await page.addScriptTag({ content: '(' + PAGE_LIB.toString() + ')()' });

  const result = { url, issues: [], contrast: {}, meta: {}, consoleErrors };

  if (!opts.contrastOnly) {
    result.issues.push(...await page.evaluate(STATIC_RULES));
    const kb = await keyboardChecks(page, opts);
    result.issues.push(...kb.issues);
    result.keyboard = { tabStops: kb.tabStops, tabPresses: kb.tabPresses, expected: kb.expected };
    const dlg = await dialogChecks(page);
    result.issues.push(...dlg.issues);
    result.dialog = dlg.skipped ? 'n/a' : 'checked';
  }

  // Metadata inventory (Phase 16 support — reported, not scored here).
  result.meta = await page.evaluate(() => {
    const g = (sel, attr) => { const n = document.querySelector(sel); return n ? n.getAttribute(attr) : null; };
    return {
      title: document.title,
      description: g('meta[name="description"]', 'content'),
      canonical: g('link[rel="canonical"]', 'href'),
      ogTitle: g('meta[property="og:title"]', 'content'),
      ogDescription: g('meta[property="og:description"]', 'content'),
      ogUrl: g('meta[property="og:url"]', 'content'),
      ogType: g('meta[property="og:type"]', 'content'),
      twitterCard: g('meta[name="twitter:card"]', 'content'),
      twitterTitle: g('meta[name="twitter:title"]', 'content'),
      jsonLd: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map((s) => {
        try { const d = JSON.parse(s.textContent); return Array.isArray(d['@graph']) ? d['@graph'].map((x) => x['@type']).join('+') : d['@type']; }
        catch (e) { return 'INVALID JSON: ' + e.message; }
      }),
    };
  });

  // Contrast in both themes.
  //
  // Two things have to happen first or the numbers are wrong rather than merely
  // incomplete:
  //  1. body has a 220ms background-color/color transition, so a theme flip
  //     measured too early samples a half-blended colour that exists nowhere in
  //     the design. Transitions are killed outright before sampling.
  //  2. `.reveal` sections sit at opacity:0 until their IntersectionObserver
  //     fires, and fullPage screenshots/virtual viewports do not fire it — the
  //     page has to be really scrolled.
  await page.addStyleTag({
    content: '*, *::before, *::after { transition: none !important; animation: none !important; }',
  });
  await page.evaluate(async () => {
    const step = Math.round(window.innerHeight * 0.8);
    for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 60));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(300);
  const revealsLeft = await page.evaluate(() => document.querySelectorAll('.reveal:not(.is-in)').length);
  result.revealsNotShown = revealsLeft;

  for (const theme of ['dark', 'light']) {
    await page.evaluate((t) => {
      document.documentElement.setAttribute('data-theme', t);
      try { localStorage.setItem('portfolio-theme', t); } catch (e) { /* private mode */ }
    }, theme);
    await page.waitForTimeout(150);
    result.contrast[theme] = await page.evaluate(CONTRAST_SCAN);
  }

  await page.close();
  return result;
}

function printReport(results, opts) {
  const L = (s) => process.stdout.write(s + '\n');
  let fails = 0, warns = 0;

  L('');
  L('='.repeat(78));
  L('  ACCESSIBILITY AUDIT — Hermes Skills Portfolio');
  L('  base: ' + opts.base + '   ' + new Date().toISOString());
  L('='.repeat(78));

  for (const r of results) {
    const f = r.issues.filter((i) => i.level === 'fail');
    const w = r.issues.filter((i) => i.level === 'warn');
    fails += f.length; warns += w.length;
    L('');
    L('-'.repeat(78));
    L(r.url);
    L('-'.repeat(78));
    if (r.keyboard) {
      L('  keyboard: ' + r.keyboard.tabStops + ' tab stops reached of ' + r.keyboard.expected +
        ' expected (' + r.keyboard.tabPresses + ' Tab presses) · dialog: ' + r.dialog);
    }
    if (r.consoleErrors && r.consoleErrors.length) {
      L('  page errors: ' + r.consoleErrors.length + ' — ' + r.consoleErrors[0]);
    }
    if (!f.length && !w.length) { L('  no issues'); }

    const group = (list, tag) => {
      const byRule = {};
      list.forEach((i) => { (byRule[i.rule] = byRule[i.rule] || []).push(i); });
      Object.keys(byRule).sort().forEach((rule) => {
        const items = byRule[rule];
        L('  [' + tag + '] ' + rule + ' ×' + items.length);
        items.slice(0, 6).forEach((i) => {
          L('        ' + i.target);
          L('          ' + i.detail);
        });
        if (items.length > 6) L('        … and ' + (items.length - 6) + ' more');
      });
    };
    group(f, 'FAIL');
    group(w, 'WARN');
  }

  // ---- contrast ----
  L('');
  L('='.repeat(78));
  L('  COLOUR CONTRAST — real computed pairs, both themes (WCAG AA)');
  L('='.repeat(78));
  for (const theme of ['dark', 'light']) {
    const seen = new Map();
    for (const r of results) {
      for (const c of (r.contrast[theme] || [])) {
        const k = [c.fg, c.bg, c.size, c.weight].join('|');
        if (!seen.has(k)) seen.set(k, Object.assign({ pages: new Set() }, c));
        seen.get(k).pages.add(r.url.replace(opts.base, '') || '/');
      }
    }
    const rows = Array.from(seen.values()).sort((a, b) => a.ratio - b.ratio);
    const bad = rows.filter((r) => !r.pass);
    L('');
    L('  data-theme="' + theme + '" — ' + rows.length + ' distinct fg/bg/size combinations, ' +
      bad.length + ' below AA');
    L('  ' + 'ratio'.padStart(6) + '  ' + 'need'.padStart(4) + '  ' + 'fg'.padEnd(8) + ' ' + 'bg'.padEnd(8) +
      ' ' + 'px'.padStart(5) + ' ' + 'wt'.padStart(4) + '  sample');
    rows.forEach((c) => {
      const mark = c.pass ? 'PASS' : 'FAIL';
      L('  ' + String(c.ratio.toFixed(2)).padStart(6) + '  ' + String(c.required).padStart(4) + '  ' +
        c.fg.padEnd(8) + ' ' + c.bg.padEnd(8) + ' ' + String(c.size).padStart(5) + ' ' +
        String(c.weight).padStart(4) + '  ' + mark + '  ' + c.sample.slice(0, 60));
    });
    bad.forEach(() => { /* contrast failures are reported, not counted as script FAILs */ });
  }

  // ---- SEO metadata inventory (Phase 16 companion) ----
  L('');
  L('='.repeat(78));
  L('  SEO METADATA — uniqueness and completeness per page');
  L('='.repeat(78));
  const REQUIRED = ['title', 'description', 'canonical', 'ogTitle', 'ogDescription', 'ogUrl', 'ogType', 'twitterCard'];
  const seenTitle = new Map(), seenDesc = new Map(), seenCanon = new Map();
  for (const r of results) {
    const page = r.url.replace(opts.base, '') || '/';
    const missing = REQUIRED.filter((k) => !r.meta[k]);
    const ld = r.meta.jsonLd || [];
    L('');
    L('  ' + page);
    L('    title      ' + (r.meta.title || '(none)'));
    L('    canonical  ' + (r.meta.canonical || '(none)'));
    L('    json-ld    ' + (ld.length ? ld.join(', ') : '(none)'));
    L('    missing    ' + (missing.length ? missing.join(', ') : 'nothing'));
    [[seenTitle, r.meta.title], [seenDesc, r.meta.description], [seenCanon, r.meta.canonical]]
      .forEach(([map, val]) => { if (val) map.set(val, (map.get(val) || []).concat(page)); });
  }
  const dupes = [];
  [['title', seenTitle], ['description', seenDesc], ['canonical', seenCanon]].forEach(([label, map]) => {
    map.forEach((pages, val) => {
      if (pages.length > 1) dupes.push(label + ' shared by ' + pages.join(' + ') + ': "' + String(val).slice(0, 60) + '"');
    });
  });
  L('');
  L('  duplicates: ' + (dupes.length ? '' : 'none'));
  dupes.forEach((d) => L('    ' + d));

  L('');
  L('='.repeat(78));
  L('  RESULT: ' + fails + ' failure(s), ' + warns + ' warning(s) across ' + results.length + ' page(s)');
  L('='.repeat(78));
  L('');
  return fails;
}

(async () => {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log('usage: node scripts/audit_a11y.js [--base URL] [--contrast-only] [--json FILE] [--max-tabs N]');
    process.exit(0);
  }
  const base = opts.base.replace(/\/+$/, '');
  const slug = firstSkillSlug();
  const urls = [
    base + '/index.html',
    base + '/bundles.html',
    base + '/submit.html',
    base + '/changelog.html',
    base + '/skills/' + slug + '/index.html',
  ];

  const browser = await chromium.launch();
  const results = [];
  try {
    for (const url of urls) {
      results.push(await auditPage(browser, url, opts, {}));
    }
  } finally {
    await browser.close();
  }

  if (opts.json) {
    fs.writeFileSync(opts.json, JSON.stringify(results, (k, v) => (v instanceof Set ? Array.from(v) : v), 2));
  }
  const fails = printReport(results, { base });
  process.exit(fails > 0 ? 1 : 0);
})().catch((err) => {
  console.error('audit_a11y: ' + (err && err.stack ? err.stack : err));
  process.exit(2);
});
