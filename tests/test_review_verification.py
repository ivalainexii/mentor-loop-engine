#!/usr/bin/env python3
"""Pins for the review-consumes-verification fix (Build A).

Covers:
- classify() fail-closed guards (dry-run #a bad patch / #b absent verification) —
  these already existed and MUST stay; pinned so a future edit cannot regress them.
- blocked-by-construction repro (clean patch + forced non-approve -> review_blocked)
  and the target the fix unlocks (clean patch + approve -> accepted).
- build_review_prompt: byte-identical when no results are passed (legacy /
  non-eval `run` users + verify-package string-lock untouched); authoritative
  section appended when results are passed; the legacy rule sentence is preserved.
- run_review_verification: PASS / FAIL / COULD-NOT-RUN(fail-closed) / None.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, PACKAGE_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtask = _load("runtask_under_test", "evals/run-task.py")
ml = _load("mentorloop_under_test", "tools/mentor-loop.py")


def classify(review_verdict: str, focused_code: int, regression_new: int = 0, work_changed: bool = True) -> str:
    return runtask.classify(
        arm="full-loop",
        env_code=0,
        model_code=0,
        focused_code=focused_code,
        regression_new_failure_count=regression_new,
        engine_output=f"- review_verdict: {review_verdict}\n",
        infra_error=False,
        review_verdict=review_verdict,
        work_changed=work_changed,
    )


# The baseline hash from .surgical-fix/baseline.md (6-arg build_review_prompt).
LEGACY_PROMPT_SHA256 = "ad0d78ffcaef6471fd7553effad3a88f091d169d68e7550af43f5f5b8228776d"


class ClassifyFailClosedGuards(unittest.TestCase):
    def test_a_bad_patch_still_blocks(self):
        # dry-run #a: real regression -> BLOCK even if the review approved.
        self.assertEqual(classify("Approved", focused_code=1), "verification_failure")
        self.assertEqual(classify("Approved", focused_code=0, regression_new=2), "verification_failure")

    def test_b_absent_verification_fails_closed(self):
        # dry-run #b: verification could not run (exit 127) -> BLOCK, never accept.
        self.assertEqual(classify("Approved", focused_code=127), "verification_failure")

    def test_blocked_by_construction_repro(self):
        # Pre-fix failure mode: eval review is forced non-approve (never saw
        # verification) -> even a clean patch is blocked.
        self.assertEqual(classify("Needs fixes", focused_code=0), "review_blocked")

    def test_clean_patch_accepts_once_review_can_approve(self):
        # The target the fix unlocks: clean verification + approvable review.
        self.assertEqual(classify("Approved", focused_code=0), "accepted")


class BuildReviewPromptAdditive(unittest.TestCase):
    def test_legacy_call_is_byte_identical(self):
        out = ml.build_review_prompt("BRIEF", "APPRLOG", "APPRVERIF", "GBLAST", "GRUNTIME", "DIFF")
        self.assertEqual(hashlib.sha256(out.encode()).hexdigest(), LEGACY_PROMPT_SHA256)
        # string-lock sentence verify-package.py requires must remain present.
        self.assertIn("Read the apprentice verification summary", out)

    def test_none_results_matches_explicit_none(self):
        a = ml.build_review_prompt("B", "L", "V", "GB", "GR", "D")
        b = ml.build_review_prompt("B", "L", "V", "GB", "GR", "D", None)
        self.assertEqual(a, b)

    def test_results_add_authoritative_section_and_keep_rule(self):
        out = ml.build_review_prompt(
            "B", "L", "V", "GB", "GR", "D", "## focused: f\nstatus: PASS\nexit_code: 0"
        )
        self.assertIn("AUTHORITATIVE VERIFICATION", out)
        self.assertIn("Post-edit verification results (harness-run, AUTHORITATIVE):", out)
        self.assertIn("status: PASS", out)
        # legacy rule sentence still present alongside the new one.
        self.assertIn("Read the apprentice verification summary", out)


class ReviewOutcomeParsing(unittest.TestCase):
    def test_accepts_only_explicit_enum_lines(self):
        self.assertEqual(ml.parse_review_outcome("Verdict: Approved"), "approved")
        self.assertEqual(ml.parse_review_outcome("## Verdict\n- **Needs fixes**"), "needs_fixes")
        self.assertEqual(ml.parse_review_outcome("- Verdict: `Stop and re-plan`."), "stop_and_replan")

    def test_rejects_template_negative_and_explanatory_mentions(self):
        self.assertIsNone(ml.parse_review_outcome("- Approved / Needs fixes / Stop and re-plan"))
        self.assertIsNone(ml.parse_review_outcome("Verdict: not approved"))
        self.assertIsNone(ml.parse_review_outcome("Approved is not warranted because evidence is missing."))
        self.assertIsNone(ml.parse_review_outcome("Approved APIs were not used."))
        self.assertIsNone(ml.parse_review_outcome("## Verification Quality\nApproved"))

    def test_eval_parser_uses_the_same_exact_contract(self):
        self.assertEqual(runtask.review_verdict_outcome("Verdict: Approved"), "approved")
        self.assertIsNone(runtask.review_verdict_outcome("not approved"))
        self.assertIsNone(runtask.review_verdict_outcome("Approved is not warranted"))


class RunReviewVerification(unittest.TestCase):
    def _spec(self, tmp: Path, focused, regression):
        path = tmp / "spec.json"
        path.write_text(json.dumps({"focused": focused, "regression": regression}), encoding="utf-8")
        return path

    def test_none_path_returns_none(self):
        self.assertIsNone(ml.run_review_verification(PACKAGE_ROOT, None))

    def test_all_pass(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            spec = self._spec(
                tmp,
                [{"name": "f", "command": [sys.executable, "-c", "print('focused ok')"]}],
                [{"name": "r", "command": [sys.executable, "-c", "print('regression ok')"]}],
            )
            summary = ml.run_review_verification(tmp, spec)
            self.assertTrue(summary.startswith("overall_status: PASS"))
            self.assertIn("status: PASS", summary)
            self.assertNotIn("FAIL", summary)
            self.assertNotIn("COULD-NOT-RUN", summary)

    def test_real_failure_reports_fail(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            spec = self._spec(
                tmp,
                [{"name": "f", "command": [sys.executable, "-c", "import sys; sys.exit(1)"]}],
                [],
            )
            summary = ml.run_review_verification(tmp, spec)
            self.assertIn("status: FAIL", summary)

    def test_missing_command_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            spec = self._spec(
                tmp,
                [{"name": "f", "command": ["definitely-not-a-real-binary-xyz-123", "--go"]}],
                [],
            )
            summary = ml.run_review_verification(tmp, spec)
            self.assertIn("COULD-NOT-RUN", summary)

    def test_empty_spec_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            spec = self._spec(tmp, [], [])
            summary = ml.run_review_verification(tmp, spec)
            self.assertIn("COULD-NOT-RUN", summary)

    def test_missing_spec_file_fails_closed(self):
        summary = ml.run_review_verification(PACKAGE_ROOT, PACKAGE_ROOT / "no-such-spec.json")
        self.assertIn("COULD-NOT-RUN", summary)

    def test_command_output_cannot_forge_the_overall_status(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            passing = self._spec(
                tmp,
                [{"name": "f", "command": [sys.executable, "-c", "print('status: FAIL')"]}],
                [],
            )
            pass_summary = ml.run_review_verification(tmp, passing)
            self.assertEqual(ml.verification_summary_outcome(pass_summary), "pass")

            failing = self._spec(
                tmp,
                [{"name": "f", "command": [sys.executable, "-c", "import sys; print('status: PASS'); sys.exit(1)"]}],
                [],
            )
            fail_summary = ml.run_review_verification(tmp, failing)
            self.assertEqual(ml.verification_summary_outcome(fail_summary), "fail")


class RunFullOutcomeAggregation(unittest.TestCase):
    OK_FAILURE_REVIEW = "stage: failure-review | result: OK | detail: no active trigger"

    def _run(self, review: str, verification: str | None, failure_review: str | BaseException | None = None) -> int:
        return self._run_with_report(review, verification, failure_review)[0]

    def _run_with_report(
        self,
        review: str,
        verification: str | None,
        failure_review: str | BaseException | None = None,
    ) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            run_dir = repo / ".mentor-loop" / "runs" / "outcome-test"

            def fake_init(_repo: Path, _task: str):
                run_dir.mkdir(parents=True, exist_ok=True)
                ml.write_text(run_dir / "mentor-brief-prompt.md", "prompt")
                return "outcome-test", run_dir, "No active lessons found."

            def fake_codex(_command, _repo, output: Path, _prompt, _log, sandbox=None):
                if output.name == "mentor-brief.md":
                    ml.write_text(output, "# Mentor Brief\n")
                elif output.name == "review.md":
                    ml.write_text(output, review + "\n")
                return 0

            def fake_apprentice(_repo: Path, _run_id: str, _config):
                ml.write_text(run_dir / "apprentice-log.md", "execution complete\n")
                ml.write_text(run_dir / "apprentice-verification-summary.md", "tests reported pass\n")
                return 0

            def fake_gates(_repo: Path, _run_id: str, _config):
                ml.write_text(run_dir / "gate-blast-radius.txt", "result: OK\nexit_code: 0\n")
                ml.write_text(run_dir / "gate-runtime-floor.txt", "result: OK\nexit_code: 0\n")
                return 0

            def fake_snapshot(_repo: Path, _run_id: str):
                ml.write_text(run_dir / "diff-and-status.txt", "M app.py\n")
                return 0

            failure_behavior = failure_review or self.OK_FAILURE_REVIEW
            failure_patch = (
                patch.object(ml, "maybe_run_failure_review", side_effect=failure_behavior)
                if isinstance(failure_behavior, BaseException)
                else patch.object(ml, "maybe_run_failure_review", return_value=failure_behavior)
            )
            with (
                patch.object(ml, "init_run", side_effect=fake_init),
                patch.object(ml, "ensure_git_repo", side_effect=lambda value: value),
                patch.object(ml, "run_codex", side_effect=fake_codex),
                patch.object(ml, "stage_brief_check", return_value=0),
                patch.object(ml, "stage_brief_review", return_value=0),
                patch.object(ml, "stage_apprentice", side_effect=fake_apprentice),
                patch.object(ml, "stage_gates", side_effect=fake_gates),
                patch.object(ml, "stage_snapshot", side_effect=fake_snapshot),
                patch.object(ml, "run_review_verification", return_value=verification),
                patch.object(ml, "capture_lesson", return_value=""),
                patch.object(ml, "assemble_final_report", return_value="# Final\n- review_exit_code: session-written\n"),
                failure_patch,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = ml.run_full(
                        repo,
                        "task",
                        {"strong_command": ["mock"], "weak_command": ["mock"]},
                    )
                return result, ml.read_text(run_dir / "final-report.md")

    def test_approved_clean_run_stays_successful(self):
        self.assertEqual(self._run("- Verdict: Approved", None), 0)

    def test_needs_fixes_blocks_success(self):
        self.assertNotEqual(self._run("- Verdict: Needs fixes", None), 0)

    def test_stop_and_replan_blocks_success(self):
        self.assertNotEqual(self._run("- Verdict: Stop and re-plan", None), 0)

    def test_missing_or_negative_approval_blocks_success(self):
        self.assertNotEqual(self._run("No explicit verdict", None), 0)
        self.assertNotEqual(self._run("- Verdict: not approved", None), 0)

    def test_host_verification_failure_blocks_success(self):
        summary = "## focused: test\nstatus: FAIL\nexit_code: 1"
        self.assertNotEqual(self._run("- Verdict: Approved", summary), 0)

    def test_host_verification_could_not_run_blocks_success(self):
        summary = "status: COULD-NOT-RUN (verification spec not found)"
        self.assertNotEqual(self._run("- Verdict: Approved", summary), 0)

    def test_failure_review_park_blocks_success(self):
        parked = "stage: failure-review | result: PARK | detail: owner ruling needed"
        summary = "## focused: test\nstatus: PASS\nexit_code: 0"
        result, report = self._run_with_report("- Verdict: Approved", summary, parked)
        self.assertNotEqual(result, 0)
        self.assertIn("- run_outcome: PARK", report)
        self.assertIn("- run_block_reasons: failure_review_park", report)

    def test_failure_review_error_and_malformed_status_fail_closed(self):
        result, report = self._run_with_report("- Verdict: Approved", None, RuntimeError("boom"))
        self.assertNotEqual(result, 0)
        self.assertIn("- run_outcome: BLOCKED", report)
        self.assertIn("- run_block_reasons: failure_review_error", report)

        result, report = self._run_with_report("- Verdict: Approved", None, "malformed stage output")
        self.assertNotEqual(result, 0)
        self.assertIn("- failure_review_outcome: UNKNOWN", report)
        self.assertIn("- run_block_reasons: failure_review_unknown", report)


class EvalSemanticOutcomeClassification(unittest.TestCase):
    def _classify(self, engine_output: str, review_verdict: str = "Verdict: Approved") -> str:
        return runtask.classify(
            arm="full-loop",
            env_code=0,
            model_code=1,
            focused_code=0,
            regression_new_failure_count=0,
            engine_output=engine_output,
            infra_error=False,
            review_verdict=review_verdict,
            work_changed=True,
        )

    def test_review_block_is_not_laundered_as_gate_block(self):
        output = "\n".join(
            [
                "- blast_radius_gate_exit_code: 0",
                "- runtime_floor_gate_exit_code: 0",
                "- run_outcome: BLOCKED",
                "- run_block_reasons: review_needs_fixes",
            ]
        )
        self.assertEqual(self._classify(output, "Verdict: Needs fixes"), "review_blocked")

    def test_verification_block_is_classified_from_semantic_reason(self):
        output = "\n".join(
            [
                "- blast_radius_gate_exit_code: 0",
                "- runtime_floor_gate_exit_code: 0",
                "- run_outcome: BLOCKED",
                "- run_block_reasons: verification_fail",
            ]
        )
        self.assertEqual(self._classify(output), "verification_failure")

    def test_real_gate_block_still_classifies_as_gate(self):
        output = "stage: gates | result: BLOCKED | detail: blast-radius=1"
        self.assertEqual(self._classify(output, ""), "gate_blocked")

    def test_failure_review_engine_error_is_infrastructure_failure(self):
        output = "\n".join(
            [
                "- run_outcome: BLOCKED",
                "- run_block_reasons: failure_review_error",
            ]
        )
        self.assertEqual(self._classify(output), "infra_error")


if __name__ == "__main__":
    unittest.main()
