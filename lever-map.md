# Weak-Model Failure Lever Map

This map connects the original product thesis to the actual package artifacts.

The core idea:

> Weak models lack judgment. Turn judgment into artifacts, gates, examples, and
> review loops, and weak models can approach stronger-model behavior on repeated
> work.

## Coverage Table

| Weak-model failure | Lever | v0 artifact | Product potential | Evidence status |
|---|---|---|---|---|
| Missing context | Repo context, Context Pack, and mandatory pre-read | `repo-context-template.md`, `mentor-brief-template.md`, `apprentice-execute.md` | High as workflow discipline | Used in protocol; not isolated as an ablation. |
| Weak planning | Strong brief, weak execution | `mentor-brief-template.md`, `operator-runbook.md` | High as handoff format | Briefs improved auditability; success-rate lift unproven. |
| Weak self-correction | Environment feedback and gates | `gates/blast-radius-check.py`, `gates/runtime-floor-check.py`, verification sections in briefs/reviews | High as deterministic tooling | Gates now cover scope drift and a narrow Python runtime-floor failure; broader semantic correctness still needs tests/review. |
| High error cost | Isolated runs and Best-of-N | `best-of-n-rubric.md`, scorecards, clean worktree protocol | Medium; useful when verification is cheap | Protocol exists; cost ratio unmeasured. |
| Local blindness after writing | Fresh-context review | `mentor-review-template.md` | Medium to high; strong model used as judge | Review caught runtime-floor and weakened-test issues. |
| Missing taste or format | Templates and examples | `lesson-ledger-example.md`, `mentor-brief-template.md`, `lesson-capture-template.md` | Medium; especially useful for weak models | Added as few-shot shape; not separately tested. |
| Repeated mistakes | Lessons, consolidation, gate promotion | `lesson-capture-template.md`, `lesson-ledger-example.md`, `future/lesson-ledger-v1.md` | High; main v1 direction | Same-repo lesson transfer shown in tiny `jc-687` case study. |

## How The Pieces Work Together

```text
strong model supplies judgment
  -> Mentor Brief turns it into an executable work order
  -> Apprentice rules force context reading and narrow execution
  -> Verification and gates make the environment answer back
  -> Best-of-N makes cheap failure useful when checks are cheap
  -> Strong review catches judgment failures tests missed
  -> Lesson ledger captures reusable corrections
  -> Repeated lessons become gates
```

This is why the package should not start with model routing. Routing tries to
predict whether the weak model is smart enough. Mentor Loop changes the task so
the weak model needs less hidden judgment.

## What Is Usage Discipline

These are habits first, products second:

- Write or maintain repo instructions such as `CLAUDE.md` or `AGENTS.md`.
- Use isolated worktrees or clean checkouts.
- Run focused and regression verification before accepting a patch.
- Keep raw run records and scorecards.
- Use Best-of-N only when verification is cheap.

They are still important. Without them, the product layer has nothing reliable
to enforce.

## What Has Product Potential

These are the strongest product-shaped pieces:

- Mentor Brief as an auditable handoff format.
- Apprentice Execute as a weak-model execution skill.
- Blast-radius gate as a deterministic hook.
- Runtime-floor gate as a narrow compatibility hook.
- Mentor Review as a fresh-context review skill.
- Lesson ledger as a durable memory system with decay.
- Lesson-to-gate promotion as the judgment distillation engine.

The likely v1 order remains:

1. Lesson ledger.
2. Lesson consolidation review.
3. Blast-radius hook installation.
4. Apprentice execution skill.
5. Mentor review skill.

## Evidence Boundaries

Safe to say:

- The loop is manually operable.
- Same-repo lessons transferred in a small related-task case study.
- Review caught failures focused tests missed.
- A real protocol failure improved a deterministic gate.
- A real runtime-floor failure became a narrow Python gate.
- Briefs improved auditability more clearly than success rate.

Do not claim:

- Weak models matched strong models.
- The workflow reduces cost by a measured amount.
- Cross-repo lesson transfer is proven.
- Mentor Briefs alone improved success rate.
- The package is a benchmark.

## Completion Implication

The current v0 covers all seven failure categories as workflow artifacts.

It does not yet satisfy the full end-state of "weak models feel
indistinguishable from strong-direct execution." That would require more
dogfooding, stronger automation, cost accounting, and product-level evidence.

For now, the package is a lean, evidence-backed operating surface for judgment
distillation.
