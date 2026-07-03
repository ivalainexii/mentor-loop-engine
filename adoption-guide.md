# Adoption Guide

Use this when bringing Mentor Loop into a real repository.

The rule:

> Start with files and habits. Add hooks, skills, and subagents only after the
> manual loop produces repeated pain.

## What To Copy First

Create a folder in your target repo:

```text
mentor-loop/
```

Copy:

```text
mentor-loop/operator-runbook.md
mentor-loop/quickstart.md
mentor-loop/role-cards.md
mentor-loop/model-policy.md
mentor-loop/best-of-n-rubric.md
mentor-loop/repo-context-template.md
mentor-loop/mentor-brief-template.md
mentor-loop/apprentice-execute.md
mentor-loop/mentor-review-template.md
mentor-loop/lesson-capture-template.md
mentor-loop/lesson-ledger-example.md
mentor-loop/gates/blast-radius-check.py
mentor-loop/gates/runtime-floor-check.py
mentor-loop/hooks/pre-commit.sample
mentor-loop/subagents/strong-mentor.md
mentor-loop/subagents/weak-apprentice.md
mentor-loop/subagents/strong-reviewer.md
mentor-loop/subagents/lesson-curator.md
mentor-loop/skills/apprentice-execute/SKILL.md
mentor-loop/skills/mentor-review/SKILL.md
mentor-loop/skills/lesson-capture/SKILL.md
```

Create:

```text
mentor-loop/lessons.md
mentor-loop/repo-context.md
mentor-loop/runs/
```

Add to `.gitignore` only if you do not want run artifacts committed:

```text
mentor-loop/runs/
```

Do commit:

- templates,
- gates,
- durable lessons,
- repo-specific operating rules.

Do not commit:

- scratch worktrees,
- model transcripts with secrets,
- temporary patches,
- unreviewed run artifacts.

## First Week

Run the loop manually on three small tasks.

For each task:

1. Create `mentor-loop/runs/<task-id>/`.
2. Save the strong-model brief as `mentor-brief.md`.
3. Save the weak-model report as `apprentice-log.md`.
4. Save gate output as `gate-output.txt`.
5. Save verification output as `verification.txt`.
6. Save strong review as `review.md`.
7. Add at most one lesson to `mentor-loop/lessons.md`.

Do not automate during the first week.

At the end of the week, ask:

- Which step was repeated and annoying?
- Which review finding happened more than once?
- Which lesson would be better as a deterministic check?
- Which files did weak models repeatedly fail to read?

Those answers decide the roadmap.

## Repo Instruction File

Add a short pointer to your existing `CLAUDE.md` or `AGENTS.md`:

```markdown
## Mentor Loop

For existing-code bug fixes, prefer `mentor-loop/quickstart.md`.

Reusable lessons live in `mentor-loop/lessons.md`.
Repo context lives in `mentor-loop/repo-context.md`.

Before editing, read the task Mentor Brief and every Context Pack file.
Do not edit outside the Blast Radius. Run `mentor-loop/gates/blast-radius-check.py`
before claiming completion.

For Python projects with a declared runtime floor, also run
`mentor-loop/gates/runtime-floor-check.py`.
```

Keep this pointer short. Put detailed rules in `mentor-loop/`, not in a giant
root instruction file.

Use `repo-context-template.md` to create `mentor-loop/repo-context.md`. Keep it
focused on project map, authoritative files, coupled changes, runtime rules,
verification commands, and common stop conditions.

## Lesson File Shape

Start `mentor-loop/lessons.md` with:

```markdown
# Lessons

## Active

<!-- New reusable lessons go here. -->

## Candidate Gates

<!-- Lessons with repeated hits move here. -->

## Retired

<!-- Lessons no longer injected into runs. -->
```

Each lesson should include:

- `created_at`
- `source_failure`
- `source_artifact`
- `hit_count`
- `last_hit_at`
- `status`
- `trigger`
- `mistake`
- `rule`
- `example`
- `candidate_gate`

If a lesson has `hit_count >= 3`, consider turning it into a gate.

Use `lesson-ledger-example.md` as a few-shot example for what "good" looks
like: one active lesson, one candidate gate, one retired lesson, and a short
consolidation note.

