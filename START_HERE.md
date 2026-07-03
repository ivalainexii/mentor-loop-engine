# Start Here

Mentor Loop has four entry paths. Pick one.

## I Want To Understand The Idea

Read:

1. `writeup-draft.md`
2. `README.md`
3. `lever-map.md`
4. `package-readiness.md`
5. `evidence-index.md`

Use this path if you are evaluating the thesis:

> Weak models lack judgment. Turn judgment into artifacts, gates, and durable
> memory, and weak models can approach stronger-model behavior on repeated work.

## I Want To Try It In My Repo

Read:

1. `quickstart.md`
2. `adoption-guide.md`
3. `operator-runbook.md`
4. `role-cards.md`
5. `model-policy.md`
6. `best-of-n-rubric.md`

For Claude Code one-command orchestration, copy `.claude/` into your target
repo root and run:

```text
/mentor-loop "fix <bug description>"
```

This should create `.mentor-loop/` artifacts, spawn the cheap apprentice
subagent, run both gates, review the diff, and capture a lesson only if review
finds a reusable mistake.

Copy these first:

```text
mentor-brief-template.md
apprentice-execute.md
mentor-review-template.md
lesson-capture-template.md
lesson-ledger-example.md
repo-context-template.md
gates/blast-radius-check.py
gates/runtime-floor-check.py
hooks/pre-commit.sample
subagents/strong-mentor.md
subagents/weak-apprentice.md
subagents/strong-reviewer.md
subagents/lesson-curator.md
skills/apprentice-execute/SKILL.md
skills/mentor-review/SKILL.md
skills/lesson-capture/SKILL.md
.claude/skills/mentor-loop/SKILL.md
.claude/agents/mentor-loop-apprentice.md
```

Run it manually once before installing anything.

Use `best-of-n-rubric.md` only after the first manual run, when verification is
cheap enough to compare two or three weak-model candidates.

## I Want To Inspect The Evidence

Read:

1. `evidence-index.md`
2. `experiments/README.md`
3. `experiments/jc-687-ablation-results.md`
4. `experiments/jc-685-live-results.md`
5. `experiments/pflow-389-boundary-results.md`

Important boundaries:

- This is a case study, not a benchmark.
- Cost reduction is unmeasured.
- `pflow-389` is `verification_incomplete`.
- Mentor Brief success-rate lift is unproven; auditability is the clearer
  signal.

## I Want To Publish Or Discuss It

Read:

1. `writeup-draft.md`
2. `publication-assets.md`
3. `package-readiness.md`
4. `evidence-index.md`

Safe headline:

> Lessons transferred. Briefs mostly bought auditability. Gates were the real
> prize.

Do not claim:

- weak models matched strong models,
- cost savings,
- cross-repo transfer,
- benchmark results.

## I Want To Build On It

Read:

1. `integration-map.md`
2. `future/README.md`
3. `future/lesson-ledger-v1.md`
4. `operator-runbook.md`

Recommended automation order:

1. Lesson capture with metadata.
2. Lesson consolidation review.
3. Blast-radius hook installation.
4. Apprentice execution skill.
5. Mentor review skill.

Do not start with model routing. The point is not to guess whether a weak model
can handle the task. The point is to make the task easier for the weak model to
handle.

## File Map

Core workflow:

- `quickstart.md`
- `adoption-guide.md`
- `operator-runbook.md`
- `role-cards.md`
- `model-policy.md`
- `lever-map.md`
- `repo-context-template.md`
- `best-of-n-rubric.md`
- `mentor-brief-template.md`
- `apprentice-execute.md`
- `mentor-review-template.md`
- `lesson-capture-template.md`
- `lesson-ledger-example.md`
- `gates/blast-radius-check.py`
- `gates/runtime-floor-check.py`
- `hooks/pre-commit.sample`
- `subagents/strong-mentor.md`
- `subagents/weak-apprentice.md`
- `subagents/strong-reviewer.md`
- `subagents/lesson-curator.md`
- `skills/apprentice-execute/SKILL.md`
- `skills/mentor-review/SKILL.md`
- `skills/lesson-capture/SKILL.md`
- `.claude/skills/mentor-loop/SKILL.md`
- `.claude/agents/mentor-loop-apprentice.md`

Evidence:

- `experiments/`
- `evidence-index.md`

Publication:

- `writeup-draft.md`
- `publication-assets.md`
- `package-readiness.md`

Release check:

- `tools/verify-package.py`

Future integration:

- `integration-map.md`
- `future/README.md`
- `future/lesson-ledger-v1.md`

Reports:

- `reports/claude-code-v0-report.md`
