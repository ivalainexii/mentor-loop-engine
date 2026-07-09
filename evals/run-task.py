#!/usr/bin/env python3
"""Run one eval task in one arm and append one scorecard row."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = Path(__file__).resolve().parent
ENGINE = PACKAGE_ROOT / "tools" / "mentor-loop.py"
PREFLIGHT = PACKAGE_ROOT / "gates" / "env-preflight-check.py"
OUTCOME_TYPES = {
    "accepted",
    "review_blocked",
    "gate_blocked",
    "verification_failure",
    "verification_incomplete",
    "env_failure",
    "infra_error",
    "protocol_violation",
    "no_op",
}
SCORECARD_COLUMNS = [
    "task_id",
    "arm",
    "run_id",
    "repo",
    "base_ref",
    "issue_url",
    "fix_pr_url",
    "close_date",
    "training_cutoff_relation",
    "lesson_origin_relation",
    "outcome_type",
    "env_preflight_exit",
    "model_exit",
    "focused_exit",
    "regression_exit",
    "regression_baseline_failures",
    "regression_new_failures",
    "gate_exit",
    "review_verdict",
    "artifacts_dir",
    "notes",
]


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_command(
    command: list[str], cwd: Path, input_text: str | None = None, timeout: int | None = None
) -> tuple[int, str]:
    command = resolve_command(command)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return completed.returncode, completed.stdout
    except FileNotFoundError as error:
        return 127, str(error)
    except subprocess.TimeoutExpired as error:
        output = error.stdout if isinstance(error.stdout, str) else ""
        return 124, f"TIMEOUT after {timeout}s\n{output}"


def resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    head = command[0]
    if any(sep in head for sep in ("/", "\\")) or Path(head).is_absolute():
        return command
    resolved = shutil.which(head)
    if resolved:
        return [resolved, *command[1:]]
    return command


def stage_summary(result: str, detail: str) -> str:
    return f"stage: eval-run-task | result: {result} | detail: {detail}"


def template_values(repo: Path | None = None, output: Path | None = None) -> dict[str, str]:
    return {
        "repo": str(repo or ""),
        "output": str(output or ""),
        "evals": str(EVALS_ROOT),
        "package": str(PACKAGE_ROOT),
        "python": sys.executable,
    }


def render_template(value: str, repo: Path | None = None, output: Path | None = None) -> str:
    return value.format(**template_values(repo, output))


def repo_slug(repo_url: str) -> str:
    if repo_url.startswith("__mock__"):
        raw = repo_url.strip("_/") or "mock"
    else:
        raw = repo_url
        for prefix in ("https://", "http://", "git@"):
            raw = raw.removeprefix(prefix)
        raw = raw.removesuffix(".git")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip("-")
    return slug or "repo"


def ensure_mock_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").exists():
        run_command(["git", "init"], repo)
        run_command(["git", "config", "user.email", "eval@example.invalid"], repo)
        run_command(["git", "config", "user.name", "Mentor Loop Eval"], repo)
        (repo / "setup.py").write_text("from setuptools import setup\nsetup(python_requires='>=3.8')\n", encoding="utf-8")
        (repo / "app.py").write_text("def smoke():\n    return 'ok'\n", encoding="utf-8")
        run_command(["git", "add", "."], repo)
        run_command(["git", "commit", "-m", "mock smoke base"], repo)


def prepare_repo(task: dict, work_root: Path, run_id: str) -> Path:
    repo_url = task["repo"]["url"]
    source = work_root / "sources" / repo_slug(repo_url)
    if repo_url.startswith("__mock__"):
        ensure_mock_repo(source)
    else:
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            code, output = run_command(["git", "clone", repo_url, str(source)], work_root)
            if code != 0:
                raise RuntimeError("git clone failed:\n" + output)
        code, output = run_command(["git", "fetch", "--all", "--tags"], source)
        if code != 0:
            raise RuntimeError("git fetch failed:\n" + output)

    worktree = work_root / f"{task['id']}-{run_id}"
    if worktree.exists():
        shutil.rmtree(worktree)
    base_ref = task["repo"].get("base_ref", "HEAD")
    code, output = run_command(["git", "worktree", "add", "--detach", str(worktree), base_ref], source)
    if code != 0:
        raise RuntimeError("git worktree add failed:\n" + output)
    return worktree


def command_from_template(template: list[str], repo: Path, output: Path) -> list[str]:
    return [render_template(part, repo, output) for part in template]


def issue_text(task: dict) -> str:
    issue = task["issue"]
    return "\n".join(
        [
            f"Task id: {task['id']}",
            f"Issue URL: {task['ground_truth']['issue_url']}",
            f"Title: {issue['title']}",
            "",
            issue["body"],
        ]
    )


def active_lessons() -> str:
    path = PACKAGE_ROOT / "evals" / "fixtures" / "package-lessons.md"
    if not path.exists():
        raise RuntimeError(f"package lesson seed missing: {path}")
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise RuntimeError(f"package lesson seed contains no active lessons: {path}")
    seed_match = re.search(r"(?m)^- `seed_id`:\s*(\S+)\s*$", text)
    if not seed_match:
        raise RuntimeError(f"package lesson seed missing seed_id: {path}")
    entries: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            entry = "\n".join(current).strip()
            if "`status`: active" in entry:
                entries.append(entry)
            current = [line]
        else:
            current.append(line)
    if current:
        entry = "\n".join(current).strip()
        if "`status`: active" in entry:
            entries.append(entry)
    if not entries:
        raise RuntimeError(f"package lesson seed contains no active lessons: {path}")
    return f"- `seed_id`: {seed_match.group(1)}\n\n" + "\n\n".join(entries)


def lesson_origin_relation(task: dict) -> str:
    repo_url = task.get("repo", {}).get("url", "")
    return "same-repo" if "github.com/kellyjonbrazil/jc" in repo_url else "cross-repo"


def run_model_arm(task: dict, arm: str, repo: Path, run_dir: Path, config: dict) -> tuple[int, str]:
    prompt = issue_text(task)
    if arm == "lessons-only":
        prompt += "\n\nActive lessons from versioned package seed:\n" + active_lessons()
    (run_dir / f"{arm}-prompt.md").write_text(prompt, encoding="utf-8")
    output = run_dir / f"{arm}-codex-output.md"
    command = command_from_template(config["cheap_command"], repo, output)
    return run_command(command, repo, prompt, timeout=7200)


def run_setup(task: dict, repo: Path, log_path: Path) -> int:
    """Run the task's env.setup_commands (dependency install). Failure = env problem."""
    sections: list[str] = []
    worst = 0
    for check in task.get("env", {}).get("setup_commands", []):
        name = check.get("name", "unnamed")
        command = check.get("command", [])
        code, output = run_command(command, repo, timeout=1800)
        sections.append(f"## setup: {name}\nexit_code: {code}\n\n{output}")
        if code != 0:
            # corepack enable needs write access to the node install dir
            # (EPERM here); preflight already proved the package manager is
            # available, so a corepack bootstrap failure is not fatal.
            if command and command[0] == "corepack":
                sections.append("(non-fatal: package manager availability already verified by preflight)")
                continue
            worst = code
            break
    log_path.write_text("\n\n".join(sections), encoding="utf-8")
    return worst


