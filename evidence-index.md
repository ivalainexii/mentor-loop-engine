# Evidence Index

This file maps publishable claims to the raw evidence in this package. Use it
when linking the writeup or answering methodology criticism.

## Claim Matrix

| Claim | Evidence | Caveat |
|---|---|---|
| Same-repo lessons transferred across related tasks. | `experiments/jc-687-ablation-results.md`, `experiments/jc-687-ablation-results.csv` | Sample is tiny; treat as case-study evidence, not statistical uplift. |
| Mentor Briefs improved auditability more clearly than success rate. | `experiments/jc-687-ablation-results.md` compares lessons-only vs lessons-plus-brief. | Both B and C arms were accepted, so brief's marginal success-rate lift is unproven. |
| Strong review caught failures focused tests missed. | `experiments/jc-685-live-results.md`, especially `jc-685,weak-direct,3` and `jc-685,strong-direct,1`. | Review is a measurement instrument here, not a deterministic gate. |
| Runtime-floor awareness became a reusable lesson and narrow gate. | `experiments/jc-685-live-results.md` documents `python_requires='>=3.6'` vs `str.removeprefix()`; `gates/runtime-floor-check.py` checks a small Python API table. | This is not a general compatibility proof; it only covers known Python APIs in the gate table. |
| A real protocol failure improved the blast-radius gate. | `experiments/jc-687-ablation-results.md` documents the `.surgical-fix/` artifact; `gates/blast-radius-check.py` now reads `git status --porcelain`. | The gate checks scope, not semantic correctness. |
| Cross-repo lesson transfer is not proven. | `experiments/pflow-389-boundary-results.md`, `experiments/pflow-389-boundary-results.csv`. | pflow rows are `verification_incomplete` because tests could not run. |
| Lesson files need depreciation, not just capture. | `writeup-draft.md` describes lesson rot; `future/lesson-ledger-v1.md` specifies metadata, consolidation, gate promotion, and retirement audits. | This is v1 design guidance, not implemented product behavior in v0. |
| Cost reduction is unmeasured. | `experiments/jc-685-live-results.md`, `experiments/README.md`, `writeup-draft.md`. | Subagent token counts were unavailable. |
| This is a case study, not a benchmark. | All result CSVs are included; `publication-assets.md` contains explicit `Do Not Claim` guardrails. | Do not use row counts as benchmark rates. |

## Raw Data Files

- `experiments/jc-685-live-results.csv`
- `experiments/jc-685-live-results.md`
- `experiments/jc-687-ablation-results.csv`
- `experiments/jc-687-ablation-results.md`
- `experiments/pflow-389-boundary-results.csv`
- `experiments/pflow-389-boundary-results.md`

## Gate Evidence

- `gates/blast-radius-check.py`
- `gates/runtime-floor-check.py`
- `tools/verify-package.py`
- The older standalone blast-radius hook outside this lean zip has also been
  backfilled with the same default `git status --porcelain` behavior, but the
  publishable package entrypoint is the gate above.

Relevant behavior:

- Reads `git status --porcelain` when `--changed` is omitted.
- Normalizes changed paths.
- Blocks files outside the Mentor Brief blast radius.
- Includes untracked paths that `git diff --name-only` would miss.
- The runtime-floor gate checks a narrow Python API table, including
  `removeprefix` and `removesuffix`, against `python_requires` or
  `requires-python`.
- The package verifier checks manifest presence, experiment CSV parsing, gate
  help commands, unit tests, and optional zip/manifest consistency.

## Publication Claims To Use

Use these:

- "Same-repo lessons transferred in a small related-task case study."
- "Mentor Briefs bought auditability in this sample."
- "Two real failures became durable assets: a narrow runtime-floor gate and a
  stronger blast-radius gate."
- "The useful mechanism was `review -> lesson -> gate`."
- "The v1 lesson ledger needs depreciation: metadata, consolidation, gate
  promotion, and retirement audits."
- "Cost ratio is unmeasured."

Avoid these:

- "Weak models matched strong models."
- "Mentor Loop reduces cost by X%."
- "Mentor Briefs improved success rate."
- "Cross-repo lessons transferred."
- "This is a benchmark."

## Methodology Replies

If someone says "n is tiny":

> Correct. This is a case study with raw rows, not a benchmark. The useful part
> is the failure-mode analysis and the `review -> lesson -> gate` mechanism.

If someone says "pflow did not pass tests":

> Correct. pflow is recorded as `verification_incomplete` and used only as a
> boundary note.

If someone says "aider/Claude Code already do architect/editor":

> Yes. The strong/weak split is not the differentiator. The differentiator is
> turning repeated review findings into lessons and then gates.

If someone says "why not just use the strong model":

> For one-off or high-stakes tasks, that may be right. The loop matters when
> repeated work in the same repo lets lessons and gates compound.
