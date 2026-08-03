// Real-browser verification for the Dusk / sidebar-filter catalog.
//
// Checks behaviour, not just that CSS parses: facet counts match the real
// catalog and act as the distribution chart, facets filter, search
// works (fuzzy + scoped paths), the detail overlay opens and
// renders markdown, and no viewport scrolls horizontally.
//
// Usage: node scripts/verify_ui.js [baseUrl]
const { chromium } = require("playwright");

const BASE = process.argv[2] || "http://127.0.0.1:8231";
const WIDTHS = [320, 375, 414, 768, 1280];

let failures = 0;
function check(name, ok, detail) {
  const status = ok ? "PASS" : "FAIL";
  if (!ok) failures++;
  console.log(`  ${status}  ${name}${detail ? " — " + detail : ""}`);
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push("pageerror: " + e.message));

  console.log(`\nVerifying ${BASE}\n`);

  // ---------- Catalog ----------
  console.log("Catalog page");
  await page.goto(`${BASE}/index.html`, { waitUntil: "networkidle" });
  await page.waitForSelector(".poster", { timeout: 10000 });

  const total = await page.evaluate(async () => {
    const r = await fetch("./skills-index.json");
    return (await r.json()).skills.length;
  });

  check("theme defaults to dark", (await page.getAttribute("html", "data-theme")) === "dark");

  // Every card's copy action must carry a raw URL — a blob URL installs
  // GitHub's HTML page as the skill body while still exiting 0.
  const cardCmds = await page.$$eval("#catalog-grid .poster-quick", (els) =>
    els.map((e) => e.getAttribute("data-copy")));
  check("every card's copy action uses a raw install URL",
    cardCmds.length > 0 && cardCmds.every((c) =>
      c.startsWith("hermes skills install https://raw.githubusercontent.com/")),
    `${cardCmds.length} cards`);

  const gridCount = await page.locator("#catalog-grid .poster").count();
  check("grid renders every skill", gridCount === total, `${gridCount} of ${total}`);

  // Facet counts ARE the distribution chart — they must sum to the real catalog.
  const catSum = await page.$$eval("#facet-category .facet-count", (els) =>
    els.reduce((a, e) => a + Number(e.textContent), 0));
  check("category facets sum to the catalog size", catSum === total, `${catSum} vs ${total}`);
  const tierSum = await page.$$eval("#facet-tier .facet-count", (els) =>
    els.reduce((a, e) => a + Number(e.textContent), 0));
  check("tier facets sum to the catalog size", tierSum === total, `${tierSum} vs ${total}`);

  const sortedDesc = await page.$$eval("#facet-category .facet-count", (els) => {
    const v = els.map((e) => Number(e.textContent));
    return v.every((n, i) => i === 0 || v[i - 1] >= n);
  });
  check("category facets sorted most to least", sortedDesc);

  // Regression: .facet-bar is a <span>. Geometry must be asserted in pixels —
  // an inline box silently ignores width and every bar renders empty.
  await page.waitForTimeout(700);
  const barPx = await page.$$eval("#facet-category .facet-bar", (els) =>
    els.map((e) => e.getBoundingClientRect().width));
  check("facet distribution bars have real width", barPx.length > 0 && barPx.every((w) => w > 0),
    barPx.map((w) => w.toFixed(0)).join("/"));
  check("facet bars are proportional (largest > smallest)",
    barPx.length > 1 && barPx[0] > barPx[barPx.length - 1]);

  // Clicking a facet must actually filter.
  const firstFacetCount = await page.$eval("#facet-category .facet-row .facet-count", (e) => Number(e.textContent));
  await page.click("#facet-category .facet-row");
  await page.waitForTimeout(300);
  const afterFacet = await page.locator("#catalog-grid .poster").count();
  check("clicking a category facet filters the grid", afterFacet === firstFacetCount,
    `${afterFacet} vs ${firstFacetCount}`);
  await page.click("#facet-category .facet-row");
  await page.waitForTimeout(300);

  const newsCount = await page.locator(".whatsnew-item").count();
  check("what's-new feed has real entries", newsCount > 0, `${newsCount} entries`);

  // ---------- Search ----------
  console.log("\nSearch");
  await page.fill("#search-input", "dockr");
  await page.waitForTimeout(320);
  const fuzzy = await page.locator("#catalog-grid .poster").count();
  check("fuzzy search tolerates a typo ('dockr')", fuzzy > 0, `${fuzzy} results`);

  await page.fill("#search-input", "cat:devops");
  await page.waitForTimeout(320);
  const scoped = await page.$$eval("#catalog-grid .poster", (els) => els.length);
  const devops = await page.evaluate(async () => {
    const r = await fetch("./skills-index.json");
    return (await r.json()).skills.filter((s) => s.category === "devops").length;
  });
  check("cat: scope filters correctly", scoped === devops, `${scoped} vs ${devops}`);

  await page.fill("#search-input", "tier:core");
  await page.waitForTimeout(320);
  const coreShown = await page.locator("#catalog-grid .poster").count();
  const coreReal = await page.evaluate(async () => {
    const r = await fetch("./skills-index.json");
    return (await r.json()).skills.filter((s) => s.tier === "core").length;
  });
  check("tier: scope filters correctly", coreShown === coreReal, `${coreShown} vs ${coreReal}`);

  await page.fill("#search-input", "");
  await page.waitForTimeout(320);

  // ---------- Detail overlay ----------
  console.log("\nDetail overlay");
  await page.locator("#catalog-grid .poster").first().click();
  await page.waitForSelector("#detail-overlay:not([hidden])", { timeout: 5000 });
  check("overlay opens", true);

  const detailCmd = (await page.textContent("#detail-install-cmd")).trim();
  check("detail install command uses the raw URL",
    detailCmd.startsWith("hermes skills install https://raw.githubusercontent.com/"));

  const ghHref = await page.getAttribute("#detail-skillmd-link", "href");
  check("'View on GitHub' points at the blob page, not the raw URL",
    ghHref.includes("/blob/"), ghHref.slice(0, 70) + "…");

  await page.click('.detail-tab[data-tab="skillmd"]');
  await page.waitForTimeout(200);
  const mdHeadings = await page.locator("#detail-skillmd-content h1, #detail-skillmd-content h2").count();
  check("SKILL.md renders as real markdown (not a text dump)", mdHeadings > 0, `${mdHeadings} headings`);
  const copyBtns = await page.locator("#detail-skillmd-content .md-copy").count();
  check("code blocks have copy buttons", copyBtns > 0, `${copyBtns} blocks`);
  // Regression: the code-fence placeholder is stripped by line.trim() if it is
  // space-delimited, which drops every block AND leaks the raw token as text.
  const leaked = await page.evaluate(() =>
    /%%MDBLOCK|\bBLOCK\d\b/.test(document.getElementById("detail-skillmd-content").innerText));
  check("no code-fence placeholder leaks into the rendered text", !leaked);

  // My List round-trip
  await page.click('.detail-tab[data-tab="overview"]');
  await page.click("#detail-mylist-btn");
  await page.waitForTimeout(150);
  const pressed = await page.getAttribute("#detail-mylist-btn", "aria-pressed");
  check("My List toggles on", pressed === "true");
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem("portfolio-mylist") || "[]").length);
  check("My List persists to localStorage", stored === 1, `${stored} saved`);
  await page.click("#detail-mylist-btn");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(200);
  check("Escape closes the overlay", await page.locator("#detail-overlay").isHidden());

  // ---------- Responsive ----------
  console.log("\nResponsive — no horizontal page scroll");
  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.waitForTimeout(250);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(`${w}px`, overflow <= 1, `overflow ${overflow}px`);
  }

  // Regression: wrapping nav links broke onto a second line and burst out of the
  // fixed-height bar at 375px. Gate 49 — no two-line clickable text.
  console.log("\nResponsive — nav stays one line (gate 49)");
  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.waitForTimeout(220);
    const nav = await page.evaluate(() => {
      const bar = document.querySelector(".nav-inner");
      const links = Array.from(document.querySelectorAll(".nav-links a"))
        .filter((a) => a.offsetParent !== null);
      const barRect = bar.getBoundingClientRect();
      return {
        barHeight: Math.round(barRect.height),
        overflowing: links.some((a) => {
          const r = a.getBoundingClientRect();
          return r.bottom > barRect.bottom + 1 || r.top < barRect.top - 1;
        }),
        visible: links.length
      };
    });
    check(`${w}px — ${nav.visible} link(s), bar ${nav.barHeight}px`,
      !nav.overflowing && nav.barHeight <= 64);
  }
  // Regression: the sidebar's base `display: flex` sat AFTER the collapse
  // query, so at equal specificity it beat `display: none` and the panel was
  // stuck open on phones regardless of aria-expanded.
  console.log("\nSidebar disclosure (mobile)");
  await page.setViewportSize({ width: 375, height: 812 });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector(".poster");
  const collapsed = await page.evaluate(() => {
    const b = document.getElementById("side-body");
    const t = document.getElementById("side-toggle");
    return {
      hidden: getComputedStyle(b).display === "none",
      toggleVisible: getComputedStyle(t).display !== "none",
      expanded: t.getAttribute("aria-expanded")
    };
  });
  check("sidebar starts collapsed at 375px", collapsed.hidden && collapsed.expanded === "false");
  check("disclosure button is visible at 375px", collapsed.toggleVisible);
  await page.click("#side-toggle");
  await page.waitForTimeout(200);
  const opened = await page.evaluate(() =>
    getComputedStyle(document.getElementById("side-body")).display !== "none");
  check("disclosure opens the sidebar", opened);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector(".poster");
  const desktopOpen = await page.evaluate(() =>
    getComputedStyle(document.getElementById("side-body")).display !== "none");
  check("sidebar is always open on desktop", desktopOpen);

  // ---------- Other pages ----------
  console.log("\nOther pages");
  for (const p of ["bundles.html", "changelog.html", "submit.html"]) {
    await page.goto(`${BASE}/${p}`, { waitUntil: "networkidle" });
    const navSolid = await page.evaluate(() => {
      const n = document.getElementById("nav");
      return !!n && n.classList.contains("is-solid");
    });
    const footerCols = await page.locator(".footer-col").count();
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    check(`${p} — nav solid, colophon footer, dark canvas`,
      navSolid && footerCols === 3 && bg !== "rgb(255, 255, 255)", bg);
  }

  // changelog must still render from the extracted shared data
  await page.goto(`${BASE}/changelog.html`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  const clEntries = await page.locator(".changelog-groups li, .changelog-entry").count();
  check("changelog still renders after the data extraction", clEntries > 0, `${clEntries} entries`);

  console.log("\nConsole errors: " + (consoleErrors.length ? consoleErrors.length : "none"));
  consoleErrors.slice(0, 8).forEach((e) => console.log("   " + e.slice(0, 160)));
  if (consoleErrors.length) failures++;

  await browser.close();
  console.log(`\n${failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"}\n`);
  process.exit(failures === 0 ? 0 : 1);
})();
