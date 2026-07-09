#!/usr/bin/env python3
"""Codex-native Mentor Loop driver."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value.lower())
    return "-".join(words[:6]) or "task"


def now_run_id(task: str) -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slugify(task)}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def run_local(args: list[str], cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode, completed.stdout


def run_local_channels(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a command while preserving stdout as data and stderr as diagnostics."""
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.returncode, completed.stdout, completed.stderr


def git_porcelain_status(repo: Path) -> tuple[int, str, str]:
    return run_local_channels(["git", "status", "--porcelain"], repo)


def process_output(stdout: str, stderr: str) -> str:
    return "\n".join(part.rstrip() for part in (stdout, stderr) if part.strip())


def read_git_porcelain_status(repo: Path) -> tuple[str, str]:
    code, status, diagnostics = git_porcelain_status(repo)
    if code != 0:
        details = process_output(status, diagnostics)
        raise RuntimeError("could not read git status:\n" + (details or "(no diagnostics)"))
    return status, diagnostics


def ensure_git_repo(repo: Path) -> Path:
    code, output = run_local(["git", "rev-parse", "--show-toplevel"], repo)
    if code != 0:
        raise RuntimeError("target repo is not a git worktree:\n" + output)
    return Path(output.strip()).resolve()


def ensure_local_exclude(repo: Path, paths: list[str]) -> None:
    code, output = run_local(["git", "rev-parse", "--git-path", "info/exclude"], repo)
    if code != 0:
        raise RuntimeError("could not locate repo-local git exclude:\n" + output)
    exclude = repo / output.strip()
    existing = exclude.read_text(encoding="utf-8-sig", errors="ignore") if exclude.exists() else ""
    additions = [path for path in paths if path not in existing.splitlines()]
    if additions:
        append_text(exclude, "\n" + "\n".join(additions) + "\n")


def ensure_clean_worktree(repo: Path) -> None:
    status, diagnostics = read_git_porcelain_status(repo)
    if status.strip():
        details = status.rstrip()
        if diagnostics.strip():
            details += "\n\ngit diagnostics:\n" + diagnostics.rstrip()
        raise RuntimeError(
            "target repo has existing uncommitted changes; commit, stash, or use a clean worktree before running mentor-loop:\n"
            + details
        )


