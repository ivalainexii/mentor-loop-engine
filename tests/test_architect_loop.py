#!/usr/bin/env python3
"""Tests for architect-loop functions in tools/mentor-loop.py (ml-v2 BUILD-C).

Tests the architect-loop closure functions that close B's escalation:
- C-2 precedent injection: load_precedents, build_brief_prompt with precedents
- C-1 packet assembly: extract_dec_sections, build_architect_packet, stage_architect_packet
- C-3 stamp + disposition: stamp_architect_ratified, build_disposition_skeleton, stage_architect_ratify
- C-4 auto-consult: run_architect_consult (runs deterministic; output checked elsewhere)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, PACKAGE_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ml = _load("ml_bc_under_test", "tools/mentor-loop.py")


# Shared fixture for all tests
DECISIONS = """# ledger
## DEC-001 — first thing
- Status: Accepted
- Decision: do the thing.
- **Consequences / guardrail for future briefs:** never touch app/x.js without a tripwire.

### Note N-1 — not a guardrail
irrelevant.

## DEC-007 — seventh thing
- Decision: seven.
- Consequences / guardrail for future briefs: keep the exec channel opt-in.
"""


class GitPorcelainChannelTests(unittest.TestCase):
    """Git diagnostics must not be interpreted as porcelain status data."""

    @staticmethod
    def _git_result(*, returncode: int = 0, stdout: str = "", stderr: str = ""):
        def fake_run(*args, **kwargs):
            if kwargs.get("stderr") == subprocess.STDOUT:
                return SimpleNamespace(returncode=returncode, stdout=stdout + stderr)
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

        return fake_run

    def test_clean_worktree_ignores_zero_exit_git_diagnostic(self):
        warning = "warning: unable to access global excludes file: Permission denied\n"
        with mock.patch.object(
            ml.subprocess,
            "run",
            side_effect=self._git_result(stderr=warning),
        ):
            ml.ensure_clean_worktree(Path("."))

    def test_clean_worktree_still_blocks_real_porcelain_output(self):
        warning = "warning: unable to access global excludes file: Permission denied\n"
        with mock.patch.object(
            ml.subprocess,
            "run",
            side_effect=self._git_result(stdout=" M app.py\n", stderr=warning),
        ):
            with self.assertRaisesRegex(RuntimeError, "app.py"):
                ml.ensure_clean_worktree(Path("."))

    def test_clean_worktree_still_blocks_failed_git_status(self):
        with mock.patch.object(
            ml.subprocess,
            "run",
            side_effect=self._git_result(returncode=128, stderr="fatal: not a work tree\n"),
        ):
            with self.assertRaisesRegex(RuntimeError, "could not read git status"):
                ml.ensure_clean_worktree(Path("."))

    def test_snapshot_cannot_recover_from_an_initial_git_status_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / ".mentor-loop" / "runs" / "run-1").mkdir(parents=True)
            status_results = [
                (128, "", "fatal: first status failed\n"),
                (0, "", ""),
            ]
            with mock.patch.object(ml, "ensure_git_repo", return_value=repo):
                with mock.patch.object(
                    ml,
                    "git_porcelain_status",
                    side_effect=status_results,
                ) as status_mock:
                    with mock.patch.object(ml, "run_local", return_value=(0, "")):
                        with self.assertRaisesRegex(RuntimeError, "first status failed"):
                            ml.stage_snapshot(repo, "run-1")

            self.assertEqual(status_mock.call_count, 1)


class LoadPrecedentsTests(unittest.TestCase):
    """Tests for load_precedents() -- C-2 precedent injection (pure)."""

    def test_load_precedents_with_decisions_file(self):
        """load_precedents returns precedents string with DEC sections and guardrails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / ".mentor-loop").mkdir(parents=True, exist_ok=True)
            ml.write_text(repo / ".mentor-loop" / "decisions.md", DECISIONS)

            result = ml.load_precedents(repo)

            self.assertIn("DEC-001 — first thing", result)
            self.assertIn("never touch app/x.js", result)
            self.assertIn("keep the exec channel opt-in", result)
            self.assertNotIn("irrelevant", result)

    def test_load_precedents_no_mentor_loop_dir(self):
        """load_precedents returns exact marker when .mentor-loop/decisions.md missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            result = ml.load_precedents(repo)
            self.assertEqual(result, "No architecture precedents found.")

    def test_build_brief_prompt_with_precedents(self):
        """build_brief_prompt(task, lessons, prec) CONTAINS precedent sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / ".mentor-loop").mkdir(parents=True, exist_ok=True)
            ml.write_text(repo / ".mentor-loop" / "decisions.md", DECISIONS)

            prec = ml.load_precedents(repo)
            result = ml.build_brief_prompt("task", "No active lessons found.", prec)

            self.assertIn("Architecture precedents from this repo", result)
            self.assertIn("never touch app/x.js", result)
            self.assertIn("Active lessons from this repo:", result)

    def test_build_brief_prompt_backward_compat_two_args(self):
        """build_brief_prompt(task, lessons) with two args is callable and contains default."""
        result = ml.build_brief_prompt("t", "L")
        self.assertIn("No architecture precedents found.", result)


