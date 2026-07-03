# Mentor Loop Lean v0 Handover

This package is ready for an outside agent to evaluate. Start here if you are
not part of the original build session.

## One-Sentence Summary

Mentor Loop tests whether strong-model judgment can be distilled into briefs,
gates, review artifacts, and lessons so weaker coding models perform more
reliably.

## Current Status

- Package shape: lean v0, intentionally not a general agent framework.
- Primary claim: lessons plus gates are the main durable lever; Mentor Briefs
  mostly buy auditability.
- Stage engine: `tools/mentor-loop.py`.
- Eval runner: `evals/run-task.py`.
- Eval suite: 12 real GitHub tasks, balanced 6 Python / 6 JavaScript-TypeScript.
- Known polluted tasks excluded: `jc-685`, `jc-687`.
- Latest verifier status: green, including zip manifest check.
- Latest zip: `../mentor-loop-lean-v0.zip` relative to this directory.

## What To Read First

1. `README.md` - thesis and package overview.
2. `START_HERE.md` - which path to use.
3. `writeup-draft.md` - current public case-study draft.
4. `reports/eval-suite-v0-report.md` - what the eval suite contains.
5. `evals/RUNBOOK.md` - how to run the live baseline.
6. `.mentor-loop/lessons.md` - current judgment ledger.

## Important Paths

```text
tools/mentor-loop.py                  # stage engine and one-shot run mode
evals/run-task.py                     # headless eval runner
evals/tasks/*.json                    # 12 real tasks plus mock-smoke
gates/blast-radius-check.py           # changed-file / artifact scope gate
gates/runtime-floor-check.py          # Python runtime compatibility gate
gates/env-preflight-check.py          # host/repo environment gate
tools/verify-package.py               # package verifier
writeup-draft.md                      # current article draft
publication-assets.md                 # publishing support material
package-readiness.md                  # readiness/status checklist
```

## How To Verify The Package

From the parent workspace:

```powershell
python outputs\mentor-loop-lean-v0\tools\verify-package.py
python outputs\mentor-loop-lean-v0\tools\verify-package.py --zip outputs\mentor-loop-lean-v0.zip
```

Expected result: every line starts with `OK`, ending with:

```text
OK  zip matches manifest (96 entries)
```

## How To Run A Small Live Probe

Use `evals/RUNBOOK.md` for full details. The smallest meaningful probe is one
real task across all three arms:

```powershell
$pkg = "path\to\mentor-loop-engine"
$work = "path\to\eval-runs"
$scorecard = "$work\scorecard.csv"
$task = "$pkg\evals\tasks\jc-694-lsattr-spaces.json"

python "$pkg\evals\run-task.py" --task "$task" --arm raw-weak --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
python "$pkg\evals\run-task.py" --task "$task" --arm lessons-only --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
python "$pkg\evals\run-task.py" --task "$task" --arm full-loop --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
```

The live runner uses local `codex exec`. If `codex` is not on PATH, fix the
local Codex CLI installation instead of changing the package to a machine-
specific absolute path.

## Eval Arms

- `raw-weak`: weak model gets only issue text.
- `lessons-only`: weak model gets issue text plus active lessons from this
  package's `.mentor-loop/lessons.md`.
- `full-loop`: one-shot Mentor Loop path with strong brief/review and weak
  apprentice.

The scorecard includes:

- `lesson_origin_relation`: `same-repo` for `kellyjonbrazil/jc`, `cross-repo`
  for other repos.
- `regression_baseline_failures` and `regression_new_failures`: regression
  classification is baseline-relative, not absolute pass/fail.
- `outcome_type`: includes `infra_error` so runner/engine failures are not
  mistaken for model protocol violations.

## Current Findings

- Same-repo lessons transferred in the small `jc-687` ablation.
- Briefs did not show clear success-rate lift over lessons-only at tiny sample
  size, but improved auditability.
- Strong review caught runtime-floor mistakes that focused tests missed.
- Real failures became gates:
  - untracked artifact detection via `git status --porcelain`;
  - environment preflight before model execution;
  - baseline-relative regression classification in eval tooling.
- Live dogfooding found that the loop also disciplines strong models: it caught
  skipped logs, bad narratives, bad acceptance design, and verbose output.

## Known Limits

- This is a case study, not a statistical benchmark.
- Cost reduction is unmeasured; GUI/subagent token accounting is incomplete.
- Cross-repo lesson transfer is not yet a product claim.
- Full 12-task baseline still requires live execution in an unrestricted
  terminal.
- Do not add token accounting or three-slot model config until the first full
  baseline is actually run.

## Do Not Build Yet

Park these until after live baseline data exists:

- token accounting;
- three-slot strong/weak/reviewer config;
- dashboards;
- CI;
- parallel runner;
- generic provider registry;
- model router.

## Suggested Evaluation Prompts

Use these with a fresh agent:

```text
You are evaluating Mentor Loop Lean v0. Read HANDOVER.md, README.md,
writeup-draft.md, reports/eval-suite-v0-report.md, evals/RUNBOOK.md, and
evals/run-task.py. Do not implement new features. Assess:
1. Is the package internally coherent?
2. Are the evidence claims supported by the artifacts?
3. Can the eval runner produce trustworthy baseline data?
4. What must be fixed before publication?
Return findings first, ordered by severity, with file references.
```

For a code-focused review:

```text
Review tools/mentor-loop.py, evals/run-task.py, gates/*.py, and
tools/verify-package.py. Focus on bugs, Windows portability, scorecard
correctness, and ways the runner could misclassify outcomes. Do not propose
new product features.
```

For a publication review:

```text
Read writeup-draft.md plus evidence-index.md and publication-assets.md. Check
whether every public claim is backed by an artifact, whether any conclusion is
overstated, and whether the story is understandable to HN/LocalLLaMA readers.
```

## Last Known Good Verification

The last local package verification passed after Work Order 3:

- full-loop `{package}` config rendering;
- `infra_error` classification;
- per-repo source clone cache;
- baseline-relative regression classification;
- package lessons seeded into `lessons-only`;
- zip contents match manifest.

