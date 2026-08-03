"""Tests for the community-submission scaffolder.

Everything here runs against a throwaway repo root built in a temp directory —
no test writes into the real ``skills/`` tree or reads the real index for a
duplicate check, so a passing run can never leave a stray skill behind.

The install-URL assertions exist because of a real, silent bug: a
``github.com/.../blob/...`` URL serves ``text/html``, so
``hermes skills install <blob-url>`` exits 0 while writing GitHub's web page
into the skill body. Anything this scaffolder emits must be the raw form.
"""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.scaffold_skill import (
    EXIT_INVALID,
    EXIT_OK,
    SubmissionError,
    blob_source_url,
    build_index_entry,
    check_duplicate,
    check_name,
    derive_tags,
    find_similar_skills,
    frontmatter_description,
    main,
    normalize_submission,
    parse_issue_body,
    raw_install_url,
    scaffold,
)

# The pattern skills-index.schema.json enforces on install_url.
SCHEMA_INSTALL_RE = re.compile(r"^https://raw\.githubusercontent\.com/.+/SKILL\.md$")

VALID = {
    "name": "log-analyzer",
    "category": "utility",
    "tier": "featured",
    "description": "Scan a log file and report the errors that actually matter.",
    "when_to_use": (
        "- The user has a log file and wants to know what went wrong\n"
        "- The user says \"why did this crash\" or \"read these logs\"\n"
    ),
    "what_it_does": (
        "The agent reads the log, groups repeated lines, and reports the distinct "
        "errors with counts and first/last timestamps."
    ),
    "prerequisites": "- A readable log file on disk",
    "origin": "original",
    "submitter": "octocat",
    "issue_number": 42,
}

EXISTING_SKILLS = ("http-api-tester", "docker-umbrella")


def _make_repo(tmp: Path) -> Path:
    """Build a minimal fake repo root: two existing skills + an index."""
    (tmp / "skills").mkdir(parents=True)
    skills = []
    for name in EXISTING_SKILLS:
        d = tmp / "skills" / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        (d / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        skills.append(
            {
                "name": name,
                "category": "backend" if "api" in name else "devops",
                "tier": "core",
                "description": f"Existing {name} skill for testing.",
                "install_url": raw_install_url(name),
                "path": f"skills/{name}",
            }
        )
    (tmp / "skills-index.json").write_text(
        json.dumps({"version": "1.0.0", "skills": skills, "categories": {}}, indent=2),
        encoding="utf-8",
    )
    return tmp


class TempRepoTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="scaffold-test-")
        self.repo = _make_repo(Path(self._tmp))

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)


class NameValidationTests(unittest.TestCase):
    def test_kebab_case_name_is_accepted(self):
        self.assertEqual(check_name("log-analyzer"), [])
        self.assertEqual(check_name("s3"), ["name 's3' is too short (minimum 3 characters)"])

    def test_uppercase_name_is_rejected(self):
        self.assertTrue(any("kebab-case" in p for p in check_name("LogAnalyzer")))

    def test_underscore_name_is_rejected(self):
        self.assertTrue(any("kebab-case" in p for p in check_name("log_analyzer")))

    def test_spaces_and_slashes_are_rejected(self):
        self.assertTrue(check_name("log analyzer"))
        self.assertTrue(check_name("skills/log-analyzer"))

    def test_leading_or_doubled_hyphens_are_rejected(self):
        self.assertTrue(check_name("-log-analyzer"))
        self.assertTrue(check_name("log--analyzer"))
        self.assertTrue(check_name("log-analyzer-"))

    def test_empty_name_is_rejected(self):
        self.assertTrue(check_name(""))

    def test_reserved_name_is_rejected(self):
        self.assertTrue(any("reserved" in p for p in check_name("scripts")))

    def test_overlong_name_is_rejected(self):
        self.assertTrue(any("too long" in p for p in check_name("a" + "-b" * 40)))


