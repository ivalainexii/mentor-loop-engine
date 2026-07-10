# Package Readiness

Archive status (2026-07-10):

> Preserved research prototype with a mechanically verified package surface.
> Historical publication and dogfood checklists remain for reproducibility, but
> they are not an active release plan. Further product-level validation is not
> being pursued. `README.md` is the current claim source of truth.

Not ready to claim:

> benchmark uplift, cost savings, cross-repo transfer, or full product parity
> with strong-direct execution.

Also not ready to claim:

> `/mentor-loop` has completed a live real-repo bug fix end-to-end.

For the Codex-native target, not ready to claim:

> `mentor-loop <task>` has completed a live real-repo bug fix end-to-end.

## Preserved Artifacts

Publication assets:

- `writeup-draft.md`
- `publication-assets.md`
- `evidence-index.md`
- `START_HERE.md`

Manual operation:

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
- `subagents/strong-mentor.md`
- `subagents/weak-apprentice.md`
- `subagents/strong-reviewer.md`
- `subagents/lesson-curator.md`
- `skills/apprentice-execute/SKILL.md`
- `skills/mentor-review/SKILL.md`
- `skills/lesson-capture/SKILL.md`
- `gates/blast-radius-check.py`
- `gates/runtime-floor-check.py`
- `hooks/pre-commit.sample`

Gate tests:

- `tests/test_blast_radius_check.py`
- `tests/test_runtime_floor_check.py`

Release tooling:

- `tools/verify-package.py`
- `tools/mentor-loop.py`
- `mentor-loop.config.json`
- `codex-cli-verified-flags.md`

Claude Code one-command wiring:

- `.claude/skills/mentor-loop/SKILL.md`
- `.claude/agents/mentor-loop-apprentice.md`
- `.claude/skills/mentor-loop/templates/mentor-brief-template.md`
- `.claude/skills/mentor-loop/templates/apprentice-execute.md`
- `.claude/skills/mentor-loop/templates/mentor-review-template.md`
- `.claude/skills/mentor-loop/templates/lesson-capture-template.md`
- `.claude/skills/mentor-loop/scripts/blast-radius-check.py`
- `.claude/skills/mentor-loop/scripts/runtime-floor-check.py`
- `reports/claude-code-v0-report.md`
- `reports/codex-cli-limitation-report.md`

Evidence:

- `experiments/jc-685-live-results.csv`
- `experiments/jc-685-live-results.md`
- `experiments/jc-687-ablation-results.csv`
- `experiments/jc-687-ablation-results.md`
- `experiments/pflow-389-boundary-results.csv`
- `experiments/pflow-389-boundary-results.md`

Integration notes:

- `integration-map.md`
- `future/README.md`
- `future/lesson-ledger-v1.md`

## Goal Coverage

The package now covers the requested weak-to-strong approximation levers as a
manual v0:

| Goal layer | Current evidence/artifact | Status |
|---|---|---|
| Markdown workflow | `quickstart.md`, `operator-runbook.md`, templates | Manual replay documents preserved; not product-validated. |
| Context discipline | `repo-context-template.md`, Context Pack in `mentor-brief-template.md` | Usage-discipline artifacts preserved. |
| Strong planning, weak execution | `model-policy.md`, `role-cards.md`, `mentor-brief-template.md`, `apprentice-execute.md` | Manually specified; not automated or outcome-validated. |
| Environment feedback | `gates/blast-radius-check.py`, `gates/runtime-floor-check.py`, verification sections, scorecards | Scope and narrow Python runtime-floor checks are tested; broader semantic gates were not built. |
| Cheap trial | `best-of-n-rubric.md` | Manual selection protocol preserved; cost claim unmeasured. |
| Fresh review | `mentor-review-template.md`, `role-cards.md` | Manual review artifact preserved; evidence is limited to author-run cases. |
| Templates and examples | `lesson-ledger-example.md`, brief/review/lesson templates | Few-shot examples preserved. |
| Durable lessons | `lesson-capture-template.md`, `lesson-ledger-example.md`, `future/lesson-ledger-v1.md` | Manual template preserved; v1 ledger not implemented. |
| Hook | `gates/blast-radius-check.py`, `gates/runtime-floor-check.py`, `hooks/pre-commit.sample` | Working gates plus manual sample hook; no installer. |
| Skill/subagent path | `integration-map.md`, `role-cards.md`, `subagents/*.md`, `skills/*/SKILL.md`, `future/lesson-ledger-v1.md` | Manual prompt cards and skill-shaped wrappers included; not auto-installed automation. |
| Claude Code one-command path | `.claude/skills/mentor-loop/SKILL.md`, `.claude/agents/mentor-loop-apprentice.md`, bundled templates/gates | Wired as a Claude Code project skill; live end-to-end bug-fix run still required. |
| Stage engine path | `tools/mentor-loop.py`, `mentor-loop.config.json`, `codex-cli-verified-flags.md` | Wired as a GUI-drivable stage engine; stage smoke verified; live real bug-fix run still required. |

The preserved package mechanically provides:

> A manual workflow that splits judgment, execution, gates, review, and lessons,
> with tested deterministic mechanisms and author-run case-study artifacts.

It does not yet satisfy:

> A fully automated skill/hook/subagent product that makes weak-model work feel
> indistinguishable from outsourcing everything to the strongest model.

## Observed In Author-Run Cases (Not Product Proof)

