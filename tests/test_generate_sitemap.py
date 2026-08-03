"""Tests for the sitemap/robots generator.

The failure this locks down: a sitemap that lists a hand-maintained set of
pages. Every other list on this site is derived from skills-index.json at
render time, and the sitemap has to work the same way or it silently stops
listing new skills the day someone forgets to edit it.
"""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.generate_sitemap import (
    BASE_URL,
    ROOT,
    TOP_LEVEL_PAGES,
    build_urls,
    check,
    load_index,
    render_robots,
    render_sitemap,
    write,
)

SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

FAKE_INDEX = {
    "generated_at": "2026-07-20T08:54:32Z",
    "skills": [
        {"name": "zebra-skill", "recency": "2026-07-02"},
        {"name": "alpha-skill", "recency": "2026-07-01"},
        {"name": "no-date-skill"},
    ],
}


class BuildUrlsTests(unittest.TestCase):
    def test_covers_every_top_level_page_and_every_skill(self):
        urls = build_urls(FAKE_INDEX)
        self.assertEqual(len(urls), len(TOP_LEVEL_PAGES) + len(FAKE_INDEX["skills"]))

    def test_skill_urls_are_directory_urls_under_skills(self):
        locs = [u["loc"] for u in build_urls(FAKE_INDEX)]
        self.assertIn(BASE_URL + "skills/alpha-skill/", locs)

    def test_catalog_is_the_bare_base_url_not_index_html(self):
        locs = [u["loc"] for u in build_urls(FAKE_INDEX)]
        self.assertIn(BASE_URL, locs)
        self.assertNotIn(BASE_URL + "index.html", locs)

    def test_skill_entries_are_sorted_so_output_is_stable(self):
        skill_locs = [u["loc"] for u in build_urls(FAKE_INDEX) if "/skills/" in u["loc"]]
        self.assertEqual(skill_locs, sorted(skill_locs))

    def test_lastmod_comes_from_the_skill_and_is_omitted_when_unknown(self):
        by_loc = {u["loc"]: u for u in build_urls(FAKE_INDEX)}
        self.assertEqual(by_loc[BASE_URL + "skills/alpha-skill/"]["lastmod"], "2026-07-01")
        self.assertIsNone(by_loc[BASE_URL + "skills/no-date-skill/"]["lastmod"])

    def test_top_level_lastmod_comes_from_the_index_generated_at(self):
        by_loc = {u["loc"]: u for u in build_urls(FAKE_INDEX)}
        self.assertEqual(by_loc[BASE_URL]["lastmod"], "2026-07-20T08:54:32Z")

    def test_a_new_skill_appears_without_touching_the_script(self):
        """The regression that matters: the list is derived, never hardcoded."""
        before = len(build_urls(FAKE_INDEX))
        grown = dict(FAKE_INDEX, skills=FAKE_INDEX["skills"] + [{"name": "brand-new"}])
        after = build_urls(grown)
        self.assertEqual(len(after), before + 1)
        self.assertIn(BASE_URL + "skills/brand-new/", [u["loc"] for u in after])


class RenderTests(unittest.TestCase):
    def test_output_is_wellformed_sitemap_xml(self):
        root = ET.fromstring(render_sitemap(build_urls(FAKE_INDEX)))
        self.assertEqual(root.tag, SM_NS + "urlset")
        self.assertEqual(len(root.findall(SM_NS + "url")), len(build_urls(FAKE_INDEX)))

    def test_entries_without_a_date_emit_no_lastmod_element(self):
        root = ET.fromstring(render_sitemap(build_urls(FAKE_INDEX)))
        for url in root.findall(SM_NS + "url"):
            if url.findtext(SM_NS + "loc").endswith("no-date-skill/"):
                self.assertIsNone(url.find(SM_NS + "lastmod"))
                break
        else:
            self.fail("no-date-skill was not in the sitemap")

    def test_urls_are_escaped(self):
        xml = render_sitemap([{"loc": "https://example.com/?a=1&b=2", "priority": "0.5"}])
        self.assertIn("&amp;", xml)
        ET.fromstring(xml)  # must still parse

    def test_robots_allows_crawling_and_points_at_the_sitemap(self):
        robots = render_robots()
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn(f"Sitemap: {BASE_URL}sitemap.xml", robots)
        self.assertNotIn("Disallow: /\n", robots)


class WriteAndCheckTests(unittest.TestCase):
    def test_write_produces_byte_identical_files_in_every_output_dir(self):
        with TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "site", Path(tmp) / "docs"
            write(output_dirs=(a, b), index=FAKE_INDEX)
            for name in ("sitemap.xml", "robots.txt"):
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())

    def test_check_passes_immediately_after_a_write(self):
        with TemporaryDirectory() as tmp:
            dirs = (Path(tmp) / "site", Path(tmp) / "docs")
            write(output_dirs=dirs, index=FAKE_INDEX)
            self.assertEqual(check(output_dirs=dirs, index=FAKE_INDEX), [])

    def test_check_reports_a_missing_file(self):
        with TemporaryDirectory() as tmp:
            dirs = (Path(tmp) / "site",)
            problems = check(output_dirs=dirs, index=FAKE_INDEX)
            self.assertTrue(any("missing" in p for p in problems), problems)

    def test_check_reports_a_stale_file_when_a_skill_is_added(self):
        with TemporaryDirectory() as tmp:
            dirs = (Path(tmp) / "site",)
            write(output_dirs=dirs, index=FAKE_INDEX)
            grown = dict(FAKE_INDEX, skills=FAKE_INDEX["skills"] + [{"name": "brand-new"}])
            problems = check(output_dirs=dirs, index=grown)
            self.assertTrue(any("stale" in p for p in problems), problems)


class RealRepoTests(unittest.TestCase):
    """Guards on the files actually committed to this repo."""

    def setUp(self):
        self.index = load_index()

    def test_the_committed_sitemap_is_current(self):
        self.assertEqual(check(index=self.index), [])

    def test_the_committed_sitemap_covers_four_pages_and_every_skill(self):
        expected = len(TOP_LEVEL_PAGES) + len(self.index["skills"])
        root = ET.fromstring((ROOT / "site" / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertEqual(len(root.findall(SM_NS + "url")), expected)

    def test_every_skill_url_resolves_to_a_real_generated_page(self):
        root = ET.fromstring((ROOT / "site" / "sitemap.xml").read_text(encoding="utf-8"))
        missing = []
        for url in root.findall(SM_NS + "url"):
            loc = url.findtext(SM_NS + "loc")
            rel = loc[len(BASE_URL):]
            if not rel.startswith("skills/"):
                continue
            page = ROOT / "site" / rel / "index.html"
            if not page.exists():
                missing.append(rel)
        self.assertEqual(missing, [], f"sitemap lists pages that do not exist: {missing}")

    def test_site_and_docs_copies_are_byte_identical(self):
        for name in ("sitemap.xml", "robots.txt"):
            self.assertEqual(
                (ROOT / "site" / name).read_bytes(),
                (ROOT / "docs" / name).read_bytes(),
                f"{name} differs between site/ and docs/",
            )

    def test_index_json_is_the_only_source_of_the_skill_list(self):
        """No skill name may be hardcoded in the generator."""
        source = (ROOT / "scripts" / "generate_sitemap.py").read_text(encoding="utf-8")
        names = [s["name"] for s in self.index["skills"]]
        hardcoded = [n for n in names if n in source]
        self.assertEqual(hardcoded, [], f"skill names hardcoded in the generator: {hardcoded}")


if __name__ == "__main__":
    unittest.main()
