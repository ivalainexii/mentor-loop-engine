# pflow-389 Boundary Run Ledger

This is a cheap boundary run, not a benchmark. Its purpose is to mark the edge
of same-repository lesson transfer after `jc-687`.

## Baseline

Source checkout:

- `work/public-dogfood/pflow`

That directory was not a git repository, so a local baseline repository was
created from the public checkout:

- `work/mentor-loop-runs/pflow-389-baseline-repo`

Run directories:

- `work/mentor-loop-runs/pflow-389-raw-weak-1`
- `work/mentor-loop-runs/pflow-389-lessons-only-1`
- `work/mentor-loop-runs/pflow-389-lessons-only-2`

## Environment Boundary

The public task requested:

```powershell
uv run pytest tests/test_core/test_markdown_parser.py -q
```

The available environment could not run the focused parser tests:

- `uv` was not found.
- `python` was not found in the weak-model run PATH.
- Bundled Python was available to the coordinator, but it lacked `pytest` and
  `PyYAML`.

Therefore this run records patch shape, gate behavior, and review plausibility.
It does not prove functional success.

## Arms

### A: Raw Weak

- Directory: `work/mentor-loop-runs/pflow-389-raw-weak-1`
- Prompt: issue only, no transferred lessons.
- Changed files:
  - `src/pflow/core/markdown_parser.py`
  - `tests/test_core/test_markdown_parser.py`
- Gate: passed.
- Verification: incomplete because dependencies were unavailable.

### B1: Lessons Only

- Directory: `work/mentor-loop-runs/pflow-389-lessons-only-1`
- Prompt: issue plus transferred lessons.
- Changed files:
  - `src/pflow/core/markdown_parser.py`
  - `tests/test_core/test_markdown_parser.py`
- Gate: passed.
- Verification: incomplete because dependencies were unavailable.
- Lesson hit: the model explicitly applied the nested-context-before-surface-
  syntax lesson.

### B2: Lessons Only

- Directory: `work/mentor-loop-runs/pflow-389-lessons-only-2`
- Prompt: issue plus transferred lessons.
- Changed files:
  - `src/pflow/core/markdown_parser.py`
  - `tests/test_core/test_markdown_parser.py`
- Gate: passed.
- Verification: incomplete because dependencies were unavailable.
- Lesson hit: the model explicitly applied the nested-context-before-surface-
  syntax lesson.
