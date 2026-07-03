# Lesson Ledger v1 Design Brief

This is the first v1 feature to build after publication feedback or repeated
manual dogfood pain. It should replace append-only lesson notes with a small
judgment asset ledger.

The hard part is depreciation, not capture. A lesson system can die while still
capturing every correction if the file becomes a junk drawer of stale,
contradictory, or over-broad rules.

Do not build a general agent framework first.

## Problem

Lesson capture is not enough. Long-running instruction files decay:

- stale rules stay active after models improve,
- duplicate lessons bloat context,
- repo-specific and general lessons get mixed together,
- prose rules survive even after they should become deterministic gates,
- no hit count means there is no way to know what mattered.

The failure mode is a rotting `CLAUDE.md`: more text, less signal.

## Product Thesis

The durable asset is not a bigger prompt. It is a reconciled ledger of judgment,
with admission rules, depreciation, and a path from prose to code:

```text
review catches mistake
  -> lesson prevents repeat
    -> gate makes it free
      -> retirement audit removes stale prose
```

Each step should either make a rule cheaper to apply or remove it when it no
longer changes behavior.

Think of the ledger as a judgment balance sheet. Every month, it needs a close:
what is still active, what should be merged, what should be written down, and
what has become reliable enough to compile into a gate.

## Lesson Record

Minimum fields:

```yaml
lesson_id:
scope: repo | project_family | general
created_at:
created_by:
source_failure:
source_artifact:
trigger:
mistake:
rule_for_next_time:
example:
hit_count: 0
last_hit_at:
status: active
candidate_gate:
retirement_notes:
```

Allowed `status` values:

- `active`: inject into relevant future runs.
- `candidate_gate`: repeated often enough that a deterministic check may be
  better.
- `retired`: kept for history; do not inject.

Scope matters:

- `repo`: only inject in the repository where it was learned.
- `project_family`: inject across closely related repos or task families.
- `general`: inject broadly, but keep rare. Most lessons should not be general.

## Ledger Operations

### Capture

Input:

- strong review finding,
- gate failure,
- verification failure,
- human correction.

Output:

- at most one new lesson,
- or a hit on an existing lesson,
- or a gate candidate.

Capture rule:

> If the lesson would not have prevented this failure, do not save it.

### Hit Counting

Increment `hit_count` when:

- a weak model explicitly uses the lesson before editing,
- review catches a repeat that the lesson described,
- a gate derived from the lesson fires,
- consolidation finds that two lessons describe the same repeated failure.

Do not increment when:

- the lesson was merely present in context,
- the run never touched the relevant trigger,
- the model claims it used the rule but no evidence supports that.

Gate-triggered hits are the cheapest instrumentation. If a gate exists because
of a prior lesson, the gate should be able to write a hit back to that lesson's
record. Without hit counts, there is no way to know which lessons should be
promoted and which should be deleted.

### Consolidation

Run weekly or every N runs.

Inputs:

- active lessons,
- run scorecards,
- review findings,
- gate outputs.

Actions:

- merge duplicates,
- delete contradictions,
- narrow over-broad rules,
- split mixed rules,
- promote repeated rules to `candidate_gate`,
- retire rules with no hits after a chosen window.

Output:

- a shorter active lesson set,
- a candidate gate list,
- a short changelog explaining what changed.

This is the core anti-rot ritual. Capture without consolidation creates
context debt. Consolidation turns scattered corrections into a smaller,
ranked, auditable set of judgment assets.

### Gate Promotion

Promote a lesson when:

- it has `hit_count >= 3`,
- the trigger is machine-detectable,
- false positives are acceptable or easy to suppress,
- the check is cheaper than another strong-model review.

Examples:

- untracked artifacts outside blast radius,
- unsupported runtime API usage,
- missing required context files in the apprentice report,
- changed files outside the Mentor Brief blast radius.

### Retirement Audit

Run when changing the execution model.

Procedure:

1. Pick a sample of older active lessons.
2. Disable them for a representative run or archived replay.
3. Compare behavior with and without the lessons.
4. Retire lessons the new model no longer needs.
5. Keep lessons that still change behavior.
6. Promote deterministic repeats into gates.

Success looks like a thinner active lesson file after a model upgrade.

The lesson file should get thinner as models improve. A lesson that only exists
because an older weak model lacked a capability should be retired once the new
execution model stops making that mistake. A ledger that only grows is not an
asset; it is a liability.

## Injection Policy

Do not inject every lesson into every run.

Default order:

1. Repo-scoped active lessons for the current repo.
2. Project-family lessons matching the task type.
3. General lessons only when their trigger is likely.
4. Candidate gates as commands or checklists, not prose.
5. Never inject retired lessons.

If active lesson context becomes large, prefer:

- trigger-based selection,
- shorter consolidated rules,
- gate promotion,
- retirement.

Do not solve context bloat with summarization alone. Summaries can hide
contradictions; consolidation must remove or reconcile them.

## Future Skill Shape

A `lesson-curator` skill should do one narrow job:

> Given a run record and existing lessons, decide whether to create, update,
> promote, or retire lessons.

It should return:

- `no_change`,
- `new_lesson`,
- `increment_hit`,
- `merge_lessons`,
- `promote_to_gate`,
- `retire_lesson`.

It should not:

- edit code,
- decide task routing,
- run providers,
- rewrite the whole repo instruction file.

## Future Hook Shape

A hook can support the ledger only when the signal is deterministic.

Good hook candidates:

- changed files outside blast radius,
- untracked artifacts,
- required context files not listed in the apprentice report,
- runtime floor incompatible with changed APIs,
- missing verification output.

Bad hook candidates:

- "code quality",
- "taste",
- broad architecture judgment,
- anything that requires reading intent from prose.

## Acceptance Criteria

The v1 ledger is useful when:

- every lesson has a source failure and source artifact,
- every active lesson has either recent hits or a reason to stay active,
- repeated lessons become candidate gates,
- gates can write hits back to the source lesson,
- model upgrades can retire obsolete lessons,
- the active lesson set can shrink after consolidation,
- users can inspect why a rule exists.

The v1 ledger is not useful if:

- it only appends lessons,
- it makes prompts longer every week,
- it cannot distinguish repo rules from general rules,
- it never deletes or retires anything,
- it treats all model mistakes as prose memory instead of gate candidates.

## Non-Goals

Do not include:

- model router,
- provider registry,
- execution launcher,
- automatic multi-agent orchestration,
- full experiment harness,
- generic long-term memory system.

This feature exists to keep judgment assets clean enough that weak models can
reuse them without drowning in stale context.
