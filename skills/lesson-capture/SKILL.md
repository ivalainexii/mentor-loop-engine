---
name: mentor-loop-lesson-capture
description: Use after a Mentor Loop run, review finding, gate failure, verification failure, or human correction to decide whether to create, update, promote, merge, or retire a reusable lesson.
---

# Mentor Loop Lesson Capture

Decide whether a run should create, update, promote, merge, or retire a lesson.

Before deciding, read:

- `../../role-cards.md`, Lesson Curator section
- `../../lesson-capture-template.md`
- `../../lesson-ledger-example.md`
- existing lesson ledger
- review/gate/verification evidence

## Allowed Actions

Return exactly one:

- `no_change`
- `new_lesson`
- `increment_hit`
- `merge_lessons`
- `promote_to_gate`
- `retire_lesson`

## Capture Rule

Save a lesson only if it would have prevented or caught the failure.

Do not save:

- vague reminders,
- one-off task details,
- duplicate lessons,
- repo-specific rules as global rules,
- prose rules that should already be deterministic gates.

## Required Metadata

Every new or updated lesson must include:

- `lesson_id`
- `scope`
- `created_at`
- `source_failure`
- `source_artifact`
- `trigger`
- `mistake`
- `rule_for_next_time`
- `example`
- `hit_count`
- `last_hit_at`
- `status`
- `candidate_gate`
- `retirement_notes`
