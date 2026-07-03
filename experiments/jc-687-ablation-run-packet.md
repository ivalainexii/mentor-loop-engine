# jc-687 Ablation Run Packet

Use this packet to test whether `jc-685` lessons transfer to `jc-687`, and
whether a Mentor Brief adds value above those lessons.

Do not use `pflow-389` yet.

## Shared Environment Hygiene

Every arm gets the same environment instructions:

```powershell
$env:TZ='PST8PDT'
C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

Focused verification:

```powershell
$env:TZ='PST8PDT'
python -m unittest tests.test_dir
```

Known local baseline under this environment:

- `Ran 9 tests`
- `OK`

Project runtime floor:

- `setup.py` declares `python_requires='>=3.6'`.
- Do not use Python APIs newer than Python 3.6.

## Source Task

Fix `kellyjonbrazil/jc` issue 687:

- The `dir` parser mishandles Windows directory headers such as
  ` Directory of D:\Users\testuser`.
- The current parser can strip the `D` from the drive-letter path.
- The parent path should remain `D:\Users\testuser`.

## Four Arms

Run order:

1. A: raw weak, two runs.
2. B: weak + jc-685 lessons only, two runs.
3. C: weak + jc-685 lessons + Mentor Brief, two runs.
4. D: strong-direct, one run.

Rationale:

- A is the clean weak-model baseline.
- B measures cross-task lesson transfer.
- C measures the Mentor Brief's marginal value above lessons.
- D is the strong-model quality and cost reference.

Every arm must use a fresh model session and an independent checkout.

## A: Raw Weak Prompt

Use for:

- `jc-687,raw-weak,1`
- `jc-687,raw-weak,2`

```text
You are working in the `kellyjonbrazil/jc` repository.

Fix issue 687:

The `dir` parser mishandles Windows directory headers like
` Directory of D:\Users\testuser`. The parser should preserve the drive letter
in the parent directory path, returning `D:\Users\testuser`, not a path with the
`D` stripped off.

Please make the smallest correct code change, add or update tests if
appropriate, and run the relevant verification.

Uniform environment:

- Set `TZ=PST8PDT` before running tests.
- If `python` is not available in PATH, use:
  `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Return:

- Files read.
- Files changed.
- Verification commands and results.
- Unified diff.
```

## B: Lessons-Only Prompt

Use for:

- `jc-687,lessons-only,1`
- `jc-687,lessons-only,2`

```text
You are working in the `kellyjonbrazil/jc` repository.

Fix issue 687:

The `dir` parser mishandles Windows directory headers like
` Directory of D:\Users\testuser`. The parser should preserve the drive letter
in the parent directory path, returning `D:\Users\testuser`, not a path with the
`D` stripped off.

Use these lessons from a previous task:

1. Environment lesson: set `TZ=PST8PDT` before running tests. If `python` is not
   available in PATH, use
   `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
2. Test lesson: prefer focused field-level assertions for parser regressions
   instead of replacing existing fixture coverage.
3. Runtime lesson: check project metadata such as `python_requires` before using
   newer language APIs.
4. Prefix lesson: `strip`, `lstrip`, and `rstrip` remove character sets, not
   literal strings. When removing a known fixed prefix, remove exactly that
   prefix.

Please make the smallest correct code change, add or update tests if
appropriate, and run the relevant verification.

Return:

- Files read.
- Files changed.
- Verification commands and results.
- Compatibility constraints checked.
- Unified diff.
```

## C: Lessons + Mentor Brief Prompt

Use for:

- `jc-687,lessons-brief,1`
- `jc-687,lessons-brief,2`

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
8. Extract runtime, dependency, and compatibility constraints.

Use these lessons:

1. Set `TZ=PST8PDT` before running tests.
2. If `python` is not available in PATH, use
   `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
3. Prefer focused field-level assertions for parser regressions instead of
   replacing existing fixture coverage.
4. Check project metadata such as `python_requires` before using newer language
   APIs.