class DuplicateDetectionTests(TempRepoTestCase):
    def test_free_name_is_not_a_duplicate(self):
        self.assertEqual(check_duplicate("log-analyzer", self.repo), [])

    def test_existing_directory_is_a_duplicate(self):
        problems = check_duplicate("docker-umbrella", self.repo)
        self.assertTrue(problems)
        self.assertIn("skills/docker-umbrella/ already exists", problems[0])

    def test_index_only_entry_is_still_a_duplicate(self):
        """A name in the index but not yet on disk must still be refused."""
        index_path = self.repo / "skills-index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["skills"].append({"name": "ghost-skill", "category": "utility"})
        index_path.write_text(json.dumps(index), encoding="utf-8")

        problems = check_duplicate("ghost-skill", self.repo)
        self.assertTrue(problems)
        self.assertIn("skills-index.json already has an entry", problems[0])

    def test_scaffold_refuses_a_duplicate_and_writes_nothing(self):
        sub = dict(VALID, name="docker-umbrella")
        with self.assertRaises(SubmissionError) as ctx:
            scaffold(sub, self.repo)
        self.assertIn("duplicate skill name", str(ctx.exception))
        # The pre-existing skill must be untouched.
        self.assertEqual(
            (self.repo / "skills" / "docker-umbrella" / "README.md").read_text(encoding="utf-8"),
            "# docker-umbrella\n",
        )


