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
- `verification_incomplete`: verification could not run, including a missing command or timeout.
- `env_failure`: environment failed before model capability was tested.
- `infra_error`: a reviewer, architect, or engine process failed before a semantic verdict was available.
- `protocol_violation`: the model violated the arm protocol or hidden-context
  rules.

When several structured block reasons coexist, primary scorecard attribution is
ordered as: verification incomplete, verification failure, infrastructure error,
semantic review block, invalid-review protocol, then deterministic gate. The run
record retains every reason; this ordering only selects its primary scorecard label.

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

## Optional Engine Automation (advisor / architect commands)

The CLI engine (`tools/mentor-loop.py`) runs the loop above with deterministic gates.
Two OPTIONAL commands extend it. Both are OFF by default, their advice is never
auto-applied, and neither can unlock an escalation on its own. The advisor is
non-blocking; the architect is fail-closed when a triggered BUILD-D audit requires it.

- `advisor_command` — cross-vendor advisory brief-review. Runs a second-vendor model
  (read-only) over the Mentor Brief plus its change intent and blast-radius file list, and
  writes findings to a brief appendix. Findings are ADVISORY only: the mentor may adopt or
  reject each with one line, and the run's pass/fail is unchanged. If the command cannot run
  (for example a Windows sandbox restriction, or a non-zero exit), the stage SKIPs and the
  brief is marked "not cross-vendor reviewed" (未经跨厂审). There is no same-vendor fallback.

- `architect_command` — architect verdict auto-draft. For a brief that escalated at the
  honesty gate, this drafts a verdict for the human to review. It NEVER auto-stamps and NEVER
  auto-unlocks: a person must read the draft and run the ratify step, which applies the
  `[architect-ratified: <ref>]` stamp. If the command cannot run during BUILD-C, the stage
  SKIPs and the brief stays BLOCKED. If a triggered BUILD-D audit cannot run it, the run
  PARKs for the owner rather than guessing a direction.

Both commands are declared ONLY in `mentor-loop.config.json.example`, never in the shipped
`mentor-loop.config.json`. A missing advisor key and the BUILD-C architect draft stage SKIP;
a triggered BUILD-D audit with no architect key PARKs. To enable one, copy
`mentor-loop.config.json.example` to `mentor-loop.config.json` and rename
`_optional_advisor_command` / `_optional_architect_command` to `advisor_command` /
`architect_command`. Pin an explicit model in each command.

## Failure-Review Loop (BUILD-D, fail-closed when triggered)

BUILD-C escalates *before* the apprentice runs, on a fail-open guard. BUILD-D is
the sibling that escalates *after* execution, when the **same target** keeps
failing. Repeated failure is often "the task was defined wrong," not "the
apprentice is weak," so this loop audits the mentor's **direction** (goal,
assumptions, scope) — it never reviews or writes code.

### When it fires

All triggers are scoped to one stable `target_id` (see below) and accumulate
**non-consecutively** across runs:

- the same target fails **2 or more times** (`FAILURE_TRIGGER_N = 2`),
- `verification_failure` on the same target 2 or more times,
- the apprentice emits a structured `brief_blocker: <reason>` line,
- review returns `Stop and re-plan` (reason-code `direction_unclear`),
- the mentor revised the brief and the target **still** fails.

### `target_id`: what it is and why `--target` exists

`target_id` is derived once from the normalized task string (`run`'s
positional `task` argument) and frozen for the life of that piece of work. A
plain retry of the same task re-derives the same id, so its counters
accumulate naturally. When the mentor **narrows, re-routes, or rewrites** the
task after a verdict, pass the parent's frozen id forward explicitly so the
successor inherits the same failure history (and the same "already audited"
status) instead of starting a fresh counter:

```powershell
python tools\mentor-loop.py run --repo path\to\target-repo --target <parent-target-id> "<narrowed task text>"
```

Omit `--target` to derive a fresh id from the task text. v0 limitation: two
*unrelated* tasks with identical wording would otherwise share one counter —
disambiguate those with an explicit `--target`.

### What happens when it fires

1. State for the target lives at `.mentor-loop/state/brief-review-loop.json`
   (persisted across runs, since each CLI invocation is a separate process).
2. The engine assembles a failure-attribution packet: the per-attempt history
   for this target, the current Mentor Brief being audited, and blast-radius
   context.
3. The packet goes to the configured `architect_command` (same config key
   BUILD-C uses — see "Optional Engine Automation" above). If no
   `architect_command` is configured, or the command fails to run, the loop
   **parks** (fail-closed) rather than guessing or skipping silently.
4. The architect may return exactly one of these verdicts (no others are
   legal):
   - `revised_brief`, `narrowed_task`, `route_change`, `keep_brief_retry`,
     `brief_sound_capability_gap`, `park_report`.
5. **No-code enforcement**: if the architect's verdict contains a fenced code
   block, a unified-diff marker, or a `file:line` edit, the whole verdict is
   **rejected and parked** — never stripped or laundered into an executable
   one. The architect audits direction; it does not patch.
6. The audit is **one-shot per target**: once a target has been audited, a
   successor inherits that "already audited" flag (via `--target`) rather than
   getting a fresh quota. Only the owner can reset a target's quota and
   counters. If a target still fails after its one audit, it parks for the
   owner with the architect's verdict text attached for context.

The architect's direction is additive and advisory: it is recorded but never
auto-applied, and it never rewrites the original execution, verification, or review
facts. The BUILD-D control gate itself is fail-closed: PARK, an unknown status, or a
diagnostic error appends a block reason and may tighten PASS to PARK/BLOCKED, but it
can never turn a failure into success. A target that never triggers the loop is not
affected.
The metric series it writes (`.mentor-loop/state/failure-review-metric.jsonl`)
is separate from the apprentice correction-rate ledger, so "does the brief
review compound in value" stays a falsifiable, separately-measured question
rather than folded into execution stats.

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
