# Apprentice Execute

Execute the Mentor Brief exactly. Treat it as a contract.

## Preflight Gate

Before editing:

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
- Refactor unrelated code.
- Edit outside the Blast Radius.
- Use language/runtime APIs newer than the project's supported floor.
- Treat an issue author's suggested fix as proven without checking source/tests.
- Claim completion without verification output.

## Output

Return:

- Files read and one finding from each.
- Files changed and why.
- Stop conditions checked.
- Runtime and compatibility constraints checked.
- Verification command and result.
- Remaining uncertainty.
- A unified diff if you cannot edit the workspace directly.
