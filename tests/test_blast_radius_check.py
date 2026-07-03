from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "gates" / "blast-radius-check.py"

spec = importlib.util.spec_from_file_location("blast_radius_check", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


BRIEF = """# Mentor Brief

## Blast Radius

Likely touched files:

- src/parser.py
- tests/test_parser.py

Do not touch:

- src/generated.py

Potentially affected behavior:

- parser output
"""


class BlastRadiusCheckTests(unittest.TestCase):
    def test_extracts_allowed_and_do_not_touch_files(self) -> None:
        allowed, do_not_touch = gate.extract_blast_radius(BRIEF)

        self.assertEqual(allowed, ["src/parser.py", "tests/test_parser.py"])
        self.assertEqual(do_not_touch, ["src/generated.py"])

    def test_allows_only_files_inside_blast_radius(self) -> None:
        result = gate.check_blast_radius(BRIEF, ["src/parser.py", ".\\tests\\test_parser.py"])

        self.assertTrue(result["ok"])
        self.assertEqual(result["outside_blast_radius"], [])
        self.assertEqual(result["do_not_touch_violations"], [])

    def test_blocks_files_outside_blast_radius(self) -> None:
        result = gate.check_blast_radius(BRIEF, ["src/parser.py", "README.md"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["outside_blast_radius"], ["README.md"])

    def test_blocks_do_not_touch_files(self) -> None:
        result = gate.check_blast_radius(BRIEF, ["src/generated.py"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["do_not_touch_violations"], ["src/generated.py"])

    def test_status_line_parser_handles_untracked_modified_and_renamed_files(self) -> None:
        self.assertEqual(gate._path_from_status_line("?? scratch.txt"), "scratch.txt")
        self.assertEqual(gate._path_from_status_line(" M src/parser.py"), "src/parser.py")
        self.assertEqual(gate._path_from_status_line("R  old.py -> new.py"), "new.py")

    def test_git_changed_files_reads_porcelain_status_and_deduplicates(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> object:
            calls.append(command)
            if command[:2] == ["git", "rev-parse"]:
                return SimpleNamespace(stdout="true\n", stderr="")
            if command == ["git", "status", "--porcelain"]:
                return SimpleNamespace(
                    stdout=" M src/parser.py\n?? scratch.txt\nR  old.py -> new.py\n?? scratch.txt\n",
                    stderr="",
                )
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(subprocess, "run", side_effect=fake_run):
            changed = gate.git_changed_files()

        self.assertEqual(calls, [["git", "rev-parse", "--is-inside-work-tree"], ["git", "status", "--porcelain"]])
        self.assertEqual(changed, ["src/parser.py", "scratch.txt", "new.py"])


if __name__ == "__main__":
    unittest.main()
