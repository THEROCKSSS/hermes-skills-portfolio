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
    and minimal JS for tab switching. No external dependencies beyond styles.css.
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
    install_url = skill.get("install_url", "")
    install_cmd = f"hermes skills install {install_url}" if install_url else ""
    skillmd = skill.get("skillmd_content", "SKILL.md content not available.")
    readme = skill.get("readme_content", "README.md content not available.")
    recency = skill.get("recency", "")

    # Source attribution
    sa = skill.get("source_attribution")
    source_link_html = ""
    if isinstance(sa, dict) and sa.get("origin_url"):
        source_link_html = f'<a class="detail-source-link" href="{_escape(sa["origin_url"])}" target="_blank" rel="noopener">View original source ↗</a>'
    elif isinstance(sa, str) and sa:
        source_link_html = f'<a class="detail-source-link" href="{_escape(sa)}" target="_blank" rel="noopener">View original source ↗</a>'

    page_url = f"{base_url}/skills/{name}/" if base_url else f"/skills/{name}/"
    meta_desc = build_meta_description(skill)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape(name)} — Hermes Skill</title>
  <meta name="description" content="{_escape(meta_desc)}">
  <link rel="canonical" href="{_escape(page_url)}">
  <meta property="og:title" content="{_escape(name)} — Hermes Skill">
  <meta property="og:description" content="{_escape(meta_desc)}">
  <meta property="og:url" content="{_escape(page_url)}">
  <meta property="og:type" content="article">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{_escape(name)} — Hermes Skill">
  <meta name="twitter:description" content="{_escape(meta_desc)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../styles.css">
</head>
<body>
  <a class="skip-link" href="#skill-content">Skip to content</a>
  <header class="masthead">
    <div class="masthead-inner">
      <div class="masthead-top">
        <div class="masthead-titles">
          <p class="detail-back-link"><a href="../../">&#8592; Back to portfolio</a></p>
          <h1>{_escape(name)}</h1>
          <p class="tagline">{_escape(description)}</p>
        </div>
        <div class="masthead-actions">
          <span class="tier-badge {tier}">{tier_label}</span>
        </div>
      </div>
      <div class="meta-row">
        <span class="meta-item"><strong>Category:</strong> {_escape(cat_name)}</span>
        <span class="meta-sep">&middot;</span>
        <span class="meta-item"><strong>Tier:</strong> {_escape(tier_desc)}</span>
        <span class="meta-sep">&middot;</span>
        <span class="meta-item"><strong>Source:</strong> {_escape(source_label)}</span>
        {f'<span class="meta-sep">&middot;</span><span class="meta-item"><strong>Updated:</strong> {_escape(recency)}</span>' if recency else ''}
      </div>
    </div>
  </header>

  <main id="skill-content" class="skill-detail-main">
    <div class="skill-detail-inner">
      <div class="detail-tabs">
        <button class="detail-tab active" data-tab="overview" onclick="switchTab('overview')">Overview</button>
        <button class="detail-tab" data-tab="skillmd" onclick="switchTab('skillmd')">SKILL.md</button>
        <button class="detail-tab" data-tab="readme" onclick="switchTab('readme')">README</button>
      </div>

      <div class="detail-tab-content active" id="tab-overview">
        <section class="detail-section">
          <h3>What it does</h3>
          <p>{_escape(user_use)}</p>
        </section>
        <section class="detail-section">
          <h3>How an agent uses it</h3>
          {agent_use_html}
        </section>
        <section class="detail-section">
          <h3>What you get</h3>
          <p>Install this skill and your Hermes agent can {_escape(description.lower())} No manual setup, no scripts to run &mdash; the agent handles it.</p>
        </section>
        {f'''
        <div class="install-block">
          <h4>Install command</h4>
          <code id="install-cmd">{_escape(install_cmd)}</code>
          <button class="copy-btn" id="copy-btn" onclick="copyInstall()">Copy</button>
        </div>
        ''' if install_cmd else ''}
        <div class="detail-links">
          <a class="detail-skillmd-link" href="{_escape(install_url)}" target="_blank" rel="noopener">View SKILL.md on GitHub &#8599;</a>
          {source_link_html}
        </div>
      </div>

      <div class="detail-tab-content" id="tab-skillmd">
        <pre class="skillmd-viewer">{_escape(skillmd)}</pre>
      </div>

      <div class="detail-tab-content" id="tab-readme">
        <pre class="skillmd-viewer">{_escape(readme)}</pre>
      </div>
    </div>
  </main>

  <footer class="footer">
    <p><a href="../../">&#8592; Back to Hermes Skills Portfolio</a></p>
    <p>Install with <code>hermes skills install {_escape(install_url)}</code> or clone the repo.</p>
    <p class="keyboard-hints">Keyboard: <kbd>Esc</kbd> go back</p>
  </footer>

  <script>
  function switchTab(tabName) {{
    document.querySelectorAll('.detail-tab').forEach(function(t) {{ t.classList.remove('active'); }});
    document.querySelectorAll('.detail-tab-content').forEach(function(c) {{ c.classList.remove('active'); }});
    document.querySelector('.detail-tab[data-tab="' + tabName + '"]').classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
  }}
  function copyInstall() {{
    var cmd = document.getElementById('install-cmd').textContent;
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(cmd).then(function() {{
        var btn = document.getElementById('copy-btn');
        btn.textContent = 'Copied!'; btn.classList.add('copied');
        setTimeout(function() {{ btn.textContent = 'Copy'; btn.classList.remove('copied'); }}, 2000);
      }});
    }}
  }}
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') window.location.href = '../../';
  }});
  </script>
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