# Claude Code v0 Wiring Report

## Wired

- Added a project skill at `.claude/skills/mentor-loop/SKILL.md`, invoked as
  `/mentor-loop <task description>` in Claude Code.
- Added a cheap execution subagent at
  `.claude/agents/mentor-loop-apprentice.md` with `model: haiku`.
- Bundled the five existing Mentor Loop templates into the skill:
  - `mentor-brief-template.md`
  - `apprentice-execute.md`
  - `mentor-review-template.md`
  - `lesson-capture-template.md`
  - existing gate scripts for blast radius and runtime floor
- The skill writes run artifacts under `.mentor-loop/runs/<run-id>/`.
- The skill adds `.mentor-loop/` to the repo-local git exclude file discovered
  via `git rev-parse --git-path info/exclude`, so run artifacts stay out of
  `git status --porcelain` without changing tracked project files.
- The quickstart now tells users to either commit `.claude/` as project tooling
  or add `.claude/` to the same repo-local exclude file for local-only dogfood,
  preventing the blast-radius gate from blocking the install files.
- The skill requires the main session to run baseline verification before any
  apprentice edit.
- The skill runs both deterministic gates after apprentice execution:
  - blast radius via `git status --porcelain`
  - runtime-floor compatibility check
- The skill requires the main session to review only the brief, diff, execution
  log, gate outputs, and git status.
- The skill appends metadata-bearing lessons to `.mentor-loop/lessons.md` only
  when review finds a reusable mistake.

## Template Ambiguities Fixed During Wiring

- The old manual workflow did not specify a run artifact layout. The Claude
  Code skill now standardizes `.mentor-loop/runs/<run-id>/`.
- The original wiring idea used `.mentor-loop/.gitignore`, but that does not
  hide the `.mentor-loop/` directory itself from `git status --porcelain`. The
  skill now uses the repo-local git exclude file instead.
- Local dogfood installs of `.claude/` are also scope drift unless committed or
  excluded, so quickstart now makes that setup step explicit.
- The old lesson template used `source_failure` and `source_artifact`, but the
  one-command workflow also needs `source_run_id`; the skill requires it.
- The old manual workflow said "run gates" but did not define where stdout,
  stderr, and exit codes go. The skill now writes `gate-blast-radius.txt` and
  `gate-runtime-floor.txt`.
- The old workflow allowed human copy/paste between roles. The skill now
  requires an `apprentice-prompt.md` artifact and saves the subagent result as
  `apprentice-log.md`.

## Friction Remaining

- This has not yet been proven by a live Claude Code `/mentor-loop` run on a
  real bug fix. That remains the completion gate.
- Current verification environment did not have the `claude` command available,
  so live Claude Code dogfood could not be run here.
- The skill relies on Claude Code's Agent tool to invoke
  `mentor-loop-apprentice`; if the user's permissions deny agent spawning, the
  run will stop before apprentice execution.
- The skill assumes `python` or `python3` is available to run the bundled gates.
  If repeated real runs fail here, add only an env-preflight check.
- There is no automatic retry/escalation loop. If review returns "Needs fixes,"
  the main session must decide whether to run another apprentice pass.
- There is no installer. For v0, users copy `.claude/` into the repo root.

## Not Built

- Model router.
- Provider registry.
- API adapter.
- Cross-platform launcher.
- Generic orchestration framework.
- New gates beyond the existing blast-radius and runtime-floor checks.
