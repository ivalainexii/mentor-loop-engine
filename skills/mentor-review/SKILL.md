---
name: mentor-loop-review
description: Use when reviewing a weak-model coding run against a Mentor Brief, diff, apprentice log, gate output, and verification evidence to decide Approved, Needs fixes, or Stop and re-plan.
---

# Mentor Loop Review

Review the weak-model run from a fresh context.

Before reviewing, read:

- `../../role-cards.md`, Strong Reviewer section
- `../../mentor-review-template.md`
- the Mentor Brief
- the diff
- the apprentice log
- gate output
- verification output

## Review For

- Scope drift.
- Missed required context.
- Unsupported runtime or dependency changes.
- Weakened tests.
- Missing or weak verification.
- Assumptions not supported by source/tests.
- Lesson or gate candidates.

## Verdicts

Return exactly one:

- `Approved`: patch can be accepted.
- `Needs fixes`: weak model may make only the listed fixes.
- `Stop and re-plan`: discard, rerun, or escalate to strong-direct.

## Output

Return:

- verdict,
- blocking issues,
- non-blocking concerns,
- required fixes,
- lesson candidate if any,
- gate candidate if any.

Do not rewrite the patch unless escalation has happened.
