# Repo Context Template

Use this to keep `CLAUDE.md`, `AGENTS.md`, or `mentor-loop/repo-context.md`
short, current, and useful.

The goal is to give weak models the project judgment they usually fail to
discover on their own.

Do not turn this into a long essay. Put only rules that should affect future
edits.

## Project Map

- Primary language/framework:
- Main source directories:
- Main test directories:
- Generated/vendor directories to avoid:
- Important config files:

## Authoritative Files

When changing this area, these files are the source of truth:

| Area | Read first | Why it is authoritative |
|---|---|---|
|  |  |  |

Examples:

- Parser behavior: implementation file plus focused parser tests.
- Runtime support: `setup.py`, `pyproject.toml`, `package.json`, CI config, or
  equivalent version metadata.
- UI behavior: component file plus existing story/test/screenshot fixture.

## Coupled Changes

If you change X, also check Y:

| Change | Also inspect/update | Reason |
|---|---|---|
|  |  |  |

Examples:

- Parser output shape -> parser tests and downstream formatter tests.
- Public API -> docs, examples, changelog, and compatibility tests.
- Config schema -> parser, defaults, validation, and docs.

## Runtime And Dependency Rules

- Supported runtime floor:
- Supported platforms:
- Dependency policy:
- APIs/features to avoid:
- Compatibility promises:

Rule:

> Do not use newer language, framework, or dependency APIs until you have
> checked the declared support floor.

## Verification Commands

Focused checks:

```text

```

Regression/no-breakage checks:

```text

```

If full regression checks are too expensive, document the smallest acceptable
substitute and its blind spots.

## Common Stop Conditions

Stop and ask for a new brief if:

- Required authoritative files are missing or unreadable.
- The change needs files outside the blast radius.
- Runtime/dependency constraints are unknown and may matter.
- Verification cannot run.
- Existing tests contradict the requested behavior.
- The task requires architecture judgment not named in the brief.

## Durable Lessons Pointer

Reusable lessons live in:

```text
mentor-loop/lessons.md
```

Do not duplicate the whole lesson ledger here. Keep this file as a pointer and
project map. Detailed lessons should stay in the ledger so they can be counted,
consolidated, promoted to gates, or retired.

## Maintenance

Review this file when:

- the project structure changes,
- runtime/dependency support changes,
- a lesson becomes a repo-wide rule,
- a rule has not mattered for several weeks,
- a newer execution model no longer needs an old warning.

Delete stale rules. A shorter accurate context file beats a long haunted one.
