"""Tests for the content-quality checker.

These lock down the parts that are easy to get subtly wrong:

* the metric lint firing on a fabricated claim but *not* on a legitimate number
  (a tax rate, a port, an error-correction level — this corpus is full of them);
* the metric lint not firing on a phrase a skill is explicitly telling you not
  to write (`hallmark-readme` is an entire skill about anti-slop and its tables
  quote every claim the linter hunts for);
* the frontmatter check catching a missing key and a name/directory mismatch;
* the duplicate detector separating near-identical text from unrelated text.

Every filesystem test builds a throwaway skill tree in a tmp dir, so none of
them depend on the state of the real catalog.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_content_quality import (
    FAIL,
    REVIEW,
    _mini_yaml,
    check_duplicates,
    check_frontmatter,
    check_links,
    check_tiers,
    extract_urls,
    find_duplicate_pairs,
    lint_metrics_text,
    load_skills,
    parse_frontmatter,
    strip_code,
    tier_scope_findings,
    validate_url_shape,
)

FULL_FRONTMATTER = """---
name: {name}
description: Use when the user wants a widget built.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [widget, demo]
    related_skills: []
---

# {name}

## Overview

{overview}
"""


def write_skill(root: Path, name: str, *, frontmatter: str | None = None,
                overview: str = "Builds a widget.", readme: str = "# readme\n") -> Path:
    directory = root / "skills" / name
    directory.mkdir(parents=True, exist_ok=True)
    body = frontmatter if frontmatter is not None else FULL_FRONTMATTER.format(
        name=name, overview=overview
    )
    (directory / "SKILL.md").write_text(body, encoding="utf-8")
    (directory / "README.md").write_text(readme, encoding="utf-8")
    return directory


class TmpRepo(unittest.TestCase):
    """Base class handing each test its own empty repo."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)


# --------------------------------------------------------------------------- #
# Invented-metric lint
# --------------------------------------------------------------------------- #


class MetricLintTests(unittest.TestCase):
    def _reported(self, text: str):
        return [h for h in lint_metrics_text(text) if not h.suppressed_by]

    def test_catches_a_fabricated_adoption_claim(self):
        hits = self._reported("Trusted by 50,000+ developers at companies worldwide.")
        self.assertTrue(hits, "expected the fabricated adoption claim to be flagged")
        self.assertTrue(any(h.level == FAIL for h in hits))

    def test_catches_an_invented_percentage_improvement(self):
        hits = self._reported("Increases developer productivity by 47% on average.")
        self.assertTrue(any(h.pattern_id == "percent-claim" and h.level == FAIL for h in hits), hits)

    def test_catches_a_star_count(self):
        hits = self._reported("Backed by 12,400 GitHub stars and growing.")
        self.assertTrue(any(h.pattern_id == "star-count" for h in hits), hits)

    def test_does_not_flag_a_legitimate_tax_rate(self):
        text = "Show tax as its own line with the rate in parentheses, for example Tax (20%)."
        self.assertEqual(self._reported(text), [])

    def test_does_not_flag_a_legitimate_config_number(self):
        text = "A logo covering more than 30% of the QR code makes it unscannable."
        self.assertEqual(self._reported(text), [])

    def test_does_not_flag_a_version_or_port_number(self):
        text = "Requires version 2.1.0 and binds port 8080 on 1.5 GB of RAM."
        self.assertEqual(self._reported(text), [])

    def test_does_not_flag_a_plain_count_of_things(self):
        text = "The bundle groups 5 skills that share one workflow."
        self.assertEqual(self._reported(text), [])

    def test_hex_format_string_in_code_is_not_a_multiplier(self):
        """`{:02x}` reads as '02x'. Code is stripped before the prose is linted."""
        text = 'Convert to hex:\n\n```python\nreturn f"#{rgb[0]:02x}"\n```\n'
        self.assertEqual(self._reported(text), [])

    def test_inline_code_is_not_linted(self):
        text = "Set the token with `--ink: oklch(20% 0.01 240)` before rendering."
        self.assertEqual(self._reported(text), [])

    def test_quoted_anti_pattern_in_a_table_is_suppressed(self):
        """hallmark-readme's own 'Wrong | Right' table must not trip its own lint."""
        text = '| Wrong | Right |\n|---|---|\n| "Trusted by 50,000+ developers" | (omit) |\n'
        hits = lint_metrics_text(text)
        self.assertTrue(hits, "the phrase should still be detected")
        self.assertTrue(all(h.suppressed_by for h in hits), hits)

    def test_negated_quoted_phrase_is_suppressed(self):
        text = '- No "powerful, seamless, comprehensive" filler copy\n'
        hits = lint_metrics_text(text)
        self.assertTrue(all(h.suppressed_by for h in hits), hits)

    def test_a_number_one_complaint_is_not_a_ranking_claim(self):
        """'the #1 complaint' is ordinary prose; '#1 choice' is marketing."""
        self.assertEqual(self._reported('That is the #1 "my PDF looks wrong" complaint.'), [])
        self.assertTrue(self._reported("The #1 choice for teams that ship."))

    def test_time_promise_needs_a_value_claim_in_the_same_sentence(self):
        """'PINs fall in minutes' is a threat model, not a marketing promise."""
        self.assertEqual(self._reported("10,000 PINs fall in minutes."), [])
        self.assertTrue(self._reported("This skill gets it running on your machine in minutes."))

    def test_unsourced_multiplier_is_review_not_fail(self):
        hits = self._reported("GPU inference is 5-10x faster than CPU.")
        self.assertTrue(hits)
        self.assertTrue(all(h.level == REVIEW for h in hits), hits)

    def test_strip_code_preserves_line_numbers(self):
        text = "one\n```\ntwo\n```\nfour"
        self.assertEqual(len(strip_code(text).splitlines()), len(text.splitlines()))


