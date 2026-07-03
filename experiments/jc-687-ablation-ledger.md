# jc-687 Ablation Ledger

Use this ledger for the four-arm `jc-687` experiment.

## Run Map

| Scorecard row | Arm | Run directory | Prompt source | Status |
|---|---|---|---|---|
| `jc-687,raw-weak,1` | A | `work/mentor-loop-runs/jc-687-raw-weak-clean1` | `jc-687-ablation-run-packet.md` Arm A | Complete: protocol violation |
| `jc-687,raw-weak,2` | A | `work/mentor-loop-runs/jc-687-raw-weak-clean2` | `jc-687-ablation-run-packet.md` Arm A | Complete: accepted |
| `jc-687,lessons-only,1` | B | `work/mentor-loop-runs/jc-687-lessons-only-clean1` | `jc-687-ablation-run-packet.md` Arm B | Complete: accepted |
| `jc-687,lessons-only,2` | B | `work/mentor-loop-runs/jc-687-lessons-only-clean2` | `jc-687-ablation-run-packet.md` Arm B | Complete: accepted |
| `jc-687,lessons-brief,1` | C | `work/mentor-loop-runs/jc-687-lessons-brief-clean1` | `jc-687-ablation-run-packet.md` Arm C | Complete: accepted |
| `jc-687,lessons-brief,2` | C | `work/mentor-loop-runs/jc-687-lessons-brief-clean2` | `jc-687-ablation-run-packet.md` Arm C | Complete: accepted |
| `jc-687,strong-direct,1` | D | `work/mentor-loop-runs/jc-687-strong-direct-clean1` | `jc-687-ablation-run-packet.md` Arm D | Complete: accepted |

## Baseline Confirmation

All seven directories were checked before live runs:

- `git status --short` was clean.
- With `TZ=PST8PDT`, `python -m unittest tests.test_dir` returned `Ran 9 tests`
  and `OK`.

## Scoring Rules

Use `outcome_type`:

- `accepted`: patch fixes the behavior, focused tests pass, review accepts.
- `env_failure`: run cannot proceed because the environment command is missing
  or misconfigured.
- `verification_failure`: focused verification fails.
- `review_blocked`: focused tests pass but review finds a blocking issue.
- `no_patch`: model stops or returns no usable patch.
- `protocol_violation`: run uses hidden workflow help, creates out-of-scope
  artifacts, or otherwise violates the arm definition.

Review every weak arm after execution. Review is the measurement instrument, not
part of the weak-model prompt.
