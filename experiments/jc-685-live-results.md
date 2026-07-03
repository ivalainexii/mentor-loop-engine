# jc-685 Live Results

This file records the first real model runs for `jc-685`.

Model used for both arms:

- `gpt-5.3-codex-spark`
- Reasoning effort: `low`

These results are valid model-run evidence, but they do not prove product-level
uplift yet because updated packet lessons helped both weak-direct and Mentor
Loop runs, and strong-direct token cost is still unavailable.

Accounting caveats:

- `jc-685,weak-direct,1` is `outcome_type=env_failure`; exclude it from
  model-capability comparisons.
- `jc-685` became task-contaminated after early lessons were added back into the
  packet. Later successes show task-internal lesson effectiveness, not
  cross-task lesson transfer.
- `weak-direct,2` and `weak-direct,3` are lesson-enriched weak-direct runs, not
  raw issue-only runs.
- Strong review is treated as a measurement instrument for every weak arm.
  Review-blocked patches are failures even when focused tests pass.

## Summary

| Row | Result | Notes |
|---|---|---|
| `jc-685,strong-direct,1` | Blocked by review | The strong model fixed code behavior but weakened an existing test instead of adding a regression. |
| `jc-685,weak-direct,1` | Failed safely | The weak model read two relevant files but stopped before editing because it could not find `python`, `py`, or `pytest` in PATH. |
| `jc-685,mentor-loop,1` | Partial | The weak model changed the right code sites and stayed inside blast radius, but wrote a failing regression test. |
| `jc-685,mentor-loop,2` | Passed focused gate | The updated packet gave the weak model a known Python path and field-level test instructions; it produced a passing focused patch inside blast radius. |
| `jc-685,weak-direct,2` | Passed focused gate | The same packet lessons also let weak-direct produce a passing focused patch inside blast radius. |
| `jc-685,mentor-loop,3` | Passed focused gate | Mentor Loop reproduced the passing focused patch using the updated brief. |
| `jc-685,weak-direct,3` | Blocked by review | Focused tests passed, but the patch used `str.removeprefix()` even though the project supports Python 3.6+. |

## Strong Direct Run 1

Run directory:

- `work/mentor-loop-runs/jc-685-strong-direct-clean1`

Prompt arm:

- Issue-only strong-direct prompt, plus the shared Python path for environment
  hygiene.

Model:

- `gpt-5.5`
- Reasoning effort: `medium`

Model result:

- Files read:
  - `.gitignore`
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
  - `runtests.sh`
  - `setup.py`
  - `setup.cfg`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Modified the existing `test_ifconfig_utun_ipv4` sample from `0xffffffff` to
  `0x00000000` instead of adding a new focused regression test.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python:

- `Ran 13 tests`
- `OK`

External behavior check:

- `0.0.0.0`
- `0.0.0.0`

Blast-radius gate:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

- `Ran 1524 tests`
- `FAILED (failures=156, skipped=17)`

Strong-review verdict:

- Blocked.

Blocking issue:

- The code fix is correct, but the test change weakens existing coverage by
  replacing the previous `0xffffffff -> 255.255.255.255` fixture assertion.
- A correct patch should preserve the existing fixture coverage and add a new
  focused regression for `0x00000000`.

Evidence value:

- Strong direct did better on code reasoning and runtime compatibility than the
  blocked weak-direct run.
- Strong direct still needed review: focused tests and blast-radius gates did
  not catch the coverage regression.
- Token cost was unavailable from the subagent session, so this row still does
  not provide a usable cost denominator.

## Weak Direct Run 1

Run directory:

- `work/mentor-loop-runs/jc-685-weak-direct-clean1`

Prompt arm:

- `jc-685-live-run-packet.md` Arm A

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
- Files changed:
  - None
- Model-reported blocker:
  - `python`, `py`, and `pytest` were not available in PATH.
- Model stopped before editing.

External verification:

```powershell
git diff --name-only
```

Result:

- No changed files.

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python:

- `Ran 13 tests`
- `OK`

```powershell
python outputs/mentor-loop-lean-v0/gates/blast-radius-check.py --brief outputs/public-test-jc-685-mentor-brief.md
```

Result:

- `changed_files: (none)`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

```powershell
python -m unittest discover tests
```

Result:

- `Ran 1524 tests`
- `FAILED (failures=156, skipped=17)`

Interpretation:

- This run failed the task because no patch was produced.
- It failed safely: it did not edit outside scope or invent an unverified fix.
- The failure is an environment-discovery failure, not a code reasoning failure.

Lesson candidate:

