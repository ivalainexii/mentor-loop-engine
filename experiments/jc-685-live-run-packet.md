# jc-685 Live Run Packet

Use this packet to collect real weak-model evidence for `jc-685`.

This is not automation. It is the manual glue for running the first valid
experiment without changing the v0 protocol.

## Rule

Do not use the protocol dry-run patch as hidden context.

Each arm must start from a fresh checkout or independent worktree and a fresh
model session.

## Source Task

Task:

- Fix `kellyjonbrazil/jc` issue 685.
- `ifconfig` parser uses `lstrip('0x')` for hex subnet masks.
- `0x00000000` should become `0.0.0.0`, not an empty string.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Known local Python executable for this workspace:

```powershell
C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

If `python` is not available in PATH, use:

```powershell
& 'C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_ifconfig
```

Broader regression check:

```powershell
python -m unittest discover tests
```

Known environment note:

- On this Windows/Toronto machine, the broader command currently fails before
  editing with `156 failures, 17 skipped`, mostly timestamp/epoch differences.
- Treat focused ifconfig success as the usable local gate.
- Treat full-suite no-regression as inconclusive unless the same command is
  green before editing in the run environment.

## Human Setup For Each Run

1. Create a fresh copy or worktree of `jc`.
2. Start a fresh model session.
3. Do not reveal results from other arms.
4. Record model name, prompt text, and token counts if available.
5. After the model finishes, run:

```powershell
git diff --name-only
python -m unittest tests.test_ifconfig
python -m unittest discover tests
```

6. Run the blast-radius gate from the target `jc` checkout root. Keep the
   current directory inside the checkout so the gate reads that checkout's
   `git diff`:

```powershell
python <mentor-loop-root>/outputs/mentor-loop-lean-v0/gates/blast-radius-check.py --brief <mentor-loop-root>/outputs/public-test-jc-685-mentor-brief.md
```

If the checkout is not a git worktree, pass changed files manually:

```powershell
python <mentor-loop-root>/outputs/mentor-loop-lean-v0/gates/blast-radius-check.py --brief <mentor-loop-root>/outputs/public-test-jc-685-mentor-brief.md --changed jc/parsers/ifconfig.py --changed tests/test_ifconfig.py
```

## Prepared Local Run Directories

These directories are pre-cloned from a clean local baseline and are ready for
live weak-model runs:

Weak direct:

- `work/mentor-loop-runs/jc-685-weak-direct-clean1`
- `work/mentor-loop-runs/jc-685-weak-direct-clean2`
- `work/mentor-loop-runs/jc-685-weak-direct-clean3`

Mentor Loop:

- `work/mentor-loop-runs/jc-685-mentor-loop-clean1`
- `work/mentor-loop-runs/jc-685-mentor-loop-clean2`
- `work/mentor-loop-runs/jc-685-mentor-loop-clean3`

Baseline status:

- All six directories have clean `git status --short`.
- All six directories pass `python -m unittest tests.test_ifconfig` with
  `Ran 13 tests` and `OK`.

Do not use these superseded setup directories for scorecard runs:

- `work/mentor-loop-runs/jc-685-weak-direct-run1`
- `work/mentor-loop-runs/jc-685-weak-direct-run2`
- `work/mentor-loop-runs/jc-685-weak-direct-run3`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run1`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run2`
- `work/mentor-loop-runs/jc-685-mentor-loop-live-run3`

They were created before clone-time line-ending settings were corrected and
show dirty fixture diffs on Windows.

## Arm A: Weak Direct Prompt

Paste this into a fresh weak-model session:

```text
You are working in the `kellyjonbrazil/jc` repository.

Fix issue 685:

The `ifconfig` parser mishandles macOS/FreeBSD-style hex netmasks because it
uses `lstrip('0x')`. For a netmask like `0x00000000`, the parser should return
`0.0.0.0`, not an empty string.

Please make the smallest code change, add or update tests if appropriate, and
run the relevant verification.

If `python` is not available in PATH, use:

`C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

For the regression test, prefer field-level assertions:

- `result[0]['ipv4_mask'] == '0.0.0.0'`
- `result[0]['ipv4'][0]['mask'] == '0.0.0.0'`

Do not assert the entire parsed object unless every expected field is included.

Check the project's supported Python floor before choosing an implementation.
Do not use APIs newer than that floor.

Return:

- Files read.
- Files changed.
- Verification commands and results.
- Unified diff.
```

Run this arm 2-3 times if budget allows. Record each run separately.

## Arm B: Mentor Loop Prompt

Paste this into a fresh weak-model session:

```text
You are the Apprentice.

Execute the Mentor Brief exactly. Treat it as a contract. Do not expand the
task. Do not edit outside the Blast Radius. Stop if a stop condition is hit.

Before editing:

1. Read the entire Mentor Brief.
2. Read every Context Pack file.
3. Record one concrete finding from each file.
4. Extract allowed files from Blast Radius.
5. Extract do-not-touch files or areas.
6. Extract stop conditions.
7. Extract verification commands.
8. Run the baseline verification before editing.

If `python` is not available in PATH, use:

`C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Output after execution:

- Files read and one finding from each.
- Baseline command and result.
- Files changed and why.
- Stop conditions checked.
- Verification command and result.
- Remaining uncertainty.
- Unified diff.

Mentor Brief:

---

# Public Test Mentor Brief: `kellyjonbrazil/jc` Issue 685

Source issue: https://github.com/kellyjonbrazil/jc/issues/685

## User Task

Fix `jc/parsers/ifconfig.py` so macOS/FreeBSD-style hex subnet masks such as
`0x00000000` convert to dotted-quad form correctly. The expected result for
`0x00000000` is `0.0.0.0`, not an empty string.

## Context Pack

Read these files before editing:

1. `jc/parsers/ifconfig.py`
2. `tests/test_ifconfig.py`
3. `CONTRIBUTING.md`
4. `setup.py`

Do not proceed unless all required files are found and read.

## Project Constraints

- `setup.py` declares `python_requires='>=3.6'`.
- Do not use Python APIs newer than Python 3.6 for this fix.

## Blast Radius

Likely touched files:

- `jc/parsers/ifconfig.py`
- `tests/test_ifconfig.py`

Potentially affected behavior:

- Conversion of macOS/FreeBSD-style `0x...` IPv4 netmasks to dotted-quad form.
- Existing Linux, macOS, and FreeBSD ifconfig parser tests.

Do not touch:

- Other parsers.
- CLI behavior.
- Fixture formats outside the new focused regression case unless the existing
  test style requires a fixture update.
- IPv6 mask conversion.
- CIDR-to-quad conversion logic.

## Baseline Before Editing

Run:

- `python -m unittest tests.test_ifconfig`

Expected current result:

- The command exits with code 0.

Also reproduce the bug:

- Parse an `ifconfig` sample containing `netmask 0x00000000`.
- Confirm the current result is wrong before editing.
- If `python` is not available in PATH, use
  `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

If the baseline fails before editing, stop.

## Execution Plan

1. Locate both `lstrip('0x')` calls used for IPv4 hex mask conversion.
2. Add a focused regression test for `netmask 0x00000000` that expects
   `ipv4_mask == '0.0.0.0'`.
   Prefer field-level assertions for `ipv4_mask` and `ipv4[0]['mask']`; do not
   assert the entire parsed object unless every expected field is included.
3. Replace each `new_mask.lstrip('0x')` used for known `0x`-prefixed masks with
   literal prefix removal.
4. Do not alter behavior for masks that do not start with `0x`.
5. Run focused ifconfig tests.

## Stop Conditions

Stop if:

- Required files are missing.
- Required files were not read.
- Implementation requires files outside the blast radius.
- The fix uses a Python API newer than the project-supported floor.
- Existing tests are fixture-only and adding an inline regression test conflicts
  with project style.
- Test failures appear unrelated to `ifconfig`.
- The parser has another authoritative mask conversion helper that should be
  used instead of local slicing.
- You are about to change CIDR or IPv6 mask behavior.

## Verification

Run:

- `python -m unittest tests.test_ifconfig`

Expected result:

- The command exits with code 0.
- A focused regression test proves `0x00000000` becomes `0.0.0.0`.
- Existing ifconfig fixture tests still pass.
```

Run this arm 2-3 times if budget allows. Record each run separately.

## Strong Review Prompt

After each Mentor Loop run, paste the Mentor Brief, diff, execution log, and
verification output into a strong-model session:

```text
Review the diff and execution log against the Mentor Brief.

Focus on:

- Whether both `lstrip('0x')` sites were handled.
- Whether the fix removes only the literal `0x` prefix.
- Whether non-hex, CIDR, and IPv6 mask behavior was preserved.
- Whether the test would fail before the fix and pass after it.
- Whether the weak model touched files outside the blast radius.
- Whether verification output supports completion.

Return only:

- Blocking issues.
- Non-blocking concerns.
- Required fixes.
- Whether another review pass is needed.
- Any reusable lesson candidate.
```

## Scorecard Mapping

Fill one row per run in `scorecard-template.csv`.

- `task`: `jc-685`
- `arm`: `weak-direct` or `mentor-loop`
- `run_id`: `1`, `2`, or `3`
- `success`: true only if focused tests pass and the diff fixes the bug
- `focused_tests_passed`: result of `python -m unittest tests.test_ifconfig`
- `regression_tests_passed`: result of `python -m unittest discover tests`
- `no_unrelated_breakage`: true only if regression check was clean or failures
  matched pre-edit baseline
- `strong_brief_tokens`: Mentor Loop only
- `strong_review_tokens`: Mentor Loop only
- `strong_escalation_tokens`: any strong-model fix after weak execution
- `weak_tokens`: weak-model generation tokens
- `human_interventions`: number of manual corrections during the run
- `gate_failures`: number of blast-radius or verification failures
- `lessons_captured`: number of reusable rules recorded

Do not mark this task as uplift evidence until at least one weak-direct run and
one Mentor Loop run have been collected from fresh weak-model sessions.
