from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "gates" / "runtime-floor-check.py"

spec = importlib.util.spec_from_file_location("runtime_floor_check", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class RuntimeFloorCheckTests(unittest.TestCase):
    def test_parse_python_requires_from_setup_py_text(self) -> None:
        text = "setup(name='demo', python_requires='>=3.6')"

        self.assertEqual(gate.parse_python_requires(text), (3, 6))

    def test_parse_python_requires_from_pyproject_text(self) -> None:
        text = '[project]\nrequires-python = ">=3.8"\n'

        self.assertEqual(gate.parse_python_requires(text), (3, 8))

    def test_blocks_python_39_api_when_floor_is_36(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "src" / "parser.py"
            path.parent.mkdir()
            path.write_text("value = name.removeprefix('x')\n", encoding="utf-8")

            result = gate.check_runtime_floor(root, (3, 6), ["src/parser.py"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["blocked"][0]["api"], "removeprefix")

    def test_allows_python_39_api_when_floor_is_39(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "src" / "parser.py"
            path.parent.mkdir()
            path.write_text("value = name.removeprefix('x')\n", encoding="utf-8")

            result = gate.check_runtime_floor(root, (3, 9), ["src/parser.py"])

        self.assertTrue(result["ok"])
        self.assertEqual(result["blocked"], [])

    def test_ignores_non_python_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = gate.check_runtime_floor(root, (3, 6), ["README.md"])

        self.assertTrue(result["ok"])
        self.assertEqual(result["python_files"], [])

    def test_git_changed_files_reads_porcelain_status(self) -> None:
        def fake_run(command: list[str], **_: object) -> object:
            if command[:2] == ["git", "rev-parse"]:
                return SimpleNamespace(stdout="true\n", stderr="")
            if command == ["git", "status", "--porcelain"]:
                return SimpleNamespace(stdout=" M src/parser.py\n?? scratch.py\n", stderr="")
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(subprocess, "run", side_effect=fake_run):
            changed = gate.git_changed_files()

        self.assertEqual(changed, ["src/parser.py", "scratch.py"])


if __name__ == "__main__":
    unittest.main()