- In a tiny, confounded same-repo case, accepted lesson-seeded runs followed an
  earlier related task; this does not establish causal lesson transfer.
- Mentor Briefs made baseline, repro, context, stop conditions, and review inputs
  more inspectable; success-rate lift remains unproven.
- Strong review caught failures that focused tests missed.
- A real protocol failure improved the blast-radius gate.
- A real runtime-floor failure produced a narrow Python compatibility gate.
- Lesson decay needs to be part of v1 design.
- All seven weak-model failure modes have a corresponding v0 artifact in
  `lever-map.md`.
- The cases produced the reusable engineering sequence `review -> lesson -> gate`;
  they did not establish a general outcome benefit.

## Not Proven

- Statistical uplift.
- Cost reduction.
- Cross-repo lesson transfer.
- Mentor Briefs alone improving success rate.
- Fully automated workflow.
- Live `/mentor-loop` end-to-end run on a real bug fix.
- Live GUI stage-engine end-to-end run on a real bug fix.
- Model router value.
- Distributed or auto-installed skills/subagents.
- Product-level parity with strong-direct execution.

## Known Caveats

- `jc-685` became task-contaminated after early lessons were fed back into later
  runs.
- `jc-685,weak-direct,1` was an environment failure, not a model-capability
  failure.
- `jc-687` has tiny sample sizes.
- `pflow-389` is `verification_incomplete` because the environment lacked
  `uv`, `pytest`, and `PyYAML`.
- Token counts were unavailable, so cost ratio is unmeasured.

## Historical Publication Checklist (Archived)

The following was the pre-closeout checklist. It is retained for reproducibility,
not as a current instruction to publish:

- Verify `START_HERE.md` points to the right files.
- Verify `publication-assets.md` includes explicit `Do Not Claim` guardrails.
- Verify `evidence-index.md` maps each safe claim to raw evidence.
- Verify `lever-map.md` still matches the core package.
- Run `tools/verify-package.py`.
- Refresh the zip from `manifest.json`.
- Run `tools/verify-package.py --zip ../mentor-loop-lean-v0.zip`.
- For Claude Code release, run one real repo bug fix from
  `/mentor-loop "<task>"` and inspect `.mentor-loop/runs/<run-id>/`.

Current release gate status:

- Navigation present.
- Publication assets present.
- Evidence index present.
- Lever map present.
- Manifest files present.
- CSV files parse.
- Claude Code `/mentor-loop` static wiring checks pass.
- Claude Code skill and apprentice subagent frontmatter sanity checks pass.
- `.mentor-loop/` run artifacts and local-only `.claude/` installs are hidden
  from `git status --porcelain` by repo-local git exclude in a smoke repo.
- Blast-radius smoke test accepts an allowed changed file while local
  `.claude/` and `.mentor-loop/` artifacts are present but ignored.
- Codex-native driver config and dry-run checks pass.
- Codex-native stage engine smoke checks pass.
- Codex-native driver injects active lessons into the brief prompt.
- Codex-native subprocess input/output is pinned to UTF-8.
- Codex command resolution failure reports `ENV_FAILURE` without traceback.
- Snapshot writes `apprentice-verification-summary.md` before review.
- Windows encoding smoke checks pass for UTF-8 BOM reads and UTF-8 stdio.
- Tracked eval seed `evals/fixtures/package-lessons.md` captures the Windows
  text encoding rule with `hit_count: 3`; mutable target ledgers remain runtime state.
- The seed is frozen as `mentor-loop-eval-lessons-2026-06-11-v1`; every lesson
  source artifact is packaged and the verifier runs `lessons-only` from an isolated manifest bundle.
- Codex-native final report includes an apprentice verification summary.
- Eval suite defines 12 real GitHub tasks across Python and JavaScript/TypeScript.
- Eval suite verifier checks task count, language coverage, diff size, ground
  truth URLs, checkout metadata, env deps, and focused/regression commands.
- Blast-radius gate help runs.
- Runtime-floor gate help runs.
- Blast-radius gate unit tests pass.
- Runtime-floor gate unit tests pass.
- Package verifier exists.
- Zip refreshed after latest edits.
- Claude Code one-command wiring present.
- GUI live run for `jc-685` accepted.
- Codex CLI flags are verified in `codex-cli-verified-flags.md`.
- Codex-native driver dry-run passes.
- Codex desktop sandbox still cannot execute `codex --version`; it returns
  `Access is denied`.

## Archived Restart Conditions

There is no active "next work" list. Only if an owner explicitly reopens this
research should a new measurement contract precede any live dogfood, publication
claim, or automation decision. At minimum, a restart would need an independent
baseline, product-level outcome definition, cost/accounting method, and explicit
authority for the target repository and data.

Without that decision, do not add a router, provider registry, launcher, bundle
builder, e2e harness, or new product claims. Evidence-backed defects in preserved
mechanisms and deliberate component reuse remain in scope.

## Completion Boundary

This preserved package has mechanically achieved:

> A lean, manually operable v0 with tested gates, stage wiring, and an artifact
> trail, plus historical author-run case-study records.

It has not achieved:

> A live-proven one-command system that makes weak models indistinguishable
> from strong models.

The A′ measurement design was falsified; the underlying uplift, cost, and
judgment-compounding theses remain unproven, not disproven. Further product-level
validation is not pursued. That distinction should stay visible in every public
description.
