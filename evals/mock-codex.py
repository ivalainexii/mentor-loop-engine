#!/usr/bin/env python3
"""Tiny codex exec stand-in for eval runner dry verification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--mode", default="auto")
    args, _unknown = parser.parse_known_args()

    prompt = sys.stdin.read()
    output_name = args.output.name
    if "mentor-brief" in output_name:
        text = """## Baseline Before Editing

Actual output: mock baseline passed

## Blast Radius

Likely touched files:
- app.py

Do not touch:
- setup.py

## Verification

Focused:
- python -c "print('focused ok')"

Regression:
- python -c "print('regression ok')"
"""
    elif "review" in output_name:
        text = "Verdict: Approved\n\n## Lesson Candidate\n- Trigger: None\n- Mistake: None\n- Rule for next time: None\n- Suggested destination: None\n"
    else:
        text = "Mock apprentice completed.\nVerification: passed\nexit code: 0\n"
        # A real apprentice edits the worktree; the runner's no-op check
        # requires a dirty tree, so touch the allowed file.
        app = Path.cwd() / "app.py"
        if app.exists():
            with app.open("a", encoding="utf-8") as handle:
                handle.write("# mock apprentice touch\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"mock-codex wrote {args.output}")
    print(f"prompt_chars: {len(prompt)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
