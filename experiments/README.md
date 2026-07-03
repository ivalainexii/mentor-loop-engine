# Three-Task Evidence Package

This directory records the three public tasks used to shape the Mentor Loop
case study. Do not treat these rows as a benchmark.

## Tasks

1. `jc-685-ifconfig-hex-mask.md`
2. `jc-687-dir-drive-letter.md`
3. `pflow-389-yaml-block-scalar.md`

The sequence was: start with `jc-685`, use `jc-687` for ablation, then use
`pflow-389` as a cheap cross-repository boundary note.

Use:

- `jc-685-live-run-packet.md` for prompts, commands, and review instructions.
- `jc-685-live-run-ledger.md` to map each run to one scorecard row.
- `jc-685-protocol-dry-run.md` only as protocol evidence, not as uplift data.
- `jc-687-ablation-run-packet.md` for the four-arm ablation.
- `jc-687-ablation-ledger.md` to map each ablation run to one scorecard row.
- `pflow-389-boundary-results.md` for the cheap cross-repository boundary run.
- `pflow-389-boundary-ledger.md` to map the pflow run directories to rows.

## Arms

The original default shape was three arms:

- Strong direct: strong model solves the task directly.
- Weak direct: weak model receives the user issue only.
- Mentor Loop: strong model writes brief, weak model executes, gate runs, strong
  model reviews diff.

When lessons are added back into the packet and then shared with weak-direct,
record those runs as lesson-enriched weak-direct in the notes. They answer a
different question: whether durable lessons improve weak models generally, not
whether Mentor Briefs alone beat raw weak-direct.

For `jc-687`, use a four-arm ablation instead:

- A: raw weak, no lessons and no brief.
- B: weak plus only `jc-685` lessons.
- C: weak plus `jc-685` lessons and a Mentor Brief.
- D: strong direct.

This answers two questions:

- Whether lessons transfer across tasks.
- Whether the Mentor Brief adds value above transferred lessons.

## Experiment Hygiene

Use the same hygiene rules for every arm:

- Start each arm in an independent worktree or fresh checkout.
- Start each arm in a fresh model session with no memory of other arms.
- Give every arm the same environment hygiene.
- Run the weak-direct and Mentor Loop arms 2-3 times when budget allows, then
  record each run separately or note the selected run.
- Count escalation cost. If a weak run escalates to a strong model, include that
  strong-model token cost in the arm total.
- Do not reuse patches, logs, or hidden context across arms.

## Metrics

Record in `scorecard-template.csv`:

- Success.
- Focused tests passed.
- Regression tests passed.
- No unrelated behavior broke.
- Strong-model tokens for direct solution.
- Strong-model tokens for brief.
- Strong-model tokens for review.
- Strong-model escalation tokens.
- Weak-model tokens.
- Human interventions.
- Gate failures.
- Lessons captured.

The planned cost metric was:

`(strong brief + strong review + weak execution) / strong direct`

This ratio remains unmeasured because subagent token counts were unavailable.
The current evidence supports discipline and auditability claims, not cost
arbitrage.

The headline quality metric is not only "fixed A." It is:

`fixed A without breaking B`

Every task must include at least one focused verification command and one
broader regression/no-breakage check. If the broader check cannot run, mark the
run as incomplete rather than treating focused success as full success.

## Evidence Boundary

The package currently has:

- A passing protocol dry run for `jc-685`.
- Six clean local checkouts used for `jc-685` live weak-model runs.
- First live weak-model evidence for `jc-685`.
- Passing weak-direct and Mentor Loop results for `jc-685` after packet lessons.
- A completed `jc-687` four-arm ablation.

Accounting rules learned from `jc-685`:

- Environment failures are recorded as `outcome_type=env_failure` and excluded
  from model-capability comparisons.
- Later `jc-685` runs are task-contaminated by lessons from earlier `jc-685`
  runs. They show task-internal lesson effectiveness, not cross-task transfer.
- If a weak-direct arm receives lessons, record it as lesson-enriched
  weak-direct in notes. Do not compare it to raw weak-direct as if the prompt
  were still issue-only.
- Strong review applies to every weak arm as a measurement instrument. Review
  blocks count as failures even when focused tests pass.

The first minimum evidence threshold was:

- `jc-685,weak-direct,1`
- `jc-685,mentor-loop,1`

Result:

- Weak direct failed safely with no patch.
- Mentor Loop run 1 produced a scoped patch but failed focused verification
  because its regression test expected the wrong object shape.
- Mentor Loop run 2 used the captured lessons and produced a passing focused
  patch.
- Weak-direct run 2 also produced a passing focused patch after the same
  environment and test-shape lessons were added to the packet.
- Mentor Loop run 3 reproduced the passing focused patch.
- Weak-direct run 3 passed focused tests but was blocked because it used
  `str.removeprefix()` despite the project declaring `python_requires='>=3.6'`.
- Strong-direct run 1 passed focused tests but was blocked because it weakened
  an existing fixture test instead of adding a regression.

`jc-687` result:

- Raw weak: 1 accepted, 1 protocol violation.
- Lessons only: 2 accepted.
- Lessons plus brief: 2 accepted.
- Strong direct: 1 accepted.

Interpretation:

- Same-repo lesson transfer is supported.
- Mentor Brief improved auditability, not success rate, on this task.
- Cost uplift remains unproven.

`pflow-389` boundary result:

- Raw weak: 1 verification-incomplete plausible patch.
- Lessons only: 2 verification-incomplete plausible patches.
- All three runs changed only the parser and parser tests.
- All three runs passed the blast-radius gate.
- Focused tests could not run because `uv`, `pytest`, and `PyYAML` were
  unavailable in the environment.

Interpretation:

- Cross-repo lesson transfer did not produce a measurable success-rate lift in
  this sample.
- The meta-level parser-state lesson did transfer conceptually: both
  lessons-only runs explicitly applied "preserve nested context before checking
  surface syntax."
- Treat pflow as a boundary note for the writeup, not as product proof.

The six prepared `jc-685` weak-model rows are now filled. Cost evidence still
requires token counts that are not available from these subagent runs.