class ExtractDecSectionsTests(unittest.TestCase):
    """Tests for extract_dec_sections() -- C-1 packet assembly (pure)."""

    def test_extract_dec_sections_single_dec(self):
        """extract_dec_sections with [DEC-007] returns that DEC's full section."""
        result = ml.extract_dec_sections(DECISIONS, ["DEC-007"])
        self.assertIn("keep the exec channel opt-in", result)
        self.assertIn("DEC-007", result)
        self.assertNotIn("first thing", result)

    def test_extract_dec_sections_empty_list(self):
        """extract_dec_sections with [] returns no-DEC-ids marker."""
        result = ml.extract_dec_sections(DECISIONS, [])
        self.assertIn("no DEC ids cited", result)

    def test_extract_dec_sections_missing_dec(self):
        """extract_dec_sections with missing DEC id notes 'not found'."""
        result = ml.extract_dec_sections(DECISIONS, ["DEC-999"])
        self.assertIn("not found", result)

    def test_extract_dec_sections_multiple_decs(self):
        """extract_dec_sections with multiple ids returns all sections."""
        result = ml.extract_dec_sections(DECISIONS, ["DEC-001", "DEC-007"])
        self.assertIn("DEC-001", result)
        self.assertIn("DEC-007", result)
        self.assertIn("never touch app/x.js", result)
        self.assertIn("keep the exec channel opt-in", result)


class BuildArchitectPacketTests(unittest.TestCase):
    """Tests for build_architect_packet() -- C-1 packet assembly (pure)."""

    def test_build_architect_packet_contains_all_required_parts(self):
        """build_architect_packet includes all required fields and markers."""
        result = ml.build_architect_packet(
            "RID", "INBOX-X", "INTENT-X", "BLAST-X", "DEC-SECS-X", "LESSON-X"
        )
        self.assertIn("RID", result)
        self.assertIn("INBOX-X", result)
        self.assertIn("INTENT-X", result)
        self.assertIn("BLAST-X", result)
        self.assertIn("DEC-SECS-X", result)
        self.assertIn("LESSON-X", result)
        self.assertIn("用户明示指令", result)
        self.assertIn("Opus 倾向", result)
        self.assertIn("FAIL-CLOSED", result)
        self.assertIn("architect-ratify --run RID", result)