def run_verification(task: dict, repo: Path, key: str, log_path: Path) -> int:
    worst = 0
    lines: list[str] = []
    for check in task["verification"].get(key, []):
        name = check.get("name", "unnamed")
        command = check.get("command", [])
        code, output = run_command(command, repo, timeout=3600)
        lines.append(f"## {key}: {name}\nexit_code: {code}\n\n{output}")
        worst = aggregate_verification_exit(worst, code)
    log_path.write_text("\n\n".join(lines), encoding="utf-8")
    return worst


def parse_failure_count(output: str, exit_code: int) -> int:
    counts = [int(value) for value in re.findall(r"(?:failures|errors)=(\d+)", output)]
    if counts:
        return sum(counts)
    match = re.search(r"=+\s+(\d+)\s+failed", output)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s+failed\b", output)
    if match:
        return int(match.group(1))
    return 1 if exit_code != 0 else 0


def parse_failure_ids(output: str) -> set[str]:
    ids: set[str] = set()
    for line in output.splitlines():
        stripped = line.strip()
        match = re.match(r"^(FAIL|ERROR):\s+(.+)$", stripped)
        if match:
            ids.add(match.group(2).strip())
            continue
        match = re.match(r"^FAILED\s+(\S+)", stripped)
        if match:
            ids.add(match.group(1).strip())
            continue
        match = re.match(r"^(.+?)\s+\.\.\.\s+(FAIL|ERROR)$", stripped)
        if match:
            ids.add(match.group(1).strip())
    return ids


def verification_exit_incomplete(exit_code: int) -> bool:
    return exit_code in {124, 127}


