#!/usr/bin/env python3
"""Preflight runtime/dependency checks for one eval task."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stage_summary(result: str, detail: str) -> str:
    return f"stage: env-preflight | result: {result} | detail: {detail}"


def run_command(command: list[str], cwd: Path) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return completed.returncode, completed.stdout
    except FileNotFoundError as error:
        return 127, str(error)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Run eval task environment preflight checks.")
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()

    task = read_json(args.task)
    repo = args.repo.resolve()
    env = task.get("env", {})
    missing_files = [path for path in env.get("required_files", []) if not (repo / path).exists()]
    if missing_files:
        print(stage_summary("BLOCKED", "missing files: " + ", ".join(missing_files)))
        return 1

    failures: list[str] = []
    for check in env.get("preflight_commands", []):
        name = check.get("name", "unnamed")
        command = check.get("command", [])
        if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
            failures.append(f"{name}: command must be a string array")
            continue
        code, output = run_command(command, repo)
        print(f"check: {name} | exit_code: {code}")
        if output.strip():
            print(output.strip())
        if code != 0:
            failures.append(f"{name} exit_code={code}")

    if failures:
        print(stage_summary("BLOCKED", "; ".join(failures)))
        return 1
    print(stage_summary("OK", "all checks passed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
