#!/usr/bin/env python3
"""Tests for cross-vendor brief-review functions in tools/mentor-loop.py.

Tests the advisory brief-review stage (ml-v2 BUILD-B.2) that provides semantic
gap detection without blocking:
- extract_blast_radius: surface the brief's Blast Radius section for the packet
- build_brief_review_prompt: the advisory prompt that carries ground truth
- count_advisory_findings: count non-empty advisory bullets
- advisory_appendix: non-binding appendix appended to the brief
- advisory_record: the authoritative advisory artifact (brief-advisory.md)
- stage_brief_review: the stage runner (fail-open by design, always returns 0)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, PACKAGE_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ml = _load("mentorloop_bR_under_test", "tools/mentor-loop.py")


class CountAdvisoryFindingsTests(unittest.TestCase):
    """Pure function tests for count_advisory_findings()."""

    def test_count_two_gaps(self):
        """Two gap bullets are counted as 2."""
        raw = "- [gap] a\n- [gap] b"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 2)

    def test_none_is_not_counted(self):
        """A line containing 'none' is not counted."""
        raw = "- none"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 0)

    def test_empty_string_is_zero(self):
        """Empty string returns 0."""
        raw = ""
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 0)

    def test_none_with_real_finding(self):
        """'none' does not count; real finding counts."""
        raw = "- none\n- [gap] real"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 1)

    def test_line_not_starting_with_dash_not_counted(self):
        """A line not starting with '-' is not counted."""
        raw = "some text\n- [gap] real"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 1)

    def test_none_with_period_not_counted(self):
        """'none.' is also treated as 'none'."""
        raw = "- none.\n- [gap] real"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 1)

    def test_n_slash_a_not_counted(self):
        """'n/a' is not counted."""
        raw = "- n/a\n- [gap] real"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 1)

    def test_case_insensitive_none(self):
        """'NONE' (uppercase) is not counted."""
        raw = "- NONE\n- [gap] real"
        result = ml.count_advisory_findings(raw)
        self.assertEqual(result, 1)


class ExtractBlastRadiusTests(unittest.TestCase):
    """Pure function tests for extract_blast_radius()."""

    def test_extracts_blast_radius_section(self):
        """A brief with Blast Radius section returns its body."""
        brief = """## Blast Radius

- app/x.js
- app/y.js
"""
        result = ml.extract_blast_radius(brief)
        self.assertIn("app/x.js", result)
        self.assertIn("app/y.js", result)

    def test_no_blast_radius_section(self):
        """A brief without Blast Radius section returns the 'no section' marker."""
        brief = """## Change Surface

- something
"""
        result = ml.extract_blast_radius(brief)
        self.assertIn("no Blast Radius section", result)

    def test_case_insensitive_heading(self):
        """Heading search is case-insensitive."""
        brief = """## BLAST RADIUS

