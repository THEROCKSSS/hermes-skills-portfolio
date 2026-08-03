"""Tests for the install-URL normalizer.

The bug these lock down: `install_url` pointed at a github.com/blob page, which
serves text/html. The CLI accepts any HTTP(S) URL, so the install succeeded and
wrote GitHub's page markup into the skill body — an entirely silent failure.
"""

import unittest

from scripts.normalize_install_urls import (
    INSTALL_CMD_RE,
    blob_to_raw,
    normalize,
    raw_to_blob,
    verify,
)

BLOB = "https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/tailscale-deploy/SKILL.md"
RAW = "https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/tailscale-deploy/SKILL.md"


class UrlConversionTests(unittest.TestCase):
    def test_blob_url_converts_to_raw(self):
        self.assertEqual(blob_to_raw(BLOB), RAW)

    def test_raw_url_converts_back_to_blob(self):
        self.assertEqual(raw_to_blob(RAW), BLOB)

    def test_conversion_is_idempotent(self):
        self.assertEqual(blob_to_raw(blob_to_raw(BLOB)), RAW)

    def test_non_github_urls_pass_through_untouched(self):
        other = "https://example.com/some/SKILL.md"
        self.assertEqual(blob_to_raw(other), other)


class NormalizeTests(unittest.TestCase):
    def test_normalize_splits_install_target_from_human_link(self):
        index = {"skills": [{"name": "tailscale-deploy", "install_url": BLOB}]}
        index, changed = normalize(index)
        skill = index["skills"][0]
        self.assertEqual(skill["install_url"], RAW)
        self.assertEqual(skill["source_url"], BLOB)
        self.assertEqual(changed, ["tailscale-deploy"])

    def test_normalize_is_a_noop_on_already_correct_entries(self):
        index = {"skills": [{"name": "x", "install_url": RAW, "source_url": BLOB}]}
        _, changed = normalize(index)
        self.assertEqual(changed, [])


class VerifyTests(unittest.TestCase):
    def test_verify_rejects_a_blob_install_url(self):
        problems = verify({"skills": [{"name": "x", "install_url": BLOB}]})
        self.assertTrue(any("blob" in p for p in problems), problems)

    def test_verify_rejects_a_url_that_is_not_a_skill_md(self):
        bad = "https://raw.githubusercontent.com/o/r/main/skills/x/README.md"
        problems = verify({"skills": [{"name": "x", "install_url": bad}]})
        self.assertTrue(any("SKILL.md" in p for p in problems), problems)

    def test_verify_accepts_a_correct_entry(self):
        self.assertEqual(verify({"skills": [{"name": "x", "install_url": RAW}]}), [])


class MarkdownRewriteTests(unittest.TestCase):
    def test_regex_matches_an_install_command_in_a_fenced_block(self):
        text = f"```bash\nhermes skills install {BLOB}\n```"
        self.assertIsNotNone(INSTALL_CMD_RE.search(text))

    def test_regex_leaves_a_plain_prose_link_alone(self):
        """A bare blob link is a legitimate 'view the source' link, not a bug."""
        text = f"See the source at {BLOB} for details."
        self.assertIsNone(INSTALL_CMD_RE.search(text))


if __name__ == "__main__":
    unittest.main()