- Trigger: A live-run prompt asks the weak model to run verification.
- Mistake: The prompt assumes `python` is available in PATH.
- Rule: Include the known Python executable path, or include a deterministic
  environment discovery step before treating verification as blocked.

## Mentor Loop Run 1

Run directory:

- `work/mentor-loop-runs/jc-685-mentor-loop-clean1`

Prompt arm:

- `jc-685-live-run-packet.md` Arm B

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
  - `CONTRIBUTING.md`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
- Model-reported blocker:
  - Could not execute Python in its shell environment.

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Added `test_ifconfig_hex_mask_zero`.

External behavior check:

```powershell
python -c "import jc.parsers.ifconfig as p; data='''en0: flags=8843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500\ninet 10.0.0.2 netmask 0x00000000\n'''; r=p.parse(data, quiet=True); print(r[0]['ipv4_mask']); print(r[0]['ipv4'][0]['mask'])"
```

Result:

- `0.0.0.0`
- `0.0.0.0`

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result:

- `Ran 14 tests`
- `FAILED (failures=1)`

Failure:

- `test_ifconfig_hex_mask_zero` expected the full parsed object but omitted the
  parser's `ipv4` list.

Blast-radius gate:

```powershell
python outputs/mentor-loop-lean-v0/gates/blast-radius-check.py --brief outputs/public-test-jc-685-mentor-brief.md
```

Result:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

```powershell
python -m unittest discover tests
```

Result:

- `Ran 1525 tests`
- `FAILED (failures=157, skipped=17)`

Interpretation:

- The extra failure over the known baseline is the weak model's failing focused
  test.
- The code behavior appears correct under direct external check.
- The patch cannot be accepted because focused verification fails.

Strong-review verdict:

- Needs fixes.

Blocking issue:

- The regression test is too broad and has an incorrect expected object shape.

Non-blocking observation:

- The Mentor Brief improved task targeting: the weak model found both code sites
  and stayed inside blast radius.

Lesson candidate:

- Trigger: Adding a focused parser regression test.
- Mistake: The test asserts a full parsed object when only one or two fields are
  relevant, increasing the chance of schema omissions.
- Rule: Prefer field-level assertions for focused parser bug regressions unless
  the project convention requires full-object fixtures.

## Mentor Loop Run 2

Run directory:

- `work/mentor-loop-runs/jc-685-mentor-loop-clean2`

Prompt arm:

- `jc-685-live-run-packet.md` Arm B, updated with:
  - The known bundled Python executable path.
  - Field-level assertions for the focused regression test.

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
  - `CONTRIBUTING.md`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
- Model-reported blocker:
  - `python` was not available in PATH, but the model used the provided bundled
    Python path and continued.

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Added `test_ifconfig_zero_hex_mask` with field-level assertions.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python:

- `Ran 14 tests`
- `OK`

External behavior check:

```powershell
python -c "import jc.parsers.ifconfig as p; data='''en0: flags=8843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500\ninet 10.0.0.2 netmask 0x00000000\n'''; r=p.parse(data, quiet=True); print(r[0]['ipv4_mask']); print(r[0]['ipv4'][0]['mask'])"
```

Result:

- `0.0.0.0`
- `0.0.0.0`

Blast-radius gate:

```powershell
python outputs/mentor-loop-lean-v0/gates/blast-radius-check.py --brief outputs/public-test-jc-685-mentor-brief.md
```

Result:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

```powershell
python -m unittest discover tests
```

Result:

- `Ran 1525 tests`
- `FAILED (failures=156, skipped=17)`

Interpretation:

- The broader suite still fails for the known environment baseline.
- Unlike Mentor Loop run 1, this run did not add an extra focused-test failure.
- The patch fixed the target behavior, passed focused verification, and stayed
  inside blast radius.

Strong-review verdict:

- Acceptable for the `jc-685` focused fix, with broader-suite failures treated
  as pre-existing environment noise.

Evidence value:

- This is the first passing live Mentor Loop weak-model result.
- It is directional uplift evidence for `jc-685`, not product-level proof.
- Cost remains unknown because token counts were not available from the weak
  model session.

## Weak Direct Run 2

Run directory:

- `work/mentor-loop-runs/jc-685-weak-direct-clean2`

Prompt arm:

- `jc-685-live-run-packet.md` Arm A, updated with:
  - The known bundled Python executable path.
  - Field-level assertions for the focused regression test.

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Added `test_ifconfig_zero_hex_netmask` with field-level assertions.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python:

- `Ran 14 tests`
- `OK`

External behavior check:

- `0.0.0.0`
- `0.0.0.0`

Blast-radius gate:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

