#!/usr/bin/env python3
"""Join codex session token usage onto eval scorecard rows.

Read-only: scans ~/.codex/sessions rollout files, joins them to scorecard
rows by exact worktree path (session_meta.cwd == scorecard.repo), and emits
per-run token totals plus a per-arm aggregate. Safe to run while a batch is
in progress; runs without a finished token_count event are skipped.

Stage attribution for full-loop runs is by session order within the run's
worktree (engine order: brief, apprentice, review, lesson) and is labeled a
GUESS in the output; raw per-session numbers are always included.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


TOKEN_FIELDS = [
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
]
FULL_LOOP_STAGE_GUESS = ["brief", "apprentice", "review", "lesson"]


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_session_file(path: Path) -> dict | None:
    """Return {cwd, started_at, model, usage} or None if not a finished exec session."""
    cwd = ""
    started_at = ""
    model = ""
    usage: dict | None = None
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = record.get("payload", {})
                record_type = record.get("type", "")
                if record_type == "session_meta":
                    cwd = payload.get("cwd", "")
                    started_at = payload.get("timestamp", record.get("timestamp", ""))
                elif record_type == "turn_context" and not model:
                    model = payload.get("model", "")
                elif record_type == "event_msg" and payload.get("type") == "token_count":
                    info = payload.get("info") or {}
                    total = info.get("total_token_usage")
                    if total:
                        usage = total  # keep the LAST one = session cumulative total
    except OSError:
        return None
    if not cwd or usage is None:
        return None
    return {"cwd": cwd, "started_at": started_at, "model": model, "usage": usage}


def collect_sessions(sessions_root: Path) -> dict[str, list[dict]]:
    by_cwd: dict[str, list[dict]] = {}
    for path in sorted(sessions_root.rglob("rollout-*.jsonl")):
        session = parse_session_file(path)
        if session is None:
            continue
        by_cwd.setdefault(session["cwd"].lower(), []).append(session)
    for sessions in by_cwd.values():
        sessions.sort(key=lambda item: item["started_at"])
    return by_cwd


def sum_usage(sessions: list[dict]) -> dict[str, int]:
    totals = {field: 0 for field in TOKEN_FIELDS}
    for session in sessions:
        for field in TOKEN_FIELDS:
            totals[field] += int(session["usage"].get(field, 0) or 0)
    return totals


def session_breakdown(sessions: list[dict], arm: str) -> str:
    parts = []
    for index, session in enumerate(sessions):
        if arm == "full-loop" and len(sessions) <= len(FULL_LOOP_STAGE_GUESS):
            label = FULL_LOOP_STAGE_GUESS[index] + "?"
        else:
            label = f"s{index + 1}"
        total = int(session["usage"].get("total_tokens", 0) or 0)
        output = int(session["usage"].get("output_tokens", 0) or 0)
        parts.append(f"{label}={total}(out:{output})")
    return "; ".join(parts)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Per-run codex token accounting for the eval scorecard.")
    parser.add_argument("--scorecard", required=True, type=Path)
    parser.add_argument("--sessions", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--output", type=Path, help="optional CSV output path")
    args = parser.parse_args()

    by_cwd = collect_sessions(args.sessions)

    with args.scorecard.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    out_columns = [
        "run_id", "task_id", "arm", "outcome_type", "codex_sessions",
        *TOKEN_FIELDS, "model", "session_breakdown",
    ]
    out_rows: list[dict[str, str]] = []
    arm_totals: dict[str, dict[str, int]] = {}
    arm_runs: dict[str, int] = {}
    unmatched = 0

    for row in rows:
        repo = (row.get("repo") or "").lower()
        sessions = by_cwd.get(repo, [])
        if not sessions:
            unmatched += 1
            continue
        totals = sum_usage(sessions)
        arm = row.get("arm", "")
        arm_runs[arm] = arm_runs.get(arm, 0) + 1
        bucket = arm_totals.setdefault(arm, {field: 0 for field in TOKEN_FIELDS})
        for field in TOKEN_FIELDS:
            bucket[field] += totals[field]
        out_rows.append({
            "run_id": row.get("run_id", ""),
            "task_id": row.get("task_id", ""),
            "arm": arm,
            "outcome_type": row.get("outcome_type", ""),
            "codex_sessions": str(len(sessions)),
            **{field: str(totals[field]) for field in TOKEN_FIELDS},
            "model": sessions[0]["model"],
            "session_breakdown": session_breakdown(sessions, arm),
        })

    if args.output:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=out_columns)
            writer.writeheader()
            writer.writerows(out_rows)

    print(f"scorecard rows: {len(rows)}; matched to codex sessions: {len(out_rows)}; unmatched: {unmatched}")
    print()
    header = f"{'run_id':<28} {'task_id':<32} {'arm':<13} {'outcome':<22} {'sessions':>8} {'total':>10} {'output':>8}"
    print(header)
    print("-" * len(header))
    for row in out_rows:
        print(
            f"{row['run_id']:<28} {row['task_id']:<32} {row['arm']:<13} "
            f"{row['outcome_type']:<22} {row['codex_sessions']:>8} "
            f"{row['total_tokens']:>10} {row['output_tokens']:>8}"
        )
    print()
    print("Per-arm aggregate (matched runs only):")
    for arm, totals in sorted(arm_totals.items()):
        runs = arm_runs[arm]
        mean_total = totals["total_tokens"] // runs if runs else 0
        mean_output = totals["output_tokens"] // runs if runs else 0
        print(
            f"  {arm:<13} runs={runs:<3} mean_total={mean_total:<10} "
            f"mean_output={mean_output:<8} sum_total={totals['total_tokens']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
