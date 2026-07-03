# Lesson Capture

Save a lesson only for reusable corrections. Do not save vague reminders.

## Lesson

- `lesson_id`:
- `created_at`:
- `source_failure`:
- `source_artifact`:
- `hit_count`: 0
- `last_hit_at`:
- `status`: active
- `trigger`:
- `mistake`:
- `rule_for_next_time`:
- `example`:
- `candidate_gate`:
- `save_to`:

Allowed statuses:

- `active`: still useful enough to inject into future runs.
- `candidate_gate`: repeated enough that a deterministic gate may be better.
- `retired`: kept only for history; do not inject into future runs.

## Common Lesson Shapes

- Runtime floor: if a fix uses a newer language API, first check project
  metadata such as `python_requires`, `engines`, or equivalent version gates.
- Artifact hygiene: if a run creates untracked helper files or directories,
  treat them as scope drift unless they are explicitly allowed.

## Maintenance

Treat lessons as a judgment asset ledger, not an append-only notes file.

Run consolidation weekly or every N runs:

- Merge duplicate lessons.
- Remove stale or contradictory lessons.
- Increment `hit_count` when a lesson prevents or catches a repeated failure.
- Promote lessons with repeated hits into `candidate_gate`.
- If a gate fires because of a known lesson, count that as a lesson hit.
- Keep only rules that still change model behavior.

Run a retirement audit when the execution model changes:

- Temporarily remove a small sample of older active lessons.
- Rerun representative tasks or replay archived failures.
- Retire lessons for mistakes the new model no longer makes.
- Keep lessons that still prevent failures.
- Promote deterministic repeats into gates instead of keeping them as prose.

The intended lifecycle is:

```text
review catches mistake
  -> lesson prevents repeat
    -> gate makes it free
      -> retirement audit removes stale prose
```

## Quality Check

The lesson is valid only if:

- It would have prevented this mistake.
- It is specific enough to apply next time.
- It does not overfit to one file unless the rule is file-specific.
- It tells the model what to do differently.
- It has a source failure that can be inspected later.
- It can be retired if a newer model no longer needs it.
