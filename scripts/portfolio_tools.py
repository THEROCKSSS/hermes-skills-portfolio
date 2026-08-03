#!/usr/bin/env python3
"""Portfolio tools: per-skill page generation, provenance validation, catalog routing.

Used by scripts/generate_skill_pages.py and tests/test_portfolio_tools.py.
"""

import html
import json
import os
import re
from pathlib import Path

TIER_LABELS = {"core": "Core", "featured": "Featured", "utility": "Utility"}
TIER_DESCS = {
    "core": "Broadly empowering, nearly any user benefits",
    "featured": "Highly useful within a category",
    "utility": "Useful for specific workflows",
}
SOURCE_LABELS = {
    "new": "Newly authored",
    "generalized": "Generalized from existing",
    "adapted": "Adapted with attribution",
}


def build_meta_description(skill):
    """Build a meta description combining user_use and agent_use, capped at ~300 chars."""
    user_use = skill.get("user_use") or skill.get("description", "")
    agent_use = skill.get("agent_use", "")
    # Strip markdown bullets for meta description
    agent_clean = re.sub(r"^\s*-\s*", "", agent_use, flags=re.MULTILINE).strip()
    parts = []
    if user_use:
        parts.append(f"What it does: {user_use}")
    if agent_clean:
        parts.append(f"How the agent uses it: {agent_clean}")
    desc = " ".join(parts) if parts else skill.get("description", "")
    # Cap at 300 chars at a word boundary
    if len(desc) > 300:
        desc = desc[:297].rsplit(" ", 1)[0] + "..."
    return desc


def _escape(text):
    """HTML-escape text for safe rendering."""
    return html.escape(str(text), quote=True)


def _agent_use_to_html(agent_use):
    """Convert agent_use markdown (bullet lists) to safe HTML."""
    if not agent_use:
        return "<p>See the SKILL.md tab for full usage instructions.</p>"
    lines = agent_use.strip().split("\n")
    list_items = []
    paragraphs = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            in_list = True
            list_items.append(stripped[2:])
        elif stripped:
            if in_list and list_items:
                paragraphs.append("<ul>" + "".join(f"<li>{_escape(li)}</li>" for li in list_items) + "</ul>")
                list_items = []
                in_list = False
            if stripped:
                paragraphs.append(f"<p>{_escape(stripped)}</p>")
    if list_items:
        paragraphs.append("<ul>" + "".join(f"<li>{_escape(li)}</li>" for li in list_items) + "</ul>")
    return "\n".join(paragraphs) if paragraphs else "<p>See the SKILL.md tab for full usage instructions.</p>"


