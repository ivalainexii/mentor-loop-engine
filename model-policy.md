# Fixed Model Policy

This package does not use an automatic model router in v0.

Use a fixed policy first:

> Spend strong-model tokens on judgment. Spend weak-model tokens on execution.
> Escalate only when gates, verification, or review prove the weak path is not
> enough.

## Default Assignment

| Role | Default model tier | Why |
|---|---|---|
| Human Operator | human | Owns risk, scope, and final accept/reject. |
| Strong Mentor | strong | Writes the work order and externalizes judgment. |
| Weak Apprentice | weak | Executes a narrow, checkable plan. |
| Gate Runner | deterministic code | Checks what should not require model judgment. |
| Strong Reviewer | strong | Reviews diff and evidence from a fresh context. |
| Lesson Curator | strong or medium | Consolidates reusable judgment; can be batched. |
| Best-of-N Selector | deterministic checks first, then strong reviewer for ties | Selection should be evidence-ranked, not vibes-ranked. |

Use the cheapest model that can reliably perform the role, but do not let the
weak execution model decide whether the task is safe for itself.

## No Router In v0

Do not start by asking a model:

> Is this task easy enough for the weak model?

That question itself requires judgment.

Instead, use observable signals:

- number of likely files,
- blast radius size,
- availability of focused tests,
- availability of regression checks,
- presence of runtime/dependency constraints,
- whether the task requires architecture judgment,
- whether wrong output can silently corrupt user data.

If the signals look risky, use strong-direct or strong planning before weak
execution. If the signals look narrow and checkable, use Mentor Loop.

## Weak-First Path

Use weak execution when all are true:

- the brief names concrete files,
- the blast radius is narrow,
- verification is machine-checkable,
- stop conditions are explicit,
- repo context and active lessons are available,
- the patch can be reviewed as a diff.

Recommended path:

```text
strong mentor -> weak apprentice -> gates -> strong reviewer -> lesson curator
```

For very cheap verification, use:

```text
strong mentor -> weak apprentice x2/x3 -> gates -> strong reviewer selects
```

Use `best-of-n-rubric.md` for the second path.

## Strong-Direct Path

Use strong-direct when any are true:

- the task is high-stakes,
- verification is unavailable,
- the change requires architecture judgment,
- the weak model would need to discover the plan from scratch,
- the blast radius is broad or unknown,
- the cost of a wrong patch is higher than the cost of strong execution,
- the user needs speed more than process evidence.

Strong-direct is not failure. It is the right route when judgment cannot be
externalized cheaply.

## Escalation Triggers

Escalate from weak execution to strong model when:

- the weak model fails the same gate twice,
- focused or regression verification fails and the fix is not mechanical,
- strong review blocks for reasoning quality,
- the weak model needs files outside the original blast radius,
- the patch requires a new dependency or newer runtime,
- candidates in Best-of-N disagree in a way that requires architecture judgment,
- verification remains inconclusive after environment hygiene is fixed.

Escalation packet:

- original user task,
- Mentor Brief,
- repo context,
- active lessons,
- weak-model log,
- diff,
- gate output,
- verification output,
- reviewer blockers,
- rejected candidate summaries if Best-of-N was used.

Failed weak attempts should become context for the strong model, not discarded
noise.

## Cost Accounting

When token data is available, record:

- strong direct tokens,
- strong brief tokens,
- weak execution tokens,
- strong review tokens,
- strong escalation tokens,
- lesson-curation tokens.

The planned ratio is:

```text
(strong brief + weak execution + strong review + strong escalation + lesson curation)
/ strong direct
```

Do not claim cost savings until this ratio is measured on comparable tasks.

## Model Upgrade Rule

When the weak execution model improves:

1. Keep the same gates.
2. Keep the same scorecard.
3. Run a retirement audit on old lessons.
4. Rerun a small set of representative tasks.
5. Delete lessons the new model no longer needs.

The workflow should benefit from stronger weak models. It should not trap users
in old prompt workarounds.

## Anti-Patterns

- Letting the weak model self-certify task difficulty.
- Spending strong-model tokens to route every tiny task before any cheap signal.
- Treating a failed weak run as wasted instead of evidence for review or
  escalation.
- Using Best-of-N when verification is unavailable.
- Claiming cost savings without token accounting.
- Keeping old lessons after the execution model has outgrown them.

The stable principle is:

> Judgment moves downward when it can: strong model -> brief/review -> lesson ->
> gate. Execution stays cheap when the remaining task is narrow and checkable.