# --------------------------------------------------------------------------- #
# Frontmatter revalidation
# --------------------------------------------------------------------------- #


class FrontmatterTests(TmpRepo):
    def _failures(self):
        return check_frontmatter(load_skills(self.root)).failures

    def test_a_complete_skill_passes(self):
        write_skill(self.root, "widget-build")
        self.assertEqual(self._failures(), [])

    def test_catches_a_missing_required_key(self):
        write_skill(
            self.root,
            "widget-build",
            frontmatter=(
                "---\nname: widget-build\n"
                "description: Use when a widget is needed.\n"
                "version: 1.0.0\nauthor: Hermes Agent\n---\n\n# widget-build\n"
            ),
        )
        failures = self._failures()
        self.assertEqual(len(failures), 1, failures)
        self.assertIn("license", failures[0].message)

    def test_catches_a_name_directory_mismatch(self):
        write_skill(
            self.root,
            "widget-build",
            frontmatter=FULL_FRONTMATTER.format(name="widget-builder", overview="x"),
        )
        failures = self._failures()
        self.assertTrue(any("directory" in f.message for f in failures), failures)

    def test_reports_every_offender_not_just_the_first(self):
        for name in ("alpha", "beta", "gamma"):
            write_skill(
                self.root,
                name,
                frontmatter=f"---\nname: {name}\ndescription: Use when.\n---\n\n# {name}\n",
            )
        failures = self._failures()
        self.assertEqual({f.subject for f in failures}, {"alpha", "beta", "gamma"})

    def test_catches_a_missing_skill_md(self):
        (self.root / "skills" / "empty-skill").mkdir(parents=True)
        failures = self._failures()
        self.assertTrue(any("does not exist" in f.message for f in failures), failures)

    def test_unquoted_colon_in_a_value_is_a_parse_failure(self):
        """PyYAML rejects it, so the fallback parser must too — CI has no PyYAML."""
        write_skill(
            self.root,
            "widget-build",
            frontmatter=(
                "---\nname: widget-build\n"
                "description: Use when it misbehaves: a filter that does nothing.\n"
                "version: 1.0.0\nauthor: Hermes Agent\nlicense: MIT\n---\n\n# widget-build\n"
            ),
        )
        failures = self._failures()
        self.assertTrue(any("does not parse" in f.message for f in failures), failures)

    def test_missing_use_when_prefix_is_review_only(self):
        write_skill(
            self.root,
            "widget-build",
            frontmatter=(
                "---\nname: widget-build\ndescription: Builds widgets fast.\n"
                "version: 1.0.0\nauthor: Hermes Agent\nlicense: MIT\n"
                "metadata:\n  hermes:\n    tags: [widget]\n---\n\n# widget-build\n"
            ),
        )
        result = check_frontmatter(load_skills(self.root))
        self.assertEqual(result.failures, [])
        self.assertTrue(any("Use when" in f.message for f in result.reviews), result.reviews)

    def test_parse_frontmatter_rejects_a_file_with_no_fence(self):
        data, err = parse_frontmatter("# just a heading\n")
        self.assertEqual(data, {})
        self.assertIsNotNone(err)


