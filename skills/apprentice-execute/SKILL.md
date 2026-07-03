---
name: mentor-loop-apprentice-execute
description: Use when a weak or lower-cost coding model must execute an existing Mentor Brief exactly, read required context files, stay inside the blast radius, run verification, and report uncertainty without reinterpreting the task.
---

# Mentor Loop Apprentice Execute

Execute the Mentor Brief exactly. Treat it as a contract.

Before editing, read:

- `../../role-cards.md`, Weak Apprentice section
- `../../apprentice-execute.md`
- the task's `mentor-brief.md`
- applicable active lessons

## Required Preflight

1. Read the entire Mentor Brief.
2. Read every Context Pack file.
3. Record one concrete finding from each file.
4. Extract allowed files from Blast Radius.
5. Extract do-not-touch files or areas.
6. Extract stop conditions.
7. Extract verification commands.
8. Extract runtime, dependency, and compatibility constraints.

Stop if any preflight item fails.

## Execution Rules

Allowed:

- Make the smallest change that satisfies the brief.
- Add or update focused tests named in the brief.
- Run the verification commands.
- Stop and report uncertainty.

Not allowed:

- Expand the task.
- Edit outside the Blast Radius.
- Use language/runtime APIs newer than the project's supported floor.
- Create helper artifacts unless explicitly allowed.
- Claim completion without verification output.

## Output

Return:

- files read and one finding from each,
- files changed and why,
- stop conditions checked,
- runtime and compatibility constraints checked,
- verification command and result,
- remaining uncertainty,
- diff summary.