## Stage 0: Manual Only

Use:

- markdown templates,
- human copy/paste,
- manual gate command,
- strong review in a fresh context.

Use `role-cards.md` to keep each participant narrow: strong mentor plans, weak
apprentice executes, gates check, strong reviewer judges, lesson curator updates
memory.

Use `subagents/*.md` as copy/paste prompt cards for separate model windows.
They are not an automated launcher.

Use `skills/*/SKILL.md` as source material if you later install these workflows
as Codex skills. In this lean package they are not auto-installed.

Use `model-policy.md` to decide when to stay weak-first, when to run Best-of-N,
and when to escalate to strong-direct.

Success looks like:

- weak-model patches stay inside scope,
- review catches fewer repeated mistakes,
- lessons become more specific,
- the run record is good enough to inspect later.

Do not measure success by automation count.

## Stage 1: Hook The Gate

Automate only the blast-radius check first.

Recommended behavior:

- Run after weak-model edits.
- Read `git status --porcelain`.
- Block untracked artifacts.
- Fail closed if not in a git worktree.
- Print changed files, allowed files, and outside-blast-radius files.

Do not automate semantic review yet.

For Python projects, also consider installing `gates/runtime-floor-check.py`.
It is intentionally narrow: it catches known API/runtime-floor mismatches, not
all compatibility issues.

Use `hooks/pre-commit.sample` as a starting point after manual runs show the
gate is worth enforcing. It expects:

- gates under `mentor-loop/gates/`,
- an active brief at `mentor-brief.md`, or `MENTOR_BRIEF` set to another path,
- `python` on PATH, or `PYTHON` set to a specific executable.

It skips the blast-radius gate if no brief is found, but still runs the
runtime-floor gate when available. Edit this policy if your repo should fail
closed when no brief exists.

## Optional Stage: Best-of-N

After the first manual run, use `best-of-n-rubric.md` when verification is cheap
and weak-model attempts are independent.

Keep the discipline strict:

- one fresh context per candidate,
- one clean checkout or worktree per candidate,
- same brief and lessons for every candidate,
- same gate and verification commands,
- no hidden feedback between candidates.

This is a selection protocol, not a license to accept unverified patches.

## Stage 2: Skill The Apprentice

Turn `apprentice-execute.md` into a skill when weak models repeatedly skip the
same preflight steps.

The skill should enforce:

- read every Context Pack file,
- record one finding per file,
- extract Blast Radius,
- extract stop conditions,
- extract runtime/dependency constraints,
- run verification,
- report uncertainty.

The skill should stop, not improvise, when the brief is incomplete.

## Stage 3: Skill The Review

Turn `mentor-review-template.md` into a skill when reviews become repetitive.

The skill should check:

- scope drift,
- missed context,
- compatibility breakage,
- weakened tests,
- missing verification,
- lesson candidates.

Keep the reviewer in a fresh context. A clean reviewer catches mistakes the
implementer rationalized away.

## Stage 4: Lesson Consolidation

Once `mentor-loop/lessons.md` has more than ten active lessons, schedule a
consolidation review.

Ask a strong model to:

- merge duplicates,
- delete stale lessons,
- identify contradictions,
- promote repeated lessons to `candidate_gate`,
- count gate triggers as lesson hits when the gate exists because of a lesson,
- retire lessons that newer models no longer need.

This prevents `lessons.md` from becoming a junk drawer.

When changing the execution model, run a retirement audit:

- Disable a small sample of older active lessons.
- Rerun representative tasks or archived failures.
- Retire lessons for mistakes the new model no longer makes.
- Keep lessons that still change behavior.
- Promote deterministic repeats into gates.

## What Not To Adopt First

Do not start with:

- model router,
- provider registry,
- launcher adapter,
- run-state machine,
- bundle builder,
- e2e harness.

Those solve scale problems. You do not have scale problems until the manual
loop has repeated enough to be annoying.

## Adoption Milestone

The first real milestone is not:

> I installed Mentor Loop.

It is:

> A weak model repeated a mistake, review caught it, the lesson prevented it
> next time, and then a gate made the check automatic.
