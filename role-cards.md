# Mentor Loop Role Cards

Use these cards when splitting one task across a human operator, a strong model,
a weak model, deterministic gates, and a fresh reviewer.

They are manual v0 role boundaries. They are also the future subagent contract.

## Human Operator

Owns final judgment and run hygiene.

Inputs:

- user task,
- target repository,
- repo context,
- available verification commands,
- model budget and risk tolerance.

Allowed:

- create clean worktrees or checkouts,
- choose whether Mentor Loop is appropriate,
- run gates and verification,
- decide whether to escalate,
- reject unverifiable patches.

Not allowed:

- count `verification_incomplete` as success,
- compare runs that received different hidden context as if they were the same
  arm,
- accept a patch only because it looks plausible.

Outputs:

- run directory,
- scorecard row,
- final accept/reject/escalate decision.

## Strong Mentor

Turns judgment into an executable work order.

Inputs:

- user task,
- issue/reproduction,
- repo context,
- relevant source/tests/config,
- active lessons that apply to the repo or task family,
- `mentor-brief-template.md`.

Allowed:

- name required Context Pack files,
- define blast radius,
- identify runtime/dependency constraints,
- write step-by-step execution plan,
- define baseline, focused verification, regression verification, and stop
  conditions.

Not allowed:

- leave context discovery vague,
- ask the weak model to make broad architecture decisions,
- omit verification when verification is available,
- hide assumptions that the reviewer will need later.

Outputs:

- `mentor-brief.md`,
- caveats or stop conditions,
- any explicit uncertainty that should block weak execution.

## Weak Apprentice

Executes the work order without reinterpreting the task.

Inputs:

- `mentor-brief.md`,
- `apprentice-execute.md`,
- applicable active lessons,
- target clean checkout.

Allowed:

- read required Context Pack files,
- record one finding per file,
- edit only inside the blast radius,
- add or update focused tests named by the brief,
- run specified verification,
- stop and report uncertainty.

Not allowed:

- expand the task,
- edit outside the blast radius,
- use newer runtime APIs than the project supports,
- create untracked helper artifacts unless explicitly allowed,
- claim completion without verification output,
- silently ignore a stop condition.

Outputs:

- files read and findings,
- files changed and why,
- verification output,
- uncertainty,
- diff summary.

## Gate Runner

Turns machine-checkable judgment into a hard stop.

Inputs:

- `mentor-brief.md`,
- current git worktree,
- gate command,
- focused and regression verification commands.

Allowed:

- run `gates/blast-radius-check.py`,
- run focused verification,
- run regression/no-breakage verification,
- record exact command output.

Not allowed:

- waive a gate because the patch looks good,
- treat a missing test environment as success,
- ignore untracked artifacts.

Outputs:

- gate result,
- verification result,
- outcome label such as `gate_blocked`, `verification_failure`, or
  `verification_incomplete`.

## Strong Reviewer

Reviews evidence from a fresh context.

Inputs:

- Mentor Brief,
- diff,
- Apprentice log,
- gate output,
- verification output,
- relevant active lessons.

Allowed:

- approve,
- request narrow fixes,
- block and escalate,
- identify lesson candidates,
- identify gate candidates.

Not allowed:

- rewrite the patch from scratch unless escalation has happened,
- review without seeing gate and verification evidence,
- accept weakened tests,
- accept unsupported runtime/dependency changes.

Outputs:

- verdict: `Approved`, `Needs fixes`, or `Stop and re-plan`,
- blocking issues,
- non-blocking concerns,
- required fixes,
- lesson or gate candidates.

## Lesson Curator

Turns repeated judgment into durable memory or gates.

Inputs:

- review finding,
- gate failure,
- verification failure,
- existing lesson ledger,
- `lesson-capture-template.md`,
- `lesson-ledger-example.md`.

Allowed:

- create one focused lesson,
- increment a lesson hit,
- merge duplicate lessons,
- promote repeated lessons to `candidate_gate`,
- retire stale lessons.

Not allowed:

- save vague reminders,
- duplicate existing lessons,
- keep repo-specific rules as global rules,
- keep prose when a deterministic gate is available.

Outputs:

- no change,
- new lesson,
- updated `hit_count`,
- candidate gate,
- retired lesson,
- consolidation note.

## Best-of-N Selector

Ranks multiple isolated weak-model attempts when verification is cheap.

Inputs:

- candidate run records,
- gate outputs,
- verification outputs,
- reviewer verdicts,
- `best-of-n-rubric.md`.

Allowed:

- reject candidates that fail hard gates,
- compare accepted candidates by evidence,
- ask the strong reviewer to compare tied diffs,
- escalate if all candidates fail.

Not allowed:

- let candidates share hidden feedback,
- choose a candidate before verification,
- treat hinted reruns as clean independent attempts.

Outputs:

- selected candidate,
- rejected candidates with reasons,
- escalation packet if no candidate is acceptable,
- repeated failure lesson/gate candidate.

## Handoff Rule

Every role must produce an artifact that the next role can inspect.

```text
repo context
  -> mentor brief
    -> apprentice log + diff
      -> gate output + verification output
        -> review verdict
          -> lesson/gate update
            -> scorecard row
```

If a handoff artifact is missing, stop instead of filling the gap from memory.
