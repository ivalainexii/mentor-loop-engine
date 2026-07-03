# Mentor Loop Stage Engine v0 Wiring Report

## Wired

- Refactored `tools/mentor-loop.py` into a stage-based engine for interactive
  GUI mentor sessions.
- Kept the one-shot `run` mode for automation.
- Added `mentor-loop.config.json` as the only model/command config.
- The config contains two argv command templates:
  - `strong_command`
  - `apprentice_command`
- Command templates are JSON arrays, not shell strings, so repo/output paths
  with spaces are passed safely to `subprocess.run`.
- The apprentice command uses `codex exec` with a cheaper model profile.
- Long prompts are sent over stdin, not argv, to avoid Windows command-line
  length limits.
- Subprocess prompt input and output are forced through UTF-8 with replacement
  errors, so Chinese task descriptions and Codex output do not depend on the
  Windows system locale.
- `codex exec -o <file>` captures the final apprentice message in stage mode.
  One-shot mode still uses it for the brief, apprentice log, and review.
- Active lessons from the target repo's `.mentor-loop/lessons.md` are injected
  into both the Mentor Brief prompt and the apprentice prompt.
- Stage mode is file-driven:
  - `init`
  - `brief-check`
  - `apprentice`
  - `gates`
  - `snapshot`
  - `capture-lesson`
  - `report`
- Each stage prints one machine-readable summary line:
  `stage: <name> | result: <result> | detail: <detail>`.
- Codex command heads are resolved with `shutil.which()` before subprocess
  execution, so Windows npm `.cmd` shims work when they are on PATH. Missing
  command heads now produce `result: ENV_FAILURE` instead of a bare traceback.
- `snapshot` writes `apprentice-verification-summary.md` before review, and
  the one-shot review prompt explicitly requires reading it before verdict.
- The review pass reuses `strong_command` but overrides the sandbox to
  `read-only` in one-shot mode. In stage mode, the GUI mentor writes
  `review.md` directly.
- The review prompt explicitly says not to edit files or run fix commands.
- Run artifacts are written under `.mentor-loop/runs/<run-id>/`.
- `.mentor-loop/` is added to repo-local `git info/exclude`.
- The driver refuses to start on a dirty worktree, so apprentice edits do not
  mix with pre-existing user changes.
- The driver runs both existing gates:
  - `gates/blast-radius-check.py`
  - `gates/runtime-floor-check.py`
- The driver writes:
  - `mentor-brief-prompt.md`
  - `mentor-brief.md`
  - `mentor-brief-codex.log`
  - `active-lessons.md`
  - `apprentice-prompt.md`
  - `apprentice-log.md`
  - `apprentice-codex.log`
  - `apprentice-exit-code.txt`
  - `gate-blast-radius.txt`
  - `gate-runtime-floor.txt`
  - `diff-and-status.txt`
  - `review-prompt.md`
  - `review.md`
  - `review-codex.log`
  - `lesson.md` only when a reusable lesson is captured
  - `final-report.md`
- `final-report.md` now includes the apprentice verification summary, gate
  results, changed files, review verdict, lesson status, and artifact pointers.

## Verified Inputs

The CLI flags came from `codex-cli-verified-flags.md`, verified on this
machine with `codex-cli 0.139.0`.

Required facts verified there:

- `codex exec` exists.
- `-m` selects model.
- `-C` selects working directory.
- `-s workspace-write` selects sandbox.
- `-o` captures the final message.
- Prompt can be passed on stdin.

## Sandbox Capability Test

From this Codex desktop sandbox, `codex --version` was tested and still fails:

```text
Access is denied
```

No workaround was built. The stage engine remains valid for GUI-driven mentor
sessions, and the apprentice shell-out is still expected to run from an
environment where the independent Codex CLI is executable.

## GUI Live Run

`jc-685` passed through the GUI live-run path with `outcome=accepted`.

Acceptance follow-up fixes captured from that run:

- Resolve codex command heads with `shutil.which()` and report missing command
  heads as `ENV_FAILURE`.
- Treat apprentice runtime availability as an environment concern; if the
  apprentice sandbox cannot find `python`, env-preflight or explicit runtime
  policy must catch it before relying on apprentice self-verification.
- Generate `apprentice-verification-summary.md` during `snapshot`, before
  strong review.

## Template Ambiguities Fixed During Wiring

- The manual workflow did not define machine artifact names; the driver now
  standardizes them under `.mentor-loop/runs/<run-id>/`.
- The lesson template had source metadata but not a driver run id; the driver
  writes `source_run_id`.
- The manual workflow did not say how to persist gate output; the driver writes
  one file per gate with exit code and output.
- The manual workflow assumed a human moved text between models; the engine
  now writes prompt bundles and stage artifacts so a GUI session can drive the
  workflow through files.
- The brief template named Baseline Before Editing, but automation needs proof
  that the baseline actually ran. The driver now stops before apprentice
  execution unless the generated brief includes baseline output or an exit code.
- The strong brief step runs with workspace write permissions because baseline
  commands may need them, but the driver checks the worktree again after brief
  generation and stops before apprentice execution if the brief step changed
  files.
- The manual workflow assumed a clean checkout. The driver now enforces that
  precondition before invoking any model.
- The original wiring captured lessons but did not read them back. The driver
  now reads `status: active` lesson entries and injects them into the next run's
  brief and apprentice prompts.
- Windows text-mode subprocess defaults were ambiguous. The driver now sets
  `encoding="utf-8"` and `errors="replace"` on subprocess calls.
- Windows BOM and console encodings caused a third real failure. Engine and
  gate text reads now use `encoding="utf-8-sig"`, engine stdout/stderr are
  reconfigured to UTF-8 with replacement errors, and verifier includes a
  Windows encoding smoke check.
- The GUI live run showed that reviewer-visible verification summaries must be
  created before review, not only in the final report.
- The one-shot driver was a black box. The engine now exposes independent
  stages so an interactive strong mentor can ask questions, write the brief,
  inspect artifacts, write review, and let deterministic commands handle the
  rest.

## Friction Remaining

- A real bug fix in a real repo has not yet completed end-to-end from this
  stage engine.
- In stage mode, the GUI mentor must write `mentor-brief.md` and `review.md`
  between engine stages.
- The lesson capture parser is intentionally narrow: it captures one lesson
  only when the review fills the expected `Lesson Candidate` bullets.
- Lesson `hit_count` is not updated yet; v0 injects active lessons, while usage
  accounting remains a v1.1 concern.
- No retry loop is built. If review says `Needs fixes`, the current v0 reports
  that verdict rather than launching another apprentice pass.

## Not Built

- Model router.
- Provider registry.
- Generic adapter layer.
- Claude Code port.
- Env preflight gate, because the apprentice path has not yet died from missing
  dependencies in this driver.
