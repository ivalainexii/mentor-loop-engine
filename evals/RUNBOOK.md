# Eval Baseline Runbook

This is the copy-paste sequence for the human live baseline. The Codex desktop
sandbox cannot execute the Codex CLI, so live runs happen in your normal
terminal.

## 0. Set Paths

```powershell
$pkg = "path\to\mentor-loop-engine"
$work = "path\to\eval-runs"
$scorecard = "$work\scorecard.csv"
New-Item -ItemType Directory -Force -Path $work | Out-Null
python -m pip install pytest
```

## 1. Verify The Mock Runner

```powershell
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm raw-weak --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\mock-codex.config.json"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm lessons-only --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\mock-codex.config.json"
python "$pkg\evals\run-task.py" --task "$pkg\evals\tasks\mock-smoke.json" --arm full-loop --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\mock-codex.config.json"
```

Expected: all three print `outcome_type=accepted`.

## 2. Verify Real Codex CLI

```powershell
codex --version
codex exec --help
```

Expected: both commands print help/version output.

## 3. Run One Real Task Across All Arms

```powershell
$task = "$pkg\evals\tasks\<task-id>.json"
python "$pkg\evals\run-task.py" --task "$task" --arm raw-weak --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
python "$pkg\evals\run-task.py" --task "$task" --arm lessons-only --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
python "$pkg\evals\run-task.py" --task "$task" --arm full-loop --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
```

## 4. Run Full Baseline

```powershell
$arms = @("raw-weak", "lessons-only", "full-loop")
Get-ChildItem "$pkg\evals\tasks" -Filter "*.json" |
  Where-Object { $_.Name -ne "mock-smoke.json" } |
  ForEach-Object {
    foreach ($arm in $arms) {
      python "$pkg\evals\run-task.py" --task $_.FullName --arm $arm --work-root "$work" --scorecard "$scorecard" --config "$pkg\evals\codex-live.config.json"
    }
  }
```

Expected runtime: plan for 20-45 minutes per task-arm on small repos once env
deps are installed. For 12 tasks x 3 arms, budget one long day or split across
several sessions.

Rough token budget: expect 10k-30k tokens per raw/lessons run and 25k-60k per
full-loop run, depending on repo size and tests. The scorecard records outcomes
but not token counts; record token observations manually in the `notes` column
when available.

## 5. Read Results

```powershell
Import-Csv $scorecard | Format-Table task_id,arm,outcome_type,env_preflight_exit,model_exit,focused_exit,regression_exit -AutoSize
```

Any `env_failure` after 30 minutes of setup means swap the task.

## 6. Collect Replacement Candidates

Use this only when a task must be swapped:

```powershell
python "$pkg\evals\collect-tasks.py" --output "$pkg\evals\candidates.json"
```

If GitHub rate limits you:

```powershell
$env:GH_TOKEN = "<fine-grained read-only GitHub token>"
python "$pkg\evals\collect-tasks.py" --output "$pkg\evals\candidates.json"
```
