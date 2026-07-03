#!/usr/bin/env python3
"""Verify the Mentor Loop lean v0 package before publication."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def ok(message: str) -> None:
    print(f"OK  {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)


def load_manifest() -> tuple[dict, list[str]]:
    manifest_path = PACKAGE_ROOT / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"manifest.json could not be read: {exc}") from exc

    files: list[str] = []
    for value in manifest.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    files.append(item)
    return manifest, files


def check_manifest_files(files: list[str]) -> None:
    missing = [path for path in files if not (PACKAGE_ROOT / path).is_file()]
    if missing:
        raise RuntimeError("manifest references missing files: " + ", ".join(missing))
    ok(f"manifest files present ({len(files)} files)")


def check_csv_files() -> None:
    csv_paths = sorted((PACKAGE_ROOT / "experiments").glob("*.csv"))
    if not csv_paths:
        raise RuntimeError("no experiment CSV files found")

    for path in csv_paths:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        if not rows:
            raise RuntimeError(f"{path.relative_to(PACKAGE_ROOT)} is empty")
        if not rows[0]:
            raise RuntimeError(f"{path.relative_to(PACKAGE_ROOT)} has no header")
        ok(
            f"{path.relative_to(PACKAGE_ROOT)} parses "
            f"({len(rows[0])} columns, {max(len(rows) - 1, 0)} rows)"
        )


def run_command(args: list[str], label: str) -> None:
    result = subprocess.run(
        args,
        cwd=PACKAGE_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        fail(result.stdout.strip())
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")
    ok(label)


def check_gates() -> None:
    run_command(
        [sys.executable, "gates/blast-radius-check.py", "--help"],
        "blast-radius gate help runs",
    )
    run_command(
        [sys.executable, "gates/runtime-floor-check.py", "--help"],
        "runtime-floor gate help runs",
    )


def check_tests() -> None:
    run_command(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        "unit tests pass",
    )


def require_text(path: Path, needles: list[str], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        relative = path.relative_to(PACKAGE_ROOT)
        raise RuntimeError(
            f"{label} missing required text in {relative}: " + ", ".join(missing)
        )


def parse_simple_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise RuntimeError(f"{path.relative_to(PACKAGE_ROOT)} missing YAML frontmatter")
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    raise RuntimeError(f"{path.relative_to(PACKAGE_ROOT)} frontmatter is not closed")


def require_frontmatter(path: Path, expected: dict[str, str], label: str) -> None:
    data = parse_simple_frontmatter(path)
    mismatches: list[str] = []
    for key, value in expected.items():
        actual = data.get(key)
        if actual != value:
            mismatches.append(f"{key}={actual!r}, expected {value!r}")
    if mismatches:
        raise RuntimeError(f"{label} frontmatter mismatch: " + "; ".join(mismatches))


def check_claude_code_wiring() -> None:
    skill = PACKAGE_ROOT / ".claude" / "skills" / "mentor-loop" / "SKILL.md"
    agent = PACKAGE_ROOT / ".claude" / "agents" / "mentor-loop-apprentice.md"
    resources = [
        ".claude/skills/mentor-loop/templates/mentor-brief-template.md",
        ".claude/skills/mentor-loop/templates/apprentice-execute.md",
        ".claude/skills/mentor-loop/templates/mentor-review-template.md",
        ".claude/skills/mentor-loop/templates/lesson-capture-template.md",
        ".claude/skills/mentor-loop/scripts/blast-radius-check.py",
        ".claude/skills/mentor-loop/scripts/runtime-floor-check.py",
    ]

    for relative in resources:
        if not (PACKAGE_ROOT / relative).is_file():
            raise RuntimeError(f"Claude Code skill resource missing: {relative}")

    require_frontmatter(
        skill,
        {
            "name": "mentor-loop",
            "argument-hint": '"<task description>"',
            "disable-model-invocation": "true",
            "model": "inherit",
        },
        "Claude Code mentor-loop skill",
    )
    require_frontmatter(
        agent,
        {
            "name": "mentor-loop-apprentice",
            "model": "haiku",
            "permissionMode": "acceptEdits",
        },
        "Claude Code apprentice subagent",
    )

    require_text(
        skill,
        [
            "disable-model-invocation: true",
            "Agent(mentor-loop-apprentice)",
            "${CLAUDE_SKILL_DIR}/templates/mentor-brief-template.md",
            "${CLAUDE_SKILL_DIR}/templates/apprentice-execute.md",
            "${CLAUDE_SKILL_DIR}/templates/mentor-review-template.md",
            "${CLAUDE_SKILL_DIR}/templates/lesson-capture-template.md",
            "${CLAUDE_SKILL_DIR}/scripts/blast-radius-check.py",
            "${CLAUDE_SKILL_DIR}/scripts/runtime-floor-check.py",
            ".mentor-loop/runs/<YYYYMMDD-HHMMSS>-<short-slug>/",
            "git rev-parse --git-path info/exclude",
            "if ! grep -qxF \".mentor-loop/\"",
            "if ! grep -qxF \".claude/\"",
            ".claude/` is a local-only copy",
            "Run the Baseline Before Editing commands before any edit.",
            "Invoke the `mentor-loop-apprentice` subagent",
            "Save stdout/stderr and exit code to `gate-blast-radius.txt`.",
            "Save stdout/stderr and exit code to `gate-runtime-floor.txt`.",
            "Review only:",
            "Append one lesson to `.mentor-loop/lessons.md`.",
            "`source_run_id`: this run directory id.",
            "`trigger`.",
            "`hit_count`: 0.",
            "Write `final-report.md`",
        ],
        "Claude Code mentor-loop skill",
    )

    require_text(
        agent,
        [
            "name: mentor-loop-apprentice",
            "model: haiku",
            "permissionMode: acceptEdits",
            "Run the Baseline Before Editing commands before any edit.",
            "Edit only files listed under Blast Radius",
            "Return an execution log",
            "Do not perform review. Do not capture lessons.",
        ],
        "Claude Code apprentice subagent",
    )

    ok("Claude Code /mentor-loop wiring checks pass")


def check_local_artifacts_are_gitignored() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        exclude_file = subprocess.run(
            ["git", "rev-parse", "--git-path", "info/exclude"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout.strip()
        exclude_path = repo / exclude_file
        with exclude_path.open("a", encoding="utf-8") as handle:
            handle.write("\n.mentor-loop/\n.claude/\n")

        run_dir = repo / ".mentor-loop" / "runs" / "smoke"
        run_dir.mkdir(parents=True)
        (run_dir / "final-report.md").write_text("smoke\n", encoding="utf-8")
        skill_dir = repo / ".claude" / "skills" / "mentor-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("smoke\n", encoding="utf-8")
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout
        if ".mentor-loop" in status:
            raise RuntimeError(".mentor-loop artifacts are visible to git status --porcelain")
        if ".claude" in status:
            raise RuntimeError(".claude local install is visible to git status --porcelain")
    ok(".mentor-loop and local .claude artifacts are hidden by repo-local git exclude")


def check_blast_radius_with_local_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        exclude_file = subprocess.run(
            ["git", "rev-parse", "--git-path", "info/exclude"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout.strip()
        with (repo / exclude_file).open("a", encoding="utf-8") as handle:
            handle.write("\n.mentor-loop/\n.claude/\n")

        (repo / "app.py").write_text("print('fixed')\n", encoding="utf-8")
        brief = repo / ".mentor-loop" / "runs" / "smoke" / "mentor-brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text(
            "\n".join(
                [
                    "# Mentor Brief",
                    "",
                    "## Blast Radius",
                    "",
                    "Likely touched files:",
                    "",
                    "- app.py",
                    "",
                    "Do not touch:",
                    "",
                    "- README.md",
                    "",
                    "Potentially affected behavior:",
                    "",
                    "- smoke",
                ]
            ),
            encoding="utf-8",
        )
        skill_dir = repo / ".claude" / "skills" / "mentor-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("smoke\n", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(PACKAGE_ROOT / "gates" / "blast-radius-check.py"), "--brief", str(brief)],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode != 0:
            fail(result.stdout.strip())
            raise RuntimeError("blast-radius smoke with local artifacts failed")
        if ".claude" in result.stdout or ".mentor-loop" in result.stdout:
            raise RuntimeError("blast-radius smoke included ignored local artifacts")
    ok("blast-radius gate ignores local artifacts and accepts allowed changed file")


def check_codex_native_driver() -> None:
    config_path = PACKAGE_ROOT / "mentor-loop.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    allowed_keys = {"strong_command", "apprentice_command", "python"}
    if set(config) != allowed_keys:
        raise RuntimeError("mentor-loop.config.json must contain only: " + ", ".join(sorted(allowed_keys)))
    for key in ("strong_command", "apprentice_command"):
        value = config[key]
        if not isinstance(value, list) or not all(isinstance(part, str) for part in value):
            raise RuntimeError(f"{key} must be a list of command arguments")
        command_name = Path(value[0]).stem.lower() if value else ""
        if command_name not in {"codex", "codex-cli"}:
            raise RuntimeError(f"{key} command head must resolve to codex or codex-cli")
        required = ["exec", "-m", "-s", "workspace-write", "-C", "{repo}", "-o", "{output}"]
        missing = [item for item in required if item not in value]
        if missing:
            raise RuntimeError(f"{key} missing required command fragments: " + ", ".join(missing))

    driver = PACKAGE_ROOT / "tools" / "mentor-loop.py"
    require_text(
        driver,
        [
            "codex exec reads the prompt from stdin",
            "build_brief_prompt",
            "build_apprentice_prompt",
            "load_active_lessons",
            "Active lessons from this repo:",
            "encoding=\"utf-8\"",
            "encoding=\"utf-8-sig\"",
            "errors=\"replace\"",
            "sys.stdout.reconfigure",
            "sys.stderr.reconfigure",
            "build_review_prompt",
            "Read the apprentice verification summary",
            "resolve_command_head",
            "shutil.which",
            "result: ENV_FAILURE",
            "gates\" / \"blast-radius-check.py",
            "gates\" / \"runtime-floor-check.py",
            "source_run_id",
            "hit_count`: 0",
            "final-report.md",
            "command template must be a list",
            "with_sandbox",
            "sandbox=\"read-only\"",
            "Do not edit files. Do not run fix commands.",
            "blast_radius_gate_result",
            "runtime_floor_gate_result",
            "review_verdict",
            "summarize_apprentice_verification",
            "apprentice_verification_summary",
            "apprentice-verification-summary.md",
            "brief_has_baseline_output",
            "Actual output:",
            "stopped_before_apprentice",
            "Strong brief step changed the worktree before apprentice execution.",
            "ensure_clean_worktree",
            "existing uncommitted changes",
            "## Verification",
            "## Gate Results",
            "## Changed Files",
            "stage_summary",
            "stage_init",
            "stage_brief_check",
            "stage_apprentice",
            "stage_gates",
            "stage_snapshot",
            "stage_capture_lesson",
            "stage_report",
            "stage_summary(\"gates\"",
            "mentor-brief.md missing",
        ],
        "Codex-native mentor-loop driver",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "repo with spaces"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lessons = repo / ".mentor-loop" / "lessons.md"
        lessons.parent.mkdir(parents=True)
        lessons.write_text(
            "## 2026-06-11 smoke\n\n"
            "- `trigger`: smoke task\n"
            "- `rule_for_next_time`: always read active lessons\n"
            "- `status`: active\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(driver),
                "--repo",
                str(repo),
                "--dry-run",
                "fix smoke bug",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode != 0:
            fail(result.stdout.strip())
            raise RuntimeError("Codex-native mentor-loop dry-run failed")
        reports = list((repo / ".mentor-loop" / "runs").glob("*/final-report.md"))
        if not reports:
            raise RuntimeError("Codex-native mentor-loop dry-run did not create final-report.md")
        final_report = reports[0].read_text(encoding="utf-8")
        for heading in ("## Verification", "## Gate Results", "## Changed Files", "## Review"):
            if heading not in final_report:
                raise RuntimeError(f"Codex-native mentor-loop dry-run report missing {heading}")
        prompts = list((repo / ".mentor-loop" / "runs").glob("*/mentor-brief-prompt.md"))
        if not prompts:
            raise RuntimeError("Codex-native mentor-loop dry-run did not create mentor-brief-prompt.md")
        prompt_text = prompts[0].read_text(encoding="utf-8")
        if "always read active lessons" not in prompt_text:
            raise RuntimeError("Codex-native mentor-loop dry-run did not inject active lessons into brief prompt")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "stage repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        init_result = subprocess.run(
            [
                sys.executable,
                str(driver),
                "init",
                "--repo",
                str(repo),
                "fix staged smoke bug",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if init_result.returncode != 0 or "stage: init | result: OK" not in init_result.stdout:
            fail(init_result.stdout.strip())
            raise RuntimeError("Codex-native stage init failed")
        match = re.search(r"run_id:\s*(\S+)", init_result.stdout)
        if not match:
            raise RuntimeError("Codex-native stage init did not print run_id")
        run_id = match.group(1)
        run_dir = repo / ".mentor-loop" / "runs" / run_id
        (run_dir / "mentor-brief.md").write_text(
            "## Baseline Before Editing\n\nActual output: baseline passed\n\n"
            "## Blast Radius\n\n- app.py\n",
            encoding="utf-8",
        )
        brief_check = subprocess.run(
            [sys.executable, str(driver), "brief-check", "--repo", str(repo), "--run", run_id],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if brief_check.returncode != 0 or "stage: brief-check | result: OK" not in brief_check.stdout:
            fail(brief_check.stdout.strip())
            raise RuntimeError("Codex-native stage brief-check failed")
        (run_dir / "apprentice-log.md").write_text("Verification: passed\nexit code: 0\n", encoding="utf-8")
        snapshot = subprocess.run(
            [sys.executable, str(driver), "snapshot", "--repo", str(repo), "--run", run_id],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if snapshot.returncode != 0 or "stage: snapshot | result: OK" not in snapshot.stdout:
            fail(snapshot.stdout.strip())
            raise RuntimeError("Codex-native stage snapshot failed")
        summary_path = run_dir / "apprentice-verification-summary.md"
        if "Verification: passed" not in summary_path.read_text(encoding="utf-8"):
            raise RuntimeError("Codex-native stage snapshot did not write apprentice verification summary")
        (run_dir / "review.md").write_text(
            "Verdict: Approved\n\n## Lesson Candidate\n"
            "- Trigger: staged smoke\n"
            "- Mistake: staged smoke mistake\n"
            "- Rule for next time: staged smoke rule\n"
            "- Suggested destination: .mentor-loop/lessons.md\n",
            encoding="utf-8",
        )
        capture = subprocess.run(
            [sys.executable, str(driver), "capture-lesson", "--repo", str(repo), "--run", run_id],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if capture.returncode != 0 or "stage: capture-lesson | result: OK" not in capture.stdout:
            fail(capture.stdout.strip())
            raise RuntimeError("Codex-native stage capture-lesson failed")
        (run_dir / "gate-blast-radius.txt").write_text("exit_code: 0\n\nresult: OK\n", encoding="utf-8")
        (run_dir / "gate-runtime-floor.txt").write_text("exit_code: 0\n\nresult: OK\n", encoding="utf-8")
        report = subprocess.run(
            [sys.executable, str(driver), "report", "--repo", str(repo), "--run", run_id],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if report.returncode != 0 or "stage: report | result: OK" not in report.stdout:
            fail(report.stdout.strip())
            raise RuntimeError("Codex-native stage report failed")
        if not (run_dir / "final-report.md").exists():
            raise RuntimeError("Codex-native stage report did not write final-report.md")
        lessons_text = (repo / ".mentor-loop" / "lessons.md").read_text(encoding="utf-8")
        if "staged smoke rule" not in lessons_text:
            raise RuntimeError("Codex-native stage capture-lesson did not append lesson")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "env failure repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        bad_config = Path(tmpdir) / "bad-config.json"
        bad_config.write_text(
            json.dumps(
                {
                    "strong_command": ["definitely-missing-codex-command", "-o", "{output}"],
                    "apprentice_command": ["definitely-missing-codex-command", "-o", "{output}"],
                    "python": sys.executable,
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(driver),
                "run",
                "--repo",
                str(repo),
                "--config",
                str(bad_config),
                "fix smoke bug",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0 or "result: ENV_FAILURE" not in result.stdout or "Traceback" in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("Codex-native mentor-loop did not report missing codex command as ENV_FAILURE")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "dirty repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(driver),
                "--repo",
                str(repo),
                "--dry-run",
                "fix smoke bug",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode == 0 or "existing uncommitted changes" not in result.stdout:
            raise RuntimeError("Codex-native mentor-loop did not block a dirty worktree")
    ok("Codex-native mentor-loop driver checks pass")


def check_windows_encoding_smoke() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "encoding repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        (repo / "setup.py").write_text("from setuptools import setup\nsetup(python_requires='>=3.8')\n", encoding="utf-8-sig")
        (repo / "app.py").write_text("value = '合法 Python with BOM'\n", encoding="utf-8-sig")
        runtime = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "gates" / "runtime-floor-check.py"),
                "--root",
                str(repo),
                "--changed",
                "app.py",
            ],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if runtime.returncode != 0 or "cannot be parsed" in runtime.stdout:
            fail(runtime.stdout.strip())
            raise RuntimeError("runtime-floor gate failed UTF-8 BOM Python smoke")

        brief = repo / "brief.md"
        brief.write_text(
            "## Blast Radius\n\nLikely touched files:\n- app.py\n\nDo not touch:\n- other.py\n",
            encoding="utf-8-sig",
        )
        blast = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "gates" / "blast-radius-check.py"),
                "--brief",
                str(brief),
                "--changed",
                "app.py",
            ],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if blast.returncode != 0:
            fail(blast.stdout.strip())
            raise RuntimeError("blast-radius gate failed UTF-8 BOM brief smoke")

        run_id = "encoding-smoke"
        run_dir = repo / ".mentor-loop" / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "mentor-brief.md").write_text(
            "## Baseline Before Editing\n\nActual output: ok\n\n## Blast Radius\n\nLikely touched files:\n- app.py\n",
            encoding="utf-8-sig",
        )
        (run_dir / "apprentice-log.md").write_text("Verification: passed\nexit code: 0\n", encoding="utf-8-sig")
        (run_dir / "gate-blast-radius.txt").write_text("exit_code: 0\n\nresult: OK\n", encoding="utf-8-sig")
        (run_dir / "gate-runtime-floor.txt").write_text("exit_code: 0\n\nresult: OK\n", encoding="utf-8-sig")
        (run_dir / "diff-and-status.txt").write_text("# git status --porcelain\n\n", encoding="utf-8-sig")
        (run_dir / "apprentice-verification-summary.md").write_text("Verification: passed\n", encoding="utf-8-sig")
        (run_dir / "review.md").write_text("Verdict: Approved\n\n中文 review with BOM\n", encoding="utf-8-sig")
        report = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "tools" / "mentor-loop.py"),
                "report",
                "--repo",
                str(repo),
                "--run",
                run_id,
            ],
            cwd=PACKAGE_ROOT,
            env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if report.returncode != 0 or "中文 review with BOM" not in report.stdout:
            fail(report.stdout.strip())
            raise RuntimeError("stage report failed UTF-8 stdio/BOM smoke")

    ok("Windows encoding smoke checks pass")


def check_eval_suite() -> None:
    require_text(
        PACKAGE_ROOT / "gates" / "env-preflight-check.py",
        ["stage: env-preflight | result:", "preflight_commands", "required_files"],
        "eval env preflight gate",
    )
    require_text(
        PACKAGE_ROOT / "evals" / "env-preflight-check.py",
        ["stage: env-preflight | result:", "preflight_commands", "required_files"],
        "eval env preflight gate",
    )
    require_text(
        PACKAGE_ROOT / "evals" / "run-task.py",
        [
            "raw-weak",
            "lessons-only",
            "full-loop",
            "outcome_type",
            "scorecard",
            "lesson_origin_relation",
            "Active lessons from package ledger:",
            "shutil.which",
            "infra_error",
            "repo_slug",
            "render_template",
        ],
        "eval runner",
    )
    require_text(
        PACKAGE_ROOT / "evals" / "collect-tasks.py",
        ["api.github.com/search/issues", "GH_TOKEN", "merge_commit_sha", "base_commit", "stage: collect-tasks | result:"],
        "eval task collector",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "candidates.json"
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "evals" / "collect-tasks.py"),
                "--fixture",
                str(PACKAGE_ROOT / "evals" / "fixtures" / "collect-tasks.fixture.json"),
                "--repo",
                "kellyjonbrazil/jc",
                "--output",
                str(output),
                "--sleep-seconds",
                "0",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or "stage: collect-tasks | result: OK" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("eval task collector fixture run failed")
        candidates = json.loads(output.read_text(encoding="utf-8"))
        if candidates.get("candidate_count") != 1:
            raise RuntimeError("eval task collector fixture should produce one candidate")
        candidate = candidates["candidates"][0]
        for key in ("repo", "issue_url", "fix_pr_url", "pr_merged_at", "base_commit", "files_changed", "total_diff_lines", "verification_hint"):
            if key not in candidate:
                raise RuntimeError(f"eval task collector candidate missing {key}")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "work"
        scorecard = work / "scorecard.csv"
        task = PACKAGE_ROOT / "evals" / "tasks" / "mock-smoke.json"
        config = PACKAGE_ROOT / "evals" / "mock-codex.config.json"
        for arm in ("raw-weak", "lessons-only", "full-loop"):
            result = subprocess.run(
                [
                    sys.executable,
                    str(PACKAGE_ROOT / "evals" / "run-task.py"),
                    "--task",
                    str(task),
                    "--arm",
                    arm,
                    "--work-root",
                    str(work),
                    "--scorecard",
                    str(scorecard),
                    "--config",
                    str(config),
                ],
                cwd=PACKAGE_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0 or "outcome_type=accepted" not in result.stdout:
                fail(result.stdout.strip())
                raise RuntimeError(f"eval runner mock {arm} failed")
        rows = scorecard.read_text(encoding="utf-8").splitlines()
        if len(rows) != 4:
            raise RuntimeError("eval runner scorecard should contain header plus three rows")
        parsed_rows = list(csv.DictReader(scorecard.open(newline="", encoding="utf-8")))
        if "lesson_origin_relation" not in parsed_rows[0]:
            raise RuntimeError("eval runner scorecard missing lesson_origin_relation column")
        if "regression_baseline_failures" not in parsed_rows[0] or "regression_new_failures" not in parsed_rows[0]:
            raise RuntimeError("eval runner scorecard missing baseline-relative regression columns")
        if any(row["lesson_origin_relation"] != "cross-repo" for row in parsed_rows):
            raise RuntimeError("mock eval rows should classify lesson origin as cross-repo")
        prompt_paths = sorted((work / "artifacts" / "mock-smoke" / "lessons-only").glob("*/lessons-only-prompt.md"))
        if not prompt_paths:
            raise RuntimeError("lessons-only mock run did not write prompt artifact")
        prompt_text = prompt_paths[-1].read_text(encoding="utf-8")
        if "Active lessons from package ledger:" not in prompt_text or "windows-text-encoding" not in prompt_text:
            raise RuntimeError("lessons-only mock prompt did not include package active lessons")
        baseline_paths = sorted((work / "artifacts" / "mock-smoke" / "raw-weak").glob("*/baseline-regression.txt"))
        if not baseline_paths:
            raise RuntimeError("eval runner mock did not write baseline-regression.txt")

    with tempfile.TemporaryDirectory(dir=PACKAGE_ROOT / "evals") as packaged_tmp:
        packaged_tmp_path = Path(packaged_tmp)
        engine_config = packaged_tmp_path / "mock-engine-config.json"
        engine_config.write_text(
            json.dumps(
                {
                    "strong_command": [sys.executable, str(PACKAGE_ROOT / "evals" / "mock-codex.py"), "-o", "{output}"],
                    "apprentice_command": [sys.executable, str(PACKAGE_ROOT / "evals" / "mock-codex.py"), "-o", "{output}"],
                    "python": sys.executable,
                }
            ),
            encoding="utf-8",
        )
        runner_config = packaged_tmp_path / "runner-config.json"
        runner_config.write_text(
            json.dumps(
                {
                    "cheap_command": [sys.executable, str(PACKAGE_ROOT / "evals" / "mock-codex.py"), "-o", "{output}"],
                    "mentor_loop_config": "{package}/evals/" + packaged_tmp_path.name + "/mock-engine-config.json",
                }
            ),
            encoding="utf-8",
        )
        work = packaged_tmp_path / "work"
        scorecard = work / "scorecard.csv"
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "evals" / "run-task.py"),
                "--task",
                str(PACKAGE_ROOT / "evals" / "tasks" / "mock-smoke.json"),
                "--arm",
                "full-loop",
                "--work-root",
                str(work),
                "--scorecard",
                str(scorecard),
                "--config",
                str(runner_config),
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or "outcome_type=accepted" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("eval runner full-loop did not render {package} mentor_loop_config")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "work"
        scorecard = work / "scorecard.csv"
        task = Path(tmpdir) / "preexisting-regression-task.json"
        task.write_text(
            json.dumps(
                {
                    "id": "preexisting-regression",
                    "language": "Python",
                    "repo": {"url": "__mock__", "base_ref": "HEAD"},
                    "ground_truth": {
                        "issue_url": "mock://preexisting-regression",
                        "fix_pr_url": "mock://preexisting-regression-pr",
                        "close_date": "2026-06-11",
                        "training_cutoff_relation": "mock",
                    },
                    "issue": {"title": "Pre-existing regression", "body": "Regression is already red before editing."},
                    "verification": {
                        "focused": [{"name": "focused", "command": [sys.executable, "-c", "print('focused ok')"]}],
                        "regression": [
                            {
                                "name": "regression",
                                "command": [
                                    sys.executable,
                                    "-c",
                                    "import sys; print('FAILED test_env.py::test_timezone'); sys.exit(1)",
                                ],
                            }
                        ],
                    },
                    "env": {
                        "required_files": ["app.py", "setup.py"],
                        "preflight_commands": [{"name": "python", "command": [sys.executable, "--version"]}],
                        "required_deps": ["python"],
                    },
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "evals" / "run-task.py"),
                "--task",
                str(task),
                "--arm",
                "raw-weak",
                "--work-root",
                str(work),
                "--scorecard",
                str(scorecard),
                "--config",
                str(PACKAGE_ROOT / "evals" / "mock-codex.config.json"),
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or "outcome_type=accepted" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("baseline-relative regression mock should be accepted")
        row = next(csv.DictReader(scorecard.open(newline="", encoding="utf-8")))
        if row["regression_baseline_failures"] != "1" or row["regression_new_failures"] != "0":
            raise RuntimeError("baseline-relative regression counts were not recorded correctly")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "work"
        scorecard = work / "scorecard.csv"
        task = Path(tmpdir) / "infra-error-task.json"
        task.write_text(
            json.dumps(
                {
                    "id": "infra-error",
                    "language": "Python",
                    "repo": {"url": "__mock__/infra", "base_ref": "missing-ref"},
                    "ground_truth": {
                        "issue_url": "mock://infra-error",
                        "fix_pr_url": "mock://infra-error-pr",
                        "close_date": "2026-06-11",
                        "training_cutoff_relation": "mock",
                    },
                    "issue": {"title": "Infra error", "body": "Force a runner exception."},
                    "verification": {"focused": [], "regression": []},
                    "env": {"required_files": [], "preflight_commands": [], "required_deps": []},
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "evals" / "run-task.py"),
                "--task",
                str(task),
                "--arm",
                "raw-weak",
                "--work-root",
                str(work),
                "--scorecard",
                str(scorecard),
                "--config",
                str(PACKAGE_ROOT / "evals" / "mock-codex.config.json"),
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if "outcome_type=infra_error" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("forced runner exception should classify as infra_error")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "work"
        scorecard = work / "scorecard.csv"
        for repo_name in ("alpha", "beta"):
            task = Path(tmpdir) / f"{repo_name}.json"
            task.write_text(
                json.dumps(
                    {
                        "id": f"mock-{repo_name}",
                        "language": "Python",
                        "repo": {"url": f"__mock__/{repo_name}", "base_ref": "HEAD"},
                        "ground_truth": {
                            "issue_url": f"mock://{repo_name}",
                            "fix_pr_url": f"mock://{repo_name}-pr",
                            "close_date": "2026-06-11",
                            "training_cutoff_relation": "mock",
                        },
                        "issue": {"title": repo_name, "body": "Mock repo cache test."},
                        "verification": {
                            "focused": [{"name": "focused", "command": [sys.executable, "-c", "print('focused ok')"]}],
                            "regression": [{"name": "regression", "command": [sys.executable, "-c", "print('regression ok')"]}],
                        },
                        "env": {
                            "required_files": ["app.py", "setup.py"],
                            "preflight_commands": [{"name": "python", "command": [sys.executable, "--version"]}],
                            "required_deps": ["python"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(PACKAGE_ROOT / "evals" / "run-task.py"),
                    "--task",
                    str(task),
                    "--arm",
                    "raw-weak",
                    "--work-root",
                    str(work),
                    "--scorecard",
                    str(scorecard),
                    "--config",
                    str(PACKAGE_ROOT / "evals" / "mock-codex.config.json"),
                ],
                cwd=PACKAGE_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0 or "outcome_type=accepted" not in result.stdout:
                fail(result.stdout.strip())
                raise RuntimeError("mock repo cache task failed")
        source_dirs = [path for path in (work / "sources").iterdir() if path.is_dir()]
        if len(source_dirs) != 2:
            raise RuntimeError("eval runner should create distinct source clones per repo")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "preflight-block-repo"
        repo.mkdir()
        task = Path(tmpdir) / "missing-file-task.json"
        task.write_text(
            json.dumps(
                {
                    "env": {
                        "required_files": ["missing-required-file.txt"],
                        "preflight_commands": [],
                    }
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "evals" / "env-preflight-check.py"),
                "--task",
                str(task),
                "--repo",
                str(repo),
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0 or "stage: env-preflight | result: BLOCKED" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("env-preflight did not block missing required file")

    task_dir = PACKAGE_ROOT / "evals" / "tasks"
    real_tasks = sorted(path for path in task_dir.glob("*.json") if path.name != "mock-smoke.json")
    if not 10 <= len(real_tasks) <= 15:
        raise RuntimeError(f"eval suite must define 10-15 real tasks, found {len(real_tasks)}")
    languages: set[str] = set()
    for path in real_tasks:
        task = json.loads(path.read_text(encoding="utf-8-sig"))
        task_id = task.get("id", path.stem)
        if "685" in task_id or task.get("ground_truth", {}).get("issue_url", "").endswith("/685"):
            raise RuntimeError("eval suite must not include polluted jc-685 task")
        if "687" in task_id or task.get("ground_truth", {}).get("issue_url", "").endswith("/687"):
            raise RuntimeError("eval suite must not include polluted jc-687 task")
        language = task.get("language")
        if not language:
            raise RuntimeError(f"{path.name} missing language")
        languages.add(language)
        gt = task.get("ground_truth", {})
        for key in ("issue_url", "fix_pr_url", "close_date", "fix_diff_lines", "training_cutoff_relation"):
            if key not in gt or gt[key] in ("", None):
                raise RuntimeError(f"{path.name} missing ground_truth.{key}")
        if int(gt["fix_diff_lines"]) >= 100:
            raise RuntimeError(f"{path.name} fix diff is not under 100 lines")
        repo = task.get("repo", {})
        if not repo.get("url") or not repo.get("base_ref") or not repo.get("checkout_commands"):
            raise RuntimeError(f"{path.name} missing repo checkout metadata")
        env = task.get("env", {})
        if not env.get("required_deps") or not env.get("preflight_commands"):
            raise RuntimeError(f"{path.name} missing env deps/preflight")
        verification = task.get("verification", {})
        if not verification.get("focused") or not verification.get("regression"):
            raise RuntimeError(f"{path.name} missing focused/regression verification")
    if len(languages) < 2:
        raise RuntimeError("eval suite must cover at least two languages")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "incomplete repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        run_dir = repo / ".mentor-loop" / "runs" / "missing-artifacts"
        run_dir.mkdir(parents=True)
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "tools" / "mentor-loop.py"),
                "report",
                "--repo",
                str(repo),
                "--run",
                "missing-artifacts",
            ],
            cwd=PACKAGE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 1 or "stage: report | result: INCOMPLETE" not in result.stdout:
            fail(result.stdout.strip())
            raise RuntimeError("report stage did not return INCOMPLETE for missing artifacts")

    ok("eval suite smoke checks pass")


def check_zip(zip_path: Path, files: list[str]) -> None:
    if not zip_path.is_file():
        raise RuntimeError(f"zip not found: {zip_path}")

    expected = {path.replace("\\", "/") for path in files}
    with zipfile.ZipFile(zip_path) as archive:
        actual = {info.filename for info in archive.infolist()}

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    forbidden = sorted(
        entry for entry in actual if "__pycache__" in entry or entry.endswith(".pyc")
    )

    if missing:
        raise RuntimeError("zip is missing manifest files: " + ", ".join(missing))
    if extra:
        raise RuntimeError("zip contains files outside manifest: " + ", ".join(extra))
    if forbidden:
        raise RuntimeError("zip contains generated Python cache files: " + ", ".join(forbidden))

    ok(f"zip matches manifest ({len(actual)} entries)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the Mentor Loop lean v0 package release checks."
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        help="Optional zip file to compare against manifest.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        _, files = load_manifest()
        check_manifest_files(files)
        check_csv_files()
        check_claude_code_wiring()
        check_local_artifacts_are_gitignored()
        check_blast_radius_with_local_artifacts()
        check_codex_native_driver()
        check_windows_encoding_smoke()
        check_eval_suite()
        check_gates()
        check_tests()
        if args.zip_path is not None:
            check_zip(args.zip_path.resolve(), files)
    except Exception as exc:
        fail(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
