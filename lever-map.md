# Weak-Model Failure Lever Map

> **Archived design map (2026-07-10):** this maps an original hypothesis to
> preserved artifacts; it is not evidence that the hypothesis worked or an active
> v1 roadmap. `README.md` controls current claims.

This map connects the original product thesis to the actual package artifacts.

The original hypothesis:

> Making selected judgments explicit in artifacts, gates, examples, and review
> loops may improve weak-model work on repeated tasks.

## Coverage Table

| Weak-model failure | Lever | v0 artifact | Original rationale | Evidence status |
|---|---|---|---|---|
| Missing context | Repo context, Context Pack, and mandatory pre-read | `repo-context-template.md`, `mentor-brief-template.md`, `apprentice-execute.md` | High as workflow discipline | Used in protocol; not isolated as an ablation. |
| Weak planning | Strong brief, weak execution | `mentor-brief-template.md`, `operator-runbook.md` | Handoff-format hypothesis | Briefs made required inputs and evidence more inspectable; success-rate lift unproven. |
| Weak self-correction | Environment feedback and gates | `gates/blast-radius-check.py`, `gates/runtime-floor-check.py`, verification sections in briefs/reviews | High as deterministic tooling | Gates now cover scope drift and a narrow Python runtime-floor failure; broader semantic correctness still needs tests/review. |
| High error cost | Isolated runs and Best-of-N | `best-of-n-rubric.md`, scorecards, clean worktree protocol | Medium; useful when verification is cheap | Protocol exists; cost ratio unmeasured. |
| Local blindness after writing | Fresh-context review | `mentor-review-template.md` | Medium to high; strong model used as judge | Review caught runtime-floor and weakened-test issues. |
| Missing taste or format | Templates and examples | `lesson-ledger-example.md`, `mentor-brief-template.md`, `lesson-capture-template.md` | Medium; especially useful for weak models | Added as few-shot shape; not separately tested. |
| Repeated mistakes | Lessons, consolidation, gate promotion | `lesson-capture-template.md`, `lesson-ledger-example.md`, `future/lesson-ledger-v1.md` | Archived v1 proposal | A tiny, confounded `jc-687` sequence cannot establish causal lesson transfer. |

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

This was the rationale for not starting with model routing. The package made parts
of the task explicit; the study did not prove that this improved weak-model
outcomes.

## What Is Usage Discipline

These are habits first, products second:

- Write or maintain repo instructions such as `CLAUDE.md` or `AGENTS.md`.
- Use isolated worktrees or clean checkouts.
- Run focused and regression verification before accepting a patch.
- Keep raw run records and scorecards.
- Use Best-of-N only when verification is cheap.

They are still important. Without them, the product layer has nothing reliable
to enforce.

## Reusable Components

These pieces may be reused deliberately. Their presence does not establish product
potential or outcome benefit:

- Mentor Brief as an auditable handoff format.
- Apprentice Execute as a weak-model execution skill.
- Blast-radius gate as a deterministic hook.
- Runtime-floor gate as a narrow compatibility hook.
- Mentor Review as a fresh-context review skill.
- Lesson ledger as a durable memory system with decay.
- Lesson-to-gate promotion as the judgment distillation engine.

If explicitly reopened, the archived v1 proposal ordered them as follows:

1. Lesson ledger.
2. Lesson consolidation review.
3. Blast-radius hook installation.
4. Apprentice execution skill.
5. Mentor review skill.

## Evidence Boundaries

Safe to say:

- The loop is manually operable.
- A tiny same-repo sequence produced accepted lesson-seeded runs, with confounds;
  it does not establish causal transfer.
- Review caught failures focused tests missed.
- A real protocol failure improved a deterministic gate.
- A real runtime-floor failure became a narrow Python gate.
- Briefs made required inputs and evidence more inspectable; success-rate lift is
  unproven.

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

For now, the package is a preserved, mechanically tested operating surface plus
author-run case-study records. The A′ measurement design was falsified; the
underlying thesis remains unproven, not disproven, and further product-level
validation is not pursued.
