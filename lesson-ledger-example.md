# Lesson Ledger Example

This is a concrete example of what a small `mentor-loop/lessons.md` file can
look like after a few runs.

Use it as a shape to imitate, not as universal content to copy blindly.

## Active

### ML-JC-001: Check Runtime Floor Before Using New APIs

- `lesson_id`: ML-JC-001
- `scope`: repo
- `created_at`: 2026-06-11
- `created_by`: strong review
- `source_failure`: `jc-685,weak-direct,3`
- `source_artifact`: `experiments/jc-685-live-results.md`
- `hit_count`: 2
- `last_hit_at`: 2026-06-11
- `status`: candidate_gate
- `trigger`: A patch uses a convenient language/library API whose minimum
  supported version may be newer than the project supports.
- `mistake`: The model passed local focused tests but used `str.removeprefix()`
  in a project whose metadata supported Python 3.6.
- `rule_for_next_time`: Before choosing newer APIs, inspect project metadata
  such as `python_requires`, `engines`, `tox.ini`, CI config, or equivalent
  runtime constraints. Prefer implementations that satisfy the supported floor.
- `example`: In `jc`, check `setup.py` before using Python string helpers added
  after Python 3.6.
- `candidate_gate`: Implemented narrowly for common Python API checks in
  `gates/runtime-floor-check.py`.
- `retirement_notes`: Recheck after upgrading the execution model or after the
  target repo raises its runtime floor.

Why this moved toward a gate:

- It prevented later related `jc` runs from choosing an incompatible API.
- The first gate is intentionally narrow: it checks changed Python files for
  known APIs such as `removeprefix` and `removesuffix` against the declared
  runtime floor.

## Candidate Gates

### ML-GATE-001: Block Untracked Artifacts Outside Blast Radius

- `lesson_id`: ML-GATE-001
- `scope`: general
- `created_at`: 2026-06-11
- `created_by`: gate failure analysis
- `source_failure`: `jc-687,raw-weak,1`
- `source_artifact`: `experiments/jc-687-ablation-results.md`
- `hit_count`: 1
- `last_hit_at`: 2026-06-11
- `status`: candidate_gate
- `trigger`: A model creates helper files, scratch directories, or hidden
  workflow artifacts that were not allowed by the Mentor Brief.
- `mistake`: The original blast-radius check used `git diff --name-only`, which
  missed untracked `.surgical-fix/` artifacts.
- `rule_for_next_time`: Treat untracked files as changed files unless the brief
  explicitly allows them.
- `example`: Use `git status --porcelain`, not only `git diff --name-only`.
- `candidate_gate`: Implemented in `gates/blast-radius-check.py`.
- `retirement_notes`: Keep as a gate. Do not inject as prose when the gate is
  installed and running.

Why this moved toward a gate:

- The trigger is deterministic.
- The check is cheaper and more reliable than asking a reviewer to notice
  hidden artifacts every time.

## Retired

### ML-OLD-001: Always Remind The Model To Run Focused Tests

- `lesson_id`: ML-OLD-001
- `scope`: general
- `created_at`: 2026-06-11
- `created_by`: manual protocol setup
- `source_failure`: early dry-run hygiene
- `source_artifact`: `experiments/jc-685-protocol-dry-run.md`
- `hit_count`: 0
- `last_hit_at`:
- `status`: retired
- `trigger`: Any code change.
- `mistake`: The model might claim completion without running focused tests.
- `rule_for_next_time`: Run focused tests before claiming completion.
- `example`: Run the focused command named in the Mentor Brief.
- `candidate_gate`: Require verification output in the apprentice report.
- `retirement_notes`: Retired as prose because the Mentor Brief and Apprentice
  Execute templates already require focused verification. If this repeats,
  make it a report-shape gate instead of re-adding broad prose.

Why this is retired:

- It is too broad to inject as a lesson.
- It duplicates the core workflow.
- A missing verification output should be caught by review or a future report
  gate, not by a longer prompt.

## Consolidation Notes

After each consolidation pass, write a short note:

```text
2026-06-11:
- Kept ML-JC-001 active because later jc runs used it.
- Promoted ML-GATE-001 to candidate_gate and implemented it in the blast-radius gate.
- Retired ML-OLD-001 because it duplicated the core protocol.
```

The active lesson set should be small enough that a weak model can read it and
actually change behavior. If it only makes the prompt longer, it is debt.
