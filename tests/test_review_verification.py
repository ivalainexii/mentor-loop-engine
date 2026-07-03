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

import hashlib
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