- app/test.js
"""
        result = ml.extract_blast_radius(brief)
        self.assertIn("app/test.js", result)


class BuildBriefReviewPromptTests(unittest.TestCase):
    """Pure function tests for build_brief_review_prompt()."""

    def test_prompt_contains_all_required_parts(self):
        """Prompt contains change intent, brief, blast-radius, and advisory markers."""
        task = "INTENT-TEXT"
        brief = "BRIEF-BODY"
        blast_radius = "BLAST-TEXT"
        result = ml.build_brief_review_prompt(task, brief, blast_radius)
        self.assertIn("INTENT-TEXT", result)
        self.assertIn("BRIEF-BODY", result)
        self.assertIn("BLAST-TEXT", result)
        self.assertIn("CROSS-VENDOR", result)
        self.assertIn("ADVISORY ONLY", result)
        self.assertIn("CHANGE INTENT", result)


class AdvisoryAppendixTests(unittest.TestCase):
    """Pure function tests for advisory_appendix()."""

    def test_normal_appendix_contains_body(self):
        """Normal (non-skipped) appendix contains the body."""
        body = "BODY"
        result = ml.advisory_appendix(body, skipped=False)
        self.assertIn("BODY", result)

    def test_normal_appendix_contains_markers(self):
        """Normal appendix contains 'non-blocking' and 'execute ONLY'."""
        body = ""
        result = ml.advisory_appendix(body, skipped=False)
        self.assertIn("non-blocking", result)
        self.assertIn("execute ONLY", result)

    def test_skipped_appendix_contains_skip_marker(self):
        """Skipped appendix contains SKIP marker."""
        result = ml.advisory_appendix("", skipped=True, reason="no advisor")
        self.assertIn("SKIPPED", result)
        self.assertIn("no advisor", result)

    def test_skipped_appendix_contains_not_cross_vendor_reviewed(self):
        """Skipped appendix contains the 未经跨厂审 marker."""
        result = ml.advisory_appendix("", skipped=True, reason="no advisor")
        self.assertIn("未经跨厂审", result)


class AdvisoryRecordTests(unittest.TestCase):
    """Pure function tests for advisory_record()."""

    def test_record_contains_run_id(self):
        """Record contains the run_id."""
        result = ml.advisory_record("RID", status="OK", findings=3, detail="DET")
        self.assertIn("RID", result)

    def test_record_contains_status(self):
        """Record contains the status."""
        result = ml.advisory_record("RID", status="OK", findings=3, detail="DET")
        self.assertIn("OK", result)

    def test_record_contains_findings_count(self):
        """Record contains the findings count."""
        result = ml.advisory_record("RID", status="OK", findings=3, detail="DET")
        self.assertIn("3", result)

    def test_record_contains_detail(self):
        """Record contains the detail text."""
        result = ml.advisory_record("RID", status="OK", findings=3, detail="DET")
        self.assertIn("DET", result)

    def test_record_contains_metric_separation_marker(self):
        """Record contains the marker that separates this metric from apprentice."""
        result = ml.advisory_record("RID", status="OK", findings=3, detail="DET")
        self.assertIn("SEPARATE from the apprentice correction-rate", result)


class StageBriefReviewTests(unittest.TestCase):
    """Integration tests for stage_brief_review() using temp git repo."""

    def setUp(self):
        """Create a temp git repo and initialize a run."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo, capture_output=True)
        # Create initial commit to have a valid repo
        (self.repo / "README.md").write_text("# Test\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, capture_output=True)

    def tearDown(self):
        """Clean up temp directory."""
        self.tmpdir.cleanup()

    def _make_run(self, task: str = "TASK TEXT") -> tuple[str, Path]:
        """Initialize a run and return run_id and run_dir."""
        run_id, run_dir, _ = ml.init_run(self.repo, task)
        return run_id, run_dir

    def test_skip_when_no_advisor_command(self):
        """Stage returns 0 and marks SKIP when no advisor_command in config."""
        run_id, run_dir = self._make_run()
        brief = """## Blast Radius

- app/llm/answer-validate.js

## Guards & Fail-Directions

- none
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)
        config = {"strong_command": ["x"], "apprentice_command": ["y"], "python": "python"}
        result = ml.stage_brief_review(self.repo, run_id, config)
        self.assertEqual(result, 0)
        advisory_path = run_dir / "brief-advisory.md"
        self.assertTrue(advisory_path.exists())
        advisory = ml.read_text(advisory_path)
        self.assertIn("SKIP", advisory)
        # Check brief was marked
        brief_marked = ml.read_text(run_dir / "mentor-brief.md")
        self.assertIn("未经跨厂审", brief_marked)

    def test_skip_when_advisor_not_found(self):
        """Stage returns 0 and marks SKIP when advisor executable not found."""
        run_id, run_dir = self._make_run()
        brief = """## Blast Radius

- app/llm/answer-validate.js

## Guards & Fail-Directions

- none
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)
        config = {
            "strong_command": ["x"],
            "apprentice_command": ["y"],
            "python": "python",
            "advisor_command": ["definitely-missing-advisor-xyz", "-o", "{output}"],
        }
        result = ml.stage_brief_review(self.repo, run_id, config)
        self.assertEqual(result, 0)
        advisory_path = run_dir / "brief-advisory.md"
        self.assertTrue(advisory_path.exists())
        advisory = ml.read_text(advisory_path)
        self.assertIn("SKIP", advisory)
        brief_marked = ml.read_text(run_dir / "mentor-brief.md")
        self.assertIn("未经跨厂审", brief_marked)

    def test_ok_path_with_mock_advisor(self):
        """Stage returns 0 and records findings when advisor runs successfully."""
        run_id, run_dir = self._make_run("TASK TEXT")
        brief = """## Blast Radius

- app/llm/answer-validate.js

## Guards & Fail-Directions

- none
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)

        # Create a mock advisor that outputs findings
        mock_advisor_path = self.repo / "mock_advisor.py"
        mock_advisor_path.write_text(
            """import argparse, sys
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("-o","--output",required=True,type=Path)
a,_ = p.parse_known_args()
sys.stdin.read()
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text("- [gap] undeclared fail-open guard on validateAnswer -- launders the anchored badge\\n- [gap] blast radius omits the caller in app.js\\n", encoding="utf-8")
"""
        )

        config = {
            "strong_command": ["x"],
            "apprentice_command": ["y"],
            "python": "python",
            "advisor_command": [sys.executable, str(mock_advisor_path), "-o", "{output}"],
        }
        result = ml.stage_brief_review(self.repo, run_id, config)
        self.assertEqual(result, 0)

        # Check advisory record
        advisory_path = run_dir / "brief-advisory.md"
        self.assertTrue(advisory_path.exists())
        advisory = ml.read_text(advisory_path)
        self.assertIn("status: OK", advisory)
        self.assertIn("findings_count: 2", advisory)

        # Check brief was marked with appendix
        brief_marked = ml.read_text(run_dir / "mentor-brief.md")
        self.assertIn("undeclared fail-open guard", brief_marked)

        # Check prompt was written and contains necessary parts
        prompt_path = run_dir / "brief-review-prompt.md"
        self.assertTrue(prompt_path.exists())
        prompt = ml.read_text(prompt_path)
        self.assertIn("TASK TEXT", prompt)
        self.assertIn("answer-validate.js", prompt)


if __name__ == "__main__":
    unittest.main()