def aggregate_verification_exit(current: int, candidate: int) -> int:
    """Preserve command-missing/timeout evidence across multi-check suites."""
    if verification_exit_incomplete(current):
        return current
    if verification_exit_incomplete(candidate):
        return candidate
    return candidate if candidate != 0 else current


def run_regression(task: dict, repo: Path, log_path: Path) -> dict:
    worst = 0
    total_count = 0
    failure_ids: set[str] = set()
    parsed_any_ids = False
    sections: list[str] = []
    for check in task["verification"].get("regression", []):
        name = check.get("name", "unnamed")
        command = check.get("command", [])
        code, output = run_command(command, repo, timeout=3600)
        ids = parse_failure_ids(output)
        if ids:
            parsed_any_ids = True
            failure_ids.update(f"{name}::{item}" for item in ids)
        count = parse_failure_count(output, code)
        total_count += count
        sections.append(
            "\n".join(
                [
                    f"## regression: {name}",
                    f"exit_code: {code}",
                    f"failure_count: {count}",
                    "failure_ids:",
                    *[f"- {item}" for item in sorted(ids)],
                    "",
                    output,
                ]
            )
        )
        worst = aggregate_verification_exit(worst, code)
    log_path.write_text("\n\n".join(sections), encoding="utf-8")
    return {
        "exit_code": worst,
        "count": total_count,
        "ids": failure_ids,
        "parsed_ids": parsed_any_ids,
    }


def regression_new_failures(baseline: dict, current: dict) -> int:
    if baseline["parsed_ids"] and current["parsed_ids"]:
        return len(current["ids"] - baseline["ids"])
    return max(0, current["count"] - baseline["count"])


def make_mock_engine_config(run_dir: Path) -> Path:
    config = {
        "strong_command": [sys.executable, str(EVALS_ROOT / "mock-codex.py"), "-o", "{output}"],
        "apprentice_command": [sys.executable, str(EVALS_ROOT / "mock-codex.py"), "-o", "{output}"],
        "python": sys.executable,
    }
    path = run_dir / "mentor-loop.config.json"
    write_json(path, config)
    return path


def run_full_loop(
    task: dict, repo: Path, run_dir: Path, config: dict, baseline_failures: int
) -> tuple[int, str]:
    engine_config = config.get("mentor_loop_config")
    if engine_config == "__mock__":
        config_path = make_mock_engine_config(run_dir)
    else:
        config_path = Path(render_template(str(engine_config or PACKAGE_ROOT / "mentor-loop.config.json"), repo, run_dir))
    # The codex sandbox cannot execute python at all ("Access is denied" even
    # with an absolute path, observed live on jc-694). The harness runs the
    # baseline on the host and records it for the brief, same as the
    # paste-and-run regime used for environments the model cannot execute in.
    focused_baseline_code = run_verification(
        task, repo, "focused", run_dir / "baseline-focused.txt"
    )
    focused_tail = (run_dir / "baseline-focused.txt").read_text(
        encoding="utf-8", errors="replace"
    )[-2000:]
    issue = issue_text(task) + (
        "\n\n## Harness environment facts (carry these into the Mentor Brief)\n"
        "- The execution sandbox CANNOT run python: `python`/`py` are not on"
        " PATH and executing any interpreter by absolute path is denied. Do"
        " NOT attempt to run python commands, and do not stop because of"
        " that.\n"
        "- The eval harness already ran the baseline on the host. Use this as"
        " the Baseline Before Editing 'Actual output' (harness-recorded):\n"
        f"  - focused suite at baseline: exit code {focused_baseline_code},"
        " output tail:\n"
        f"\n```text\n{focused_tail}\n```\n"
        f"  - full regression suite at baseline: {baseline_failures}"
        " pre-existing failing tests (already accounted for; only NEW failures"
        " count).\n"
        "- Verification regime is harness-run: after execution the harness"
        " itself runs the focused and regression suites. The apprentice must"
        " implement the change plus tests and state 'verification deferred to"
        " harness' rather than executing python."
    )
    # Hand the engine the focused/regression commands so it can run them on the
    # host BEFORE its review stage; without this the engine review runs before any
    # verification and blocks every run by construction.
    verification_spec = run_dir / "engine-verification.json"
    write_json(
        verification_spec,
        {
            "focused": task["verification"].get("focused", []),
            "regression": task["verification"].get("regression", []),
        },
    )
    return run_command(
        [
            "python",
            str(ENGINE),
            "run",
            "--repo",
            str(repo),
            "--config",
            str(config_path),
            "--verification",
            str(verification_spec),
            issue,
        ],
        repo,
        timeout=10800,
    )