class FrontmatterTests(TempRepoTestCase):
    def setUp(self):
        super().setUp()
        self.result = scaffold(VALID, self.repo, today="2026-08-02")
        self.skill_md = (self.repo / "skills" / "log-analyzer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        _, _, rest = self.skill_md.partition("---\n")
        block, _, self.body = rest.partition("\n---\n")
        self.frontmatter = yaml.safe_load(block)

    def test_files_are_written_where_the_catalog_expects_them(self):
        self.assertTrue((self.repo / "skills" / "log-analyzer" / "SKILL.md").is_file())
        self.assertTrue((self.repo / "skills" / "log-analyzer" / "README.md").is_file())
        self.assertEqual(
            sorted(self.result["written"]),
            ["skills/log-analyzer/README.md", "skills/log-analyzer/SKILL.md"],
        )

    def test_frontmatter_is_valid_yaml_with_every_required_field(self):
        for key in ("name", "description", "version", "author", "license", "metadata"):
            self.assertIn(key, self.frontmatter)
        self.assertEqual(self.frontmatter["name"], "log-analyzer")
        self.assertEqual(self.frontmatter["version"], "1.0.0")
        self.assertEqual(self.frontmatter["license"], "MIT")
        self.assertEqual(self.frontmatter["author"], "@octocat")

    def test_description_is_a_use_when_trigger_line(self):
        """AGENTS.md: description states trigger conditions, starting 'Use when'."""
        desc = self.frontmatter["description"]
        self.assertTrue(desc.startswith("Use when"), desc)
        self.assertNotIn("\n", desc)
        self.assertIn("log file", desc)

    def test_description_survives_embedded_quotes(self):
        """A trigger containing double quotes must not break the YAML."""
        self.assertIn('"why did this crash"', self.frontmatter["description"])

    def test_metadata_tags_and_related_skills_are_lists(self):
        hermes = self.frontmatter["metadata"]["hermes"]
        self.assertIsInstance(hermes["tags"], list)
        self.assertIsInstance(hermes["related_skills"], list)
        self.assertTrue(hermes["tags"])

    def test_related_skills_only_reference_skills_that_exist(self):
        related = self.frontmatter["metadata"]["hermes"]["related_skills"]
        for name in related:
            self.assertTrue((self.repo / "skills" / name).is_dir(), name)

    def test_body_has_the_required_section_structure(self):
        for heading in ("## Overview", "## When to Use", "## Common Pitfalls",
                        "## Verification Checklist"):
            self.assertIn(heading, self.body)
        self.assertTrue(self.body.lstrip().startswith("# log-analyzer"))

    def test_submitter_prose_is_carried_through_verbatim(self):
        self.assertIn("groups repeated lines", self.body)
        self.assertIn("- A readable log file on disk", self.body)

    def test_sections_only_a_human_can_write_are_marked_todo(self):
        """No invented workflow/pitfalls — they must be explicit TODOs."""
        self.assertIn("TODO(maintainer)", self.body)

    def test_files_are_written_with_lf_endings(self):
        raw = (self.repo / "skills" / "log-analyzer" / "SKILL.md").read_bytes()
        self.assertNotIn(b"\r\n", raw)


class InstallUrlTests(TempRepoTestCase):
    def test_install_url_is_the_raw_form(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertEqual(
            entry["install_url"],
            "https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/"
            "main/skills/log-analyzer/SKILL.md",
        )
        self.assertRegex(entry["install_url"], SCHEMA_INSTALL_RE)

    def test_install_url_never_contains_blob(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertNotIn("/blob/", entry["install_url"])
        self.assertTrue(entry["install_url"].startswith("https://raw.githubusercontent.com/"))
        self.assertTrue(entry["install_url"].endswith("/SKILL.md"))

    def test_source_url_is_the_human_facing_blob_page(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertEqual(entry["source_url"], blob_source_url("log-analyzer"))
        self.assertIn("/blob/", entry["source_url"])
        self.assertNotEqual(entry["source_url"], entry["install_url"])

    def test_readme_install_command_uses_the_raw_url(self):
        scaffold(VALID, self.repo)
        readme = (self.repo / "skills" / "log-analyzer" / "README.md").read_text(
            encoding="utf-8"
        )
        install_lines = [ln for ln in readme.splitlines() if "hermes skills install" in ln]
        self.assertTrue(install_lines)
        for line in install_lines:
            self.assertNotIn("/blob/", line)
            self.assertIn("https://raw.githubusercontent.com/", line)

    def test_no_generated_file_documents_a_blob_install_command(self):
        result = scaffold(VALID, self.repo)
        for rel, content in result["files"].items():
            for line in content.splitlines():
                if "hermes skills install" in line:
                    self.assertNotIn("/blob/", line, f"{rel}: {line}")

    def test_owner_repo_ref_are_configurable_and_stay_raw(self):
        entry = build_index_entry(normalize_submission(VALID), owner="o", repo="r", ref="dev")
        self.assertEqual(
            entry["install_url"],
            "https://raw.githubusercontent.com/o/r/dev/skills/log-analyzer/SKILL.md",
        )
        self.assertRegex(entry["install_url"], SCHEMA_INSTALL_RE)


class IndexEntryTests(TempRepoTestCase):
    def test_entry_has_every_field_the_schema_requires(self):
        entry = build_index_entry(normalize_submission(VALID), today="2026-08-02")
        for key in ("name", "category", "tier", "description", "install_url", "path"):
            self.assertIn(key, entry)
        self.assertEqual(entry["path"], "skills/log-analyzer")
        self.assertEqual(entry["tier"], "featured")
        self.assertEqual(entry["category"], "utility")
        self.assertEqual(entry["recency"], "2026-08-02")

    def test_usage_counts_start_at_zero(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertEqual(
            entry["usage"],
            {"hub_installs": 0, "github_clones": 0, "stars": 0, "self_reported_users": 0},
        )

    def test_original_submission_is_source_new_with_community_attribution(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertEqual(entry["source"], "new")
        sa = entry["source_attribution"]
        self.assertEqual(sa["author"], "@octocat")
        self.assertEqual(sa["origin_type"], "community")
        self.assertFalse(sa["derived"])
        self.assertIn("issues/42", sa["origin_url"])

    def test_adapted_submission_carries_the_origin_url(self):
        sub = dict(VALID, origin="adapted", origin_url="https://github.com/someone/skill")
        entry = build_index_entry(normalize_submission(sub))
        self.assertEqual(entry["source"], "adapted")
        self.assertEqual(entry["source_attribution"]["origin_url"],
                         "https://github.com/someone/skill")
        self.assertTrue(entry["source_attribution"]["derived"])

    def test_adapted_without_an_origin_url_is_refused(self):
        sub = dict(VALID, origin="adapted")
        sub.pop("origin_url", None)
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission(sub)
        self.assertIn("origin_url is required", str(ctx.exception))

    def test_frontmatter_block_in_the_entry_matches_the_skill_md(self):
        result = scaffold(VALID, self.repo)
        skill_md = result["files"]["skills/log-analyzer/SKILL.md"]
        _, _, rest = skill_md.partition("---\n")
        block, _, _ = rest.partition("\n---\n")
        parsed = yaml.safe_load(block)
        self.assertEqual(parsed["description"], result["entry"]["frontmatter"]["description"])
        self.assertEqual(parsed["name"], result["entry"]["frontmatter"]["name"])
        self.assertEqual(parsed["version"], result["entry"]["frontmatter"]["version"])

    def test_agent_use_and_user_use_carry_the_submitters_words(self):
        entry = build_index_entry(normalize_submission(VALID))
        self.assertIn("- The user has a log file", entry["agent_use"])
        self.assertIn("groups repeated lines", entry["user_use"])


class SubmissionNormalizationTests(unittest.TestCase):
    def test_display_category_names_are_accepted(self):
        sub = normalize_submission(dict(VALID, category="DevOps & Infrastructure"))
        self.assertEqual(sub["category"], "devops")

    def test_dropdown_option_text_is_reduced_to_the_slug(self):
        sub = normalize_submission(
            dict(VALID, category="integrations — Connect agents to external platforms",
                 tier="core — broadly empowering")
        )
        self.assertEqual(sub["category"], "integrations")
        self.assertEqual(sub["tier"], "core")

    def test_unknown_category_is_refused(self):
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission(dict(VALID, category="machine-learning"))
        self.assertIn("category must be one of", str(ctx.exception))

    def test_unknown_tier_is_refused(self):
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission(dict(VALID, tier="platinum"))
        self.assertIn("tier must be one of", str(ctx.exception))

    def test_missing_required_fields_are_all_reported_at_once(self):
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission({"name": "ok-name", "category": "utility", "tier": "core"})
        errors = ctx.exception.errors
        self.assertTrue(any("description is required" in e for e in errors))
        self.assertTrue(any("when_to_use is required" in e for e in errors))
        self.assertTrue(any("what_it_does is required" in e for e in errors))

    def test_non_http_origin_url_is_refused(self):
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission(dict(VALID, origin="adapted", origin_url="ftp://x/y"))
        self.assertIn("http(s) URL", str(ctx.exception))

    def test_submitter_handle_is_stripped_of_its_at_sign(self):
        self.assertEqual(normalize_submission(dict(VALID, submitter="@octocat"))["submitter"],
                         "octocat")

    def test_frontmatter_description_joins_multiple_triggers(self):
        desc = frontmatter_description(
            {"when_to_use": "- A happens\n- B happens\n- C happens", "description": "x"}
        )
        self.assertTrue(desc.startswith("Use when a happens, when b happens, or when c happens"))

    def test_derive_tags_are_kebab_safe_and_bounded(self):
        tags = derive_tags(normalize_submission(VALID))
        self.assertLessEqual(len(tags), 6)
        for tag in tags:
            self.assertRegex(tag, r"^[a-z0-9][a-z0-9-]*$")
        self.assertIn("log", tags)


class IssueBodyParsingTests(unittest.TestCase):
    BODY = """### Proposed skill name

log-analyzer

### Category

utility — General-purpose capabilities for everyday workflows

### Tier

featured — highly useful within a category

### One-line description

Scan a log file and report the errors that actually matter.

### When to use it

- The user has a log file and wants to know what went wrong
- The user says "read these logs"

### What the agent does

The agent reads the log, groups repeated lines, and reports distinct errors.

### Prerequisites

_No response_

### Original or adapted

Original — I wrote this from scratch

### Origin URL

_No response_
"""

    def test_every_answered_field_is_extracted(self):
        fields = parse_issue_body(self.BODY)
        self.assertEqual(fields["name"], "log-analyzer")
        self.assertEqual(fields["tier"], "featured — highly useful within a category")
        self.assertIn("read these logs", fields["when_to_use"])
        self.assertIn("groups repeated lines", fields["what_it_does"])

    def test_no_response_placeholders_are_dropped(self):
        fields = parse_issue_body(self.BODY)
        self.assertNotIn("prerequisites", fields)
        self.assertNotIn("origin_url", fields)

    def test_parsed_body_normalizes_into_a_valid_submission(self):
        sub = normalize_submission(dict(parse_issue_body(self.BODY), issue_number=7))
        self.assertEqual(sub["name"], "log-analyzer")
        self.assertEqual(sub["category"], "utility")
        self.assertEqual(sub["tier"], "featured")
        self.assertEqual(sub["origin"], "original")

    def test_an_empty_body_yields_no_fields(self):
        self.assertEqual(parse_issue_body(""), {})

    def test_a_free_text_issue_fails_validation_rather_than_guessing(self):
        fields = parse_issue_body("I think you should build a log analyzer. Thanks!")
        self.assertEqual(fields, {})
        with self.assertRaises(SubmissionError):
            normalize_submission(fields)


class SimilarSkillTests(TempRepoTestCase):
    def test_similar_skills_come_from_the_real_index_only(self):
        index = json.loads((self.repo / "skills-index.json").read_text(encoding="utf-8"))
        similar = find_similar_skills(
            {"name": "http-api-probe", "description": "Existing http api tester skill for testing.",
             "category": "backend"},
            index,
        )
        self.assertTrue(similar)
        self.assertEqual(similar[0]["name"], "http-api-tester")
        for entry in similar:
            self.assertIn(entry["name"], EXISTING_SKILLS)

    def test_no_overlap_returns_an_empty_list(self):
        index = json.loads((self.repo / "skills-index.json").read_text(encoding="utf-8"))
        self.assertEqual(
            find_similar_skills({"name": "zzz", "description": "qqq"}, index), []
        )


class DryRunTests(TempRepoTestCase):
    def test_dry_run_writes_nothing_but_still_builds_the_entry(self):
        result = scaffold(VALID, self.repo, dry_run=True)
        self.assertFalse((self.repo / "skills" / "log-analyzer").exists())
        self.assertEqual(result["written"], [])
        self.assertEqual(result["entry"]["name"], "log-analyzer")
        self.assertEqual(len(result["files"]), 2)

    def test_dry_run_still_refuses_an_invalid_name(self):
        with self.assertRaises(SubmissionError):
            scaffold(dict(VALID, name="Log_Analyzer"), self.repo, dry_run=True)


class CliTests(TempRepoTestCase):
    def _submission_file(self, data: dict) -> str:
        path = Path(self._tmp) / "submission.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_cli_scaffolds_and_writes_the_entry_file(self):
        entry_path = Path(self._tmp) / "entry.json"
        code = main([
            "--json", self._submission_file(VALID),
            "--repo-root", str(self.repo),
            "--out-entry", str(entry_path),
        ])
        self.assertEqual(code, EXIT_OK)
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
        self.assertEqual(entry["name"], "log-analyzer")
        self.assertRegex(entry["install_url"], SCHEMA_INSTALL_RE)
        self.assertTrue((self.repo / "skills" / "log-analyzer" / "SKILL.md").is_file())

    def test_cli_never_writes_into_skills_index_json(self):
        index_path = self.repo / "skills-index.json"
        before = index_path.read_bytes()
        main(["--json", self._submission_file(VALID), "--repo-root", str(self.repo)])
        self.assertEqual(index_path.read_bytes(), before)

    def test_cli_exits_non_zero_on_a_duplicate_name(self):
        code = main([
            "--json", self._submission_file(dict(VALID, name="docker-umbrella")),
            "--repo-root", str(self.repo),
        ])
        self.assertEqual(code, EXIT_INVALID)

    def test_cli_exits_non_zero_on_an_invalid_name(self):
        code = main([
            "--json", self._submission_file(dict(VALID, name="Log Analyzer")),
            "--repo-root", str(self.repo),
        ])
        self.assertEqual(code, EXIT_INVALID)
        self.assertFalse(any(self.repo.joinpath("skills").glob("Log*")))

    def test_cli_flags_can_supply_a_whole_submission(self):
        code = main([
            "--name", "port-checker",
            "--category", "devops",
            "--tier", "utility",
            "--description", "Check whether a TCP port is open.",
            "--when-to-use", "The user asks whether a port is reachable",
            "--what-it-does", "The agent opens a socket and reports the result.",
            "--repo-root", str(self.repo),
            "--dry-run",
        ])
        self.assertEqual(code, EXIT_OK)
        self.assertFalse((self.repo / "skills" / "port-checker").exists())

    def test_check_only_reports_similar_skills_without_writing(self):
        report_path = Path(self._tmp) / "report.json"
        code = main([
            "--json", self._submission_file(VALID),
            "--repo-root", str(self.repo),
            "--check-only", "--report", str(report_path),
        ])
        self.assertEqual(code, EXIT_OK)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])
        self.assertFalse((self.repo / "skills" / "log-analyzer").exists())

    def test_check_only_on_a_duplicate_reports_the_error_and_exits_non_zero(self):
        report_path = Path(self._tmp) / "report.json"
        code = main([
            "--json", self._submission_file(dict(VALID, name="docker-umbrella")),
            "--repo-root", str(self.repo),
            "--check-only", "--report", str(report_path),
        ])
        self.assertEqual(code, EXIT_INVALID)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertFalse(report["ok"])
        self.assertTrue(any("duplicate" in e for e in report["errors"]))

    def test_cli_reads_an_issue_body_file(self):
        body_path = Path(self._tmp) / "body.md"
        body_path.write_text(IssueBodyParsingTests.BODY, encoding="utf-8")
        code = main([
            "--issue-body", str(body_path),
            "--issue-number", "7",
            "--submitter", "octocat",
            "--repo-root", str(self.repo),
            "--dry-run",
        ])
        self.assertEqual(code, EXIT_OK)


REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUE_FORM = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "skill_request.yml"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-submission.yml"


def _render_issue_form(form: dict, answers: dict) -> str:
    """Render an issue form the way GitHub renders a submitted one."""
    lines = []
    for element in form["body"]:
        if element["type"] == "markdown":
            continue
        label = element["attributes"]["label"]
        if element["type"] == "checkboxes":
            lines += [f"### {label}", ""]
            lines += [f"- [X] {o['label']}" for o in element["attributes"]["options"]] + [""]
            continue
        lines += [f"### {label}", "", answers.get(element["id"]) or "_No response_", ""]
    return "\n".join(lines)


class IssueFormContractTests(unittest.TestCase):
    """The issue form's labels ARE the parser's input contract.

    GitHub renders each field as ``### <label>``; scaffold_skill.py maps those
    headings back to fields. Renaming a label in the form without updating
    LABEL_TO_FIELD silently drops the answer, so this test renders the real
    template and parses it.
    """

    @classmethod
    def setUpClass(cls):
        cls.form = yaml.safe_load(ISSUE_FORM.read_text(encoding="utf-8"))

    def test_form_is_a_structured_issue_form_not_a_markdown_template(self):
        self.assertIn("body", self.form)
        self.assertTrue(all("type" in el for el in self.form["body"]))

    def test_form_applies_the_skill_request_label(self):
        self.assertIn("skill-request", self.form["labels"])

    def test_form_field_ids_match_the_parsers_field_map(self):
        from scripts.scaffold_skill import FIELD_IDS

        ids = {el["id"] for el in self.form["body"] if el["type"] != "markdown"}
        self.assertTrue(set(FIELD_IDS).issubset(ids), set(FIELD_IDS) - ids)

    def test_category_options_are_real_catalog_categories(self):
        from scripts.scaffold_skill import CATEGORIES, _choice

        element = next(el for el in self.form["body"] if el.get("id") == "category")
        for option in element["attributes"]["options"]:
            self.assertIn(_choice(option, CATEGORIES, "category"), CATEGORIES)

    def test_tier_options_are_the_three_real_tiers(self):
        from scripts.scaffold_skill import TIERS, _choice

        element = next(el for el in self.form["body"] if el.get("id") == "tier")
        resolved = {_choice(o, TIERS, "tier") for o in element["attributes"]["options"]}
        self.assertEqual(resolved, set(TIERS))

    def test_a_rendered_submission_parses_into_a_valid_submission(self):
        options = {el.get("id"): el["attributes"].get("options")
                   for el in self.form["body"] if el["type"] == "dropdown"}
        body = _render_issue_form(self.form, {
            "skill_name": "log-triage",
            "category": options["category"][3],
            "tier": options["tier"][1],
            "description": "Read a crash log and report the distinct errors that matter.",
            "when_to_use": '- The user hands over a log file\n- The user says "why did this crash"',
            "what_it_does": "The agent groups repeated lines and reports each distinct error.",
            "prerequisites": "",  # left blank -> _No response_
            "origin": options["origin"][0],
            "origin_url": "",
        })
        parsed = parse_issue_body(body)
        for field in ("name", "category", "tier", "description", "when_to_use", "what_it_does"):
            self.assertIn(field, parsed, f"the form's label for {field} is invisible to the parser")

        sub = normalize_submission(dict(parsed, submitter="octocat", issue_number=128))
        self.assertEqual(sub["name"], "log-triage")
        self.assertEqual(sub["category"], "utility")
        self.assertEqual(sub["tier"], "featured")
        self.assertEqual(sub["origin"], "original")
        self.assertEqual(sub["prerequisites"], "")

    def test_an_adapted_submission_without_an_origin_url_is_caught(self):
        options = {el.get("id"): el["attributes"].get("options")
                   for el in self.form["body"] if el["type"] == "dropdown"}
        body = _render_issue_form(self.form, {
            "skill_name": "log-triage",
            "category": options["category"][3],
            "tier": options["tier"][1],
            "description": "Read a crash log.",
            "when_to_use": "- The user hands over a log file",
            "what_it_does": "The agent reads it.",
            "origin": options["origin"][1],  # adapted
            "origin_url": "",                # ...but no URL
        })
        with self.assertRaises(SubmissionError) as ctx:
            normalize_submission(parse_issue_body(body))
        self.assertIn("origin_url is required", str(ctx.exception))


class WorkflowGateTests(unittest.TestCase):
    """The human approval gate is the point of the workflow — lock it down."""

    @classmethod
    def setUpClass(cls):
        cls.wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        # PyYAML resolves the bare key `on:` to the boolean True.
        cls.triggers = cls.wf.get("on", cls.wf.get(True))

    def test_the_only_trigger_is_an_issue_being_labeled(self):
        self.assertEqual(set(self.triggers), {"issues"})
        self.assertEqual(self.triggers["issues"]["types"], ["labeled"])

    def test_no_push_pull_request_or_schedule_trigger_exists(self):
        for forbidden in ("push", "pull_request", "pull_request_target", "schedule",
                          "workflow_dispatch", "issue_comment"):
            self.assertNotIn(forbidden, self.triggers)

    def test_each_job_is_gated_on_a_specific_label(self):
        conditions = {job_id: job.get("if", "") for job_id, job in self.wf["jobs"].items()}
        self.assertIn("approved", conditions["scaffold"])
        self.assertIn("rejected", conditions["decline"])
        for job_id, condition in conditions.items():
            self.assertIn("skill-request", condition, job_id)
            self.assertIn("github.event.label.name", condition, job_id)

    def test_the_approved_path_opens_a_draft_pr_and_never_pushes_to_main(self):
        steps = self.wf["jobs"]["scaffold"]["steps"]
        script = "\n".join(s.get("run", "") for s in steps)
        self.assertIn("gh pr create", script)
        self.assertIn("--draft", script)
        self.assertIn('git push origin "$branch"', script)
        self.assertNotIn("git push origin main", script)
        self.assertNotIn("gh pr merge", script)

    def test_untrusted_issue_text_reaches_scripts_only_through_env_vars(self):
        """`${{ github.event.issue.body }}` inside a run: block is a shell injection."""
        for job in self.wf["jobs"].values():
            for step in job["steps"]:
                self.assertNotIn("github.event.issue.body", step.get("run", ""),
                                 step.get("name"))
                self.assertNotIn("github.event.issue.title", step.get("run", ""),
                                 step.get("name"))


if __name__ == "__main__":
    unittest.main()
