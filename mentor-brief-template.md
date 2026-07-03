# Mentor Brief

## User Task

Describe the exact request and the expected user-visible behavior.

## Evidence Used

- User report or issue:
- Source files inspected:
- Tests inspected:
- Project rules inspected (`CLAUDE.md`, `AGENTS.md`, or
  `mentor-loop/repo-context.md`):

## Context Pack

Read these files before editing:

1.
2.
3.

Include repo context when present:

- `CLAUDE.md`, `AGENTS.md`, or `mentor-loop/repo-context.md`

Stop if any required file is missing or unreadable.

## Project Constraints

Record constraints the patch must preserve:

- Supported language/runtime versions:
- Public API or compatibility promises:
- Style or dependency rules:

Stop if the implementation would require a newer runtime, new dependency, or
unsupported platform behavior not already allowed by the project.

## Blast Radius

Likely touched files:

-

Do not touch:

-

Potentially affected behavior:

-

## Change Surface

- Touches fidelity gate or anchored contract: <yes/no>
- Anchored change: <yes/no>

If "Touches fidelity gate or anchored contract" is yes, the Verification section must pin at least
one non-happy-path round-trip (a valid input the naive check would wrongly pass or refuse), tagged
`[non-happy-path]`.

## Guards & Fail-Directions

List every guard (a fail-open / fail-closed decision point) this change introduces or moves. One
bullet per guard, in the form `name: fail-closed — one-line why`. Write `none` if the change
introduces no guard. A guard declared `fail-open` or `unsure` is routed to the architect before the
apprentice runs — you may not self-approve it. Once the architect rules, either change it to
fail-closed with a why, or record the ruling by appending `[architect-ratified: <ref>]` to the line.

- none

## Anchoring

Fill only when "Anchored change" is yes.

- Scope:
- Excluded counter-example:

## Execution Plan

1.
2.
3.

Each step must be completed before moving on.

## Baseline Before Editing

Run before changing files:

-

Expected current result:

-

If the baseline fails before editing, stop. Do not fix a moving target.

## Stop Conditions

Stop if:

- Required context files were not read.
- Project runtime or compatibility constraints are unknown and the change may
  depend on them.
- The change needs a file outside the blast radius.
- Baseline fails before editing.
- Tests fail for unclear reasons.
- Existing conventions conflict with this brief.
- You are about to invent behavior not specified here.

## Verification

Run focused verification:

-

Expected result:

-

Run regression verification:

-

Expected no-regression result:

-

If verification cannot be run, stop and explain why.

## Strong Review Prompt

Review the diff and execution log against this Mentor Brief.

Focus on:

- Scope drift.
- Missed context.
- Runtime or compatibility breakage.
- Incorrect assumptions.
- Weak-model overreach.
- Missing or weak verification.

Return only:

- Blocking issues.
- Non-blocking concerns.
- Required fixes.
- Whether another review pass is needed.

## Lesson Capture Prompt

If the weak model made a reusable mistake:

- Trigger:
- Mistake:
- Rule for next time:
- Where to save it:
