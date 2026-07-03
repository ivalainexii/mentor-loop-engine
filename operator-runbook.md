# Operator Runbook

This is the manual v0 operating procedure. It uses human glue on purpose:
automation should come only after the painful step is obvious.

## Roles

- Human operator: owns scope, worktree hygiene, gates, and final judgment.
- Strong model: writes Mentor Briefs, reviews diffs, and consolidates lessons.
- Weak model: executes narrow work orders.
- Deterministic gates: catch scope drift and machine-checkable failures.

## When To Use Mentor Loop

Use it when:

- The task touches an existing codebase.
- The failure mode is likely to involve project context, blast radius, runtime
  constraints, or repeated mistakes.
- You can define machine-checkable verification.
- You are willing to stop rather than accept an unverified patch.

Do not use it when:

- The task is urgent and high-stakes enough that strong-direct is cheaper than
  process overhead.
- You cannot run any meaningful verification.
- The task is mostly taste/design with no checkable acceptance criteria.
- The weak model would need to invent architecture rather than execute a narrow
  patch.

## One-Run Procedure

### 1. Prepare An Isolated Workspace

Use a clean checkout or worktree. Record the path.

Before any model edits:

- Check that the workspace is clean.
- Identify the focused test command.
- Identify at least one broader no-regression check, even if it is only a
  documented limitation.

### 2. Strong Model Writes The Mentor Brief

Give the strong model:

- The user task.
- Any issue link or reproduction.
- Relevant project rules such as `CLAUDE.md`, `AGENTS.md`, `setup.py`,
  `pyproject.toml`, `package.json`, or test docs.
- The `mentor-brief-template.md` format.

The brief must include:

- Context Pack: files the weak model must read.
- Project constraints: runtime floor, dependency rules, compatibility promises.
- Blast Radius: allowed files and do-not-touch areas.
- Baseline command before editing.
- Focused and regression verification.
- Stop conditions.

Reject the brief if:

- It does not name concrete files.
- It has no machine-checkable verification.
- It leaves runtime or dependency constraints unknown when they might matter.
- It asks the weak model to make broad design decisions.

### 3. Weak Model Executes As Apprentice

Give the weak model:

- The complete Mentor Brief.
- The `apprentice-execute.md` rules.
- Any active lessons that apply to this repository or bug family.

The weak model must return:

- Files read and one finding from each.
- Files changed and why.
- Stop conditions checked.
- Runtime and compatibility constraints checked.
- Verification command and output.
- Remaining uncertainty.

Block the run if the weak model:

- Edits outside the blast radius.
- Skips required context.
- Uses newer APIs than the project supports.
- Claims completion without verification.
- Creates untracked helper artifacts.
- Reinterprets the task instead of executing the brief.

### 4. Run Deterministic Gates

Run the blast-radius gate from the repository root of the run:

```powershell
python gates/blast-radius-check.py --brief mentor-brief.md
```

The gate reads `git status --porcelain`, so it catches tracked diffs and
untracked artifacts.

For Python projects with a declared runtime floor, also run the narrow
runtime-floor gate:

```powershell
python gates/runtime-floor-check.py
```

This checks changed Python files for a small table of known APIs that require a
newer Python version than the project declares. It is not a general
compatibility proof.

Also run the focused and regression verification from the brief.

If verification cannot run, record the run as:

```text
verification_incomplete
```

Do not count it as accepted.

### 5. Strong Model Reviews The Diff

Give the strong reviewer:

- Mentor Brief.
- Diff.
- Apprentice execution log.
- Verification output.
- Gate output.

Use `mentor-review-template.md`.

Reviewer verdicts:

- `Approved`: patch is accepted.
- `Needs fixes`: weak model may make only the listed fixes.
- `Stop and re-plan`: discard this run or escalate to strong-direct.

Review must check:

- Scope drift.
- Missed context.
- Runtime or compatibility breakage.
- Verification quality.
- Whether tests were weakened instead of extended.

### 6. Capture One Lesson

Capture a lesson only if it would prevent a future mistake.

Use `lesson-capture-template.md`.

Each lesson must include:

- Created at.
- Source failure.
- Hit count.
- Last hit at.
- Status.
- Trigger.
- Mistake.
- Rule for next time.
- Example.
- Destination.

Do not capture:

- Vague reminders.
- One-off task details.
- Rules that duplicate an existing lesson.
- Rules that should really be deterministic gates now.

### Optional: Best-of-N Selection

For cheap, machine-checkable tasks, run two or three independent weak-model
candidates before strong review.

Use `best-of-n-rubric.md`.

Each candidate must have:

- a fresh model context,
- a separate clean checkout or worktree,
- the same Mentor Brief,
- the same lessons,
- the same gates and verification commands.

Do not let later candidates see earlier diffs. If one candidate receives extra
hints, record it as a different arm.

Select only after gates, verification, and strong review. If all candidates
fail the same way, escalate to strong-direct and capture the repeated failure
as a lesson or gate candidate.

## Outcome Types

Use these exact labels in scorecards:

- `accepted`: verification and review passed.
- `review_blocked`: tests may pass, but strong review found a blocker.
- `gate_blocked`: deterministic gate failed.
- `verification_failure`: focused or regression check failed.
- `verification_incomplete`: verification could not run.
- `env_failure`: environment failed before model capability was tested.
- `protocol_violation`: the model violated the arm protocol or hidden-context
  rules.

## Lesson Maintenance

Every week or every N runs:

- Merge duplicate lessons.
- Remove stale or contradictory lessons.
- Increment `hit_count` when a lesson prevents or catches a repeated failure.
  If a gate fires because of a known lesson, record that hit on the lesson.
- Promote lessons with repeated hits to `candidate_gate`.
- Retire lessons that newer execution models no longer need.

When changing the execution model, run a retirement audit:

- Temporarily remove a small sample of old active lessons.
- Rerun representative tasks or replay archived failures.
- Retire lessons for mistakes the new model no longer makes.
- Keep lessons that still change behavior.
- Promote deterministic repeats into gates instead of keeping them as prose.

The target ladder is:

```text
review catches mistake
  -> lesson prevents repeat
    -> gate makes it free
```

## Escalation Rules

Escalate to strong-direct when:

- The weak model fails the same gate twice.
- Review blocks for reasoning quality, not a small mechanical fix.
- The patch requires architecture judgment outside the brief.
- Verification remains inconclusive after environment hygiene is fixed.

Escalation cost should be counted when token data is available.

## Minimum Publishable Run Record

Every run should leave behind:

- Task id.
- Arm name.
- Model and effort.
- Run directory.
- Outcome type.
- Changed files.
- Gate output.
- Focused verification output.
- Regression verification output or reason unavailable.
- Review verdict.
- Lessons captured.
- Caveats.

If any of these are missing, the run may still be useful internally, but it is
not clean public evidence.