class StampArchitectRatifiedTests(unittest.TestCase):
    """Tests for stamp_architect_ratified() -- C-3 stamp + disposition (pure)."""

    def test_stamp_architect_ratified_fail_open_guards(self):
        """stamp_architect_ratified stamps fail-open guards but not fail-closed ones."""
        brief = """## Guards & Fail-Directions

- citation gate: fail-open — no weaker than 004
- direction gate: unsure which way this should fail
- solid gate: fail-closed — must block
"""
        new, n = ml.stamp_architect_ratified(brief, "DEC-042")
        self.assertEqual(n, 2)
        self.assertIn("citation gate: fail-open — no weaker than 004 [architect-ratified: DEC-042]", new)
        self.assertIn("direction gate: unsure which way this should fail [architect-ratified: DEC-042]", new)
        self.assertEqual(new.count("[architect-ratified"), 2)

    def test_stamp_architect_ratified_idempotent(self):
        """stamp_architect_ratified on already-ratified brief returns count 0."""
        brief_with_stamp = """## Guards & Fail-Directions

- citation gate: fail-open — no weaker than 004 [architect-ratified: DEC-042]
"""
        new, n = ml.stamp_architect_ratified(brief_with_stamp, "DEC-042")
        self.assertEqual(n, 0)

    def test_stamp_architect_ratified_unlocks_honesty_gate(self):
        """After stamping, check_brief_honesty returns 'ok' status."""
        brief = """## Guards & Fail-Directions

- citation gate: fail-open — no weaker than 004
- direction gate: unsure which way this should fail
"""
        new, _ = ml.stamp_architect_ratified(brief, "DEC-042")
        honesty = ml.check_brief_honesty(new)
        self.assertEqual(honesty["status"], "ok")


class BuildDispositionSkeletonTests(unittest.TestCase):
    """Tests for build_disposition_skeleton() -- C-3 stamp + disposition (pure)."""

    def test_build_disposition_skeleton_contains_all_parts(self):
        """build_disposition_skeleton includes verdict, guards, ref, and self-check."""
        result = ml.build_disposition_skeleton(
            "RID", "DEC-042", "VERDICT-TEXT", ["citation gate", "direction gate"]
        )
        self.assertIn("VERDICT-TEXT", result)
        self.assertIn("citation gate, direction gate", result)
        self.assertIn("合宪自检", result)


class StageBriefCheckAndArchitectPacketTests(unittest.TestCase):
    """Integration tests for C-1/C-3/C-4 with temp git repo."""

    def setUp(self):
        """Create a temp git repo with DECISIONS."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo, capture_output=True)
        # Create initial commit
        (self.repo / "README.md").write_text("# Test\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, capture_output=True)
        # Set up decisions.md
        (self.repo / ".mentor-loop").mkdir(parents=True, exist_ok=True)
        ml.write_text(self.repo / ".mentor-loop" / "decisions.md", DECISIONS)

    def tearDown(self):
        """Clean up temp directory."""
        self.tmpdir.cleanup()

    def test_init_run_writes_precedents(self):
        """init_run writes precedents.md to the run directory."""
        run_id, run_dir, _ = ml.init_run(self.repo, "loosen the citation gate per DEC-007")
        self.assertTrue((run_dir / "precedents.md").exists())

    def test_stage_brief_check_blocks_on_fail_open(self):
        """stage_brief_check returns 1 (BLOCKED) on a fail-open guard."""
        run_id, run_dir, _ = ml.init_run(
            self.repo, "loosen the citation gate per DEC-007"
        )
        brief = """## Baseline Before Editing

Actual output: baseline passed

## Blast Radius

- app/llm/answer-validate.js

Applicable DEC ids: DEC-007

## Guards & Fail-Directions