class FallbackYamlParserTests(unittest.TestCase):
    """The no-PyYAML path CI actually runs. It must agree with PyYAML.

    Without block-scalar support it silently returned `>-` as the description
    for every skill that folds its trigger sentence, which then failed the
    "starts with Use when" convention check for the wrong reason.
    """

    BLOCK = (
        "\nname: github-actions-ci\n"
        "description: >-\n"
        "  Use when a user wants automated testing, builds,\n"
        "  or deployments via GitHub Actions.\n"
        "version: 1.0.0\n"
        "author: Hermes Agent\n"
        "license: MIT\n"
        "metadata:\n"
        "  hermes:\n"
        "    tags: [ci, github]\n"
        "    related_skills: [generate-dockerfile]\n"
    )

    def test_folded_block_scalar_is_joined_into_one_line(self):
        data = _mini_yaml(self.BLOCK)
        self.assertTrue(data["description"].startswith("Use when a user wants"))
        self.assertNotIn("\n", data["description"])

    def test_nested_mapping_and_flow_list(self):
        data = _mini_yaml(self.BLOCK)
        self.assertEqual(data["metadata"]["hermes"]["tags"], ["ci", "github"])
        self.assertEqual(data["metadata"]["hermes"]["related_skills"], ["generate-dockerfile"])

    def test_literal_block_scalar_keeps_line_breaks(self):
        data = _mini_yaml("description: |\n  line one\n  line two\nversion: 1.0.0\n")
        self.assertEqual(data["description"], "line one\nline two")
        self.assertEqual(data["version"], "1.0.0")

    def test_agrees_with_pyyaml_when_pyyaml_is_available(self):
        try:
            import yaml  # noqa: F401
        except ImportError:  # pragma: no cover - CI has no PyYAML
            self.skipTest("PyYAML not installed")
        expected, err = parse_frontmatter(f"---{self.BLOCK}---\n\n# body\n")
        self.assertIsNone(err)
        self.assertEqual(_mini_yaml(self.BLOCK), expected)

    def test_unquoted_colon_space_is_rejected_like_pyyaml_does(self):
        with self.assertRaises(ValueError):
            _mini_yaml("description: Use when it breaks: a filter does nothing.\n")


# --------------------------------------------------------------------------- #
# Duplicate-content detector
# --------------------------------------------------------------------------- #


class DuplicateTests(TmpRepo):
    def test_catches_near_identical_text(self):
        profiles = {
            "alpha": "convert markdown files into a styled pdf with syntax highlighting",
            "beta": "convert markdown files into a styled pdf with syntax highlight",
        }
        pairs = find_duplicate_pairs(profiles)
        self.assertEqual(len(pairs), 1, pairs)
        self.assertEqual(pairs[0][:2], ("alpha", "beta"))

    def test_ignores_unrelated_text(self):
        profiles = {
            "alpha": "convert markdown files into a styled pdf with syntax highlighting",
            "beta": "deploy a service on a tailscale tailnet for private device access",
        }
        self.assertEqual(find_duplicate_pairs(profiles), [])

    def test_reordered_wording_is_caught_by_token_overlap(self):
        """difflib is order-sensitive; the token metric is the backstop."""
        profiles = {
            "alpha": "generate secure passwords passphrases and api keys locally",
            "beta": "locally generate api keys passphrases and secure passwords",
        }
        pairs = find_duplicate_pairs(profiles)
        self.assertEqual(len(pairs), 1, pairs)
        self.assertGreaterEqual(pairs[0][3], 0.70)

    def test_end_to_end_on_a_tmp_catalog(self):
        overview = "Turns a CSV file into a filtered, merged, analysed CSV file for reporting."
        write_skill(self.root, "csv-one", overview=overview)
        write_skill(self.root, "csv-two", overview=overview)
        write_skill(self.root, "unrelated", overview="Deploys a container behind a reverse proxy.")
        result = check_duplicates(load_skills(self.root))
        subjects = [f.subject for f in result.reviews]
        self.assertEqual(subjects, ["csv-one <-> csv-two"], result.findings)
        # Never fatal: a duplicate is a curation call, not a build error.
        self.assertEqual(result.failures, [])