def load_config(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    required = {"strong_command", "apprentice_command", "python"}
    missing = sorted(required - set(data))
    if missing:
        raise RuntimeError("config missing required keys: " + ", ".join(missing))
    for key in ("strong_command", "apprentice_command"):
        if not isinstance(data[key], list) or not all(isinstance(part, str) for part in data[key]):
            raise RuntimeError(f"{key} must be a list of command arguments")
    if "advisor_command" in data:  # OPTIONAL cross-vendor brief reviewer (ml-v2 BUILD-B.2)
        advisor = data["advisor_command"]
        if not isinstance(advisor, list) or not all(isinstance(part, str) for part in advisor):
            raise RuntimeError("advisor_command must be a list of command arguments")
    if "architect_command" in data:  # OPTIONAL one-shot architect consult (ml-v2 BUILD-C, C-4)
        architect = data["architect_command"]
        if not isinstance(architect, list) or not all(isinstance(part, str) for part in architect):
            raise RuntimeError("architect_command must be a list of command arguments")
    if not isinstance(data["python"], str):
        raise RuntimeError("python must be a string")
    return data


def command_from_template(template: object, repo: Path, output: Path) -> list[str]:
    if not isinstance(template, list):
        raise RuntimeError("command template must be a list")
    return [str(part).format(repo=str(repo), output=str(output)) for part in template]


def resolve_command_head(args: list[str]) -> list[str]:
    if not args:
        raise RuntimeError("command template produced an empty command")
    head = args[0]
    if os.path.sep in head or (os.path.altsep and os.path.altsep in head):
        return args
    resolved = shutil.which(head)
    if not resolved:
        raise FileNotFoundError(f"command not found on PATH: {head}")
    return [resolved, *args[1:]]


def with_sandbox(args: list[str], sandbox: str) -> list[str]:
    updated = list(args)
    for index, value in enumerate(updated):
        if value in {"-s", "--sandbox"} and index + 1 < len(updated):
            updated[index + 1] = sandbox
            return updated
    return updated + ["-s", sandbox]


def run_codex(template: object, repo: Path, output: Path, prompt: str, log_path: Path, sandbox: str | None = None) -> int:
    args = command_from_template(template, repo, output)
    if sandbox:
        args = with_sandbox(args, sandbox)
    try:
        args = resolve_command_head(args)
    except FileNotFoundError as error:
        text = "\n".join(
            [
                f"exit_code: 127",
                f"result: ENV_FAILURE",
                str(error),
                "",
            ]
        )
        write_text(log_path, text)
        write_text(output, text)
        print(stage_summary("codex-exec", "ENV_FAILURE", str(error)))
        return 127
    # codex exec reads the prompt from stdin when no prompt arg is supplied.
    completed = subprocess.run(
        args,
        cwd=repo,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    write_text(log_path, completed.stdout)
    return completed.returncode


def render_git_snapshot(repo: Path, status: str, status_diagnostics: str) -> str:
    code_stat, stat = run_local(["git", "diff", "--stat"], repo)
    code_diff, diff = run_local(["git", "diff"], repo)
    sections = [
        "# git status --porcelain",
        status,
    ]
    if status_diagnostics.strip():
        sections.extend(["# git status diagnostics", status_diagnostics])
    sections.extend(
        [
            "# git diff --stat",
            stat if code_stat == 0 else f"(failed)\n{stat}",
            "# git diff",
            diff if code_diff == 0 else f"(failed)\n{diff}",
        ]
    )
    return "\n".join(sections)


def git_snapshot(repo: Path) -> str:
    status, status_diagnostics = read_git_porcelain_status(repo)
    return render_git_snapshot(repo, status, status_diagnostics)


def run_gate(args: list[str], repo: Path, output: Path) -> int:
    code, text = run_local(args, repo)
    write_text(output, f"exit_code: {code}\n\n{text}")
    return code


def parse_exit_code(path: Path) -> str:
    if not path.exists():
        return "missing"
    first = read_text(path).splitlines()[0] if read_text(path).splitlines() else ""
    match = re.search(r"exit_code:\s*(-?\d+)", first)
    return match.group(1) if match else "unknown"


def stage_summary(stage: str, result: str, detail: str) -> str:
    return f"stage: {stage} | result: {result} | detail: {detail}"


def run_dir_for(repo: Path, run_id: str) -> Path:
    return repo / ".mentor-loop" / "runs" / run_id


def summarize_gate(output: str) -> str:
    for line in output.splitlines():
        if line.lower().startswith("result:"):
            return line.strip()
    first = output.strip().splitlines()
    return first[0].strip() if first else "(no output)"


def _normalize_review_line(raw_line: str) -> str:
    line = raw_line.strip().lstrip("-*#>").strip()
    return re.sub(r"[*_`]", "", line).strip().lower()


def summarize_review(review: str) -> str:
    outcome = parse_review_outcome(review)
    if outcome is None:
        return "(verdict not found)"
    for line in review.splitlines():
        if parse_review_outcome(line) == outcome:
            return line.strip()
    return outcome.replace("stop_and_replan", "Stop and re-plan").replace("needs_fixes", "Needs fixes").replace("approved", "Approved")


def parse_review_outcome(review: str) -> str | None:
    """Return one explicit reviewer enum, or None for missing/ambiguous prose.

    The template contains all three choices on one line, so a line mentioning
    multiple choices is an instruction, not a verdict.  A negative phrase such
    as ``not approved`` is deliberately not accepted: the outcome must start
    with one of the contract's three enum values after an optional ``Verdict:``.
    """
    outcomes: list[str] = []
    choices = (
        ("stop and re-plan", "stop_and_replan"),
        ("needs fixes", "needs_fixes"),
        ("approved", "approved"),
    )
    in_verdict_section = False
    for raw_line in (review or "").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("#"):
            heading = _normalize_review_line(stripped.lstrip("#")).rstrip(":").strip()
            in_verdict_section = heading == "verdict"
            continue
        low = _normalize_review_line(raw_line)
        if low.startswith("verdict:"):
            low = low.split(":", 1)[1].strip()
        elif not in_verdict_section:
            continue
        low = low.rstrip(".!").strip()
        for phrase, outcome in choices:
            if low == phrase:
                outcomes.append(outcome)
                break
    unique = set(outcomes)
    return unique.pop() if len(unique) == 1 else None


def verification_summary_outcome(summary: str | None) -> str:
    """Classify host verification without changing its persisted text format."""
    if summary is None:
        return "not_configured"
    overall = re.match(r"\s*overall_status:\s*(PASS|FAIL|COULD-NOT-RUN)\b", summary, re.IGNORECASE)
    if overall:
        return overall.group(1).lower().replace("-", "_")
    # Backward-compatible fallback for pre-fix artifacts: only trust the status
    # immediately following an engine-generated verification section header.
    statuses = re.findall(
        r"(?mi)^##\s+(?:focused|regression):[^\n]*\nstatus:\s*(PASS|FAIL|COULD-NOT-RUN)\b",
        summary,
    )
    if not statuses:
        top_level = re.match(r"\s*status:\s*(PASS|FAIL|COULD-NOT-RUN)\b", summary, re.IGNORECASE)
        statuses = [top_level.group(1)] if top_level else []
    if not statuses:
        return "could_not_run"
    normalized = {status.upper() for status in statuses}
    if "COULD-NOT-RUN" in normalized:
        return "could_not_run"
    if "FAIL" in normalized:
        return "fail"
    return "pass" if normalized == {"PASS"} else "could_not_run"


def stage_result(summary: str) -> str | None:
    """Read the machine result field emitted by ``stage_summary``."""
    match = re.search(r"(?:^|\|)\s*result:\s*([A-Za-z_-]+)", summary or "", re.IGNORECASE)
    return match.group(1).upper() if match else None


def summarize_apprentice_verification(log: str) -> str:
    patterns = (
        "verification",
        "verify",
        "test",
        "pytest",
        "unittest",
        "exit code",
        "exit_code",
        "passed",
        "failed",
        " ok",
        "ran ",
    )
    hits: list[str] = []
    for raw_line in log.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if any(pattern in lowered for pattern in patterns):
            hits.append(line)
        if len(hits) >= 6:
            break
    return " | ".join(hits) if hits else "(no explicit verification lines found in apprentice log)"


def brief_has_baseline_output(brief: str) -> bool:
    baseline_index = brief.lower().find("## baseline before editing")
    if baseline_index < 0:
        return False
    section = brief[baseline_index:]
    next_heading = section.find("\n## ", 1)
    if next_heading >= 0:
        section = section[:next_heading]
    lowered = section.lower()
    markers = ("actual output", "output:", "exit code", "exit_code", "ran ", "passed", "failed")
    return any(marker in lowered for marker in markers)


def _brief_section(text: str, heading: str) -> str | None:
    """Return the body under a ``## <heading>`` section (case-insensitive), up to
    the next ``## `` heading, or None when the section is absent."""
    lowered = text.lower()
    index = lowered.find(f"## {heading.lower()}")
    if index < 0:
        return None
    start = text.find("\n", index)
    if start < 0:
        return ""
    section = text[start + 1:]
    next_heading = section.find("\n## ")
    if next_heading >= 0:
        section = section[:next_heading]
    return section


def _brief_marker(text: str, label: str) -> str | None:
    """Return the value of a ``- <label>: <value>`` (or ``<label>: <value>``) marker
    line, stripped + lowercased, or None when no such line exists."""
    prefix = label.lower() + ":"
    for raw in text.splitlines():
        line = raw.strip().lstrip("-").strip()
        if line.lower().startswith(prefix):
            return line[len(prefix):].strip().lower()
    return None


def check_brief_honesty(brief: str) -> dict[str, object]:
    """Deterministic brief-honesty gate (ml-v2 BUILD-B).

    Enforces Fable's design-note (iii) spec: a declared guard must state a
    fail-direction (fail-open / fail-closed) + a one-line why; a gate/anchor-touching
    brief must pin >=1 non-happy-path round-trip; an anchored brief must state scope +
    an excluded counter-example. Escalation predicate (item 5): a guard declared
    fail-open or unsure — and not architect-ratified — is routed to the architect
    BEFORE the apprentice runs, and the mentor may not self-approve it.

    CONDITIONAL by design: every check fires only on a marker the mentor set, so a
    brief with no markers (a plain non-guard bug fix) passes vacuously. The residual
    hole (a guard introduced but omitted from the section) is the case Fable
    pre-registered as the n=8 reclassify-trigger; it is backstopped by the template,
    the brief prompt, and the chapter-end audit, not by this gate.

    Returns ``{"status": "ok"|"blocked"|"escalate", "findings": [...],
    "escalations": [{"guard","direction","why"}]}``. ``blocked`` outranks ``escalate``:
    a malformed brief must be fixed before its escalation predicate is trustworthy.
    """
    findings: list[str] = []
    escalations: list[dict[str, str]] = []

    # --- items 2 + 5: guards & fail-directions ------------------------------
    guards_body = _brief_section(brief, "Guards & Fail-Directions")
    if guards_body is not None:
        entries = [ln.strip() for ln in guards_body.splitlines() if ln.strip().startswith("-")]
        for entry in entries:
            content = entry.lstrip("- ").strip()
            if content.lower() in {"none", "n/a", "none.", ""}:
                continue  # explicit "no guard" bullet, or a stray blank/placeholder
            low = content.lower()
            name = content.split(":", 1)[0].split("—")[0].strip() or "(unnamed guard)"
            has_open = "fail-open" in low or "fail open" in low
            has_closed = "fail-closed" in low or "fail closed" in low
            has_unsure = "unsure" in low
            ratified = "architect-ratified" in low
            if has_open and has_closed:
                findings.append(f"guard '{name}': ambiguous fail-direction (states both open and closed)")
                continue
            if not (has_open or has_closed or has_unsure):
                findings.append(f"guard '{name}': fail-direction undeclared (state fail-open or fail-closed + a why)")
                continue
            if has_open or has_closed:
                token = "fail-open" if has_open else "fail-closed"
                rest = content[low.find(token) + len(token):].strip(" —-:;\t")
                if len(rest) < 3:
                    findings.append(f"guard '{name}': fail-direction '{token}' missing a one-line why")
                    continue
            if (has_open or has_unsure) and not ratified:
                escalations.append(
                    {"guard": name, "direction": "fail-open" if has_open else "unsure", "why": content}
                )

    # --- item 1: non-happy-path round-trip for gate/anchor-touching briefs ---
    touches = _brief_marker(brief, "Touches fidelity gate or anchored contract")
    if touches is not None and touches.startswith("yes"):
        if "[non-happy-path]" not in brief.lower():
            findings.append(
                "gate/anchor-touching brief must pin >=1 non-happy-path round-trip "
                "(tag it [non-happy-path] in Verification)"
            )

    # --- item 3: anchored briefs state scope + an excluded counter-example ---
    anchored = _brief_marker(brief, "Anchored change")
    if anchored is not None and anchored.startswith("yes"):
        anchor_body = _brief_section(brief, "Anchoring") or ""
        if not _brief_marker(anchor_body, "Scope"):
            findings.append("anchored brief must state a non-empty 'Scope:' line in the Anchoring section")
        if not _brief_marker(anchor_body, "Excluded counter-example"):
            findings.append("anchored brief must state a non-empty 'Excluded counter-example:' line in the Anchoring section")

    if findings:
        status = "blocked"
    elif escalations:
        status = "escalate"
    else:
        status = "ok"
    return {"status": status, "findings": findings, "escalations": escalations}


def write_architect_inbox(repo: Path, run_dir: Path, run_id: str, escalations: list[dict[str, str]]) -> Path:
    """Write the escalation packet the mentor hands to a one-shot architect (Fable)
    BEFORE the apprentice runs. The mentor may not self-decide a fail-open guard."""
    lines = [
        "# Architect inbox — escalation from brief-check (ml-v2 BUILD-B)",
        "",
        f"- run_id: {run_id}",
        "- routed_by: brief-honesty gate (escalation predicate: fail-open / unsure guard)",
        "- rule: mentor may NOT self-decide; route to a one-shot architect BEFORE the apprentice runs.",
        "",
        "## Guards awaiting an architect ruling",
        "",
    ]
    for esc in escalations:
        lines.append(f"- guard: {esc.get('guard', '')}")
        lines.append(f"  - declared direction: {esc.get('direction', '')}")
        lines.append(f"  - mentor rationale: {esc.get('why', '')}")
        lines.append(
            "  - resolution: change the direction to fail-closed with a why, OR record the "
            "architect ruling by appending `[architect-ratified: <ref>]` to the guard line, then re-run."
        )
        lines.append("")
    path = run_dir / "architect-inbox.md"
    write_text(path, "\n".join(lines) + "\n")
    return path


# --- ml-v2 BUILD-C: close B's architect escalation loop ----------------------
# B stops at "escalated -> inbox -> BLOCKED" and leaves closure manual. C adds:
#   C-1 build_architect_packet / stage_architect_packet -- deterministic §0.5
#       consult-packet assembly (auto on escalation + a CLI stage).
#   C-3 stamp_architect_ratified / build_disposition_skeleton /
#       stage_architect_ratify -- write-back: verdict text (INPUT) -> ledger
#       disposition skeleton + brief guard-line [architect-ratified] stamp.
#   C-4 run_architect_consult -- OPTIONAL pinned-model auto-consult (mirrors
#       B.2 advisor); produces a verdict DRAFT, never auto-stamps, never unlocks.
# Fail-direction ALL fail-closed: no verdict never unlocks; assembly failure =
# BLOCKED with a reason; C-4 failure = SKIP + stay BLOCKED.


def build_architect_packet(
    run_id: str,
    inbox: str,
    task: str,
    blast_radius: str,
    dec_sections: str,
    active_lessons: str,
) -> str:
    """Assemble a §0.5-shaped architect consult packet (pure). Sections 1-5 are
    deterministic (from run artifacts + the ledger); sections 6-7 are the two
    judgment slots a human fills before consulting (the §0.5 CONSULT PACKET's
    required 用户明示指令 field + the Opus-leaning field). The VERDICT is never
    in this file -- assembly is deterministic, the ruling is not."""
    return "\n".join(
        [
            "# Architect consult packet (ml-v2 BUILD-C, §0.5-shaped)",
            "",
            f"- run_id: {run_id}",
            "- assembled_by: stage_architect_packet (deterministic; sections 6-7 are human-fill)",
            "- rule: FAIL-CLOSED -- no architect verdict, no unlock. This file carries the",
            "  question + ground truth, NOT the ruling. Record a ruling with `architect-ratify`.",
            "",
            "## 1. Escalation (from brief-check)",
            "",
            inbox.strip() or "(no escalation inbox found)",
            "",
            "## 2. Change intent (task)",
            "",
            task.strip() or "(change intent unavailable)",
            "",
            "## 3. Blast-radius file list (from the brief)",
            "",
            blast_radius.strip() or "(no blast radius found)",
            "",
            "## 4. Applicable architecture decisions (full text, from .mentor-loop/decisions.md)",
            "",
            dec_sections.strip() or "(none)",
            "",
            "## 5. Active lessons (from .mentor-loop/lessons.md)",
            "",
            active_lessons.strip() or "No active lessons found.",
            "",
            "## 6. 与本判断相关的用户明示指令 (§0.6 required -- FILL before consulting)",
            "",
            "<fill: the user's explicit instruction bearing on this decision, or 无>",
            "",
            "## 7. Opus 倾向 (mentor's leaning + one-line why -- FILL before consulting)",
            "",
            "<fill: the mentor's own leaning; the architect ranks its verdict against this>",
            "",
            "## 8. What's wanted back",
            "",
            "A verdict per escalated guard: either a fail-closed rewrite, or an architect",
            "ratification. Save the verdict under .mentor-loop/runs/<id>/ (gitignored -- keeps",
            "the worktree clean so the re-run is not blocked), then run:",
            f"  mentor-loop.py architect-ratify --run {run_id} --verdict <file> [--ref <DEC/ref>]",
            "",
        ]
    )


def run_architect_consult(repo: Path, run_dir: Path, run_id: str, architect_command: object) -> int:
    """C-4 (OPTIONAL, cuttable): run the assembled packet through a pinned-model
    architect to produce a verdict DRAFT. Mirrors B.2's codex call but is
    FAIL-CLOSED: it NEVER auto-stamps the brief and NEVER unlocks -- the mentor
    must review the draft and run `architect-ratify` (C-3). On any failure
    (codex not runnable) it records a SKIP; the loop stays BLOCKED. Always
    returns 0 (drafting is best-effort; the lock lives in brief-check)."""
    packet_path = run_dir / "architect-packet.md"
    draft_path = run_dir / "architect-verdict-draft.md"
    if not packet_path.exists():
        print(stage_summary("architect-consult", "SKIP", "architect-packet.md missing"))
        return 0
    prompt = read_text(packet_path)
    code = run_codex(
        architect_command, repo, draft_path, prompt, run_dir / "architect-consult-codex.log", sandbox="read-only"
    )
    draft = read_text(draft_path).strip() if draft_path.exists() else ""
    if code != 0 or "result: ENV_FAILURE" in draft:
        write_text(
            draft_path,
            "# Architect verdict DRAFT -- SKIPPED\n\n"
            f"- run_id: {run_id}\n"
            f"- reason: architect_command could not run (exit={code}); loop stays BLOCKED.\n"
            "- no same-vendor fallback; the mentor takes architect-packet.md to a one-shot architect manually.\n",
        )
        print(stage_summary("architect-consult", "SKIP", f"architect_command could not run (exit={code}); stays BLOCKED"))
        return 0
    print(
        stage_summary(
            "architect-consult",
            "OK",
            "verdict DRAFT written (architect-verdict-draft.md); mentor must disposition + run architect-ratify (NEVER auto-unlocks)",
        )
    )
    return 0


def stage_architect_packet(repo: Path, run_id: str, config: dict[str, object] | None = None) -> int:
    """C-1: assemble runs/<id>/architect-packet.md. Triggered automatically when
    brief-check escalates, and available as a CLI stage for a chapter-end call.

    FAIL-CLOSED: any assembly failure writes a BLOCKED packet naming the reason
    and returns 1 (a missing brief means there is nothing to consult about). On
    success returns 0. When ``config`` carries an OPTIONAL architect_command
    (C-4), the packet is also run through a pinned architect to draft a verdict
    -- that draft never unlocks; only architect-ratify (C-3) does."""
    try:
        repo = ensure_git_repo(repo)
        run_dir = run_dir_for(repo, run_id)
        packet_path = run_dir / "architect-packet.md"
        brief_path = run_dir / "mentor-brief.md"
        if not brief_path.exists():
            reason = "mentor-brief.md missing -- nothing to assemble a consult packet from"
            write_text(packet_path, f"# Architect consult packet -- BLOCKED\n\n- run_id: {run_id}\n- reason: {reason}\n")
            print(stage_summary("architect-packet", "BLOCKED", reason))
            return 1
        brief = read_text(brief_path)
        inbox_path = run_dir / "architect-inbox.md"
        inbox = read_text(inbox_path) if inbox_path.exists() else "(no escalation inbox -- chapter-end / manual invocation; packet assembled anyway)"
        task_path = run_dir / "task.txt"
        task = read_text(task_path) if task_path.exists() else "(change intent unavailable)"
        blast_radius = extract_blast_radius(brief)
        dec_ids = re.findall(r"DEC-\d+", brief)
        decisions_path = repo / ".mentor-loop" / "decisions.md"
        if decisions_path.exists():
            dec_sections = extract_dec_sections(read_text(decisions_path), dec_ids)
        else:
            dec_sections = "(no .mentor-loop/decisions.md in this repo)"
        active_path = run_dir / "active-lessons.md"
        active_lessons = read_text(active_path) if active_path.exists() else load_active_lessons(repo)
        packet = build_architect_packet(run_id, inbox, task, blast_radius, dec_sections, active_lessons)
        write_text(packet_path, packet)
        print(stage_summary("architect-packet", "OK", f"architect-packet.md assembled for {run_id}"))
        architect_command = config.get("architect_command") if config else None
        if architect_command:
            run_architect_consult(repo, run_dir, run_id, architect_command)
        return 0
    except Exception as error:  # fail-closed: any assembly error is BLOCKED, never a crash that hides the lock
        try:
            run_dir = run_dir_for(ensure_git_repo(repo), run_id)
            write_text(run_dir / "architect-packet.md", f"# Architect consult packet -- BLOCKED\n\n- run_id: {run_id}\n- reason: {error}\n")
        except Exception:
            pass
        print(stage_summary("architect-packet", "BLOCKED", str(error)))
        return 1


def stamp_architect_ratified(brief: str, ref: str) -> tuple[str, int]:
    """C-3 (pure): append ``[architect-ratified: <ref>]`` to each escalated guard
    line (fail-open / unsure, not already ratified) in the Guards &
    Fail-Directions section. Uses the SAME predicate as check_brief_honesty so a
    stamped brief passes the escalation gate on re-run. Returns (new_brief,
    stamped_count)."""
    lines = brief.splitlines(keepends=True)
    in_guards = False
    stamped = 0
    out: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("## "):
            in_guards = stripped.lower().startswith("## guards & fail-directions")
            out.append(raw)
            continue
        if in_guards and stripped.startswith("-"):
            low = stripped.lower()
            has_open = "fail-open" in low or "fail open" in low
            has_unsure = "unsure" in low
            ratified = "architect-ratified" in low
            if (has_open or has_unsure) and not ratified:
                newline = ""
                body = raw
                while body.endswith("\n") or body.endswith("\r"):
                    newline = body[-1] + newline
                    body = body[:-1]
                out.append(f"{body} [architect-ratified: {ref}]{newline}")
                stamped += 1
                continue
        out.append(raw)
    return "".join(out), stamped


def build_disposition_skeleton(run_id: str, ref: str, verdict_text: str, guards: list[str]) -> str:
    """C-3 (pure): a ledger disposition block that RECORDS an architect verdict.
    The verdict is INPUT (architect-authored) -- this only wraps it and leaves
    the §0.6 合宪自检 for the mentor to fill. It never generates a verdict."""
    guard_list = ", ".join(guards) if guards else "(none named in the escalation)"
    return "\n".join(
        [
            "",
            f"## architect-ratify — {run_id} ({ref})",
            "",
            "- **Decided by:** architect (one-shot §0.5 consult) — recorded via C-3 write-back (stage_architect_ratify).",
            f"- **Ratified guard(s):** {guard_list}",
            f"- **Ref:** {ref}",
            "- **Verdict (verbatim, architect-authored — C-3 records, does NOT generate):**",
            "",
            verdict_text.strip() or "(empty verdict file)",
            "",
            f"- **Applied:** brief guard line(s) stamped `[architect-ratified: {ref}]`; re-run brief-check to proceed.",
            "- **合宪自检 (mentor fills on adoption):** 角色经济学 / 机制免疫 / 修宪门槛 / 保真.",
            "",
        ]
    )


def stage_architect_ratify(repo: Path, run_id: str, verdict_path: str, ref: str | None = None) -> int:
    """C-3: record an architect verdict and unlock the escalation. Reads the
    architect's verdict file (INPUT), stamps the escalated guard line(s) in the
    brief, and appends a disposition skeleton to .mentor-loop/decisions.md.

    FAIL-CLOSED: a missing verdict file or missing brief is BLOCKED (no verdict
    never unlocks). It does NOT generate a verdict -- it only records the one it
    is given and applies the deterministic stamp that lets brief-check pass."""
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    verdict_file = Path(verdict_path)
    if not verdict_file.exists():
        print(stage_summary("architect-ratify", "BLOCKED", f"verdict file not found: {verdict_path} (no verdict, no unlock)"))
        return 1
    verdict_text = read_text(verdict_file)
    brief_path = run_dir / "mentor-brief.md"
    if not brief_path.exists():
        print(stage_summary("architect-ratify", "BLOCKED", "mentor-brief.md missing"))
        return 1
    brief = read_text(brief_path)
    resolved_ref = ref or run_id
    guards = [esc.get("guard", "") for esc in check_brief_honesty(brief).get("escalations", [])]
    new_brief, stamped = stamp_architect_ratified(brief, resolved_ref)
    if stamped:
        write_text(brief_path, new_brief)
    disposition = build_disposition_skeleton(run_id, resolved_ref, verdict_text, guards)
    append_text(repo / ".mentor-loop" / "decisions.md", disposition)
    write_text(run_dir / "architect-ratify.md", disposition)
    result = "OK" if stamped else "NOOP"
    detail = f"stamped {stamped} guard(s) with ref={resolved_ref}; disposition recorded to .mentor-loop/decisions.md"
    print(stage_summary("architect-ratify", result, detail))
    return 0


def extract_lesson_candidate(review: str) -> dict[str, str] | None:
    marker = "## Lesson Candidate"
    index = review.find(marker)
    if index < 0:
        return None
    section = review[index:]
    values: dict[str, str] = {}
    for key in ("Trigger", "Mistake", "Rule for next time", "Suggested destination"):
        match = re.search(rf"- {re.escape(key)}:\s*(.+)", section, re.IGNORECASE)
        if match:
            values[key.lower().replace(" ", "_")] = match.group(1).strip()
    trigger = values.get("trigger", "")
    mistake = values.get("mistake", "")
    rule = values.get("rule_for_next_time", "")
    if not trigger or trigger in {"-", "none", "None", "N/A"}:
        return None
    if not mistake or mistake in {"-", "none", "None", "N/A"}:
        return None
    if not rule or rule in {"-", "none", "None", "N/A"}:
        return None
    return values


def capture_lesson(repo: Path, run_id: str, run_dir: Path, review: str) -> str:
    candidate = extract_lesson_candidate(review)
    if not candidate:
        return "No reusable lesson captured."

    created = dt.datetime.now().isoformat(timespec="seconds")
    lesson = "\n".join(
        [
            "",
            f"## {created} {run_id}",
            "",
            f"- `created_at`: {created}",
            f"- `source_run_id`: {run_id}",
            "- `source_failure`: review finding",
            f"- `source_artifact`: {run_dir.relative_to(repo).as_posix()}/review.md",
            f"- `trigger`: {candidate.get('trigger', '')}",
            f"- `mistake`: {candidate.get('mistake', '')}",
            f"- `rule_for_next_time`: {candidate.get('rule_for_next_time', '')}",
            "- `hit_count`: 0",
            "- `last_hit_at`:",
            "- `status`: active",
            "- `candidate_gate`:",
            "",
        ]
    )
    append_text(repo / ".mentor-loop" / "lessons.md", lesson)
    write_text(run_dir / "lesson.md", lesson)
    return "Captured one reusable lesson."


def load_active_lessons(repo: Path) -> str:
    lessons_path = repo / ".mentor-loop" / "lessons.md"
    if not lessons_path.exists():
        return "No active lessons found."

    text = read_text(lessons_path)
    sections = re.split(r"(?m)^##\s+", text)
    active: list[str] = []
    for section in sections:
        if re.search(r"`?status`?\s*:\s*active\b", section, re.IGNORECASE):
            active.append("## " + section.strip())
    return "\n\n".join(active) if active else "No active lessons found."


# --- ml-v2 BUILD-C, C-2: architecture-precedent injection --------------------
# Mirrors load_active_lessons: the brief prompt carries the guardrail lines the
# architect already ruled (.mentor-loop/decisions.md) so precedents ride into
# every brief and reduce escalations. Deterministic; the mentor's DEC-ids line
# stays manual (this is context, not auto-citation).


def _dec_section_bodies(decisions_text: str) -> list[tuple[str, str]]:
    """Split a decisions.md into (header, body) pairs for each top-level
    ``## DEC-NNN ...`` section. A shared parser for load_precedents +
    extract_dec_sections so both read the ledger the same way."""
    pairs: list[tuple[str, str]] = []
    parts = re.split(r"(?m)^##\s+(DEC-\d+.*)$", decisions_text)
    # parts = [preamble, header1, body1, header2, body2, ...]
    for index in range(1, len(parts), 2):
        header = parts[index].strip()
        body = parts[index + 1] if index + 1 < len(parts) else ""
        pairs.append((header, body))
    return pairs


def _extract_guardrail(body: str) -> str:
    """Return the 'Consequences / guardrail for future briefs' text of a DEC
    body, collapsed to one line, or '' when the section has none. Stops at the
    next ``### `` (Note/Disposition) or the end of the section."""
    lowered = body.lower()
    index = lowered.find("guardrail for future briefs")
    if index < 0:
        return ""
    tail = body[index:]
    stop = tail.find("\n### ")
    if stop >= 0:
        tail = tail[:stop]
    # drop the marker label itself, keep the ruling text
    colon = tail.find(":")
    text = tail[colon + 1:] if colon >= 0 else tail
    return " ".join(text.split())


def load_precedents(repo: Path) -> str:
    """One bullet per DEC: the DEC headline + its operative guardrail, pulled
    from ``.mentor-loop/decisions.md``. Returns a fixed marker when the ledger
    is absent/empty so build_brief_prompt stays byte-stable for repos with no
    ledger (parallels load_active_lessons' 'No active lessons found.')."""
    decisions_path = repo / ".mentor-loop" / "decisions.md"
    if not decisions_path.exists():
        return "No architecture precedents found."
    text = read_text(decisions_path)
    bullets: list[str] = []
    for header, body in _dec_section_bodies(text):
        dec_id = header.split()[0] if header.split() else header
        guardrail = _extract_guardrail(body)
        if guardrail:
            bullets.append(f"- {header}\n  guardrail: {guardrail}")
        else:
            bullets.append(f"- {header}")
    return "\n".join(bullets) if bullets else "No architecture precedents found."


def extract_dec_sections(decisions_text: str, dec_ids: list[str]) -> str:
    """Return the FULL ``## DEC-NNN ...`` sections named in ``dec_ids`` (the ids
    a brief cites), verbatim, for the architect packet. Missing ids are noted
    honestly; no ids → a clear marker (never a silent empty)."""
    if not dec_ids:
        return "(no DEC ids cited in the brief — architect should consult the full ledger)"
    wanted = list(dict.fromkeys(dec_ids))  # de-dup, order-preserving
    bodies = {header.split()[0]: (header, body) for header, body in _dec_section_bodies(decisions_text)}
    out: list[str] = []
    for dec_id in wanted:
        if dec_id in bodies:
            header, body = bodies[dec_id]
            out.append(f"## {header}\n{body.rstrip()}")
        else:
            out.append(f"## {dec_id}\n(not found in .mentor-loop/decisions.md)")
    return "\n\n".join(out)


def build_brief_prompt(task: str, active_lessons: str, precedents: str = "No architecture precedents found.") -> str:
    template = read_text(PACKAGE_ROOT / "mentor-brief-template.md")
    return f"""Fill this Mentor Brief for the task below.

Rules:
- Use the template verbatim where possible.
- Name concrete context files the apprentice must read.
- Read the active lessons below and convert applicable lessons into concrete constraints, files to inspect, gates, or verification commands.
- Read the architecture precedents below (guardrails the architect already ruled) and honor each one; cite the applicable DEC ids in the brief. Do not invent DEC ids and do not restate a precedent as your own decision.
- Include Baseline Before Editing commands.
- Run baseline verification before any edit and paste the actual output into the Baseline Before Editing section.
- The Baseline Before Editing section must include an "Actual output:" or "exit code" line.
- Keep Blast Radius explicit and narrow.
- Include focused and regression verification commands.
- In "Guards & Fail-Directions", declare every guard (a fail-open/fail-closed decision point) this change introduces or moves, one bullet per guard, each with a direction and a one-line why; write `none` if there is no guard. You may NOT self-approve a fail-open or unsure honesty/fidelity guard — it is routed to the architect before the apprentice runs.
- In "Change Surface", set "Touches fidelity gate or anchored contract" to yes/no; if yes, pin at least one non-happy-path round-trip in Verification tagged [non-happy-path].
- If the change is anchored, set "Anchored change: yes" and fill "Anchoring" with a Scope line and one Excluded counter-example line.
- If required context or baseline cannot be determined, say STOP in the brief.

Task:
{task}

Active lessons from this repo:
{active_lessons}

Architecture precedents from this repo (.mentor-loop/decisions.md):
{precedents}

Template:
{template}
"""


def build_apprentice_prompt(brief: str, active_lessons: str) -> str:
    instructions = read_text(PACKAGE_ROOT / "apprentice-execute.md")
    return f"""Execute this Mentor Brief exactly.

Active lessons from this repo:
{active_lessons}

Apprentice instructions:
{instructions}

Mentor Brief:
{brief}
"""


# --- ml-v2 BUILD-B.2: cross-vendor Codex ADVISORY brief-review helpers ----------
# A COMPLEMENT to the deterministic brief-check, never a replacement. The gate reads
# only what the mentor DECLARED; a cross-vendor model reading the brief + change
# intent + blast-radius can flag a guard the mentor silently OMITTED. Advisory only.


def extract_blast_radius(brief: str) -> str:
    """Surface the brief's Blast Radius section as explicit ground truth for the
    cross-vendor packet (condition 2). Reuses the same section the deterministic gate
    reads, so the reviewer judges against the declared file list, not the brief prose."""
    body = _brief_section(brief, "Blast Radius")
    if body is None:
        return "(no Blast Radius section found in the brief)"
    return body.strip() or "(Blast Radius section is empty)"


def build_brief_review_prompt(task: str, brief: str, blast_radius: str) -> str:
    """Cross-vendor ADVISORY review prompt. Carries GROUND TRUTH — change intent +
    blast-radius file list + the brief — so the reviewer can flag a guard the brief
    SHOULD declare but did not, instead of rubber-stamping the brief's own words."""
    return f"""You are a CROSS-VENDOR reviewer reading a Mentor Brief BEFORE a cheap apprentice executes it.
A separate deterministic gate has already checked the brief's DECLARED guards. Your job is the part it
cannot do: find SEMANTIC gaps the brief is SILENT about -- a guard or fail-direction it should declare
but omitted, an unstated assumption, a blast-radius omission, or a fidelity/honesty risk this change
introduces.

Ground truth to judge against (not just the brief's own words):
- CHANGE INTENT: what the user actually asked for.
- BLAST-RADIUS FILE LIST: what the change may touch.
- the working directory is available READ-ONLY; you may read the referenced files to check the brief's
  claims against the real code.

Rules:
- ADVISORY ONLY -- you do not block. Output findings the mentor will adopt or reject.
- Be specific and terse. One line per finding: `- [gap] <what is missing or wrong> -- <why it matters>`.
- If the brief is genuinely complete, output exactly `- none` and stop. Do NOT invent findings.
- One pass. No brief rewrite, no debate, no multi-round plan.

## CHANGE INTENT
{task}

## BLAST-RADIUS FILE LIST (from the brief)
{blast_radius}

## MENTOR BRIEF
{brief}
"""


def count_advisory_findings(raw: str) -> int:
    """Count non-empty advisory bullets that are not an explicit 'none'."""
    total = 0
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        content = stripped.lstrip("-").strip().lower()
        if content and content not in {"none", "none.", "n/a"}:
            total += 1
    return total


def advisory_appendix(body: str, *, skipped: bool, reason: str = "") -> str:
    """Non-binding appendix appended to the brief (condition 1). Clearly marked so a
    real apprentice treats it as context, not execution steps."""
    header = "## Cross-Vendor Advisory (ml-v2 BUILD-B.2, non-blocking)"
    if skipped:
        lines = [
            "",
            "",
            header,
            "",
            f"SKIPPED -- this brief was NOT cross-vendor reviewed (未经跨厂审): {reason}",
            "The deterministic brief-check still applied. No same-vendor fallback was used (by design).",
            "",
        ]
    else:
        lines = [
            "",
            "",
            header,
            "",
            "ADVISORY findings from a cross-vendor Codex review, run BEFORE execution to catch semantic",
            "gaps the deterministic brief-check cannot see (a guard the mentor may have silently omitted).",
            "These are NOT execution steps and NOT part of the contract. The mentor dispositions each",
            "finding (采纳 -> fold into the brief above and re-run; or 一行驳回). Apprentice: execute ONLY",
            "the brief above; treat this section as context, not instructions.",
            "",
            body,
            "",
        ]
    return "\n".join(lines)


def advisory_record(run_id: str, *, status: str, findings: int, detail: str) -> str:
    """The authoritative advisory artifact (brief-advisory.md). Its metric is logged
    SEPARATELY from the apprentice correction-rate series (condition 5)."""
    return "\n".join(
        [
            "# Cross-Vendor Brief Advisory (ml-v2 BUILD-B.2)",
            "",
            f"- run_id: {run_id}",
            f"- status: {status}",
            f"- findings_count: {findings}",
            "- metric: cross-vendor-advisory (SEPARATE from the apprentice correction-rate series -- condition 5)",
            "- advisory: non-blocking; the mentor dispositions each finding (采纳 / 一行驳回)",
            "",
            "## Detail",
            "",
            detail,
            "",
        ]
    )


def build_review_prompt(
    brief: str,
    apprentice_log: str,
    apprentice_verification_summary: str,
    gate_blast: str,
    gate_runtime: str,
    diff: str,
    verification_results: str | None = None,
) -> str:
    template = read_text(PACKAGE_ROOT / "mentor-review-template.md")
    # When the harness has run the focused/regression suites on the edited tree
    # before this review, their results are authoritative. Deferring execution to
    # the harness is the correct protocol in that regime, so a "verification
    # missing" finding on the apprentice's deferred summary would be a false
    # block. These two inserts are empty strings when no results are supplied, so
    # the prompt is byte-identical to the legacy (apprentice-self-report) regime.
    if verification_results is not None:
        authoritative_rule = (
            "\n- AUTHORITATIVE VERIFICATION: the harness ran the focused and"
            " regression suites on the edited tree; their results appear under"
            " \"Post-edit verification results\" below and are the SOURCE OF TRUTH"
            " for whether tests pass. Deferring execution to the harness is the"
            " correct protocol here and is NOT itself a finding. Judge verification"
            " by those results: if any is FAIL or COULD-NOT-RUN, that is a blocking"
            " finding; if all PASS, do not raise a 'verification missing' finding."
        )
        authoritative_section = (
            "\n\nPost-edit verification results (harness-run, AUTHORITATIVE):\n"
            + verification_results
        )
    else:
        authoritative_rule = ""
        authoritative_section = ""
    return f"""Review this Mentor Loop run using the template below.

Rules:
- Review ONLY the Mentor Brief, apprentice execution log, git diff/status, and gate outputs below.
- Read the apprentice verification summary before writing the verdict; if it says verification is missing or inconclusive, treat that as a review finding.{authoritative_rule}
- Do not edit files. Do not run fix commands. This review pass runs read-only.
- Return Approved / Needs fixes / Stop and re-plan.
- If a reusable mistake appeared, fill Lesson Candidate with Trigger, Mistake, Rule for next time, and Suggested destination.
- If no reusable lesson exists, write "None" for the lesson candidate fields.

Template:
{template}

Mentor Brief:
{brief}

Apprentice execution log:
{apprentice_log}

Apprentice verification summary:
{apprentice_verification_summary}{authoritative_section}

Gate output: blast radius:
{gate_blast}

Gate output: runtime floor:
{gate_runtime}

Diff and status:
{diff}
"""


def invalid_verification_summary(detail: str) -> str:
    return f"overall_status: COULD-NOT-RUN\nstatus: COULD-NOT-RUN (invalid verification spec: {detail})"


def validate_verification_spec(spec: object) -> tuple[list[tuple[str, str, list[str]]], str | None]:
    """Validate the complete spec before any command can execute."""
    if not isinstance(spec, dict):
        return [], "root must be an object"
    normalized: list[tuple[str, str, list[str]]] = []
    for key in ("focused", "regression"):
        section = spec.get(key, [])
        if not isinstance(section, list):
            return [], f"{key} must be an array"
        for index, check in enumerate(section):
            if not isinstance(check, dict):
                return [], f"{key}[{index}] must be an object"
            name = check.get("name", "unnamed")
            if not isinstance(name, str):
                return [], f"{key}[{index}].name must be a string"
            command = check.get("command")
            if (
                not isinstance(command, list)
                or not command
                or not all(isinstance(part, str) and part for part in command)
            ):
                return [], f"{key}[{index}].command must be a non-empty string array"
            normalized.append((key, name or "unnamed", command))
    return normalized, None


def run_review_verification(repo: Path, verification_path: Path | None) -> str | None:
    """Run the task's focused+regression verification on the host so the review
    consumes REAL results (the codex sandbox cannot run python, but this engine
    runs on the host and can).

    Returns a PASS/FAIL/COULD-NOT-RUN summary string, or None when no
    verification spec is supplied (the review then falls back to the apprentice
    self-report, i.e. legacy behavior is unchanged). Fail-closed: a command that
    cannot run is reported COULD-NOT-RUN, never silently treated as passing.
    """
    if verification_path is None:
        return None
    verification_path = Path(verification_path)
    if not verification_path.exists():
        return "overall_status: COULD-NOT-RUN\nstatus: COULD-NOT-RUN (verification spec not found)"
    try:
        spec = json.loads(verification_path.read_text(encoding="utf-8-sig"))
    except Exception as error:  # malformed spec => fail closed
        return f"overall_status: COULD-NOT-RUN\nstatus: COULD-NOT-RUN (unreadable verification spec: {error})"
    checks, validation_error = validate_verification_spec(spec)
    if validation_error is not None:
        return invalid_verification_summary(validation_error)
    sections: list[str] = []
    statuses: list[str] = []
    for key, name, command in checks:
        try:
            code, output = run_local(resolve_command_head(command), repo)
            status = "PASS" if code == 0 else "FAIL"
        except FileNotFoundError as error:
            code, output, status = 127, str(error), "COULD-NOT-RUN"
        except Exception as error:  # any runner error => fail closed
            code, output, status = -1, str(error), "COULD-NOT-RUN"
        statuses.append(status)
        tail = output[-1000:] if output else ""
        sections.append(f"## {key}: {name}\nstatus: {status}\nexit_code: {code}\n\n{tail}")
    if not sections:
        return "overall_status: COULD-NOT-RUN\nstatus: COULD-NOT-RUN (no verification commands defined)"
    overall = "COULD-NOT-RUN" if "COULD-NOT-RUN" in statuses else "FAIL" if "FAIL" in statuses else "PASS"
    return f"overall_status: {overall}\n\n" + "\n\n".join(sections)


def write_dry_run_report(run_dir: Path, run_id: str) -> str:
    final = "\n".join(
        [
            "# Mentor Loop Final Report",
            "",
            f"- run_id: {run_id}",
            "- status: dry_run",
            "",
            "## Verification",
            "",
            "(dry run)",
            "",
            "## Gate Results",
            "",
            "(dry run)",
            "",
            "## Changed Files",
            "",
            "(dry run)",
            "",
            "## Review",
            "",
            "(dry run)",
            "",
        ]
    )
    write_text(run_dir / "final-report.md", final)
    return final


def init_run(repo: Path, task: str) -> tuple[str, Path, str]:
    repo = ensure_git_repo(repo)
    ensure_local_exclude(repo, [".mentor-loop/"])
    ensure_clean_worktree(repo)
    run_id = now_run_id(task)
    run_dir = run_dir_for(repo, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_text(run_dir / "task.txt", task)
    active_lessons = load_active_lessons(repo)
    write_text(run_dir / "active-lessons.md", active_lessons)
    precedents = load_precedents(repo)  # ml-v2 BUILD-C, C-2
    write_text(run_dir / "precedents.md", precedents)
    write_text(run_dir / "mentor-brief-prompt.md", build_brief_prompt(task, active_lessons, precedents))
    return run_id, run_dir, active_lessons


def stage_init(repo: Path, task: str) -> int:
    run_id, run_dir, active_lessons = init_run(repo, task)
    print(f"run_id: {run_id}")
    print("active_lessons:")
    print(active_lessons)
    print(stage_summary("init", "OK", f"run_id={run_id}; run_dir={run_dir}"))
    return 0


def stage_brief_check(repo: Path, run_id: str) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    brief_path = run_dir / "mentor-brief.md"
    if not brief_path.exists():
        detail = "mentor-brief.md missing"
        write_text(run_dir / "brief-check.txt", stage_summary("brief-check", "BLOCKED", detail) + "\n")
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1

    brief = read_text(brief_path)
    if "STOP" in brief[:1000]:
        detail = "brief contains STOP"
        write_text(run_dir / "brief-check.txt", stage_summary("brief-check", "BLOCKED", detail) + "\n")
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1
    if not brief_has_baseline_output(brief):
        detail = "baseline verification output missing"
        write_text(run_dir / "brief-check.txt", stage_summary("brief-check", "BLOCKED", detail) + "\n")
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1
    try:
        ensure_clean_worktree(repo)
    except RuntimeError as error:
        detail = "Strong brief step changed the worktree before apprentice execution."
        write_text(run_dir / "brief-check.txt", stage_summary("brief-check", "BLOCKED", detail) + "\n\n" + str(error) + "\n")
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1

    honesty = check_brief_honesty(brief)
    if honesty["status"] == "blocked":
        findings = honesty["findings"]
        detail = "brief-honesty gate: " + "; ".join(findings)
        body = (
            stage_summary("brief-check", "BLOCKED", detail)
            + "\n\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n"
        )
        write_text(run_dir / "brief-check.txt", body)
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1
    if honesty["status"] == "escalate":
        inbox = write_architect_inbox(repo, run_dir, run_id, honesty["escalations"])
        # ml-v2 BUILD-C, C-1: auto-assemble the architect consult packet on
        # escalation. Defensive -- packet assembly can never change the BLOCKED
        # result (stage_architect_packet is itself fail-closed; this guard is
        # belt-and-suspenders so a packet error cannot mask the lock).
        try:
            stage_architect_packet(repo, run_id)
        except Exception:
            pass
        guards = ", ".join(esc.get("guard", "") for esc in honesty["escalations"])
        detail = f"escalated to architect (fail-open/unsure guard before apprentice): {guards}"
        body = (
            stage_summary("brief-check", "BLOCKED", detail)
            + "\n\n"
            + f"Routed to architect before apprentice. See {inbox.relative_to(repo).as_posix()}\n"
        )
        write_text(run_dir / "brief-check.txt", body)
        print(stage_summary("brief-check", "BLOCKED", detail))
        return 1

    detail = "brief accepted"
    write_text(run_dir / "brief-check.txt", stage_summary("brief-check", "OK", detail) + "\n")
    print(stage_summary("brief-check", "OK", detail))
    return 0


def stage_brief_review(repo: Path, run_id: str, config: dict[str, object]) -> int:
    """Cross-vendor Codex ADVISORY review of the Mentor Brief (ml-v2 BUILD-B.2).

    Runs AFTER brief-check passes and BEFORE the apprentice. Fills the deterministic
    gate's blind spot (it reads only what the mentor DECLARED): a cross-vendor model
    reading the brief + change intent + blast-radius can flag a guard the mentor
    silently omitted. Findings are appended to the brief as a NON-BINDING appendix the
    mentor dispositions (采纳 / 一行驳回) and recorded in brief-advisory.md.

    Fail-open BY DESIGN and DECLARED (condition 4): when it cannot run -- no
    advisor_command configured, or codex is not executable on this host (the Windows
    sandbox pitfall) -- it records a SKIP and marks the brief "未经跨厂审". It NEVER
    falls back to a same-vendor reviewer (claude -p) and NEVER blocks. The
    deterministic gate stays the reproducible floor; this is a complement, not a
    replacement. Always returns 0 (advisory is non-blocking by contract).
    """
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    brief_path = run_dir / "mentor-brief.md"
    advisory_path = run_dir / "brief-advisory.md"

    def skip(reason: str) -> int:
        write_text(advisory_path, advisory_record(run_id, status="SKIP", findings=0, detail=reason))
        if brief_path.exists():
            append_text(brief_path, advisory_appendix("", skipped=True, reason=reason))
        print(stage_summary("brief-review", "SKIP", reason))
        return 0

    if not brief_path.exists():
        return skip("mentor-brief.md missing")
    advisor_command = config.get("advisor_command")
    if not advisor_command:
        return skip("no advisor_command configured (cross-vendor review disabled)")

    brief = read_text(brief_path)
    task_path = run_dir / "task.txt"
    task = read_text(task_path).strip() if task_path.exists() else "(change intent unavailable)"
    prompt = build_brief_review_prompt(task, brief, extract_blast_radius(brief))
    write_text(run_dir / "brief-review-prompt.md", prompt)

    raw_path = run_dir / "brief-review-raw.md"
    code = run_codex(
        advisor_command, repo, raw_path, prompt, run_dir / "brief-review-codex.log", sandbox="read-only"
    )
    raw = read_text(raw_path).strip() if raw_path.exists() else ""
    if code != 0 or "result: ENV_FAILURE" in raw:
        return skip(f"cross-vendor codex could not run (exit={code}); no same-vendor fallback by design")

    findings = count_advisory_findings(raw)
    write_text(advisory_path, advisory_record(run_id, status="OK", findings=findings, detail=raw))
    append_text(brief_path, advisory_appendix(raw, skipped=False))
    print(
        stage_summary(
            "brief-review",
            "OK",
            f"cross-vendor advisory captured; findings={findings} (advisory, non-blocking; metric logged separately)",
        )
    )
    return 0


def stage_apprentice(repo: Path, run_id: str, config: dict[str, object]) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    brief_path = run_dir / "mentor-brief.md"
    if not brief_path.exists():
        print(stage_summary("apprentice", "BLOCKED", "mentor-brief.md missing"))
        return 1
    brief = read_text(brief_path)
    active_lessons = read_text(run_dir / "active-lessons.md") if (run_dir / "active-lessons.md").exists() else load_active_lessons(repo)
    write_text(run_dir / "active-lessons.md", active_lessons)
    apprentice_prompt = build_apprentice_prompt(brief, active_lessons)
    write_text(run_dir / "apprentice-prompt.md", apprentice_prompt)
    code = run_codex(
        config["apprentice_command"],
        repo,
        run_dir / "apprentice-log.md",
        apprentice_prompt,
        run_dir / "apprentice-codex.log",
    )
    write_text(run_dir / "apprentice-exit-code.txt", f"exit_code: {code}\n")
    result = "OK" if code == 0 else "FAILED"
    print(stage_summary("apprentice", result, f"exit_code={code}"))
    return code


def stage_gates(repo: Path, run_id: str, config: dict[str, object]) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    python_bin = config["python"]
    blast_code = run_gate(
        [python_bin, str(PACKAGE_ROOT / "gates" / "blast-radius-check.py"), "--brief", str(run_dir / "mentor-brief.md")],
        repo,
        run_dir / "gate-blast-radius.txt",
    )
    runtime_code = run_gate(
        [python_bin, str(PACKAGE_ROOT / "gates" / "runtime-floor-check.py")],
        repo,
        run_dir / "gate-runtime-floor.txt",
    )
    detail = f"blast-radius={blast_code}; runtime-floor={runtime_code}"
    result = "OK" if blast_code == 0 and runtime_code == 0 else "BLOCKED"
    print(stage_summary("gates", result, detail))
    return 0 if result == "OK" else 1


def stage_snapshot(repo: Path, run_id: str) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    status, status_diagnostics = read_git_porcelain_status(repo)
    diff = render_git_snapshot(repo, status, status_diagnostics)
    write_text(run_dir / "diff-and-status.txt", diff)
    apprentice_log = read_text(run_dir / "apprentice-log.md") if (run_dir / "apprentice-log.md").exists() else ""
    apprentice_verification_summary = summarize_apprentice_verification(apprentice_log)
    write_text(run_dir / "apprentice-verification-summary.md", apprentice_verification_summary + "\n")
    changed = len([line for line in status.splitlines() if line.strip()])
    print(stage_summary("snapshot", "OK", f"changed_entries={changed}; apprentice_verification_summary=written"))
    return 0


def stage_capture_lesson(repo: Path, run_id: str) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    review_path = run_dir / "review.md"
    if not review_path.exists():
        print(stage_summary("capture-lesson", "BLOCKED", "review.md missing"))
        return 1
    lesson_status = capture_lesson(repo, run_id, run_dir, read_text(review_path))
    result = "OK" if lesson_status.startswith("Captured") else "NOOP"
    print(stage_summary("capture-lesson", result, lesson_status))
    return 0


def assemble_final_report(repo: Path, run_id: str) -> str:
    run_dir = run_dir_for(repo, run_id)
    gate_blast = read_text(run_dir / "gate-blast-radius.txt") if (run_dir / "gate-blast-radius.txt").exists() else ""
    gate_runtime = read_text(run_dir / "gate-runtime-floor.txt") if (run_dir / "gate-runtime-floor.txt").exists() else ""
    review = read_text(run_dir / "review.md") if (run_dir / "review.md").exists() else ""
    summary_path = run_dir / "apprentice-verification-summary.md"
    if summary_path.exists():
        apprentice_verification_summary = read_text(summary_path).strip()
    else:
        apprentice_log = read_text(run_dir / "apprentice-log.md") if (run_dir / "apprentice-log.md").exists() else ""
        apprentice_verification_summary = summarize_apprentice_verification(apprentice_log)
    lesson_status = "Captured one reusable lesson." if (run_dir / "lesson.md").exists() else "No reusable lesson captured."
    status_text = read_git_porcelain_status(repo)[0].strip()

    return "\n".join(
        [
            "# Mentor Loop Final Report",
            "",
            f"- run_id: {run_id}",
            f"- apprentice_exit_code: {parse_exit_code(run_dir / 'apprentice-exit-code.txt')}",
            f"- blast_radius_gate_exit_code: {parse_exit_code(run_dir / 'gate-blast-radius.txt')}",
            f"- runtime_floor_gate_exit_code: {parse_exit_code(run_dir / 'gate-runtime-floor.txt')}",
            "- review_exit_code: session-written",
            f"- blast_radius_gate_result: {summarize_gate(gate_blast)}",
            f"- runtime_floor_gate_result: {summarize_gate(gate_runtime)}",
            f"- review_verdict: {summarize_review(review)}",
            f"- apprentice_verification_summary: {apprentice_verification_summary}",
            f"- lessons: {lesson_status}",
            "",
            "## Verification",
            "",
            f"Apprentice verification summary: {apprentice_verification_summary}",
            "",
            "See `mentor-brief.md` for baseline/focused/regression commands and `apprentice-log.md` for full apprentice verification output.",
            "",
            "## Gate Results",
            "",
            f"- blast-radius: {summarize_gate(gate_blast)}",
            f"- runtime-floor: {summarize_gate(gate_runtime)}",
            "",
            "## Changed Files",
            "",
            "```text",
            status_text,
            "```",
            "",
            "## Artifacts",
            "",
            "- mentor-brief.md",
            "- active-lessons.md",
            "- apprentice-log.md",
            "- apprentice-verification-summary.md",
            "- gate-blast-radius.txt",
            "- gate-runtime-floor.txt",
            "- diff-and-status.txt",
            "- review.md",
            "- lesson.md, if captured",
            "",
            "## Review",
            "",
            review.strip(),
            "",
        ]
    )


def stage_report(repo: Path, run_id: str) -> int:
    repo = ensure_git_repo(repo)
    run_dir = run_dir_for(repo, run_id)
    required = [
        "mentor-brief.md",
        "apprentice-log.md",
        "gate-blast-radius.txt",
        "gate-runtime-floor.txt",
        "diff-and-status.txt",
        "apprentice-verification-summary.md",
        "review.md",
    ]
    missing = [name for name in required if not (run_dir / name).exists()]
    if missing:
        final = "\n".join(
            [
                "# Mentor Loop Final Report",
                "",
                f"- run_id: {run_id}",
                "- status: incomplete",
                "- missing_artifacts: " + ", ".join(missing),
                "",
            ]
        )
        write_text(run_dir / "final-report.md", final)
        print(final)
        print(stage_summary("report", "INCOMPLETE", "missing " + ", ".join(missing)))
        return 1
    final = assemble_final_report(repo, run_id)
    write_text(run_dir / "final-report.md", final)
    print(final)
    print(stage_summary("report", "OK", f"final-report.md written for {run_id}"))
    return 0


# --- ml-v2 BUILD-D: failure-attribution architect loop (.mentor-loop/spec-brief-review-loop.md) ---
# C escalates on the PRE-exec brief-honesty gate (fail-open guards). D escalates on POST-exec
# REPEATED failure of the SAME TARGET: repeated failure is often "the task was defined wrong,"
# not "the apprentice is weak," so D audits the mentor's DIRECTION (goal / assumptions / scope) and
# NEVER writes code. Constitution §1 五原则⑤; PLAYBOOK 复核回路细则. trigger_source: failure_loop.
# Architect direction is advisory and never auto-applied. The D control gate is fail-closed:
# PARK, unknown output, or diagnostics may tighten PASS to PARK/BLOCKED, never failure to success.

FAILURE_LOOP_STATE_REL = ".mentor-loop/state/brief-review-loop.json"
FAILURE_REVIEW_METRIC_REL = ".mentor-loop/state/failure-review-metric.jsonl"
FAILURE_TRIGGER_N = 2  # PLAYBOOK-pinned threshold: same-target failures, NON-consecutive OK (Codex P2).
ARCHITECT_VERDICTS = (
    "revised_brief",
    "narrowed_task",
    "route_change",
    "keep_brief_retry",
    "brief_sound_capability_gap",
    "park_report",
)
_CODE_FENCE_RE = re.compile(r"```")
_DIFF_MARKER_RE = re.compile(r"^(?:---[ \t]\S|\+\+\+[ \t]\S|@@[ \t])", re.MULTILINE)
# file:line edits: a filename with a code/config/markup extension followed by :line. The leading `\b`
# matches with OR without a path prefix (`app.css:12` and `src/app.css:12` both hit). URL/domain ports
# (`api.example.com:443`, `https://api.example.com:443`) are NOT flagged because a TLD is not in the
# whitelist (CV P3 rounds 1-3). Residual: an exotic non-whitelisted extension slips (bounded: the
# architect is instructed no-code and this path is advisory/opt-in).
_FILE_LINE_RE = re.compile(
    r"\b[\w-]+\.(?:py|js|ts|tsx|jsx|mjs|cjs|json|md|txt|java|go|rs|c|cc|cpp|h|hpp|cs|kt|swift|rb|php|"
    r"sh|ps1|bat|css|scss|sass|less|html?|xml|sql|vue|svelte|ya?ml|toml|cfg|ini|lua|pl|r)\b:\d+"
)


def compute_target_id(task: str) -> str:
    """Stable target identity (spec ⟢⟡ / Codex P1): derived from the change intent (the task
    string) ONLY -- never the mutable, mentor-generated brief goal -- so a brief revision does NOT
    wash the failure count. A plain retry of the same task re-derives the same id (counters
    accumulate); a narrowed / re-routed successor inherits it via ``run --target <id>``.
    v0 LIMIT (cross-vendor CV P1-c): the spec's 'task_id + blast-radius' inputs are not available
    before a run, so identity is the normalized task alone -- two unrelated tasks with identical
    wording would share counters and a fail-closed audit quota (disambiguate with an explicit --target)."""
    normalized = " ".join((task or "").split()).strip().lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def _new_target_entry(target_id: str, task: str) -> dict[str, object]:
    return {
        "target_id": target_id,
        "task": task,
        "attempts": 0,
        "failures": 0,
        "verification_failures": 0,
        "brief_revision_count": 0,
        "audited": False,
        "history": [],
        "last": {},
    }


def load_loop_state(repo: Path) -> dict[str, object]:
    path = repo / FAILURE_LOOP_STATE_REL
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        # Unreadable state must never crash a run. Empty => no false trigger (fail-safe, not fail-open).
        return {}


def save_loop_state(repo: Path, state: dict[str, object]) -> None:
    path = repo / FAILURE_LOOP_STATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def loop_state_corrupt(repo: Path) -> bool:
    """True iff the state file EXISTS but does not parse to a JSON object (cross-vendor CV P1). A
    MISSING file is NOT corrupt (a legit first run). Callers fail-closed on corruption instead of
    silently resetting the failure count."""
    path = repo / FAILURE_LOOP_STATE_REL
    if not path.exists():
        return False
    try:
        return not isinstance(json.loads(path.read_text(encoding="utf-8-sig")), dict)
    except Exception:
        return True


def _quarantine_corrupt_state(repo: Path) -> Path:
    """Preserve a corrupt state file (rename to *.corrupt) so evidence is never destroyed and the
    failure count is never silently reset. Returns the backup path (best-effort)."""
    path = repo / FAILURE_LOOP_STATE_REL
    backup = path.with_name(path.name + ".corrupt")
    try:
        if backup.exists():
            backup.unlink()
        path.rename(backup)
    except Exception:
        backup = path
    return backup


def _persist_entry(repo: Path, entry: dict[str, object]) -> None:
    state = load_loop_state(repo)
    state[str(entry["target_id"])] = entry
    save_loop_state(repo, state)


def update_loop_state(repo: Path, target_id: str, task: str, signals: dict[str, object]) -> dict[str, object]:
    """Record one attempt's outcome under ``target_id`` (PERSISTED -- the engine is a CLI, so
    in-memory counters die per run, Codex P1). ``signals`` = {run_id, failed, verification_failed,
    brief_blocker, review_reason, brief_revised}. Returns the updated entry."""
    state = load_loop_state(repo)
    raw = state.get(target_id)
    entry = raw if isinstance(raw, dict) else _new_target_entry(target_id, task)
    entry["attempts"] = int(entry.get("attempts", 0)) + 1
    if signals.get("failed"):
        entry["failures"] = int(entry.get("failures", 0)) + 1
    if signals.get("verification_failed"):
        entry["verification_failures"] = int(entry.get("verification_failures", 0)) + 1
    if signals.get("brief_revised"):
        entry["brief_revision_count"] = int(entry.get("brief_revision_count", 0)) + 1
    record = {
        "run_id": signals.get("run_id"),
        "failed": bool(signals.get("failed")),
        "verification_failed": bool(signals.get("verification_failed")),
        "brief_blocker": bool(signals.get("brief_blocker")),
        "brief_blocker_reason": signals.get("brief_blocker_reason") or "",
        "review_reason": signals.get("review_reason"),
    }
    entry["history"] = (list(entry.get("history", [])) + [record])[-20:]
    entry["last"] = record
    state[target_id] = entry
    save_loop_state(repo, state)
    return entry


def failure_triggers(entry: dict[str, object]) -> list[str]:
    """Which repeated-failure triggers fired for this target (pure). All same-target; thresholds
    are NON-consecutive accumulations (Codex P2). N is PLAYBOOK-pinned (FAILURE_TRIGGER_N)."""
    fired: list[str] = []
    if int(entry.get("failures", 0)) >= FAILURE_TRIGGER_N:
        fired.append(f"failures>={FAILURE_TRIGGER_N}")
    if int(entry.get("verification_failures", 0)) >= FAILURE_TRIGGER_N:
        fired.append(f"verification_failures>={FAILURE_TRIGGER_N}")
    last = entry.get("last") or {}
    if isinstance(last, dict):
        if last.get("brief_blocker"):
            fired.append("brief_blocker")
        if last.get("review_reason") == "direction_unclear":
            fired.append("review:direction_unclear")
        if int(entry.get("brief_revision_count", 0)) >= 1 and last.get("failed"):
            fired.append("revised_brief_still_failing")
    return fired


def classify_review_reason(review: str) -> str:
    """Map a review verdict to a reason-code (pure), keyed on the review's own vocabulary
    (Approved / Needs fixes / Stop and re-plan). 'Stop and re-plan' => direction_unclear."""
    outcome = parse_review_outcome(review)
    if outcome == "stop_and_replan":
        return "direction_unclear"
    if outcome == "needs_fixes":
        return "needs_fixes"
    if outcome == "approved":
        return "approved"
    return "other"


def detect_brief_blocker(apprentice_log: str) -> tuple[bool, str]:
    """Structured brief_blocker detection (cross-vendor CV P2): the apprentice signals an unworkable
    brief with a LINE that starts with ``brief_blocker: <reason>`` -- NOT a substring anywhere, so
    'No brief_blocker: it was clear' does NOT false-trigger a park. Returns (found, reason)."""
    for line in (apprentice_log or "").splitlines():
        stripped = line.strip().lstrip("-*#>").strip()
        if stripped.lower().startswith("brief_blocker:"):
            return True, stripped.split(":", 1)[1].strip()
    return False, ""


def lint_architect_output(text: str) -> list[str]:
    """No-code enforcement (spec Fable red-flag b + Codex P2). Detect EXPLICIT code in the
    architect's DIRECTION verdict: fenced blocks, unified-diff markers, file:line edits. A hit
    means the verdict tried to WRITE code -- the caller REJECTS + parks the whole verdict, NEVER
    strips (stripping could launder a code verdict into an 'executable' one; DEC-003)."""
    findings: list[str] = []
    if _CODE_FENCE_RE.search(text or ""):
        findings.append("fenced_code_block")
    if _DIFF_MARKER_RE.search(text or ""):
        findings.append("unified_diff_marker")
    if _FILE_LINE_RE.search(text or ""):
        findings.append("file_line_edit")
    return findings


def parse_architect_verdict(text: str) -> str | None:
    """Extract the single legal verdict enum value the architect chose (pure). Scans EVERY
    ``verdict: <enum>`` line; returns the enum only if exactly ONE distinct legal verdict is present.
    Zero legal verdicts, or multiple DISTINCT ones (ambiguous schema), returns None => park for a
    clean re-verdict (cross-vendor CV P2). Case-insensitive; tolerant of a leading list marker."""
    found: list[str] = []
    for line in (text or "").splitlines():
        low = line.strip().lstrip("-*").strip().lower()
        if low.startswith("verdict:"):
            value = low.split(":", 1)[1].strip()
            token = (value.split()[0] if value else "").strip("`.,")
            if token in ARCHITECT_VERDICTS:
                found.append(token)
    distinct = set(found)
    return found[0] if len(distinct) == 1 else None


def _indent(text: str) -> str:
    return "\n".join("    " + line for line in (text or "").splitlines())


def _append_metric(path: Path, run_id: str, target_id: str, fired: list[str], outcome: str) -> None:
    """Append one line to the SEPARATE failure-review metric series (like the B.2 CV log; NOT the
    apprentice correction-rate). Keeps 'brief = top defect source' falsifiable, not presupposed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": run_id,
        "target_id": target_id,
        "trigger_source": "failure_loop",
        "triggers": fired,
        "outcome": outcome,
    }
    append_text(path, json.dumps(record, ensure_ascii=False) + "\n")


def build_failure_packet(
    target_id: str,
    entry: dict[str, object],
    task: str,
    brief: str,
    blast_radius: str,
    precedents: str,
) -> str:
    """Assemble the failure-attribution architect packet (pure; sibling of build_architect_packet).
    Carries the repeated-failure history + the CURRENT mentor brief (the object being audited, CV P2)
    + the 5 DIRECTION questions + the CONSTRAINED verdict enum + the no-code rule. The architect
    audits DIRECTION; it never writes code."""
    hist = entry.get("history") or []
    hist_lines = "\n".join(
        f"- attempt {i + 1}: run={h.get('run_id', '?')} failed={h.get('failed')} "
        f"verification_failed={h.get('verification_failed')} review_reason={h.get('review_reason')} "
        f"brief_blocker={h.get('brief_blocker')}"
        + (f" reason={h.get('brief_blocker_reason')!r}" if h.get("brief_blocker_reason") else "")
        for i, h in enumerate(hist)
        if isinstance(h, dict)
    ) or "- (no per-attempt history recorded)"
    verdict_enum = "\n".join(f"  - `{v}`" for v in ARCHITECT_VERDICTS)
    return "\n".join(
        [
            f"# Failure-review packet — target {target_id} (ml-v2 BUILD-D, trigger_source: failure_loop)",
            "",
            "- assembled_by: maybe_run_failure_review (deterministic; POST-execution)",
            "- rule: FAIL-CLOSED. You AUDIT THE MENTOR'S DIRECTION (goal / assumptions / scope).",
            "  You do NOT solve the bug and you do NOT write code. A verdict containing code, a diff,",
            "  or a file:line edit is REJECTED WHOLE (never stripped) and the loop parks for the owner.",
            "",
            "## 1. Why you were called",
            f"- The same target has repeatedly FAILED (attempts={entry.get('attempts')}, "
            f"failures={entry.get('failures')}, verification_failures={entry.get('verification_failures')}).",
            '- Repeated failure is often "the task was defined wrong," not "the apprentice is weak."',
            "",
            "## 2. Failure history",
            hist_lines,
            "",
            "## 3. The change intent (task) the mentor is briefing against",
            "```",
            (task or "").strip(),
            "```",
            "",
            "## 3b. The current mentor brief (THIS is what you audit — goal / assumptions / scope)",
            (brief or "").strip() or "(no brief artifact)",
            "",
            "## 4. Blast radius (from the run's gate artifact)",
            (blast_radius or "").strip() or "(none)",
            "",
            "## 5. Applicable precedents / guardrails (.mentor-loop/decisions.md)",
            (precedents or "").strip() or "(none)",
            "",
            "## 6. The five DIRECTION questions",
            "1. Is the mentor's GOAL definition right?",
            "2. Is the BLAST RADIUS missing anything?",
            "3. Are the ASSUMPTIONS wrong?",
            "4. Is what the apprentice was asked TOO BIG / TOO ABSTRACT?",
            "5. Continue / break smaller / change route / park & ask owner?",
            "",
            "## 7. Your verdict — CONSTRAINED (no patch field)",
            "Answer with exactly one line `verdict: <one of>` from this enum, then a short rationale:",
            verdict_enum,
            "",
            "  - `revised_brief` — a reworked brief in WORDS only; it RE-FLOWS through the honesty gate.",
            "  - `brief_sound_capability_gap` — the brief has NO defect; the gap is execution capability",
            "    (recommend upgrading the apprentice model / changing channel / parking).",
            "The mentor RECORDS your verdict; it is NEVER auto-applied. Do not write code.",
            "",
        ]
    )


def maybe_run_failure_review(
    repo: Path,
    run_dir: Path,
    run_id: str,
    task: str,
    target_id: str,
    signals: dict[str, object],
    config: dict[str, object] | None,
) -> str:
    """BUILD-D orchestration. Architect direction is advisory and NEVER auto-applied, while the
    control gate is fail-closed and may tighten PASS to PARK/BLOCKED. Records this attempt under
    ``target_id``, checks the repeated-failure triggers, and on a FRESH
    (un-audited) trigger routes a FAILURE packet to a CONSTRAINED architect brief-review. Fail-closed:
    no architect_command, a code-laundering verdict, an illegal verdict, or a re-failing already-audited
    target => PARK & ask owner. One audit attempt per target (owner-only reset). Returns a status."""
    metric_path = repo / FAILURE_REVIEW_METRIC_REL

    # P1 (cross-vendor CV): a corrupt/unreadable state file must NOT silently reset the failure count
    # (that would launder it + violate owner-only reset). Preserve the evidence and PARK for the owner.
    if loop_state_corrupt(repo):
        backup = _quarantine_corrupt_state(repo)
        reason = f"loop state corrupt/unreadable; preserved at {backup.name}; owner must inspect (counters NOT auto-reset)"
        write_text(
            run_dir / "failure-review-park.md",
            f"# BUILD-D failure-review PARK — {run_id} (target {target_id})\n"
            f"- trigger_source: failure_loop\n- reason: {reason}\n",
        )
        _append_metric(metric_path, run_id, target_id, ["state_corrupt"], f"park:{reason}")
        return stage_summary("failure-review", "PARK", reason)

    entry = update_loop_state(repo, target_id, task, signals)
    fired = failure_triggers(entry)
    # P1 (cross-vendor CV): triggers 3/4 (brief_blocker, review:direction_unclear) are THIS-run signals
    # and fire regardless of exit code; the accumulation triggers only escalate when THIS run actually
    # failed, so a later PASSING run can't re-open an accumulated-failure trigger.
    if not signals.get("failed"):
        fired = [t for t in fired if t in ("brief_blocker", "review:direction_unclear")]
    if not fired:
        return stage_summary("failure-review", "OK", f"no active trigger (target {target_id})")

    def _park(reason: str, verdict_text: str = "") -> str:
        lines = [
            f"# BUILD-D failure-review PARK — {run_id} (target {target_id})",
            "- trigger_source: failure_loop",
            f"- reason: {reason}",
            f"- triggers: {', '.join(fired)}",
            f"- attempts={entry['attempts']} failures={entry['failures']} "
            f"verification_failures={entry['verification_failures']}",
        ]
        if verdict_text:
            lines += ["- architect verdict (REJECTED / for owner context, verbatim):", _indent(verdict_text)]
            # Persist even a REJECTED/ambiguous verdict so a later already-audited re-fail can attach it (CV P2).
            entry["verdict_excerpt"] = verdict_text[:1000]
            _persist_entry(repo, entry)
        write_text(run_dir / "failure-review-park.md", "\n".join(lines) + "\n")
        _append_metric(metric_path, run_id, target_id, fired, f"park:{reason}")
        return stage_summary("failure-review", "PARK", reason)

    # Cost guard: at most ONE audit per target; a re-failing audited target -> owner (fail-closed),
    # WITH the prior architect verdict attached for owner context (cross-vendor CV P2).
    if entry.get("audited"):
        return _park(
            "target already audited once and still failing -> owner ruling needed",
            str(entry.get("verdict_excerpt", "")),
        )

    # This IS the one audit attempt for this target; mark it now, regardless of the outcome below.
    entry["audited"] = True
    _persist_entry(repo, entry)

    architect_command = config.get("architect_command") if config else None
    if not architect_command:
        return _park("no architect_command configured (fail-closed: absent architect => park)")

    blast_radius = (
        read_text(run_dir / "gate-blast-radius.txt")
        if (run_dir / "gate-blast-radius.txt").exists()
        else "(no blast-radius artifact)"
    )
    brief = read_text(run_dir / "mentor-brief.md") if (run_dir / "mentor-brief.md").exists() else "(no brief artifact)"
    packet = build_failure_packet(target_id, entry, task, brief, blast_radius, load_precedents(repo))
    write_text(run_dir / "failure-review-packet.md", packet)
    draft_path = run_dir / "failure-review-verdict-draft.md"
    code = run_codex(
        architect_command, repo, draft_path, packet, run_dir / "failure-review-codex.log", sandbox="read-only"
    )
    if code != 0 or not draft_path.exists():
        return _park(f"architect_command could not run (exit={code})")
    verdict_text = read_text(draft_path)
    lint = lint_architect_output(verdict_text)
    if lint:
        return _park(f"architect verdict contained code ({', '.join(lint)}); REJECTED not stripped (DEC-003)", verdict_text)
    verdict = parse_architect_verdict(verdict_text)
    if verdict is None:
        return _park("architect verdict names no legal enum value; clean re-verdict needed", verdict_text)
    write_text(run_dir / "failure-review-verdict.md", verdict_text)
    entry["verdict"] = verdict
    entry["verdict_excerpt"] = verdict_text[:1000]  # persisted so an already-audited re-fail can attach it (CV P2)
    _persist_entry(repo, entry)
    _append_metric(metric_path, run_id, target_id, fired, f"verdict:{verdict}")
    return stage_summary(
        "failure-review", "OK", f"architect direction verdict={verdict}; recorded, NEVER auto-applied (target {target_id})"
    )


def run_full(repo: Path, task: str, config: dict[str, object], dry_run: bool = False, verification_path: str | None = None, target: str | None = None) -> int:
    run_id = "unknown"
    run_dir = repo / ".mentor-loop" / "runs" / run_id
    try:
        run_id, run_dir, _active_lessons = init_run(repo, task)
        target_id = target or compute_target_id(task)  # BUILD-D: stable per-target identity
        if dry_run:
            write_text(run_dir / "mentor-brief.md", "(dry run: brief not generated)\n")
            final = write_dry_run_report(run_dir, run_id)
            print(final)
            return 0

        brief_code = run_codex(
            config["strong_command"],
            ensure_git_repo(repo),
            run_dir / "mentor-brief.md",
            read_text(run_dir / "mentor-brief-prompt.md"),
            run_dir / "mentor-brief-codex.log",
        )
        brief = read_text(run_dir / "mentor-brief.md") if (run_dir / "mentor-brief.md").exists() else ""
        if brief_code != 0 or not brief.strip():
            raise RuntimeError("strong brief generation failed")
        if "STOP" in brief[:1000]:
            final = f"# Mentor Loop Final Report\n\nrun_id: {run_id}\nstatus: stopped_during_brief\n"
            write_text(run_dir / "final-report.md", final)
            print(final)
            return 1
        if stage_brief_check(repo, run_id) != 0:
            detail = read_text(run_dir / "brief-check.txt") if (run_dir / "brief-check.txt").exists() else "brief-check failed"
            final = "\n".join(
                [
                    "# Mentor Loop Final Report",
                    "",
                    f"- run_id: {run_id}",
                    "- status: stopped_before_apprentice",
                    "- reason: Mentor Brief validation failed.",
                    "",
                    "## Details",
                    "",
                    detail,
                    "",
                ]
            )
            write_text(run_dir / "final-report.md", final)
            print(final)
            return 1

        # ml-v2 BUILD-B.2: cross-vendor Codex ADVISORY brief-review, AFTER brief-check
        # passes and BEFORE the apprentice. Non-blocking by contract (always returns 0);
        # SKIPs cleanly when no advisor_command is configured (shipped default).
        stage_brief_review(repo, run_id, config)

        apprentice_code = stage_apprentice(repo, run_id, config)
        gates_code = stage_gates(repo, run_id, config)
        gate_blast = read_text(run_dir / "gate-blast-radius.txt")
        gate_runtime = read_text(run_dir / "gate-runtime-floor.txt")

        stage_snapshot(repo, run_id)
        diff = read_text(run_dir / "diff-and-status.txt")
        apprentice_log = read_text(run_dir / "apprentice-log.md")
        apprentice_verification_summary = read_text(run_dir / "apprentice-verification-summary.md")
        # Run the focused/regression suites on the host BEFORE the review so the
        # review consumes real results instead of the apprentice's deferred
        # summary. No-op (None) when no spec is supplied => legacy behavior.
        verification_results = run_review_verification(
            repo, Path(verification_path) if verification_path else None
        )
        if verification_results is not None:
            write_text(run_dir / "review-verification-results.md", verification_results + "\n")
        review_prompt = build_review_prompt(
            brief,
            apprentice_log,
            apprentice_verification_summary,
            gate_blast,
            gate_runtime,
            diff,
            verification_results,
        )
        write_text(run_dir / "review-prompt.md", review_prompt)
        review_code = run_codex(
            config["strong_command"],
            repo,
            run_dir / "review.md",
            review_prompt,
            run_dir / "review-codex.log",
            sandbox="read-only",
        )
        review = read_text(run_dir / "review.md") if (run_dir / "review.md").exists() else ""
        write_text(run_dir / "review-exit-code.txt", f"exit_code: {review_code}\n")
        capture_lesson(repo, run_id, run_dir, review)
        review_outcome = parse_review_outcome(review)
        verification_outcome = verification_summary_outcome(verification_results)
        block_reasons: list[str] = []
        if apprentice_code != 0:
            block_reasons.append("apprentice_process")
        if gates_code != 0:
            block_reasons.append("deterministic_gates")
        if review_code != 0:
            block_reasons.append("review_process")
        if review_outcome != "approved":
            block_reasons.append(f"review_{review_outcome or 'invalid'}")
        if verification_outcome not in {"pass", "not_configured"}:
            block_reasons.append(f"verification_{verification_outcome}")
        result = 1 if block_reasons else 0
        # ml-v2 BUILD-D: post-exec failure-attribution may only preserve or
        # tighten the run result.  PARK, malformed output, or a diagnostic
        # failure is a machine-visible non-success.
        failure_review = ""
        failure_review_outcome = "ERROR"
        try:
            brief_blocked, brief_blocker_reason = detect_brief_blocker(apprentice_log)
            signals = {
                "run_id": run_id,
                "failed": result != 0,
                "verification_failed": verification_outcome == "fail",
                "brief_blocker": brief_blocked,
                "brief_blocker_reason": brief_blocker_reason,
                "review_reason": classify_review_reason(review),
                # v0 LIMIT (CV P2-b): trigger 5 dormant; "revised brief still fails" is subsumed by
                # the audited-target re-fail PARK, so brief_revised is not auto-wired in v0.
                "brief_revised": False,
            }
            failure_review = maybe_run_failure_review(repo, run_dir, run_id, task, target_id, signals, config)
            failure_review_outcome = stage_result(failure_review) or "UNKNOWN"
            if failure_review_outcome == "PARK":
                block_reasons.append("failure_review_park")
                result = 1
            elif failure_review_outcome != "OK":
                block_reasons.append("failure_review_unknown")
                result = 1
        except Exception as d_exc:  # noqa: BLE001 -- diagnostic failure blocks success but still writes the final report
            append_text(run_dir / "failure-review.log", f"failure-review error (run blocked): {d_exc}\n")
            block_reasons.append("failure_review_error")
            result = 1
        run_outcome = "PARK" if failure_review_outcome == "PARK" else "BLOCKED" if result else "PASS"
        metadata = "\n".join(
            [
                f"- review_exit_code: {review_code}",
                f"- semantic_review_outcome: {review_outcome or 'invalid'}",
                f"- host_verification_outcome: {verification_outcome}",
                f"- failure_review_outcome: {failure_review_outcome}",
                f"- run_outcome: {run_outcome}",
                f"- run_block_reasons: {', '.join(block_reasons) if block_reasons else 'none'}",
            ]
        )
        final = assemble_final_report(ensure_git_repo(repo), run_id).replace(
            "- review_exit_code: session-written",
            metadata,
            1,
        )
        write_text(run_dir / "final-report.md", final)
        print(final)
        if failure_review:
            print(failure_review)
        return result
    except Exception as exc:
        final = f"# Mentor Loop Final Report\n\n- run_id: {run_id}\n- status: failed\n- error: {exc}\n"
        write_text(run_dir / "final-report.md", final)
        print(final, file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Mentor Loop stage engine.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the full one-shot pipeline")
    run_parser.add_argument("task", nargs="+")
    run_parser.add_argument("--repo", default=".")
    run_parser.add_argument("--config", default=str(PACKAGE_ROOT / "mentor-loop.config.json"))
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--verification", default=None, help="JSON spec of focused/regression commands to run before the review")
    run_parser.add_argument("--target", default=None, help="BUILD-D: stable target_id to inherit (a narrowed/re-routed successor passes the parent's frozen id; omit to derive from the task)")

    init_parser = subparsers.add_parser("init", help="Create a run directory and prompt artifacts")
    init_parser.add_argument("task", nargs="+")
    init_parser.add_argument("--repo", default=".")

    for name in ("brief-check", "brief-review", "apprentice", "gates", "snapshot", "capture-lesson", "report"):
        stage_parser = subparsers.add_parser(name)
        stage_parser.add_argument("--run", required=True)
        stage_parser.add_argument("--repo", default=".")
        if name in {"apprentice", "gates", "brief-review"}:
            stage_parser.add_argument("--config", default=str(PACKAGE_ROOT / "mentor-loop.config.json"))

    # ml-v2 BUILD-C: architect-loop closure stages.
    packet_parser = subparsers.add_parser("architect-packet", help="Assemble the architect consult packet (C-1)")
    packet_parser.add_argument("--run", required=True)
    packet_parser.add_argument("--repo", default=".")
    packet_parser.add_argument("--config", default=None, help="OPTIONAL config with architect_command to auto-draft a verdict (C-4)")

    ratify_parser = subparsers.add_parser("architect-ratify", help="Record an architect verdict + stamp the guard line (C-3)")
    ratify_parser.add_argument("--run", required=True)
    ratify_parser.add_argument("--repo", default=".")
    ratify_parser.add_argument("--verdict", required=True, help="Path to the architect's verdict file (INPUT)")
    ratify_parser.add_argument("--ref", default=None, help="Reference recorded in the ratify stamp (default: run_id)")
    return parser


def parse_legacy(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full Mentor Loop pipeline.")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--repo", default=".", help="Target repo root")
    parser.add_argument("--config", default=str(PACKAGE_ROOT / "mentor-loop.config.json"))
    parser.add_argument("--dry-run", action="store_true", help="Create prompts/artifacts but do not invoke Codex")
    return parser.parse_args(argv)


def first_positional(argv: list[str]) -> str | None:
    skip_next = False
    options_with_values = {"--repo", "--config", "--run", "--verification", "--target", "--verdict", "--ref", "-C", "-m", "-s", "-o"}
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item in options_with_values:
            skip_next = True
            continue
        if item.startswith("-"):
            continue
        return item
    return None


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    commands = {"run", "init", "brief-check", "brief-review", "apprentice", "gates", "snapshot", "capture-lesson", "report", "architect-packet", "architect-ratify"}
    first = first_positional(sys.argv[1:])
    if first not in commands:
        args = parse_legacy(sys.argv[1:])
        return run_full(Path(args.repo).resolve(), " ".join(args.task), load_config(Path(args.config)), args.dry_run)

    parser = build_parser()
    args = parser.parse_args()
    command = args.command
    repo = Path(args.repo).resolve()
    if command == "run":
        return run_full(repo, " ".join(args.task), load_config(Path(args.config)), args.dry_run, args.verification, args.target)
    if command == "init":
        return stage_init(repo, " ".join(args.task))
    if command == "brief-check":
        return stage_brief_check(repo, args.run)
    if command == "brief-review":
        return stage_brief_review(repo, args.run, load_config(Path(args.config)))
    if command == "apprentice":
        return stage_apprentice(repo, args.run, load_config(Path(args.config)))
    if command == "gates":
        return stage_gates(repo, args.run, load_config(Path(args.config)))
    if command == "snapshot":
        return stage_snapshot(repo, args.run)
    if command == "capture-lesson":
        return stage_capture_lesson(repo, args.run)
    if command == "report":
        return stage_report(repo, args.run)
    if command == "architect-packet":
        config = load_config(Path(args.config)) if args.config else None
        return stage_architect_packet(repo, args.run, config)
    if command == "architect-ratify":
        return stage_architect_ratify(repo, args.run, args.verdict, args.ref)
    parser.error(f"unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
