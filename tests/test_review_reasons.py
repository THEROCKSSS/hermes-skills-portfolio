"""Tests for the decline-reason vocabulary.

The point of the module is that a contributor always gets a specific,
actionable answer. These lock that guarantee down.
"""

import unittest

from scripts import review_reasons as rr


class ReasonLookupTests(unittest.TestCase):
    def test_finds_the_reason_among_other_labels(self):
        labels = ["skill-request", "rejected", "decline:duplicate"]
        self.assertEqual(rr.reason_from_labels(labels), "duplicate")

    def test_no_reason_label_returns_none(self):
        self.assertIsNone(rr.reason_from_labels(["skill-request", "rejected"]))

    def test_two_reason_labels_is_ambiguous_and_returns_none(self):
        """Two reasons means the maintainer was unclear — better to say nothing
        than to pick one arbitrarily and put words in their mouth."""
        labels = ["rejected", "decline:duplicate", "decline:quality"]
        self.assertIsNone(rr.reason_from_labels(labels))

    def test_unknown_decline_label_is_ignored(self):
        self.assertIsNone(rr.reason_from_labels(["decline:vibes"]))


class RenderTests(unittest.TestCase):
    def test_every_reason_renders_headline_and_next_steps(self):
        for reason in rr.REASONS:
            out = rr.render(reason)
            with self.subTest(reason=reason):
                self.assertIn(rr.REASONS[reason]["headline"], out)
                self.assertIn("What would change the answer", out)
                # at least one actionable bullet
                self.assertIn("\n- ", out)

    def test_missing_reason_is_honest_rather_than_invented(self):
        """An unlabelled decline must not fabricate a justification."""
        out = rr.render(None)
        self.assertIn("No specific reason label was set", out)
        for reason in rr.REASONS:
            self.assertNotIn(rr.REASONS[reason]["headline"], out)

    def test_unknown_reason_falls_back_to_the_honest_text(self):
        self.assertIn("No specific reason label was set", rr.render("nonsense"))

    def test_subject_is_interpolated(self):
        self.assertIn("`my-skill`", rr.render("quality", subject="`my-skill`"))

    def test_every_reason_states_resubmission_is_allowed(self):
        """A decline is about the submission, not a permanent ban."""
        for reason in rr.REASONS:
            with self.subTest(reason=reason):
                self.assertIn("welcome to open a new proposal", rr.render(reason))


class LabelVocabularyTests(unittest.TestCase):
    def test_label_names_are_prefixed_and_sorted(self):
        labels = rr.all_reason_labels()
        self.assertEqual(labels, sorted(labels))
        for name in labels:
            self.assertTrue(name.startswith("decline:"))

    def test_vocabulary_matches_the_reasons_table(self):
        self.assertEqual(len(rr.all_reason_labels()), len(rr.REASONS))


if __name__ == "__main__":
    unittest.main()
