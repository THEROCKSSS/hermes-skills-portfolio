"""Tests for scripts/generate_feed.py — the derived Atom feed.

The feed is generated from site/js/changelog-data.js, so these tests exercise
the real repo data (not a fixture-only universe): if the shipped feed drifts
from the shipped changelog, `test_on_disk_feeds_match_the_data` goes red.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.generate_feed import (
    BASE_URL,
    DATA_PATH,
    OUTPUT_PATHS,
    FeedDataError,
    check_feed,
    entry_title,
    extract_commits,
    parse_commits,
    render_feed,
    write_feed,
)

ATOM = "{http://www.w3.org/2005/Atom}"

SAMPLE_JS = """
window.HermesChangelog = {
  COMMITS: [
    // a comment, and a trailing comma below, both legal JS
    { date: "2026-07-29", time: "17:57", hash: "649bda9",
      text: "Fixes CI & deletes <dead> files." },
    { date: "2026-07-20", time: "00:26", hash: "7f3c7f5",
      text: "Scaffolds the monorepo." },
  ]
};
"""


def write_js(directory: Path, body: str) -> Path:
    path = Path(directory) / "changelog-data.js"
    path.write_text(body, encoding="utf-8")
    return path


class ParserTests(unittest.TestCase):
    def test_parses_unquoted_keys_comments_and_trailing_commas(self):
        commits = extract_commits(SAMPLE_JS)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["hash"], "649bda9")
        self.assertEqual(commits[1]["text"], "Scaffolds the monorepo.")

    def test_real_repo_data_parses_and_is_non_empty(self):
        commits = parse_commits(DATA_PATH)
        self.assertGreater(len(commits), 0)
        for commit in commits:
            for field in ("date", "time", "hash", "text"):
                self.assertTrue(commit[field].strip(), f"{field} blank in {commit}")

    def test_missing_commits_array_raises_instead_of_emitting_empty_feed(self):
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), "window.HermesChangelog = { ENTRIES: [] };")
            with self.assertRaises(FeedDataError) as ctx:
                parse_commits(path)
            self.assertIn("COMMITS", str(ctx.exception))

    def test_renamed_global_raises(self):
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), "window.SomethingElse = { COMMITS: [] };")
            with self.assertRaises(FeedDataError):
                parse_commits(path)

    def test_empty_commits_array_raises(self):
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), "window.HermesChangelog = { COMMITS: [] };")
            with self.assertRaises(FeedDataError) as ctx:
                parse_commits(path)
            self.assertIn("empty", str(ctx.exception))

    def test_missing_field_raises(self):
        body = 'window.HermesChangelog = { COMMITS: [ { date: "2026-07-29", time: "17:57", hash: "649bda9" } ] };'
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), body)
            with self.assertRaises(FeedDataError) as ctx:
                parse_commits(path)
            self.assertIn("text", str(ctx.exception))

    def test_malformed_date_raises(self):
        body = (
            'window.HermesChangelog = { COMMITS: [ { date: "July 29", time: "17:57", '
            'hash: "649bda9", text: "x" } ] };'
        )
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), body)
            with self.assertRaises(FeedDataError) as ctx:
                parse_commits(path)
            self.assertIn("date", str(ctx.exception))

    def test_impossible_date_raises(self):
        body = (
            'window.HermesChangelog = { COMMITS: [ { date: "2026-13-45", time: "17:57", '
            'hash: "649bda9", text: "x" } ] };'
        )
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), body)
            with self.assertRaises(FeedDataError):
                parse_commits(path)

    def test_duplicate_hash_raises_because_entry_ids_must_be_unique(self):
        body = (
            'window.HermesChangelog = { COMMITS: ['
            '{ date: "2026-07-29", time: "17:57", hash: "649bda9", text: "a" },'
            '{ date: "2026-07-28", time: "10:00", hash: "649bda9", text: "b" } ] };'
        )
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), body)
            with self.assertRaises(FeedDataError) as ctx:
                parse_commits(path)
            self.assertIn("duplicate", str(ctx.exception).lower())

    def test_unsupported_js_token_raises(self):
        body = 'window.HermesChangelog = { COMMITS: [ someVariable ] };'
        with TemporaryDirectory() as tmp:
            path = write_js(Path(tmp), body)
            with self.assertRaises(FeedDataError):
                parse_commits(path)


class AtomDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commits = parse_commits(DATA_PATH)
        cls.document = render_feed(cls.commits)
        cls.root = ET.fromstring(cls.document)

    def test_feed_parses_as_xml_with_the_atom_namespace(self):
        self.assertEqual(self.root.tag, f"{ATOM}feed")

    def test_entry_count_matches_the_commit_count(self):
        entries = self.root.findall(f"{ATOM}entry")
        self.assertEqual(len(entries), len(self.commits))

    def test_every_entry_has_a_unique_id_built_on_its_commit_hash(self):
        ids = [e.findtext(f"{ATOM}id") for e in self.root.findall(f"{ATOM}entry")]
        self.assertEqual(len(ids), len(set(ids)))
        for commit in self.commits:
            self.assertIn(f"#commit-{commit['hash']}", "\n".join(ids))

    def test_feed_carries_self_and_alternate_links(self):
        links = {
            link.get("rel"): link.get("href")
            for link in self.root.findall(f"{ATOM}link")
        }
        self.assertEqual(links["self"], BASE_URL + "feed.xml")
        self.assertEqual(links["alternate"], BASE_URL + "changelog.html")

    def test_every_entry_links_to_its_changelog_anchor(self):
        for entry in self.root.findall(f"{ATOM}entry"):
            link = entry.find(f'{ATOM}link[@rel="alternate"]')
            self.assertIsNotNone(link)
            self.assertEqual(link.get("href"), entry.findtext(f"{ATOM}id"))
            self.assertTrue(link.get("href").startswith(BASE_URL + "changelog.html#commit-"))

    def test_timestamps_are_iso8601_and_ordered_newest_first(self):
        stamps = [e.findtext(f"{ATOM}updated") for e in self.root.findall(f"{ATOM}entry")]
        for stamp in stamps:
            self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(stamps, sorted(stamps, reverse=True))
        self.assertEqual(self.root.findtext(f"{ATOM}updated"), stamps[0])

    def test_entry_content_is_the_verbatim_commit_text(self):
        contents = {e.findtext(f"{ATOM}content") for e in self.root.findall(f"{ATOM}entry")}
        for commit in self.commits:
            self.assertIn(commit["text"], contents)

    def test_markup_in_commit_text_is_escaped_not_injected(self):
        document = render_feed(extract_commits(SAMPLE_JS))
        self.assertIn("&lt;dead&gt;", document)
        self.assertIn("&amp;", document)
        root = ET.fromstring(document)
        texts = [e.findtext(f"{ATOM}content") for e in root.findall(f"{ATOM}entry")]
        self.assertIn("Fixes CI & deletes <dead> files.", texts)

    def test_render_is_deterministic(self):
        self.assertEqual(render_feed(self.commits), render_feed(list(reversed(self.commits))))

    def test_entry_title_trims_to_the_first_sentence(self):
        self.assertEqual(entry_title("Adds a thing. Then another."), "Adds a thing")
        long_title = entry_title("word " * 60)
        self.assertLessEqual(len(long_title), 101)
        self.assertTrue(long_title.endswith("…"))


class CheckModeTests(unittest.TestCase):
    def setUp(self):
        self.commits = parse_commits(DATA_PATH)
        self.document = render_feed(self.commits)

    def test_check_passes_right_after_a_write(self):
        with TemporaryDirectory() as tmp:
            paths = (Path(tmp) / "site" / "feed.xml", Path(tmp) / "docs" / "feed.xml")
            write_feed(self.document, paths)
            self.assertEqual(check_feed(self.document, paths), [])

    def test_check_detects_a_missing_feed(self):
        with TemporaryDirectory() as tmp:
            paths = (Path(tmp) / "site" / "feed.xml", Path(tmp) / "docs" / "feed.xml")
            problems = check_feed(self.document, paths)
            self.assertEqual(len(problems), 2)
            self.assertTrue(all("missing" in p for p in problems))

    def test_check_detects_staleness_when_the_data_gains_an_entry(self):
        with TemporaryDirectory() as tmp:
            paths = (Path(tmp) / "site" / "feed.xml", Path(tmp) / "docs" / "feed.xml")
            write_feed(self.document, paths)
            newer = [
                {"date": "2026-08-02", "time": "09:00", "hash": "abc1234",
                 "text": "Adds an Atom feed generated from the changelog data."}
            ] + self.commits
            problems = check_feed(render_feed(newer), paths)
            self.assertEqual(len(problems), 2)
            self.assertTrue(all("stale" in p for p in problems))

    def test_check_detects_a_hand_edited_feed(self):
        with TemporaryDirectory() as tmp:
            paths = (Path(tmp) / "site" / "feed.xml", Path(tmp) / "docs" / "feed.xml")
            write_feed(self.document, paths)
            paths[1].write_text(self.document + "<!-- tampered -->\n", encoding="utf-8")
            problems = check_feed(self.document, paths)
            self.assertEqual(len(problems), 1)
            self.assertIn("stale", problems[0])

    def test_written_copies_are_byte_identical(self):
        with TemporaryDirectory() as tmp:
            paths = (Path(tmp) / "site" / "feed.xml", Path(tmp) / "docs" / "feed.xml")
            write_feed(self.document, paths)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            # newline="\n" on write — a CRLF copy would break CI's diff on Linux.
            self.assertNotIn(b"\r\n", paths[0].read_bytes())

    def test_on_disk_feeds_match_the_data(self):
        """The shipped feed must equal what the shipped changelog data renders."""
        self.assertEqual(check_feed(self.document, OUTPUT_PATHS), [])
        site_feed, docs_feed = (Path(p) for p in OUTPUT_PATHS)
        self.assertEqual(site_feed.read_bytes(), docs_feed.read_bytes())


if __name__ == "__main__":
    unittest.main()