def render_skill_page(skill, categories, base_url=""):
    """Render a complete self-contained HTML page for a single skill.

    Includes unique social metadata (OG, Twitter), server-rendered content,
    and the Cobalt design system (tokens.css + base.css + skill-page.css,
    common.js + skill-page.js for the theme toggle, cmd-k, tabs, and the
    install-command copy button). No inline styles or scripts — the page
    is styled and wired entirely through the shared site/css and site/js.
    """
    name = skill["name"]
    cat_data = categories.get(skill.get("category", ""), {})
    cat_name = cat_data.get("name", skill.get("category", ""))
    tier = skill.get("tier", "utility")
    tier_label = TIER_LABELS.get(tier, tier.title())
    tier_desc = TIER_DESCS.get(tier, "")
    source = skill.get("source", "new")
    source_label = SOURCE_LABELS.get(source, source)
    description = skill.get("description", "")
    user_use = skill.get("user_use") or description
    agent_use_html = _agent_use_to_html(skill.get("agent_use", ""))
    # install_url is the raw.githubusercontent.com URL the CLI actually fetches.
    # source_url is the github.com/blob page for humans — a blob URL serves
    # text/html, so installing from it writes GitHub's markup into the skill.
    install_url = skill.get("install_url", "")
    source_url = skill.get("source_url") or install_url
    install_cmd = f"hermes skills install {install_url}" if install_url else ""
    skillmd = skill.get("skillmd_content", "SKILL.md content not available.")
    readme = skill.get("readme_content", "README.md content not available.")
    recency = skill.get("recency", "")

    # Source attribution
    sa = skill.get("source_attribution")
    source_link_html = ""
    if isinstance(sa, dict) and sa.get("origin_url"):
        source_link_html = f'<a class="detail-link" href="{_escape(sa["origin_url"])}" target="_blank" rel="noopener">View original source <span aria-hidden="true">&#8599;</span></a>'
    elif isinstance(sa, str) and sa:
        source_link_html = f'<a class="detail-link" href="{_escape(sa)}" target="_blank" rel="noopener">View original source <span aria-hidden="true">&#8599;</span></a>'

    page_url = f"{base_url}/skills/{name}/" if base_url else f"/skills/{name}/"
    meta_desc = build_meta_description(skill)

    # Structured data. Every field is copied from real index data — no ratings,
    # no invented dates, no fabricated author. Optional fields are omitted
    # entirely rather than filled with a placeholder.
    site_root = base_url.rstrip("/") if base_url else ""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": name,
        "name": name,
        "description": description,
        "url": page_url,
        "inLanguage": "en",
        "license": "https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/LICENSE",
        "isPartOf": {
            "@type": "WebSite",
            "@id": f"{site_root}/#website" if site_root else "#website",
            "name": "Hermes Skills Portfolio",
        },
    }
    if recency:
        jsonld["dateModified"] = recency
    sa_author = sa.get("author") if isinstance(sa, dict) else None
    if sa_author:
        jsonld["author"] = {"@type": "Person", "name": sa_author}
    if isinstance(sa, dict) and sa.get("origin_url"):
        jsonld["isBasedOn"] = sa["origin_url"]

    # json.dumps escapes nothing HTML-sensitive by default; </script> inside a
    # value would break out of the block, so neutralise the sequence.
    jsonld_html = (
        '  <script type="application/ld+json">\n  '
        + json.dumps(jsonld, indent=2, ensure_ascii=False).replace("</", "<\\/")
        + "\n  </script>"
    )

    recency_html = (
        f'<span><strong>Updated:</strong> {_escape(recency)}</span>' if recency else ''
    )
    install_block_html = f'''
        <div class="install-block">
          <h3>Install command</h3>
          <div class="install-row">
            <code id="install-cmd">{_escape(install_cmd)}</code>
            <button class="btn btn-outline btn-sm" id="copy-btn" type="button">Copy</button>
          </div>
        </div>
        ''' if install_cmd else ''

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{_escape(name)} — Hermes Skill</title>
  <meta name="description" content="{_escape(meta_desc)}">
  <link rel="canonical" href="{_escape(page_url)}">
  <meta property="og:title" content="{_escape(name)} — Hermes Skill">
  <meta property="og:description" content="{_escape(meta_desc)}">
  <meta property="og:url" content="{_escape(page_url)}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Hermes Skills Portfolio">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{_escape(name)} — Hermes Skill">
  <meta name="twitter:description" content="{_escape(meta_desc)}">
  <link rel="sitemap" type="application/xml" href="../../sitemap.xml">
{jsonld_html}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/tokens.css">
  <link rel="stylesheet" href="../../css/base.css">
  <link rel="stylesheet" href="../../css/skill-page.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="nav is-solid" id="nav">
    <div class="nav-inner">
      <a class="nav-brand" href="../../index.html">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 14l4-4 4 4 8-8"/><path d="M4 20h16"/></svg>
        Hermes Skills
      </a>
      <nav class="nav-links" aria-label="Sections">
        <a href="../../index.html" data-nav="catalog">Catalog</a>
        <a href="../../bundles.html" data-nav="bundles">Bundles</a>
        <a href="../../changelog.html" data-nav="changelog">Changelog</a>
        <a href="../../submit.html" data-nav="submit">Submit a skill</a>
      </nav>
      <div class="nav-actions">
        <button class="cmdk-trigger" id="cmdk-trigger" aria-haspopup="dialog" aria-controls="cmdk-modal">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span class="cmdk-trigger-label">Search skills…</span>
          <kbd class="cmdk-trigger-kbd">&#8984;K</kbd>
        </button>
        <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="Toggle theme (t)">
          <svg class="icon-sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          <svg class="icon-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
        <a class="github-link" href="https://github.com/THEROCKSSS/hermes-skills-portfolio" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </header>

  <main id="main" class="skill-main" tabindex="-1">
    <div class="wrap">
      <div class="skill-shell">
        <p class="skill-back-link"><a href="../../index.html">&#8592; Back to catalog</a></p>

        <header class="detail-header">
          <div class="detail-titles">
            <h1>{_escape(name)}</h1>
            <span class="tier-badge {tier}">{tier_label}</span>
          </div>
          <p class="detail-desc">{_escape(description)}</p>
          <div class="detail-meta-row">
            <span><strong>Category:</strong> {_escape(cat_name)}</span>
            <span><strong>Tier:</strong> {_escape(tier_desc)}</span>
            <span><strong>Source:</strong> {_escape(source_label)}</span>
            {recency_html}
          </div>
        </header>

        <div class="detail-tabs" role="tablist" aria-label="Skill documentation">
          <button class="detail-tab active" id="tab-btn-overview" data-tab="overview" role="tab" aria-selected="true" aria-controls="tab-overview">Overview</button>
          <button class="detail-tab" id="tab-btn-skillmd" data-tab="skillmd" role="tab" aria-selected="false" aria-controls="tab-skillmd">SKILL.md</button>
          <button class="detail-tab" id="tab-btn-readme" data-tab="readme" role="tab" aria-selected="false" aria-controls="tab-readme">README</button>
        </div>

        <div class="detail-tab-content active" id="tab-overview" role="tabpanel" aria-labelledby="tab-btn-overview" tabindex="0">
          <section class="detail-section">
            <h2>What it does</h2>
            <p>{_escape(user_use)}</p>
          </section>
          <section class="detail-section">
            <h2>How an agent uses it</h2>
            {agent_use_html}
          </section>
          <section class="detail-section">
            <h2>What you get</h2>
            <p>Install this skill and your Hermes agent can {_escape(description.lower())} No manual setup, no scripts to run &mdash; the agent handles it.</p>
          </section>
          {install_block_html}
          <a class="detail-link" href="{_escape(source_url)}" target="_blank" rel="noopener">View SKILL.md on GitHub <span aria-hidden="true">&#8599;</span></a>
          {source_link_html}
        </div>

        <div class="detail-tab-content" id="tab-skillmd" role="tabpanel" aria-labelledby="tab-btn-skillmd" tabindex="0">
          <pre class="skillmd-viewer">{_escape(skillmd)}</pre>
        </div>

        <div class="detail-tab-content" id="tab-readme" role="tabpanel" aria-labelledby="tab-btn-readme" tabindex="0">
          <pre class="skillmd-viewer">{_escape(readme)}</pre>
        </div>
      </div>
    </div>
  </main>

  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-col">
        <span class="footer-word">Hermes Skills</span>
        <p class="footer-note">Install one, your agent can now do that for you.</p>
      </div>
      <div class="footer-col">
        <span class="footer-label mono">Install any skill</span>
        <code class="footer-code mono">hermes skills install &lt;url&gt;</code>
      </div>
      <div class="footer-col">
        <span class="footer-label mono">Colophon</span>
        <p class="footer-meta">By Owen &middot; MIT licensed &middot;
          <a href="https://github.com/THEROCKSSS/hermes-skills-portfolio" target="_blank" rel="noopener">Source on GitHub</a>
        </p>
      </div>
    </div>
  </footer>

  <script src="../../js/common.js"></script>
  <script src="../../js/skill-page.js"></script>