- `Ran 1525 tests`
- `FAILED (failures=156, skipped=17)`

Interpretation:

- The patch fixed the target behavior, passed focused verification, and stayed
  inside blast radius.
- The broad-suite failures match the known environment baseline.
- This row is not comparable to raw weak-direct run 1 as a pure issue-only
  prompt, because Arm A now includes the environment and focused-test lessons.

Evidence value:

- The captured lessons improved weak-direct execution too.
- This weakens any claim that Mentor Briefs alone caused the `jc-685` success.
- It strengthens the broader product thesis that durable lessons and run hygiene
  make weak models substantially more usable.

## Mentor Loop Run 3

Run directory:

- `work/mentor-loop-runs/jc-685-mentor-loop-clean3`

Prompt arm:

- `jc-685-live-run-packet.md` Arm B, updated with:
  - The known bundled Python executable path.
  - Field-level assertions for the focused regression test.

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
  - `CONTRIBUTING.md`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Added `test_ifconfig_freebsd_netmask_zero_hex` with field-level assertions.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python:

- `Ran 14 tests`
- `OK`

External behavior check:

- `0.0.0.0`
- `0.0.0.0`

Blast-radius gate:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

- `Ran 1525 tests`
- `FAILED (failures=156, skipped=17)`

Interpretation:

- Mentor Loop reproduced the passing focused patch.
- The broad-suite failures match the known environment baseline.
- This supports repeatability after lessons were added, but does not isolate the
  incremental value of the Mentor Brief.

## Weak Direct Run 3

Run directory:

- `work/mentor-loop-runs/jc-685-weak-direct-clean3`

Prompt arm:

- `jc-685-live-run-packet.md` Arm A, before the runtime-floor lesson was added.

Weak-model result:

- Files read:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`
- Files changed:
  - `jc/parsers/ifconfig.py`
  - `tests/test_ifconfig.py`

Diff shape:

- Replaced both `new_mask.lstrip('0x')` calls with
  `new_mask.removeprefix('0x')`.
- Added `test_ifconfig_freebsd_hex_mask_zero` with field-level assertions.

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result using bundled Python 3.12:

- `Ran 14 tests`
- `OK`

External behavior check:

- `0.0.0.0`
- `0.0.0.0`

Blast-radius gate:

- `changed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `allowed_files: jc/parsers/ifconfig.py, tests/test_ifconfig.py`
- `result: OK`

Broader regression:

- `Ran 1525 tests`
- `FAILED (failures=156, skipped=17)`

Strong-review verdict:

- Blocked.

Blocking issue:

- `setup.py` declares `python_requires='>=3.6'`.
- `str.removeprefix()` requires Python 3.9+.
- The patch passes on this local Python 3.12 runtime but can break supported
  Python 3.6, 3.7, and 3.8 users.

Interpretation:

- Focused tests and blast-radius gates were necessary but insufficient.
- A compatibility constraint must be part of the brief or gate when the project
  supports older runtimes.

Lesson candidate:

- Trigger: A patch uses a convenient language/library API.
- Mistake: The model checks only the local runtime and focused tests.
- Rule: Before using a newer API, inspect project metadata such as
  `python_requires`, `engines`, or equivalent runtime constraints.

## Current Evidence Boundary

These rows are the current valid live evidence:

- `jc-685,strong-direct,1`
- `jc-685,weak-direct,1`
- `jc-685,mentor-loop,1`
- `jc-685,mentor-loop,2`
- `jc-685,weak-direct,2`
- `jc-685,mentor-loop,3`
- `jc-685,weak-direct,3`

They show directional value and multiple lesson-enriched successes:

- Weak direct run 1: no patch.
- Mentor Loop run 1: better scoped patch, but failed verification.
- Mentor Loop run 2 after captured lessons: passing focused patch.
- Weak direct run 2 after captured lessons: passing focused patch.
- Mentor Loop run 3 after captured lessons: passing focused patch.
- Weak direct run 3: focused tests passed, but review blocked it for Python
  floor incompatibility.
- Strong direct run 1: focused tests passed, but review blocked it for weakening
  an existing test.

Do not claim product-level uplift yet.

Reasons:

- The raw weak-direct comparison is contaminated by an environment failure.
- Three Mentor Loop rows have run, but two used the lesson-updated packet.
- Strong-direct quality was sampled once, but token cost is not recorded.
- Weak-model token cost is unavailable.
- The strongest current signal is lesson/hygiene uplift, not isolated Mentor
  Brief uplift.
- The newest concrete template lesson is runtime-floor awareness.

Next useful action:

- Move to `jc-687` with a four-arm ablation and unified environment hygiene.
