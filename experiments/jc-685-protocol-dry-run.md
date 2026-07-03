# jc-685 Protocol Dry Run

This is a protocol dry run, not a valid weak-model experiment arm.

Purpose:

- Check that the lean v0 workflow can run end to end on `jc-685`.
- Verify the new baseline, blast-radius, focused test, and regression hygiene
  rules against a real public task.
- Avoid entering this result into `scorecard-template.csv` because no live weak
  model produced the patch.

## Setup

Source checkout:

- Original source: `work/public-dogfood/jc`
- Isolated run copy: `work/mentor-loop-runs/jc-685-mentor-loop-run1`
- Local git baseline created in the isolated copy for diff-based gate checks.

Mentor Brief:

- `outputs/public-test-jc-685-mentor-brief.md`

## Baseline Before Editing

Focused baseline:

```powershell
python -m unittest tests.test_ifconfig
```

Result:

- `Ran 13 tests`
- `OK`

Bug reproduction before editing:

```powershell
python -c "import jc.parsers.ifconfig as p; data='''lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384\n    inet 127.0.0.1 netmask 0x00000000\n'''; print(p.parse(data, quiet=True))"
```

Observed bug:

- `ipv4_mask` was `''`
- `ipv4[0].mask` was `''`

Expected:

- `0.0.0.0`

## Patch

Changed files:

- `jc/parsers/ifconfig.py`
- `tests/test_ifconfig.py`

Diff shape:

- Replace both `new_mask.lstrip('0x')` calls with `new_mask[2:]`.
- Add one focused regression test for `netmask 0x00000000`.

Patch size:

- 2 files changed
- 12 insertions
- 2 deletions

## Verification After Editing

Focused verification:

```powershell
python -m unittest tests.test_ifconfig
```

Result:

- `Ran 14 tests`
- `OK`

Bug check after editing:

```powershell
python -c "import jc.parsers.ifconfig as p; data='''lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384\n    inet 127.0.0.1 netmask 0x00000000\n'''; result=p.parse(data, quiet=True); print(result[0]['ipv4_mask']); print(result[0]['ipv4'][0]['mask'])"
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

## Regression Check

Broader regression command:

```powershell
python -m unittest discover tests
```

Result on patched isolated copy:

- `Ran 1525 tests`
- `FAILED (failures=156, skipped=17)`

Same command on the unmodified source copy:

- `Ran 1524 tests`
- `FAILED (failures=156, skipped=17)`

Interpretation:

- The broader suite is not a clean regression gate in this Windows/Toronto
  environment.
- The failures are present before this patch and are dominated by timestamp /
  epoch differences.
- This dry run cannot claim full-suite no-regression.
- It can claim focused ifconfig no-regression and blast-radius containment.

## Strong Review

Verdict:

- No blocking issues for the dry-run patch.

Evidence:

- Both `lstrip('0x')` sites identified in the Mentor Brief were changed.
- The replacement removes only the literal two-character prefix after
  `startswith('0x')`.
- The focused regression would fail before the fix and passes after the fix.
- The automatic blast-radius gate allowed exactly the two changed files.

Non-blocking concern:

- Full-suite regression is inconclusive in this environment because the
  unmodified checkout already fails the same broad command.

## Experiment Status

Do not count this as uplift evidence.

This run proves:

- The v0 protocol can guide a scoped patch.
- The new baseline rule matters.
- The automatic `git diff --name-only` gate works in an isolated git copy.
- The scorecard should distinguish focused success from full regression proof.

This run does not prove:

- Weak-model uplift.
- Cost reduction.
- Best-of-N value.
- Strong-review token cost.

Next valid experiment step:

- Run `jc-685` with a live weak model in a fresh session, 2-3 times, using this
  same Mentor Brief and the same verification commands.