</body>
</html>"""


def catalog_route(entry):
    """Generate a unique route for a catalog entry, handling duplicate slugs across repos.

    Format: catalog/<owner>-<repo>/<slug>/ — the owner-repo prefix disambiguates
    skills with the same slug from different source repositories.
    """
    repo = entry.get("repo", "unknown")
    slug = entry.get("slug", "unknown")
    repo_slug = re.sub(r"[^a-zA-Z0-9-]", "-", repo).strip("-")
    return f"catalog/{repo_slug}/{slug}/"


def validate_portfolio_data(index, skill_dirs=None):
    """Validate the portfolio index for provenance, count consistency, and structure.

    Returns a list of error strings. Empty list = valid.
    """
    errors = []
    skills = index.get("skills", [])
    portfolio = index.get("portfolio", {})

    # Check total_skills matches actual count
    declared = portfolio.get("total_skills", len(skills))
    if declared != len(skills):
        errors.append(f"portfolio.total_skills ({declared}) does not match skills array length ({len(skills)})")

    # Check directory/index sync
    if skill_dirs is not None:
        index_names = {s["name"] for s in skills}
        if index_names != skill_dirs:
            for name in skill_dirs - index_names:
                errors.append(f"directory/index mismatch: skills/{name}/ exists but not in index")
            for name in index_names - skill_dirs:
                errors.append(f"directory/index mismatch: '{name}' in index but no directory exists")

    # Check provenance per skill
    for skill in skills:
        name = skill.get("name", "?")
        source = skill.get("source", "new")
        sa = skill.get("source_attribution")

        # source_attribution must be populated (object or non-empty string)
        if not sa:
            errors.append(f"{name}: source_attribution is empty")
            continue

        if isinstance(sa, dict):
            origin_url = sa.get("origin_url", "")
            origin_type = sa.get("origin_type", "internal")
            # Adapted skills MUST have a real origin_url
            if source == "adapted" and not origin_url:
                errors.append(f"{name}: adapted skill requires source_attribution.origin_url")
            # Generalized skills: if origin_type is external, must have origin_url
            if source == "generalized" and origin_type == "external" and not origin_url:
                errors.append(f"{name}: generalized skill with external origin requires source_attribution.origin_url")

    return errors


def generate_all_pages(index_path, site_dir, docs_dir, base_url=""):
    """Generate per-skill HTML pages from skills-index.json into site/ and docs/.

    Returns a dict with counts and any errors.
    """
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    skills = index.get("skills", [])
    categories = index.get("categories", {})
    count = 0
    errors = []

    for skill in skills:
        name = skill["name"]
        page_html = render_skill_page(skill, categories, base_url)

        for target_dir in (site_dir, docs_dir):
            skill_dir = os.path.join(target_dir, "skills", name)
            os.makedirs(skill_dir, exist_ok=True)
            page_path = os.path.join(skill_dir, "index.html")
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(page_html)
        count += 1

    return {"pages_generated": count, "errors": errors}