5. `strip`, `lstrip`, and `rstrip` remove character sets, not literal strings.
   When removing a known fixed prefix, remove exactly that prefix.

Output after execution:

- Files read and one finding from each.
- Baseline command and result.
- Files changed and why.
- Stop conditions checked.
- Runtime and compatibility constraints checked.
- Verification command and result.
- Remaining uncertainty.
- Unified diff.

Mentor Brief:

---

# Public Test Mentor Brief: `kellyjonbrazil/jc` Issue 687

## User Task

Fix `jc/parsers/dir.py` so parsing a Windows directory header like
` Directory of D:\Users\testuser` preserves the drive letter. The expected
parent path is `D:\Users\testuser`.

## Context Pack

Read these files before editing:

1. `jc/parsers/dir.py`
2. `tests/test_dir.py`
3. `CONTRIBUTING.md`
4. `setup.py`

Do not proceed unless all required files are found and read.

## Project Constraints

- `setup.py` declares `python_requires='>=3.6'`.
- Do not use Python APIs newer than Python 3.6.
- Test command must set `TZ=PST8PDT`.

## Blast Radius

Likely touched files:

- `jc/parsers/dir.py`
- `tests/test_dir.py`

Potentially affected behavior:

- Parent directory extraction for Windows `dir` output.
- Existing Windows `dir` parser tests.

Do not touch:

- Other parsers.
- CLI behavior.
- Filename parsing logic.
- Date/time parsing logic.
- Directory entry size or `<DIR>` handling.

## Baseline Before Editing

Run:

- `TZ=PST8PDT python -m unittest tests.test_dir`

Expected current result:

- `Ran 9 tests`
- `OK`

Also reproduce the bug:

- Parse an input containing ` Directory of D:\Users\testuser`.
- Confirm the current parent path is wrong before editing.

If the baseline fails before editing, stop.

## Execution Plan

1. Locate parent directory header extraction in `jc/parsers/dir.py`.
2. Add focused regression coverage proving `D:\Users\testuser` is preserved.
3. Replace character-set stripping with exact prefix removal for the known
   header prefix.
4. Preserve existing `C:` and mixed fixture behavior.
5. Run focused `dir` parser tests with `TZ=PST8PDT`.

## Stop Conditions

Stop if:

- Required files are missing.
- Required files were not read.
- Implementation requires files outside the blast radius.
- The fix uses a Python API newer than the project-supported floor.
- Existing fixtures make inline regression tests inappropriate and fixture
  updates are needed.
- You are about to rewrite unrelated filename, size, date, or directory-entry
  parsing.

## Verification

Run:

- `TZ=PST8PDT python -m unittest tests.test_dir`

Expected result:

- The command exits with code 0.
- A focused regression test proves the `D:` drive letter is preserved.
- Existing Windows `dir` parser tests still pass.
```

## D: Strong Direct Prompt

Use for:

- `jc-687,strong-direct,1`

```text
You are working in the `kellyjonbrazil/jc` repository.

Fix issue 687:

The `dir` parser mishandles Windows directory headers like
` Directory of D:\Users\testuser`. The parser should preserve the drive letter
in the parent directory path, returning `D:\Users\testuser`, not a path with the
`D` stripped off.

Please make the smallest correct code change, add or update tests if
appropriate, and run the relevant verification.

Uniform environment:

- Set `TZ=PST8PDT` before running tests.
- If `python` is not available in PATH, use:
  `C:\Users\<user>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Return:

- Files read.
- Files changed.
- Verification commands and results.
- Compatibility constraints checked.
- Unified diff.
```

## Review Prompt For A/B/C

After each weak run, review the diff and log as a measurement pass.

Focus on:

- Whether the fix removes exactly the known ` Directory of ` prefix.
- Whether `D:` is preserved.
- Whether existing fixture coverage was preserved rather than replaced.
- Whether Python 3.6 compatibility was preserved.
- Whether changed files stayed inside `jc/parsers/dir.py` and `tests/test_dir.py`.
- Whether focused verification supports completion.

Record review-blocked patches as failures even if focused tests pass.