def parse_review_verdict(engine_output: str) -> str:
    match = re.search(r"^- review_verdict:\s*-?\s*(.+)$", engine_output, re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_engine_field(engine_output: str, field: str) -> str:
    match = re.search(rf"^- {re.escape(field)}:\s*(.+)$", engine_output, re.MULTILINE)
    return match.group(1).strip() if match else ""


def review_verdict_outcome(value: str) -> str | None:
    normalized = re.sub(r"[*_`]", "", (value or "")).strip().lstrip("-").strip().lower()
    if normalized.startswith("verdict:"):
        normalized = normalized.split(":", 1)[1].strip()
    normalized = normalized.rstrip(".!").strip()
    choices = {
        "approved": "approved",
        "needs fixes": "needs_fixes",
        "stop and re-plan": "stop_and_replan",
    }
    return choices.get(normalized)


def parse_gate_exit(engine_output: str) -> str:
    codes = re.findall(
        r"^- (?:blast_radius|runtime_floor)_gate_exit_code:\s*(\d+)$",
        engine_output,
        re.MULTILINE,
    )
    if not codes:
        return ""
    return str(max(int(code) for code in codes))


def classify(
    arm: str,
    env_code: int,
    model_code: int,
    focused_code: int,
    regression_new_failure_count: int,
    engine_output: str,
    infra_error: bool,
    review_verdict: str,
    work_changed: bool,
    regression_code: int = 0,
    regression_baseline_code: int = 0,
) -> str:
    if infra_error:
        return "infra_error"
    if env_code != 0:
        return "env_failure"
    run_reasons = {
        reason.strip()
        for reason in parse_engine_field(engine_output, "run_block_reasons").split(",")
        if reason.strip() and reason.strip() != "none"
    }
    if "verification_could_not_run" in run_reasons:
        return "verification_incomplete"
    if "verification_fail" in run_reasons:
        return "verification_failure"
    if {"failure_review_error", "failure_review_unknown", "review_process"} & run_reasons:
        return "infra_error"
    if {"failure_review_park", "review_needs_fixes", "review_stop_and_replan"} & run_reasons:
        return "review_blocked"
    if "review_invalid" in run_reasons:
        return "protocol_violation"
    if {"deterministic_gates", "brief_check"} & run_reasons:
        return "gate_blocked"
    if any(
        verification_exit_incomplete(code)
        for code in (focused_code, regression_code, regression_baseline_code)
    ):
        return "verification_incomplete"
    parsed_review = review_verdict_outcome(review_verdict)
    if review_verdict and parsed_review != "approved":
        return "review_blocked"
    if model_code != 0:
        if "stopped_during_brief" in engine_output:
            return "gate_blocked"
        if re.search(r"stage:\s*(?:brief-check|gates)\s*\|\s*result:\s*BLOCKED", engine_output, re.IGNORECASE):
            return "gate_blocked"
        gate_exit = parse_gate_exit(engine_output)
        if gate_exit and gate_exit != "0":
            return "gate_blocked"
        if parsed_review in {"needs_fixes", "stop_and_replan"}:
            return "review_blocked"
        if any(marker in engine_output for marker in ("Traceback", "FileNotFoundError", "No such file", "cannot find the file")):
            return "infra_error"
        return "protocol_violation"
    # Passing tests prove nothing if the model never changed the worktree.
    if not work_changed:
        return "no_op"
    if focused_code != 0 or regression_new_failure_count != 0:
        return "verification_failure"
    return "accepted"


def append_scorecard(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        normalize_scorecard(path)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORECARD_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def normalize_scorecard(path: Path) -> None:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return
    header = rows[0]
    if header == SCORECARD_COLUMNS:
        return
    normalized: list[dict[str, str]] = []
    for values in rows[1:]:
        row = {column: "" for column in SCORECARD_COLUMNS}
        if "lesson_origin_relation" not in header and len(values) == len(header) + 1:
            legacy_columns = header[:9] + ["lesson_origin_relation"] + header[9:]
        else:
            legacy_columns = header
        for column, value in zip(legacy_columns, values):
            if column in row:
                row[column] = value
        if (
            row["task_id"] == "jc-694-lsattr-spaces"
            and row["arm"] in {"raw-weak", "lessons-only"}
            and not row["regression_baseline_failures"]
            and not row["regression_new_failures"]
        ):
            notes = [part for part in row["notes"].split(";") if part]
            if "pre-baseline-relative-probe" not in notes:
                notes.append("pre-baseline-relative-probe")
            row["notes"] = ";".join(notes)
        normalized.append(row)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORECARD_COLUMNS)
        writer.writeheader()
        writer.writerows(normalized)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Run one Mentor Loop eval task arm.")
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=["raw-weak", "lessons-only", "full-loop"])
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--scorecard", required=True, type=Path)
    parser.add_argument("--config", default=str(EVALS_ROOT / "mock-codex.config.json"), type=Path)
    args = parser.parse_args()

    task_path = args.task.resolve()
    task = read_json(task_path)
    config = read_json(args.config)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_root = args.work_root.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    artifacts = run_root / "artifacts" / task["id"] / args.arm / run_id
    artifacts.mkdir(parents=True, exist_ok=True)

    env_code = model_code = focused_code = regression_code = regression_baseline_code = 0
    regression_baseline_count = regression_new_failure_count = 0
    engine_output = ""
    notes = ""
    infra_error = False
    work_changed = False
    review_verdict = ""
    gate_exit = ""
    try:
        repo = prepare_repo(task, run_root, run_id)
        env_code, env_output = run_command(["python", str(PREFLIGHT), "--task", str(task_path), "--repo", str(repo)], repo)
        (artifacts / "env-preflight.txt").write_text(env_output, encoding="utf-8")
        if env_code == 0:
            setup_code = run_setup(task, repo, artifacts / "env-setup.txt")
            if setup_code != 0:
                env_code = setup_code
                notes = "setup_commands failed; see env-setup.txt"
        if env_code == 0:
            baseline_regression = run_regression(task, repo, artifacts / "baseline-regression.txt")
            regression_baseline_count = baseline_regression["count"]
            regression_baseline_code = baseline_regression["exit_code"]
            if args.arm == "full-loop":
                model_code, engine_output = run_full_loop(
                    task, repo, artifacts, config, regression_baseline_count
                )
                (artifacts / "full-loop.txt").write_text(engine_output, encoding="utf-8")
                review_verdict = parse_review_verdict(engine_output)
                gate_exit = parse_gate_exit(engine_output)
            else:
                model_code, model_output = run_model_arm(task, args.arm, repo, artifacts, config)
                (artifacts / "model.txt").write_text(model_output, encoding="utf-8")
            status_code, status_output = run_command(["git", "status", "--porcelain"], repo)
            work_changed = status_code == 0 and bool(status_output.strip())
            (artifacts / "post-model-status.txt").write_text(status_output, encoding="utf-8")
            focused_code = run_verification(task, repo, "focused", artifacts / "focused-verification.txt")
            current_regression = run_regression(task, repo, artifacts / "regression-verification.txt")
            regression_code = current_regression["exit_code"]
            regression_new_failure_count = regression_new_failures(baseline_regression, current_regression)
    except Exception as error:
        repo = Path("")
        infra_error = True
        notes = str(error)

    outcome = classify(
        args.arm,
        env_code,
        model_code,
        focused_code,
        regression_new_failure_count,
        engine_output,
        infra_error,
        review_verdict,
        work_changed,
        regression_code=regression_code,
        regression_baseline_code=regression_baseline_code,
    )
    if outcome not in OUTCOME_TYPES:
        outcome = "protocol_violation"
    gt = task["ground_truth"]
    row = {
        "task_id": task["id"],
        "arm": args.arm,
        "run_id": run_id,
        "repo": str(repo),
        "base_ref": task["repo"].get("base_ref", ""),
        "issue_url": gt["issue_url"],
        "fix_pr_url": gt["fix_pr_url"],
        "close_date": gt["close_date"],
        "training_cutoff_relation": gt.get("training_cutoff_relation", "unknown"),
        "lesson_origin_relation": lesson_origin_relation(task),
        "outcome_type": outcome,
        "env_preflight_exit": str(env_code),
        "model_exit": str(model_code),
        "focused_exit": str(focused_code),
        "regression_exit": str(regression_code),
        "regression_baseline_failures": str(regression_baseline_count),
        "regression_new_failures": str(regression_new_failure_count),
        "gate_exit": gate_exit,
        "review_verdict": review_verdict,
        "artifacts_dir": str(artifacts),
        "notes": notes,
    }
    append_scorecard(args.scorecard, row)
    result = "OK" if outcome == "accepted" else "BLOCKED"
    print(stage_summary(result, f"task={task['id']}; arm={args.arm}; outcome_type={outcome}; artifacts={artifacts}"))
    return 0 if outcome == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
