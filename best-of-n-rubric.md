# Best-of-N Run Selection Rubric

Use this when a task is cheap to verify and weak-model attempts are cheaper
than one strong-direct attempt.

The goal is not to let weak models thrash. The goal is to make trial cheap,
isolated, and evidence-ranked.

## When To Use

Use Best-of-N when:

- The task is narrow.
- Verification is machine-checkable.
- Each run can happen in a clean worktree or checkout.
- You can give every run the same brief, lessons, and gates.
- Picking a winner is cheaper than asking the strong model to implement from
  scratch.

Do not use Best-of-N when:

- The task is high-stakes.
- Verification is unavailable.
- The patch requires broad architecture judgment.
- A wrong patch could silently corrupt data.
- You cannot keep runs isolated.

Default N:

- `N=2` for normal small fixes.
- `N=3` when verification is cheap and failure modes are varied.
- Stop after `N=1` if the first run is cleanly accepted.

## Run Hygiene

Every candidate must use:

- a fresh model context,
- a clean checkout or worktree,
- the same Mentor Brief,
- the same active lessons,
- the same gate command,
- the same focused verification,
- the same regression verification,
- no hidden feedback from other candidates.

If one candidate receives extra hints, mark it as a different arm. Do not rank
it against the others as if the prompt were identical.

## Candidate Record

For each candidate, record:

- run id,
- model and effort,
- run directory,
- files changed,
- gate result,
- focused verification result,
- regression verification result,
- review verdict,
- human interventions,
- lessons triggered,
- caveats.

Use `experiments/scorecard-template.csv` as the shape even outside formal
experiments.

## Ranking Order

Choose the winner using this order:

1. Gate passed.
2. Focused verification passed.
3. Regression verification passed.
4. Strong review verdict is `Approved`.
5. Patch changes the smallest necessary surface.
6. Patch preserves existing tests and adds focused coverage when appropriate.
7. Patch uses project-compatible APIs and dependencies.
8. Patch has the clearest explanation and uncertainty report.

Never choose a candidate that failed a hard gate just because the diff looks
nice.

## Tie Breakers

If two candidates pass all hard checks:

- Prefer the one with fewer changed files.
- Prefer the one that strengthens tests without deleting existing assertions.
- Prefer the one that follows existing project style.
- Prefer the one with fewer human interventions.
- Prefer the one whose reasoning cites concrete files it actually read.

If the tie remains, ask the strong reviewer to compare only the two diffs and
their evidence. Do not ask for a fresh implementation yet.

## Escalation

Escalate to strong-direct when:

- all candidates fail the same gate,
- all candidates fail verification,
- review blocks all candidates for reasoning quality,
- the candidates disagree in a way that requires architecture judgment,
- the task turns out to need files outside the original blast radius.

When escalation happens, give the strong model:

- the Mentor Brief,
- all candidate diffs,
- all gate and verification outputs,
- the reason each candidate was rejected,
- any reusable lesson candidates.

This turns failed weak runs into context instead of waste.

## What To Capture

After selection, capture at most one lesson:

- a repeated failure across candidates,
- a gate gap,
- a missing context file,
- a verification command that should have been in the brief,
- a project rule that changed the winner.

If multiple candidates failed the same mechanical way, prefer a gate candidate
over prose.

## Example Decision Table

| Candidate | Gate | Focused | Regression | Review | Decision |
|---|---|---|---|---|---|
| A | pass | pass | unknown | blocked | reject: review found runtime-floor issue |
| B | pass | pass | pass | approved | select |
| C | fail | pass | pass | not reviewed | reject: out-of-scope artifact |

The winner is B. Candidate A may produce a lesson. Candidate C may produce or
hit a gate.

## Anti-Patterns

- Running candidates in the same checkout.
- Letting later candidates see earlier diffs.
- Accepting `verification_incomplete` as success.
- Picking the shortest diff when it weakens tests.
- Asking the strong model to reimplement before it has compared candidates.
- Counting a hinted rerun as if it were a clean independent attempt.

Best-of-N only works when failure is cheap and selection is evidence-based.
