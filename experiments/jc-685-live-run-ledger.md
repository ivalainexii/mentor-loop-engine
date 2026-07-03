# jc-685 Live Run Ledger

Use this ledger while collecting the first real weak-model evidence.

Do not record protocol dry-run results here. Only record fresh weak-model
sessions that used one of the clean run directories below.

## Run Map

| Scorecard row | Prompt arm | Run directory | Prompt source | Status |
|---|---|---|---|---|
| `jc-685,strong-direct,1` | Strong direct | `work/mentor-loop-runs/jc-685-strong-direct-clean1` | Issue-only prompt | Complete: blocked by review |
| `jc-685,weak-direct,1` | Weak direct | `work/mentor-loop-runs/jc-685-weak-direct-clean1` | `jc-685-live-run-packet.md` Arm A | Complete: failed safely, no patch |
| `jc-685,weak-direct,2` | Weak direct | `work/mentor-loop-runs/jc-685-weak-direct-clean2` | `jc-685-live-run-packet.md` Arm A | Complete: passing patch |
| `jc-685,weak-direct,3` | Weak direct | `work/mentor-loop-runs/jc-685-weak-direct-clean3` | `jc-685-live-run-packet.md` Arm A | Complete: blocked by Python floor |
| `jc-685,mentor-loop,1` | Mentor Loop | `work/mentor-loop-runs/jc-685-mentor-loop-clean1` | `jc-685-live-run-packet.md` Arm B | Complete: partial, focused test failed |
| `jc-685,mentor-loop,2` | Mentor Loop | `work/mentor-loop-runs/jc-685-mentor-loop-clean2` | `jc-685-live-run-packet.md` Arm B | Complete: passing patch |
| `jc-685,mentor-loop,3` | Mentor Loop | `work/mentor-loop-runs/jc-685-mentor-loop-clean3` | `jc-685-live-run-packet.md` Arm B | Complete: passing patch |

## Baseline Confirmation

All six ready directories were checked before live runs:

- `git status --short` was clean.
- `python -m unittest tests.test_ifconfig` returned `Ran 13 tests` and `OK`.

If any directory becomes dirty before its model run starts, discard that
directory and create a fresh clone from:

- `work/mentor-loop-runs/jc-685-baseline-repo`

Use clone-time line-ending protection:

```powershell
git -c core.autocrlf=false clone --config core.autocrlf=false work/mentor-loop-runs/jc-685-baseline-repo <new-run-dir>
```

## Evidence To Paste After Each Run

For each row, paste or summarize:

- Model name:
- Session identifier or link:
- Prompt arm used:
- Token counts, if available:
- Human interventions:
- Files read by the weak model:
- Files changed:
- `git diff --name-only` output:
- Focused verification output:
- Broader regression output:
- Blast-radius gate output:
- Strong review verdict, Mentor Loop arm only:
- Lesson captured, if any:

## Result Rules

Mark `success=true` only when:

- The changed code fixes `0x00000000 -> 0.0.0.0`.
- `python -m unittest tests.test_ifconfig` passes.
- The diff is not obviously wrong under strong review or human inspection.

Mark `focused_tests_passed=true` only when:

- `python -m unittest tests.test_ifconfig` exits 0 after the run.

Mark `regression_tests_passed=true` only when:

- `python -m unittest discover tests` exits 0 after the run.

Mark `no_unrelated_breakage=true` only when:

- The broader regression check is clean, or
- The failures match the pre-edit baseline and the diff is inside the blast
  radius.

Mark `gate_failures` with the number of failed gates:

- Dirty checkout before starting.
- Baseline focused test failed before editing.
- Changed files outside blast radius.
- Focused verification failed after editing.
- Strong review blocked the patch.

## Current Non-Evidence

These artifacts are useful but do not count as uplift data:

- `jc-685-protocol-dry-run.md`
- `work/mentor-loop-runs/jc-685-mentor-loop-run1`

These directories are superseded setup mistakes and must not be used:

- `work/mentor-loop-runs/jc-685-weak-direct-run1`
- `work/mentor-loop-runs/jc-685-weak-direct-run2`
- `work/mentor-loop-runs/jc-685-weak-direct-run3`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run1`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run2`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run3`

## Stop Condition

Do not claim product-level uplift from `jc-685` alone.

Allowed claims:

- Task-level evidence for `jc-685`.
- Directional evidence about lesson/hygiene uplift.
- Compatibility-gate lesson from `jc-685,weak-direct,3`.

Do not claim cost uplift until strong-direct and weak-session token costs are
recorded.

See `jc-685-live-results.md` for the current live evidence.
