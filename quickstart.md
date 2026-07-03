# Quickstart

Run Mentor Loop as a stage engine, a one-shot automation, or manually.

## GUI Stage Engine Path

Use this path for the user's normal interactive Codex or Claude Code workflow.
The GUI session is the strong mentor; the engine handles deterministic stages
and the cheap apprentice shell-out.

Prerequisite:

- `codex exec --help` works in your shell.
- `codex-cli-verified-flags.md` matches your installed Codex CLI behavior.

Invoke `init` first:

```powershell
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py init --repo path\to\target-repo "fix <bug description or issue summary>"
```

Then the GUI mentor writes:

```text
.mentor-loop/runs/<run-id>/mentor-brief.md
```

Validate the brief and continue:

```powershell
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py brief-check --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py apprentice --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py gates --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py snapshot --repo path\to\target-repo --run <run-id>
```

The GUI mentor reviews the artifacts and writes:

```text
.mentor-loop/runs/<run-id>/review.md
```

Then finish:

```powershell
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py capture-lesson --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py report --repo path\to\target-repo --run <run-id>
```

Expected artifacts:

- `.mentor-loop/runs/<run-id>/mentor-brief-prompt.md`
- `.mentor-loop/runs/<run-id>/active-lessons.md`
- `.mentor-loop/runs/<run-id>/mentor-brief.md`
- `.mentor-loop/runs/<run-id>/apprentice-prompt.md`
- `.mentor-loop/runs/<run-id>/apprentice-log.md`
- `.mentor-loop/runs/<run-id>/apprentice-codex.log`
- `.mentor-loop/runs/<run-id>/apprentice-exit-code.txt`
- `.mentor-loop/runs/<run-id>/gate-blast-radius.txt`
- `.mentor-loop/runs/<run-id>/gate-runtime-floor.txt`
- `.mentor-loop/runs/<run-id>/diff-and-status.txt`
- `.mentor-loop/runs/<run-id>/review.md`
- `.mentor-loop/runs/<run-id>/final-report.md`
- `.mentor-loop/lessons.md` only when review captures a reusable lesson

Expected control flow:

1. `init` creates the run directory, prompt bundle, and active lesson file.
2. GUI mentor writes the Mentor Brief and includes baseline output.
3. `brief-check` validates the brief and clean worktree.
4. `apprentice` invokes cheap Codex in the target repo.
5. `gates` runs blast-radius and runtime-floor checks.
6. `snapshot` writes diff and status.
7. GUI mentor reviews only artifacts and writes `review.md`.
8. `capture-lesson` and `report` finish the run.

## Codex Native One-Shot Path

Use this path only for automation dogfood:

```powershell
python path\to\mentor-loop-lean-v0\tools\mentor-loop.py run --repo path\to\target-repo "fix <bug description or issue summary>"
```

## Claude Code One-Command Path

This is a later distribution path, not the main v0 target.

1. Copy `.claude/` from this package into the target repo root.
2. Either commit `.claude/` as project tooling, or add `.claude/` to the
   repo-local git exclude file for local dogfood:

```bash
exclude_file="$(git rev-parse --git-path info/exclude)" || exit 1
if ! grep -qxF ".claude/" "$exclude_file"; then
  printf "\n.claude/\n" >> "$exclude_file"
fi
```

3. Start Claude Code from the target repo root.
4. Invoke:

```text
/mentor-loop "fix <bug description or issue summary>"
```

Expected artifacts:

- `.mentor-loop/runs/<run-id>/mentor-brief.md`
- `.mentor-loop/runs/<run-id>/active-lessons.md`
- `.mentor-loop/runs/<run-id>/apprentice-prompt.md`
- `.mentor-loop/runs/<run-id>/apprentice-log.md`
- `.mentor-loop/runs/<run-id>/gate-blast-radius.txt`
- `.mentor-loop/runs/<run-id>/gate-runtime-floor.txt`
- `.mentor-loop/runs/<run-id>/review.md`
- `.mentor-loop/runs/<run-id>/final-report.md`
- `.mentor-loop/lessons.md` only when review captures a reusable lesson

The skill also adds `.mentor-loop/` to the repo's local git exclude file via
`git rev-parse --git-path info/exclude`, so run artifacts should not appear in
`git status --porcelain`.

If `.claude/` is a local-only install and is not excluded, the blast-radius gate
will correctly treat it as unrelated scope drift.

