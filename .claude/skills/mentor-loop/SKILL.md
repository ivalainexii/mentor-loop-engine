---
name: mentor-loop
description: Run the full Mentor Loop in Claude Code for a coding task: strong-session brief, cheap apprentice subagent execution, deterministic gates, strong review, optional lesson capture, and final report.
argument-hint: "<task description>"
disable-model-invocation: true
allowed-tools: Agent(mentor-loop-apprentice), Read, Grep, Glob, Bash, Write, Edit, MultiEdit
model: inherit
---

Run Mentor Loop for this task:

`$ARGUMENTS`

This is Claude Code only. Do not create routers, provider registries, API
adapters, cross-platform launchers, or extra gates. If a required step cannot
be done inside Claude Code, stop and report the blocker.

Use these bundled resources:

- `${CLAUDE_SKILL_DIR}/templates/mentor-brief-template.md`
- `${CLAUDE_SKILL_DIR}/templates/apprentice-execute.md`
- `${CLAUDE_SKILL_DIR}/templates/mentor-review-template.md`
- `${CLAUDE_SKILL_DIR}/templates/lesson-capture-template.md`
- `${CLAUDE_SKILL_DIR}/scripts/blast-radius-check.py`
- `${CLAUDE_SKILL_DIR}/scripts/runtime-floor-check.py`

## Run Directory

Before creating run artifacts, ensure the Mentor Loop installation files will
not pollute `git status --porcelain`:

- If `.claude/` is already tracked or intentionally committed in this repo,
  continue.
- If `.claude/` is a local-only copy for dogfood, add `.claude/` to the same
  repo-local exclude file described below.

Create a run directory under the target repo:

`.mentor-loop/runs/<YYYYMMDD-HHMMSS>-<short-slug>/`

Ensure `.mentor-loop/` is gitignored without changing tracked project files:

1. Run `git rev-parse --git-path info/exclude`.
2. Append `.mentor-loop/` to that exclude file if it is not already present.
3. Append `.claude/` too only when this is a local-only untracked install.
4. Stop if the target repo is not a git worktree.

This local exclude is required because `.mentor-loop/.gitignore` would still
leave the `.mentor-loop/` directory itself visible to `git status --porcelain`.
The run artifacts must not appear in the later blast-radius gate.

Use commands equivalent to:

```bash
exclude_file="$(git rev-parse --git-path info/exclude)" || exit 1
if ! grep -qxF ".mentor-loop/" "$exclude_file"; then
  printf "\n.mentor-loop/\n" >> "$exclude_file"
fi
```

For local-only dogfood installs, also add:

```bash
exclude_file="$(git rev-parse --git-path info/exclude)" || exit 1
if ! grep -qxF ".claude/" "$exclude_file"; then
  printf "\n.claude/\n" >> "$exclude_file"
fi
```

All run artifacts must go in the run directory:

- `mentor-brief.md`
- `apprentice-prompt.md`
- `apprentice-log.md`
- `gate-blast-radius.txt`
- `gate-runtime-floor.txt`
- `review.md`
- `lesson.md` only if a reusable mistake is captured
- `final-report.md`

## 1. Strong Session Writes Mentor Brief

Read `${CLAUDE_SKILL_DIR}/templates/mentor-brief-template.md`.

As the main session, write `mentor-brief.md` for `$ARGUMENTS`.

The brief must include:

- User-visible expected behavior.
- Evidence used.
- At least three relevant Context Pack files when available.
- Project rules inspected, including `CLAUDE.md`, `AGENTS.md`, or
  `mentor-loop/repo-context.md` when present.
- Runtime/dependency compatibility constraints.
- Blast Radius with explicit likely touched files and do-not-touch files.
- Baseline Before Editing commands.
- Focused verification commands.
- Regression verification commands.
- Stop conditions.

Run the Baseline Before Editing commands before any edit. Record exact command
output in `mentor-brief.md`. If baseline fails before editing, stop and write a
final report with no subagent execution.

## 2. Spawn Cheap Apprentice

Read `${CLAUDE_SKILL_DIR}/templates/apprentice-execute.md`.

Write `apprentice-prompt.md` containing:

- The full apprentice instructions.
- The full `mentor-brief.md`.
- A requirement to write all observations into the returned execution log.

Invoke the `mentor-loop-apprentice` subagent with `apprentice-prompt.md` as the
task input. The subagent should use its configured cheap model.

When it returns, save the full result as `apprentice-log.md`.

## 3. Run Deterministic Gates

After apprentice execution, run both gates from the target repo root:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/blast-radius-check.py" --brief ".mentor-loop/runs/<run-id>/mentor-brief.md"
```

Save stdout/stderr and exit code to `gate-blast-radius.txt`.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/runtime-floor-check.py"
```

Save stdout/stderr and exit code to `gate-runtime-floor.txt`.

Both gates must run automatically. If `python` is unavailable, try `python3`.
If neither works, stop and report the environment blocker. Do not add an
env-preflight gate unless repeated real runs fail because of missing
dependencies.

## 4. Strong Session Reviews Only Diff And Logs

Read `${CLAUDE_SKILL_DIR}/templates/mentor-review-template.md`.

Review only:

- `mentor-brief.md`
- `apprentice-log.md`
- `git diff --stat`
- `git diff`
- `git status --porcelain`
- `gate-blast-radius.txt`
- `gate-runtime-floor.txt`

Do not inspect unrelated files unless the diff/logs reveal ambiguity that
blocks review.

Write `review.md` with:

- Verdict: Approved, Needs fixes, or Stop and re-plan.
- Blocking issues.
- Non-blocking concerns.
- Gate results.
- Verification quality.
- Whether another apprentice pass is allowed.
- Lesson candidate, if any.

## 5. Capture Lesson If Reusable

If review finds a reusable mistake, read
`${CLAUDE_SKILL_DIR}/templates/lesson-capture-template.md`.

Append one lesson to `.mentor-loop/lessons.md`. Create the file if needed.

Each lesson entry must include:

- `created_at`: current date/time.
- `source_run_id`: this run directory id.
- `source_failure`: review finding or gate failure.
- `source_artifact`: relative path to `review.md`, gate output, or apprentice log.
- `trigger`.
- `mistake`.
- `rule_for_next_time`.
- `hit_count`: 0.
- `last_hit_at`: blank.
- `status`: active.
- `candidate_gate`: blank unless the failure is already mechanically checkable.

Also write the captured entry to `lesson.md`.

Do not save vague reminders. If no reusable mistake exists, write in
`review.md` that no lesson was captured.

## 6. Final Report

Write `final-report.md`, then report to the user:

- Run id.
- Files changed.
- Baseline result.
- Verification result.
- Blast-radius gate result.
- Runtime-floor gate result.
- Review verdict.
- Lessons captured.
- Remaining friction or blocker.

If any step fails, stop at that step and still write `final-report.md` with the
failure reason and artifacts created so far.
