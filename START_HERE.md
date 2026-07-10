# Start Here

> **Archive status (2026-07-10):** this navigation page describes a preserved
> research prototype. `README.md` is the current claim source of truth. The A′
> measurement design was falsified; the underlying thesis remains unproven, not
> disproven; further product-level validation is not pursued.

Mentor Loop has four historical entry paths. Pick one for inspection or deliberate
component reuse.

## I Want To Understand The Idea

Read:

1. `writeup-draft.md`
2. `README.md`
3. `lever-map.md`
4. `package-readiness.md`
5. `evidence-index.md`

Use this path to inspect the historical thesis, not to treat it as established:

> Can making selected judgments explicit in artifacts, gates, and memory improve
> weak-model work on repeated tasks?

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

The preserved wiring was designed to create `.mentor-loop/` artifacts, spawn the
configured apprentice subagent, run both gates, review the diff, and capture a
lesson only if review finds a reusable mistake. This is a historical replay path,
not a product-outcome claim; use a disposable repository first.

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

## I Want To Review The Historical Publication Materials

Read:

1. `writeup-draft.md`
2. `publication-assets.md`
3. `package-readiness.md`
4. `evidence-index.md`

Evidence-bounded summary:

> Author-run cases produced inspectable briefs and deterministic gates; causal
> uplift, cost advantage, and judgment compounding remain unproven.

Do not claim:

- weak models matched strong models,
- cost savings,
- cross-repo transfer,
- benchmark results.

## I Want To Reuse A Component

Read:

1. `integration-map.md`
2. `future/README.md`
3. `future/lesson-ledger-v1.md`
4. `operator-runbook.md`

There is no active v1 roadmap. If an owner explicitly reopens development, the
archived proposal ordered possible work as follows:

1. Lesson capture with metadata.
2. Lesson consolidation review.
3. Blast-radius hook installation.
4. Apprentice execution skill.
5. Mentor review skill.

Do not infer demand for model routing from these records. New automation or product
claims require a separate decision and evidence contract.

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

Historical publication drafts:

- `writeup-draft.md`
- `publication-assets.md`
- `package-readiness.md`

Release check:

- `tools/verify-package.py`

Archived integration proposals:

- `integration-map.md`
- `future/README.md`
- `future/lesson-ledger-v1.md`

Reports:

- `reports/claude-code-v0-report.md`
