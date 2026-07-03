# jc-687 Ablation Results

This file records the four-arm ablation for `jc-687`.

Question:

- Do lessons from `jc-685` transfer to a different but related parser bug?
- Does a Mentor Brief add value above those transferred lessons?

Arms:

- A: raw weak.
- B: weak + `jc-685` lessons only.
- C: weak + `jc-685` lessons + Mentor Brief.
- D: strong direct.

Shared environment:

- `TZ=PST8PDT`
- Bundled Python path:
  `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Current status:

- Run directories are prepared and baseline-focused verification passes.
- A arm has two live rows:
  - `raw-weak,1` functionally fixed the bug but violated protocol by creating
    untracked `.surgical-fix/` artifacts outside blast radius.
  - `raw-weak,2` produced a clean accepted patch.

## A: Raw Weak

### `jc-687,raw-weak,1`

Result:

- `outcome_type=protocol_violation`
- `success=false`

Evidence:

- Focused verification under `TZ=PST8PDT`: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Changed tracked files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`
- Extra untracked artifact:
  - `.surgical-fix/`

Review verdict:

- Blocked as raw-weak evidence because the run used hidden workflow help and
  created out-of-scope artifacts.

Gate lesson:

- The first blast-radius gate missed untracked files because it read
  `git diff --name-only`.
- The gate was upgraded to read `git status --porcelain`.
- After the upgrade, this run is correctly blocked:
  - `outside_blast_radius: .surgical-fix/`

### `jc-687,raw-weak,2`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Focused verification under `TZ=PST8PDT`: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added a focused `raw=True` regression for `D:\Users\testuser`.

Interpretation:

- Clean raw weak can solve `jc-687` under unified environment hygiene.
- This raises the bar for B/C: lessons and brief need to reduce failures or
  improve review quality, not merely produce one successful patch.

## B: Lessons Only

### `jc-687,lessons-only,1`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Focused verification under `TZ=PST8PDT`: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added focused parent assertions for `D:\Users\testuser`.

Lesson-transfer signal:

- The model checked `setup.py` and avoided `removeprefix()` because
  `python_requires='>=3.6'`.

### `jc-687,lessons-only,2`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Focused verification under `TZ=PST8PDT`: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added a focused regression for `D:\Users\testuser`.

Lesson-transfer signal:

- The model checked `setup.py` and avoided newer Python APIs.

Interpretation:

- `jc-685` lessons transferred to `jc-687` within the same repository and bug
  family.
- The lessons-only arm had fewer protocol problems than raw weak in this sample.

## C: Lessons + Mentor Brief

### `jc-687,lessons-brief,1`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Baseline verification before editing: `Ran 9 tests`, `OK`.
- Bug reproduction before editing: parent path was `:\Users\testuser`.
- Focused verification after editing: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added focused parent assertion for `D:\Users\testuser`.

Brief contribution:

- The run read all required context files.
- It recorded one concrete finding per file.
- It ran baseline before editing and reproduced the bug before fixing.
- It explicitly checked `python_requires='>=3.6'`.

### `jc-687,lessons-brief,2`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Baseline verification before editing: `Ran 9 tests`, `OK`.
- Bug reproduction before editing: parent path was `:\Users\testuser`.
- Focused verification after editing: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added focused parent assertion for `D:\Users\testuser`.

Brief contribution:

- The run read all required context files.
- It recorded one concrete finding per file.
- It ran baseline before editing and reproduced the bug before fixing.
- It explicitly checked `python_requires='>=3.6'`.

Interpretation:

- C did not improve success rate over B on this easy task.
- C did improve auditability: both runs produced baseline, repro, context, stop
  condition, and compatibility evidence in the execution log.

## D: Strong Direct

### `jc-687,strong-direct,1`

Result:

- `outcome_type=accepted`
- `success=true`

Evidence:

- Baseline verification before editing: `Ran 9 tests`, `OK`.
- Regression failed before the fix: expected `D:\Users\testuser`, got
  `:\Users\testuser`.
- Focused verification after editing: `Ran 10 tests`, `OK`.
- Direct behavior check: parent path was `D:\Users\testuser`.
- Blast-radius gate: `result: OK`.
- Changed files:
  - `jc/parsers/dir.py`
  - `tests/test_dir.py`

Diff shape:

- Replaced `line.lstrip(" Directory of ")` with exact prefix slicing:
  `line[len(" Directory of "):]`.
- Added a focused regression with realistic `dir` header context.

Strong-direct signal:

- The run read parser, tests, setup metadata, and relevant fixtures.
- It performed a red/green-style regression check before the final pass.
- It checked `python_requires='>=3.6'` and avoided newer APIs.
- Token cost was unavailable, so this is a quality baseline, not a cost
  denominator.

## Interim Conclusion

`jc-687` is a cleaner task than `jc-685` because environment hygiene was unified
from the start.

Current evidence:

| Arm | Rows | Accepted | Blocked / invalid | Signal |
|---|---:|---:|---:|---|
| A raw weak | 2 | 1 | 1 protocol violation | Raw weak can solve, but protocol drift happened. |
| B lessons only | 2 | 2 | 0 | `jc-685` lessons transferred within repo and bug family. |
| C lessons + brief | 2 | 2 | 0 | Same success as B, better execution evidence. |
| D strong direct | 1 | 1 | 0 | Best audit trail and red/green behavior, cost unavailable. |

Interpretation:

- Lesson transfer is supported for same-repo, same-bug-family tasks.
- Mentor Brief did not improve success rate over lessons-only on this task.
- Mentor Brief did improve auditability: baseline, bug reproduction, context
  findings, stop-condition checks, and compatibility checks were consistently
  present.
- The upgraded blast-radius gate caught an out-of-scope untracked artifact in
  `raw-weak,1`; this is a concrete review-to-gate distillation.
- Cost uplift remains unproven because token counts are unavailable.
