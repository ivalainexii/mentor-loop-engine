#!/usr/bin/env python3
"""Tests for the BUILD-D failure-attribution loop in tools/mentor-loop.py.

Authored by the mentor (not the apprentice: the apprentice's first version was found to have
git-reverted the engine, fabricated results, embedded a vacuous test, and codified a laundering bug
as "correct"). Every cross-vendor (Codex) finding below is pinned as an explicit REGRESSION test:
- P1-a: a corrupt state file must NOT silently reset the failure count -> park + quarantine.
- P1-b: brief_blocker / direction_unclear must escalate even when the run's EXIT code is passing;
        and a passing run must NOT re-open an accumulated-failure trigger.
- P2  : duplicate distinct verdict -> ambiguous -> None; packet carries the current brief;
        already-audited re-fail attaches the prior verdict.
- P3  : lint does not flag domain:port, does flag tab-separated diff headers.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, PACKAGE_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ml = _load("ml_buildd_under_test", "tools/mentor-loop.py")

STATE_REL = ".mentor-loop/state/brief-review-loop.json"


class ComputeTargetIdTests(unittest.TestCase):
    def test_returns_12_hex(self):
        tid = ml.compute_target_id("Fix the citation gate")
        self.assertEqual(len(tid), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in tid))

    def test_stable_under_whitespace_and_case(self):
        self.assertEqual(
            ml.compute_target_id("Fix the citation gate"),
            ml.compute_target_id("  fix   the CITATION gate  "),
        )

    def test_different_intent_different_id(self):
        self.assertNotEqual(ml.compute_target_id("fix the gate"), ml.compute_target_id("add a feature"))

    def test_depends_only_on_task(self):
        """Contract: identity is a function of the task alone (there is no brief parameter), so a
        brief revision cannot change it. Two calls with the same task are always equal."""
        self.assertEqual(ml.compute_target_id("same task"), ml.compute_target_id("same task"))


class ClassifyReviewReasonTests(unittest.TestCase):
    def test_stop_and_replan_direction_unclear(self):
        self.assertEqual(ml.classify_review_reason("- Verdict: Stop and re-plan"), "direction_unclear")

    def test_needs_fixes(self):
        self.assertEqual(ml.classify_review_reason("Needs fixes in module x"), "needs_fixes")

    def test_approved(self):
        self.assertEqual(ml.classify_review_reason("- Approved"), "approved")

    def test_other(self):
        self.assertEqual(ml.classify_review_reason("inconclusive text"), "other")

    def test_case_insensitive(self):
        self.assertEqual(ml.classify_review_reason("STOP AND RE-PLAN"), "direction_unclear")


class DetectBriefBlockerTests(unittest.TestCase):
    def test_structured_line_detected(self):
        found, reason = ml.detect_brief_blocker("working...\nbrief_blocker: goal too vague\ndone")
        self.assertTrue(found)
        self.assertEqual(reason, "goal too vague")

    def test_list_marker_tolerated(self):
        found, reason = ml.detect_brief_blocker("- brief_blocker: missing scope")
        self.assertTrue(found)
        self.assertEqual(reason, "missing scope")

    def test_substring_midsentence_not_triggered(self):  # CV P2 regression: no prose-sniff false positive
        found, reason = ml.detect_brief_blocker("No brief_blocker: the brief was clear and complete.")
        self.assertFalse(found)
        self.assertEqual(reason, "")

    def test_absent(self):
        self.assertEqual(ml.detect_brief_blocker("all good, tests pass"), (False, ""))


class LintArchitectOutputTests(unittest.TestCase):
    def test_fenced_code(self):
        self.assertEqual(ml.lint_architect_output("verdict: revised_brief\n```py\nx=1\n```"), ["fenced_code_block"])

    def test_space_diff_marker(self):
        self.assertIn("unified_diff_marker", ml.lint_architect_output("--- a/f.py\n+++ b/f.py"))

    def test_tab_diff_marker(self):  # CV P3 regression: tab-separated diff header must be caught
        self.assertIn("unified_diff_marker", ml.lint_architect_output("---\ta.py\n+++\tb.py"))

    def test_real_file_line_flagged(self):
        self.assertIn("file_line_edit", ml.lint_architect_output("edit tools/mentor-loop.py:42 please"))

    def test_bare_filename_line_flagged(self):
        self.assertIn("file_line_edit", ml.lint_architect_output("change x.py:10"))

    def test_clean_prose_empty(self):
        self.assertEqual(ml.lint_architect_output("verdict: narrowed_task\nJust split the task in words."), [])

    def test_bare_hr_not_flagged(self):
        self.assertEqual(ml.lint_architect_output("verdict: narrowed_task\n---\nwords only, no code"), [])

    def test_domain_port_not_flagged(self):  # CV P3 regression: domain:port is clean prose, not a file:line
        self.assertEqual(ml.lint_architect_output("Consider api.example.com:443 as the endpoint."), [])

    def test_path_file_line_flagged(self):  # CV round-2 P3 regression: src/app.css:12 must be caught
        self.assertIn("file_line_edit", ml.lint_architect_output("Change src/app.css:12 spacing."))

    def test_bare_markup_ext_flagged(self):  # broadened whitelist covers css/html/sql/xml
        self.assertIn("file_line_edit", ml.lint_architect_output("edit app.css:5"))
        self.assertIn("file_line_edit", ml.lint_architect_output("edit index.html:20"))

    def test_url_port_not_flagged(self):  # CV round-3 P3 regression: scheme://host:port is not a file:line
        self.assertEqual(ml.lint_architect_output("Use https://api.example.com:443 as the endpoint."), [])


class ParseArchitectVerdictTests(unittest.TestCase):
    def test_legal_verdict(self):
        self.assertEqual(
            ml.parse_architect_verdict("text\nverdict: brief_sound_capability_gap\nrationale"),
            "brief_sound_capability_gap",
        )

    def test_list_marker_and_backticks(self):
        self.assertEqual(ml.parse_architect_verdict("- verdict: `route_change`"), "route_change")

    def test_illegal_verdict_none(self):
        self.assertIsNone(ml.parse_architect_verdict("verdict: write_the_code_for_me"))

    def test_absent_none(self):
        self.assertIsNone(ml.parse_architect_verdict("no verdict line at all"))

    def test_duplicate_same_ok(self):
        self.assertEqual(ml.parse_architect_verdict("verdict: park_report\nverdict: park_report"), "park_report")

    def test_duplicate_distinct_ambiguous_none(self):  # CV P2 regression: ambiguous multi-verdict -> park
        self.assertIsNone(ml.parse_architect_verdict("verdict: keep_brief_retry\nverdict: park_report"))


class LoopStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_empty(self):
        self.assertEqual(ml.load_loop_state(self.repo), {})

    def test_missing_not_corrupt(self):
        self.assertFalse(ml.loop_state_corrupt(self.repo))

    def test_round_trip(self):
        ml.save_loop_state(self.repo, {"a": {"x": 1}})
        self.assertEqual(ml.load_loop_state(self.repo), {"a": {"x": 1}})

    def test_corrupt_detected_and_not_crash(self):
        path = self.repo / STATE_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{ this is : not json", encoding="utf-8")
        self.assertTrue(ml.loop_state_corrupt(self.repo))
        self.assertEqual(ml.load_loop_state(self.repo), {})  # returns {} without raising

    def test_quarantine_preserves_evidence(self):
        path = self.repo / STATE_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("CORRUPT_BYTES", encoding="utf-8")
        backup = ml._quarantine_corrupt_state(self.repo)
        self.assertTrue(backup.exists())
        self.assertIn("CORRUPT_BYTES", backup.read_text(encoding="utf-8"))
        self.assertFalse(path.exists())  # original moved aside, not left to be overwritten


class UpdateLoopStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_increments_attempts_always(self):
        ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": False})
        e = ml.update_loop_state(self.repo, "t", "task", {"run_id": "r2", "failed": False})
        self.assertEqual(e["attempts"], 2)

    def test_failures_only_on_failed(self):
        ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": False})
        e = ml.update_loop_state(self.repo, "t", "task", {"run_id": "r2", "failed": True})
        self.assertEqual(e["failures"], 1)

    def test_verification_failures(self):
        e = ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": True, "verification_failed": True})
        self.assertEqual(e["verification_failures"], 1)

    def test_brief_revision_count(self):
        e = ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": True, "brief_revised": True})
        self.assertEqual(e["brief_revision_count"], 1)

    def test_persists_across_fresh_load(self):
        ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": True})
        self.assertEqual(ml.load_loop_state(self.repo)["t"]["failures"], 1)

    def test_stores_last_and_history(self):
        e = ml.update_loop_state(self.repo, "t", "task", {"run_id": "r1", "failed": True, "review_reason": "needs_fixes"})
        self.assertEqual(e["last"]["review_reason"], "needs_fixes")
        self.assertEqual(len(e["history"]), 1)


class FailureTriggersTests(unittest.TestCase):
    def test_one_fail_no_trigger(self):
        self.assertEqual(ml.failure_triggers({"failures": 1, "last": {}}), [])

    def test_two_fails_trigger(self):
        self.assertIn("failures>=2", ml.failure_triggers({"failures": 2, "last": {}}))

    def test_verification_two_trigger(self):
        self.assertIn("verification_failures>=2", ml.failure_triggers({"verification_failures": 2, "last": {}}))

    def test_brief_blocker_trigger(self):
        self.assertIn("brief_blocker", ml.failure_triggers({"last": {"brief_blocker": True}}))

    def test_direction_unclear_trigger(self):
        self.assertIn("review:direction_unclear", ml.failure_triggers({"last": {"review_reason": "direction_unclear"}}))

    def test_revised_still_failing_trigger(self):
        fired = ml.failure_triggers({"brief_revision_count": 1, "last": {"failed": True}})
        self.assertIn("revised_brief_still_failing", fired)


class BuildFailurePacketTests(unittest.TestCase):
    def _packet(self, brief="THE_BRIEF"):
        entry = {"attempts": 2, "failures": 2, "verification_failures": 0,
                 "history": [{"run_id": "r1", "failed": True}]}
        return ml.build_failure_packet("abc123", entry, "the task", brief, "the blast", "the precedents")

    def test_contains_target_id(self):
        self.assertIn("abc123", self._packet())

    def test_contains_five_questions(self):
        self.assertIn("five DIRECTION questions", self._packet())

    def test_lists_verdict_enum(self):
        pkt = self._packet()
        for v in ("revised_brief", "narrowed_task", "route_change", "keep_brief_retry",
                  "brief_sound_capability_gap", "park_report"):
            self.assertIn(v, pkt)

    def test_states_no_code_rule(self):
        self.assertIn("do NOT write code", self._packet())

    def test_includes_current_brief(self):  # CV P2 regression: architect must see what it audits
        self.assertIn("UNIQUE_BRIEF_XYZ", self._packet(brief="UNIQUE_BRIEF_XYZ"))
        self.assertIn("current mentor brief", self._packet().lower())

    def test_includes_blast_and_history(self):
        pkt = self._packet()
        self.assertIn("the blast", pkt)
        self.assertIn("r1", pkt)


class MaybeRunFailureReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".mentor-loop").mkdir(parents=True, exist_ok=True)
        self.run_dir = self.repo / ".mentor-loop" / "runs" / "rd"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.tid = ml.compute_target_id("the task")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, run_id, signals, config=None):
        return ml.maybe_run_failure_review(self.repo, self.run_dir, run_id, "the task", self.tid, signals, config)

    def test_passing_run_no_escalation(self):
        r = self._run("r1", {"run_id": "r1", "failed": False})
        self.assertIn("no active trigger", r)

    def test_first_failing_no_trigger(self):
        r = self._run("r1", {"run_id": "r1", "failed": True})
        self.assertIn("no active trigger", r)

    def test_second_failing_parks_no_architect(self):
        self._run("r1", {"run_id": "r1", "failed": True})
        r = self._run("r2", {"run_id": "r2", "failed": True}, config={})
        self.assertIn("PARK", r)

    def test_second_failing_writes_park_and_sets_audited(self):
        self._run("r1", {"run_id": "r1", "failed": True})
        self._run("r2", {"run_id": "r2", "failed": True}, config={})
        self.assertTrue((self.run_dir / "failure-review-park.md").exists())
        self.assertTrue(ml.load_loop_state(self.repo)[self.tid]["audited"])

    def test_third_failing_already_audited_parks(self):
        self._run("r1", {"run_id": "r1", "failed": True})
        self._run("r2", {"run_id": "r2", "failed": True}, config={})
        r = self._run("r3", {"run_id": "r3", "failed": True}, config={})
        self.assertIn("PARK", r)
        self.assertIn("already audited", r)

    def test_metric_written_separately(self):
        self._run("r1", {"run_id": "r1", "failed": True})
        self._run("r2", {"run_id": "r2", "failed": True}, config={})
        metric = self.repo / ".mentor-loop" / "state" / "failure-review-metric.jsonl"
        self.assertTrue(metric.exists())
        rec = json.loads(metric.read_text().strip().split("\n")[0])
        self.assertEqual(rec["target_id"], self.tid)
        self.assertEqual(rec["trigger_source"], "failure_loop")

    def test_accumulation(self):
        self._run("r1", {"run_id": "r1", "failed": False})
        self._run("r2", {"run_id": "r2", "failed": True})
        self._run("r3", {"run_id": "r3", "failed": True}, config={})
        e = ml.load_loop_state(self.repo)[self.tid]
        self.assertEqual(e["attempts"], 3)
        self.assertEqual(e["failures"], 2)

    # --- Cross-vendor CV regressions ---
    def test_brief_blocker_escalates_on_passing_run(self):  # CV P1-b
        r = self._run("r1", {"run_id": "r1", "failed": False, "brief_blocker": True}, config={})
        self.assertIn("PARK", r)  # escalates despite passing exit; no architect => park

    def test_direction_unclear_escalates_on_passing_run(self):  # CV P1-b
        r = self._run("r1", {"run_id": "r1", "failed": False, "review_reason": "direction_unclear"}, config={})
        self.assertIn("PARK", r)

    def test_passing_run_after_audited_does_not_park(self):  # CV P1-b safety (no false escalation)
        self._run("r1", {"run_id": "r1", "failed": True})
        self._run("r2", {"run_id": "r2", "failed": True}, config={})  # audited
        r = self._run("r3", {"run_id": "r3", "failed": False}, config={})  # passes, no new signal
        self.assertNotIn("PARK", r)
        self.assertIn("no active trigger", r)

    def test_corrupt_state_parks_and_quarantines(self):  # CV P1-a (anti-laundering)
        ml.update_loop_state(self.repo, self.tid, "the task", {"run_id": "r1", "failed": True})
        state_path = self.repo / STATE_REL
        state_path.write_text("{ corrupt not json", encoding="utf-8")
        r = self._run("r2", {"run_id": "r2", "failed": True}, config={})
        self.assertIn("PARK", r)
        self.assertIn("corrupt", r.lower())
        self.assertTrue(state_path.with_name(state_path.name + ".corrupt").exists())

    def test_already_audited_park_attaches_prior_verdict(self):  # CV P2
        ml.save_loop_state(self.repo, {self.tid: {
            "target_id": self.tid, "task": "the task", "attempts": 2, "failures": 2,
            "verification_failures": 0, "brief_revision_count": 0, "audited": True,
            "verdict_excerpt": "verdict: route_change\nPRIOR_VERDICT_MARKER", "history": [], "last": {},
        }})
        r = self._run("r3", {"run_id": "r3", "failed": True}, config={})
        self.assertIn("PARK", r)
        park = ml.read_text(self.run_dir / "failure-review-park.md")
        self.assertIn("PRIOR_VERDICT_MARKER", park)

    def test_rejected_verdict_persists_excerpt(self):  # CV round-2 P2: persist on the REJECT path, not just legal verdict
        import sys
        mock = [
            sys.executable,
            "-c",
            "import sys,pathlib; pathlib.Path(sys.argv[1]).write_text('verdict: revised_brief\\n```py\\nx=1\\n```\\n', encoding='utf-8')",
            "{output}",
        ]
        cfg = {"architect_command": mock}
        self._run("r1", {"run_id": "r1", "failed": True})
        r2 = self._run("r2", {"run_id": "r2", "failed": True}, config=cfg)  # audit -> mock emits code -> lint rejects -> park
        self.assertIn("PARK", r2)
        excerpt = ml.load_loop_state(self.repo)[self.tid].get("verdict_excerpt", "")
        self.assertIn("x=1", excerpt)  # rejected verdict text persisted despite rejection
        r3 = self._run("r3", {"run_id": "r3", "failed": True}, config=cfg)  # already audited -> attaches prior text
        self.assertIn("PARK", r3)
        self.assertIn("x=1", ml.read_text(self.run_dir / "failure-review-park.md"))


if __name__ == "__main__":
    unittest.main()
