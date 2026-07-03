#!/usr/bin/env python3
"""Pins for check_brief_honesty(brief) in tools/mentor-loop.py.

Tests the deterministic brief-honesty gate (ml-v2 BUILD-B) that enforces:
- declared guards must state fail-direction + a one-line why
- gate/anchor-touching briefs must pin non-happy-path round-trips
- anchored briefs must state scope + an excluded counter-example
- fail-open/unsure guards (unless architect-ratified) escalate before apprentice runs
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, PACKAGE_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ml = _load("mentorloop_under_test", "tools/mentor-loop.py")


class HappyPathTests(unittest.TestCase):
    """Tests that should result in status == 'ok'."""

    def test_no_markers_passes(self):
        """A brief with no guard/gate/anchor markers passes."""
        brief = """## Blast Radius

- app.py
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["escalations"], [])

    def test_guards_none_passes(self):
        """A brief with explicit 'none' guard marker passes."""
        brief = """## Guards & Fail-Directions

- none
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["escalations"], [])

    def test_guard_failclosed_with_why_passes(self):
        """A guard with fail-closed and a why passes."""
        brief = """## Guards & Fail-Directions

- classify: fail-closed — bad or absent verification must block
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["escalations"], [])
        self.assertEqual(result["findings"], [])

    def test_touches_yes_with_nonhappy_passes(self):
        """A gate-touching brief with [non-happy-path] marker passes."""
        brief = """## Change Surface

- Touches fidelity gate or anchored contract: yes

## Verification

- [non-happy-path] guard declared without direction must block
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["escalations"], [])

    def test_anchored_yes_complete_passes(self):
        """An anchored brief with scope and excluded counter-example passes."""
        brief = """## Anchoring

- Anchored change: yes
- Scope: nodes n1..n5
- Excluded counter-example: a holistic root claim
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["escalations"], [])


class NonHappyPathTests(unittest.TestCase):
    """Tests that should result in status == 'blocked' or 'escalate'."""

    def test_guard_no_direction_blocks(self):
        """A guard without fail-open/fail-closed/unsure is blocked."""
        brief = """## Guards & Fail-Directions

- widget guard: blocks bad stuff
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("undeclared" in f for f in result["findings"]))

    def test_guard_failclosed_no_why_blocks(self):
        """A guard with fail-closed but no why is blocked."""
        brief = """## Guards & Fail-Directions

- classify: fail-closed
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("why" in f for f in result["findings"]))

    def test_guard_ambiguous_blocks(self):
        """A guard with both fail-open and fail-closed is blocked."""
        brief = """## Guards & Fail-Directions

- x guard: fail-open and fail-closed — mixed
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("ambiguous" in f for f in result["findings"]))

    def test_guard_failopen_escalates(self):
        """A fail-open guard (not ratified) escalates."""
        brief = """## Guards & Fail-Directions

- citation gate: fail-open — no weaker than 004
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "escalate")
        self.assertEqual(len(result["escalations"]), 1)
        self.assertEqual(result["escalations"][0]["direction"], "fail-open")
        self.assertIn("citation gate", result["escalations"][0]["guard"])

    def test_guard_unsure_escalates(self):
        """An unsure guard (not ratified) escalates."""
        brief = """## Guards & Fail-Directions

- direction gate: unsure which way this should fail
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "escalate")
        self.assertEqual(result["escalations"][0]["direction"], "unsure")

    def test_guard_failopen_ratified_passes(self):
        """A fail-open guard that is architect-ratified passes."""
        brief = """## Guards & Fail-Directions

- citation gate: fail-open [architect-ratified: DEC-999] — ruled acceptable
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["escalations"], [])

    def test_touches_yes_without_nonhappy_blocks(self):
        """A gate-touching brief without [non-happy-path] is blocked."""
        brief = """## Change Surface

- Touches fidelity gate or anchored contract: yes

## Verification

- normal test case passing
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("non-happy-path" in f for f in result["findings"]))

    def test_anchored_yes_missing_fields_blocks(self):
        """An anchored brief with missing scope/counter-example is blocked."""
        brief = """## Anchoring

- Anchored change: yes
- Scope:
- Excluded counter-example:
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")
        self.assertGreaterEqual(len(result["findings"]), 2)

    def test_blocked_outranks_escalate(self):
        """When both blocked and escalate conditions exist, blocked wins."""
        brief = """## Guards & Fail-Directions

- citation gate: fail-open — why
- other guard: does a thing
"""
        result = ml.check_brief_honesty(brief)
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