Expected control flow:

1. Main session writes the Mentor Brief.
2. Main session runs baseline verification before any edit.
3. `mentor-loop-apprentice` runs on `haiku`.
4. Main session runs both gates.
5. Main session reviews only the diff and run artifacts.
6. Main session reports changed files, verification, gates, review, and lessons.

Stop if Claude Code cannot spawn the subagent or if neither `python` nor
`python3` can run the bundled gates.

## Manual Path

Use this path when you want to run one Mentor Loop manually. No framework
installation required.

You need:

- One clean repo checkout or worktree.
- One strong model window.
- One weak model window.
- A focused test command or other machine-checkable verification.

## 1. Pick A Small Task

Good first task:

- Existing-code bug fix.
- One to three likely files.
- Clear expected behavior.
- Focused test command exists or can be added.

Bad first task:

- Broad refactor.
- Architecture redesign.
- Pure taste/design task.
- Task with no runnable verification.

## 2. Create A Mentor Brief With The Strong Model

Open `mentor-brief-template.md`.

Ask the strong model:

```text
Fill this Mentor Brief for the task below.

Rules:
- Name concrete context files the weak model must read.
- Keep the blast radius narrow.
- Include runtime/dependency constraints.
- Include baseline, focused verification, and regression/no-breakage checks.
- Add stop conditions.

Task:
<paste task>

Template:
<paste mentor-brief-template.md>
```

Save the result as:

```text
mentor-brief.md
```

Reject the brief if it says vague things like "inspect relevant files" or
"fix as needed." It must name files and checks.

## 3. Give The Brief To The Weak Model

Open `apprentice-execute.md`.

Ask the weak model:

```text
Execute this Mentor Brief exactly.

Rules:
- Read every Context Pack file before editing.
- Record one finding from each required file.
- Edit only inside the Blast Radius.
- Stop if a stop condition triggers.
- Run the verification commands.
- Return changed files, verification output, uncertainty, and a diff summary.

Apprentice rules:
<paste apprentice-execute.md>

Mentor Brief:
<paste mentor-brief.md>
```

Do not let the weak model reinterpret the task. If it needs files outside the
blast radius, stop and go back to the strong model.

## 4. Run The Gate

From the target repo root, run:

```powershell
python gates\blast-radius-check.py --brief mentor-brief.md
```

The gate reads `git status --porcelain`, so untracked helper artifacts count as
scope drift.

If the gate blocks, do not accept the patch.

For Python projects with a declared runtime floor, also run:

```powershell
python gates\runtime-floor-check.py
```

This catches a narrow set of known API/runtime-floor mismatches. It does not
replace tests or strong review.

## 5. Run Verification

Run the focused command from the brief.

Then run the broader no-regression command from the brief.

If either command cannot run, record:

```text
outcome_type=verification_incomplete
```

Do not count that run as accepted.

## 6. Strong Review

Open `mentor-review-template.md`.

Ask the strong model:

```text
Review this weak-model run.

Return only:
- verdict: Approved / Needs fixes / Stop and re-plan
- blocking issues
- non-blocking concerns
- required fixes
- lesson candidate, if any

Mentor Brief:
<paste mentor-brief.md>

Diff:
<paste diff>

Apprentice log:
<paste weak model report>

Verification output:
<paste commands and output>

Gate output:
<paste gate output>
```

Only accept `Approved`.

If the verdict is `Needs fixes`, give the weak model only the listed fixes. Do
not let it start a new task.

## 7. Capture One Lesson

If a reusable mistake appeared, open `lesson-capture-template.md`.

Capture one lesson with:

- created date
- source failure
- hit count
- status
- trigger
- mistake
- rule for next time
- example

Do not capture vague reminders.

Good lesson:

```text
Trigger: Patch uses a convenient newer language API.
Mistake: Model checked only local runtime and tests.
Rule: Before using newer APIs, inspect project metadata such as
python_requires, engines, or equivalent runtime constraints.
```

## 8. Record The Outcome

Use one outcome type:

- `accepted`
- `review_blocked`
- `gate_blocked`
- `verification_failure`
- `verification_incomplete`
- `env_failure`
- `protocol_violation`

Minimum record:

- task id
- model/effort
- run directory
- changed files
- gate output
- verification output
- review verdict
- lessons captured
- caveats

## First-Run Rule

Do not automate anything after your first run.

Run it manually once. The pain you feel is the product roadmap.