- citation gate: fail-open — matches DEC-007 intent
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)

        result = ml.stage_brief_check(self.repo, run_id)
        self.assertEqual(result, 1)

        # Check that architect inbox and packet were created
        self.assertTrue((run_dir / "architect-inbox.md").exists())
        self.assertTrue((run_dir / "architect-packet.md").exists())

        # Check packet contains DEC-007 content
        packet = ml.read_text(run_dir / "architect-packet.md")
        self.assertIn("keep the exec channel opt-in", packet)
        self.assertIn("loosen the citation gate", packet)

    def test_stage_architect_ratify_unlocks_brief(self):
        """stage_architect_ratify stamps the brief and appends disposition."""
        run_id, run_dir, _ = ml.init_run(
            self.repo, "loosen the citation gate per DEC-007"
        )
        brief = """## Baseline Before Editing

Actual output: baseline passed

## Blast Radius

- app/llm/answer-validate.js

Applicable DEC ids: DEC-007

## Guards & Fail-Directions

- citation gate: fail-open — matches DEC-007 intent
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)
        # First run brief-check to populate escalations
        ml.stage_brief_check(self.repo, run_id)

        # Write a simulated verdict under the gitignored run dir
        verdict_path = run_dir / "architect-verdict.md"
        ml.write_text(verdict_path, "ratified: acceptable here")

        # Call stage_architect_ratify
        result = ml.stage_architect_ratify(self.repo, run_id, str(verdict_path), ref="DEC-007")
        self.assertEqual(result, 0)

        # Check brief was stamped
        brief_text = ml.read_text(run_dir / "mentor-brief.md")
        self.assertIn("[architect-ratified: DEC-007]", brief_text)

        # Check disposition was appended to decisions.md
        decisions = ml.read_text(self.repo / ".mentor-loop" / "decisions.md")
        self.assertIn("architect-ratify —", decisions)
        self.assertIn("ratified: acceptable here", decisions)

    def test_stage_brief_check_after_ratify_passes(self):
        """stage_brief_check returns 0 (OK) after ratification."""
        run_id, run_dir, _ = ml.init_run(
            self.repo, "loosen the citation gate per DEC-007"
        )
        brief = """## Baseline Before Editing

Actual output: baseline passed

## Blast Radius

- app/llm/answer-validate.js

Applicable DEC ids: DEC-007

## Guards & Fail-Directions

- citation gate: fail-open — matches DEC-007 intent
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)
        # First escalation -> BLOCKED
        ml.stage_brief_check(self.repo, run_id)

        # Ratify
        verdict_path = run_dir / "architect-verdict.md"
        ml.write_text(verdict_path, "ratified: acceptable here")
        ml.stage_architect_ratify(self.repo, run_id, str(verdict_path), ref="DEC-007")

        # Re-run brief-check -> should pass
        result = ml.stage_brief_check(self.repo, run_id)
        self.assertEqual(result, 0)

    def test_stage_architect_packet_fail_closed_skip(self):
        """stage_architect_packet with missing architect command returns 0 (SKIP)."""
        run_id, run_dir, _ = ml.init_run(self.repo, "task")
        brief = """## Baseline Before Editing

Actual output: baseline passed

## Blast Radius

- app/x.js

## Guards & Fail-Directions

- none
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)

        config = {"architect_command": ["definitely-missing-architect-xyz", "-o", "{output}"]}
        result = ml.stage_architect_packet(self.repo, run_id, config)
        self.assertEqual(result, 0)

        # Check verdict draft was created with SKIPPED marker
        draft_path = run_dir / "architect-verdict-draft.md"
        self.assertTrue(draft_path.exists())
        draft = ml.read_text(draft_path)
        self.assertIn("SKIPPED", draft)

    def test_stage_architect_packet_fail_closed_blocked_no_brief(self):
        """stage_architect_packet with no brief returns 1 (BLOCKED)."""
        run_id, run_dir, _ = ml.init_run(self.repo, "another task")
        # Do NOT write a mentor-brief.md

        result = ml.stage_architect_packet(self.repo, run_id)
        self.assertEqual(result, 1)

        packet_path = run_dir / "architect-packet.md"
        self.assertTrue(packet_path.exists())
        packet = ml.read_text(packet_path)
        self.assertIn("BLOCKED", packet)

    def test_stage_architect_ratify_fail_closed_no_verdict_file(self):
        """stage_architect_ratify with missing verdict file returns 1 (BLOCKED)."""
        run_id, run_dir, _ = ml.init_run(self.repo, "task")
        brief = """## Baseline Before Editing

Actual output: baseline passed

## Blast Radius

- app/x.js

## Guards & Fail-Directions

- none
"""
        ml.write_text(run_dir / "mentor-brief.md", brief)

        result = ml.stage_architect_ratify(self.repo, run_id, str(self.repo / "does-not-exist.md"))
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
