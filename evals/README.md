# Mentor Loop Eval Suite

This directory is the permanent regression benchmark for Mentor Loop itself.
It is headless batch work: use one-shot `mentor-loop.py run` and direct
`codex exec`-style commands, not the GUI stage path.

## Arms

- `raw-weak`: cheap model receives only the issue text.
- `lessons-only`: cheap model receives issue text plus active lessons from the
  package ledger at `{package}/.mentor-loop/lessons.md`; no Mentor Brief.
- `full-loop`: the one-shot engine path runs end-to-end.

## Lessons Seeding

Fresh eval clones do not have a local `.mentor-loop/lessons.md`, so the
`lessons-only` arm is seeded from this package's own active lessons. The
scorecard records `lesson_origin_relation`: `same-repo` for
`kellyjonbrazil/jc` tasks, where several lessons were learned, and `cross-repo`
for all other repos. Treat those groups as separate claims: same-repo transfer
versus cross-domain meta-lesson value.

## Run One Mock Task

This is the local dry verification path. It does not call the real Codex CLI.

```powershell
$pkg = "path\to\mentor-loop-engine"
$work = Join-Path $env:TEMP "mentor-loop-evals-smoke"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm raw-weak --work-root "$work" --scorecard "$work\scorecard.csv" --config "$pkg\evals\mock-codex.config.json"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm lessons-only --work-root "$work" --scorecard "$work\scorecard.csv" --config "$pkg\evals\mock-codex.config.json"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm full-loop --work-root "$work" --scorecard "$work\scorecard.csv" --config "$pkg\evals\mock-codex.config.json"
```

Each run appends one row to `scorecard.csv` and prints:

```text
stage: eval-run-task | result: OK | detail: task=...; arm=...; outcome_type=...
```

## Task Set

The suite currently contains 12 real tasks:

- 6 Python tasks.
- 6 JavaScript/TypeScript tasks.
- All have closed issues, merged fix PRs, diff size under 100 lines, checkout
  metadata, env deps, and focused/regression verification commands.
- `jc-685` and `jc-687` are excluded because prior experiments contaminated
  them.

## Run A Real Task

Use a real task JSON from `evals/tasks/` and the real Codex config:

```powershell
$pkg = "path\to\mentor-loop-engine"
$work = "path\to\eval-runs"
$scorecard = "$work\scorecard.csv"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\<task-id>.json" --arm raw-weak --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
```

To collect future replacement tasks from your unrestricted terminal:

```powershell
python "$pkg\evals\collect-tasks.py" --output "$pkg\evals\candidates.json"
```

If GitHub rate limits you:

```powershell
$env:GH_TOKEN = "<fine-grained read-only GitHub token>"
python "$pkg\evals\collect-tasks.py" --output "$pkg\evals\candidates.json"
```

Repeat for `lessons-only` and `full-loop`.

## Rerun Whole Suite

After any template, gate, engine, or model change, rerun every real task across
all three arms:

```powershell
$pkg = "path\to\mentor-loop-engine"
$work = "path\to\eval-runs"
$scorecard = "$work\scorecard.csv"
$arms = @("raw-weak", "lessons-only", "full-loop")
Get-ChildItem "$pkg\evals\tasks" -Filter "*.json" |
  Where-Object { $_.Name -ne "mock-smoke.json" } |
  ForEach-Object {
    foreach ($arm in $arms) {
      python "$pkg\evals\run-task.py" --task $_.FullName --arm $arm --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
    }
  }
```

## Outcome Types

- `accepted`
- `review_blocked`
- `gate_blocked`
- `verification_failure`
- `verification_incomplete`
- `env_failure`
- `infra_error`
- `protocol_violation`

## Regression Semantics

Regression checks are baseline-relative. The runner first records the failing
regression tests on the clean checkout in `baseline-regression.txt`, then runs
the same checks after the model change and counts only new failures. A run with
pre-existing environmental failures can still be `accepted` when focused checks
pass and the regression failure set does not grow.

## Contamination Caveat

Old public fixes may be memorized by current coding models. Prefer issues
closed after the cheap model's training cutoff when that cutoff is known. If
the cutoff is unknown, record `training_cutoff_relation: unknown` and disclose
that the task may be contaminated. Keep old tasks only as regression fixtures,
not as evidence of real-world uplift.

## Swap Rule

If a task cannot pass `env-preflight-check.py` after 30 minutes of setup, swap
it out instead of heroically repairing that repo.
