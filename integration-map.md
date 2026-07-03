# Integration Map

This package is the lean publication and operating surface. It intentionally
does not install the older framework pieces by default.

Use this map to understand how the workflow can later become skills, hooks, and
subagents without changing the thesis.

## Current Lean v0 Surface

| Layer | Current artifact | Role |
|---|---|---|
| Workflow | `operator-runbook.md` | Human-run procedure for one Mentor Loop run. |
| Role split | `role-cards.md` | Manual role boundaries that can later become subagent contracts. |
| Model policy | `model-policy.md` | Fixed model assignment and escalation without an automatic router. |
| Product map | `lever-map.md` | Maps weak-model failure modes to workflow levers. |
| Cheap trial | `best-of-n-rubric.md` | Evidence-ranked selection across isolated weak-model attempts. |
| Strong planning | `mentor-brief-template.md` | Turns judgment into a work order. |
| Weak execution | `apprentice-execute.md` | Constrains the weak model to execute, not reinterpret. |
| Scope gate | `gates/blast-radius-check.py` | Blocks changed files outside the blast radius, including untracked artifacts. |
| Compatibility gate | `gates/runtime-floor-check.py` | Blocks a narrow set of Python runtime-floor API mismatches. |
| Hook sample | `hooks/pre-commit.sample` | Manual git hook sample for running gates after dogfood. |
| Strong review | `mentor-review-template.md` | Reviews diff, evidence, and brief. |
| Durable memory | `lesson-capture-template.md` | Captures one reusable lesson with decay metadata. |
| Few-shot memory | `lesson-ledger-example.md` | Shows active, candidate-gate, and retired lesson records. |
| Manual subagents | `subagents/*.md` | Copy/paste prompt cards for separate model windows. |
| Skill wrappers | `skills/*/SKILL.md` | Minimal Codex skill-shaped wrappers; not auto-installed. |

This is enough for manual dogfooding and publication.

## Existing Skill-Shaped Pieces

Lean v0 includes minimal skill-shaped wrappers:

- `skills/apprentice-execute/SKILL.md`
- `skills/mentor-review/SKILL.md`
- `skills/lesson-capture/SKILL.md`

Their current role is reference material. Do not require users to install them
for v0, and do not claim skill distribution until they have been installed and
tested in a real Codex skill environment.

If converted into installable skills later:

- `apprentice-execute` should wrap `apprentice-execute.md`.
- `mentor-review` should wrap `mentor-review-template.md`.
- `lesson-capture` should wrap `lesson-capture-template.md` and preserve lesson
  metadata/decay rules.

Do not add a model router before publication feedback proves it is needed.

## Existing Hook-Shaped Pieces

Two blast-radius checkers now share the important behavior:

- `gates/blast-radius-check.py` in this lean package
- the older standalone blast-radius hook outside this zip

Both read `git status --porcelain` when changed files are not provided, so they
catch untracked artifacts as well as tracked diffs.

The lean package should document the first path. The older hook path is useful
for migration or historical users.

The lean package also includes `gates/runtime-floor-check.py`, a narrow Python
compatibility gate grown from the `str.removeprefix()` failure in `jc-685`. It
is intentionally small and table-driven; broader runtime compatibility remains
future work.

`hooks/pre-commit.sample` shows how to wire the gates into git manually. It is a
sample, not an installer.

## Existing Subagent-Shaped Pieces

Lean v0 now includes manual subagent prompt cards:

| Subagent | Lean role |
|---|---|
| `subagents/strong-mentor.md` | Fill `mentor-brief-template.md`. |
| `subagents/weak-apprentice.md` | Execute `apprentice-execute.md`. |
| `subagents/strong-reviewer.md` | Fill `mentor-review-template.md`. |
| `subagents/lesson-curator.md` | Apply `lesson-capture-template.md` and consolidation rules. |

For v0, use these as prompt references only. They are not an automated launcher.

The lean package's source of truth for role boundaries is now
`role-cards.md`. If future subagents are regenerated, preserve those input,
allowed-action, forbidden-action, and output contracts.

## What Remains Sealed

Keep these out of the lean path until publication creates specific demand:

- model router
- model policy resolver
- provider registry
- provider adapters
- launcher adapter
- run-state auditor
- bundle builder
- mock e2e runner
- public dogfood runner
- response extractor/gate
- provider artifact gate

They are not wrong. They are premature.

## Product-Line Relationship

Mentor Loop is the umbrella pattern:

```text
weak model misses judgment
  -> make judgment explicit
  -> enforce what can be enforced
  -> review what still needs judgment
  -> distill repeated review findings into lessons/gates
```

Related entry points:

- `surgical-fix`: single-model behavior-change discipline and blast-radius
  thinking.
- `glance-first`: reader/audience judgment turned into a reviewable artifact.
- `mentor-loop`: strong/weak model handoff plus review, lessons, and gates.

The shared product sentence:

> Weak models lack judgment. Turn judgment into artifacts, gates, and durable
> memory, and weak models can approach stronger-model behavior on repeated work.

## Next Integration Step

After publication, pick only one painful manual step to automate.

Recommended order:

1. Lesson capture with metadata.
2. Lesson consolidation review.
3. Blast-radius hook installation.
4. Apprentice execution skill.
5. Mentor review skill.

Use `future/lesson-ledger-v1.md` as the design brief for the first two steps.
It defines the lesson record, hit-count rules, consolidation, gate promotion,
retirement audit, and the boundary between a skill and a hook.

Avoid starting with model routing. Routing guesses whether the weak model can
handle the task; this workflow makes the task easier for the weak model to
handle.