# --------------------------------------------------------------------------- #
# Link checking (shape only — no network in tests)
# --------------------------------------------------------------------------- #


class LinkShapeTests(TmpRepo):
    def test_extracts_urls_and_strips_trailing_punctuation(self):
        urls = extract_urls("See https://example.org/docs, and (https://example.org/other).")
        self.assertEqual(urls, ["https://example.org/docs", "https://example.org/other"])

    def test_urls_inside_code_fences_are_still_extracted(self):
        text = "```bash\nhermes skills install https://raw.githubusercontent.com/o/r/main/SKILL.md\n```"
        self.assertEqual(
            extract_urls(text), ["https://raw.githubusercontent.com/o/r/main/SKILL.md"]
        )

    def test_documentation_placeholders_are_not_treated_as_links(self):
        for url in ("https://YOUR-DOMAIN/hook", "http://localhost:8080", "https://example.com/x"):
            self.assertEqual(validate_url_shape(url).status, "placeholder", url)

    def test_single_label_container_host_is_a_placeholder_not_a_break(self):
        self.assertEqual(validate_url_shape("http://dashboard:8080").status, "placeholder")

    def test_truncated_ellipsis_url_is_a_placeholder(self):
        self.assertEqual(validate_url_shape("https://").status, "placeholder")

    def test_a_real_url_shape_is_ok(self):
        # Not example.com/.org — those are RFC 2606 documentation names and are
        # deliberately classified as placeholders, never fetched.
        self.assertEqual(
            validate_url_shape("https://raw.githubusercontent.com/o/r/main/SKILL.md").status, "ok"
        )

    def test_offline_mode_makes_no_network_calls(self):
        write_skill(
            self.root,
            "widget-build",
            readme="Docs at https://example.org/guide and https://YOUR-HOST/x\n",
        )
        result = check_links(load_skills(self.root), offline=True)
        self.assertEqual(result.failures, [])
        self.assertEqual(result.stats["unique_urls"], 2)


# --------------------------------------------------------------------------- #
# Tier consistency
# --------------------------------------------------------------------------- #


class TierTests(TmpRepo):
    def test_invalid_tier_value_is_a_failure(self):
        write_skill(self.root, "widget-build")
        (self.root / "skills-index.json").write_text(
            '{"skills": [{"name": "widget-build", "tier": "gold", "category": "utility",'
            ' "description": "Builds widgets."}]}',
            encoding="utf-8",
        )
        failures = check_tiers(load_skills(self.root), root=self.root).failures
        self.assertTrue(any("'gold'" in f.message for f in failures), failures)

    def test_a_skill_missing_from_the_index_is_a_failure(self):
        write_skill(self.root, "widget-build")
        (self.root / "skills-index.json").write_text('{"skills": []}', encoding="utf-8")
        failures = check_tiers(load_skills(self.root), root=self.root).failures
        self.assertTrue(any("no skills-index.json entry" in f.message for f in failures), failures)

    def test_narrow_core_skill_is_flagged_for_review(self):
        findings = tier_scope_findings(
            [{"name": "x", "tier": "core", "description": "Send push notifications via ntfy."}]
        )
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0].level, REVIEW)

    def test_broad_core_skill_is_not_flagged(self):
        findings = tier_scope_findings(
            [{"name": "x", "tier": "core", "description": "Write a README for any project."}]
        )
        self.assertEqual(findings, [])

    def test_heuristic_never_rewrites_the_tier(self):
        entry = {"name": "x", "tier": "core", "description": "Send push notifications via ntfy."}
        tier_scope_findings([entry])
        self.assertEqual(entry["tier"], "core")


if __name__ == "__main__":
    unittest.main()
