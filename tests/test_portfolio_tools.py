import html
import json
import tempfile
import unittest
from pathlib import Path

from scripts.portfolio_tools import (
    build_meta_description,
    catalog_route,
    render_skill_page,
    validate_portfolio_data,
)


SAMPLE_SKILL = {
    "name": "forgejo-self-host",
    "category": "devops",
    "tier": "core",
    "description": "Set up a self-hosted Forgejo Git server with Docker.",
    "user_use": "You get a private Git server with repositories, issues, pull requests, and CI.",
    "agent_use": "- Deploy Forgejo with Docker Compose.\n- Verify the API and browser UI.\n- Configure backups.",
    "install_url": "https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/forgejo-self-host/SKILL.md",
    "path": "skills/forgejo-self-host",
    "source": "generalized",
    "source_attribution": {
        "author": "Owen",
        "origin_type": "internal",
        "origin_repo": "Private internal Hermes skill library",
        "origin_url": "",
        "origin_note": "Generalized from the private forgejo skill; no separate public upstream exists.",
        "source_names": ["forgejo"],
        "license": "MIT",
        "derived": True,
    },
    "skillmd_content": "---\nname: forgejo-self-host\n---\n<script>alert(1)</script>",
    "readme_content": "# forgejo-self-host\n\nREADME body",
}

CATEGORIES = {
    "devops": {
        "name": "DevOps & Infrastructure",
        "description": "Deploy and operate services.",
        "skill_count": 1,
    }
}


class SharePageTests(unittest.TestCase):
    def test_meta_description_explains_user_and_agent_value(self):
        value = build_meta_description(SAMPLE_SKILL)
        self.assertIn("What it does:", value)
        self.assertIn("How the agent uses it:", value)
        self.assertLessEqual(len(value), 300)

    def test_rendered_page_has_unique_social_metadata_and_visible_content(self):
        page = render_skill_page(
            SAMPLE_SKILL,
            CATEGORIES,
            base_url="https://therocksss.github.io/hermes-skills-portfolio",
        )
        canonical = "https://therocksss.github.io/hermes-skills-portfolio/skills/forgejo-self-host/"
        self.assertIn(f'<link rel="canonical" href="{canonical}">', page)
        self.assertIn('<meta property="og:title" content="forgejo-self-host — Hermes Skill">', page)
        self.assertIn('<meta property="og:description"', page)
        self.assertIn('<meta name="twitter:card" content="summary">', page)
        self.assertIn("What it does", page)
        self.assertIn("How an agent uses it", page)
        self.assertIn("What you get", page)
        self.assertIn("SKILL.md", page)
        self.assertIn("README", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn(html.escape("<script>alert(1)</script>"), page)

    def test_catalog_routes_disambiguate_duplicate_slugs_by_repository(self):
        left = catalog_route({"repo": "anthropics/skills", "slug": "brand-guidelines"})
        right = catalog_route({"repo": "SkillMedev/skills", "slug": "brand-guidelines"})
        self.assertNotEqual(left, right)
        self.assertEqual(left, "catalog/anthropics-skills/brand-guidelines/")


class ProvenanceValidationTests(unittest.TestCase):
    def test_generalized_internal_source_requires_an_origin_note_not_a_fake_url(self):
        index = {
            "version": "2.0.0",
            "portfolio": {"owner": "Owen", "total_skills": 1},
            "categories": CATEGORIES,
            "skills": [SAMPLE_SKILL],
        }
        self.assertEqual(validate_portfolio_data(index, {"forgejo-self-host"}), [])

    def test_adapted_source_requires_a_real_origin_url(self):
        adapted = json.loads(json.dumps(SAMPLE_SKILL))
        adapted["source"] = "adapted"
        adapted["source_attribution"]["origin_type"] = "external"
        adapted["source_attribution"]["origin_url"] = ""
        index = {
            "version": "2.0.0",
            "portfolio": {"owner": "Owen", "total_skills": 1},
            "categories": CATEGORIES,
            "skills": [adapted],
        }
        errors = validate_portfolio_data(index, {"forgejo-self-host"})
        self.assertTrue(any("origin_url" in error for error in errors), errors)

    def test_total_skills_and_directories_must_match(self):
        index = {
            "version": "2.0.0",
            "portfolio": {"owner": "Owen", "total_skills": 2},
            "categories": CATEGORIES,
            "skills": [SAMPLE_SKILL],
        }
        errors = validate_portfolio_data(index, {"forgejo-self-host", "missing-skill"})
        self.assertTrue(any("total_skills" in error for error in errors), errors)
        self.assertTrue(any("directory/index mismatch" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
