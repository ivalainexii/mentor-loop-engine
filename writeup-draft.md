# I Tested Whether a Strong Model Could Mentor a Weak Model

> **Archived publication draft (2026-07-10):** retained as a record of the
> author-run case study, not as an active launch article or product roadmap. The
> A′ measurement design was falsified; the underlying uplift, cost, and
> judgment-compounding theses remain unproven, not disproven. Further product-level
> validation is not being pursued. `README.md` and
> `docs/aprime-postmortem.md` contain the final disposition.

Subtitle:

> Author-run cases produced inspectable briefs and deterministic gates; they did
> not establish product-level outcome uplift.

I started with a simple question:

> Can I make a cheaper, weaker coding model feel closer to a frontier model by
> having a strong model mentor it?

The original shape was obvious:

1. Strong model writes a detailed brief.
2. Weak model executes the brief.
3. A gate checks scope.
4. Strong model reviews the diff.
5. Any reusable correction becomes a lesson for next time.

That workflow was useful to inspect. But the research changed how I interpreted
the prototype.

The interesting result was not "strong model plans, weak model executes."

The interesting result was:

> A judgment can be encoded down a ladder: review -> lesson -> gate.

Once encoded, a deterministic gate can repeat a specific check without relying on
a model to remember it. The case study did not measure whether the overall workflow
was cheaper or improved product outcomes.

This is a small case study, not a benchmark. The sample is too small for
statistical claims. This archived draft is retained because the failure modes are
useful engineering records, not because the study established the product thesis.

## TLDR

- I tested a manual "Mentor Loop" workflow on public coding tasks.
- A tiny, confounded same-repo case recorded accepted lesson-seeded runs after
  `jc-685` on the related `jc-687` task; it cannot establish causal transfer.
- Mentor Briefs did not show clear success-rate lift over lessons-only in the
  small `jc-687` ablation.
- Mentor Briefs did improve auditability: baseline, reproduction, context read,
  stop conditions, and reviewer visibility.
- Two real failures became durable assets:
  - A Python runtime compatibility miss became a lesson.
  - An untracked artifact miss became a stricter gate using
    `git status --porcelain`.
- Cost reduction is unmeasured. Subagent token counts were unavailable.
- Strong-model context use dropped during dogfooding, but honest decomposition
  credits same-file familiarity and easier tasks ahead of the process itself.
- The process caught strong-model mistakes too; this is not only weak-model
  babysitting.
- The historical design interpretation favored judgment artifacts over a model
  router. It is not an active product roadmap.

## What I Built

Mentor Loop v0 is deliberately manual.

It contains five pieces:

1. `mentor-brief-template.md`
2. `apprentice-execute.md`
3. `gates/blast-radius-check.py`
4. `mentor-review-template.md`
5. `lesson-capture-template.md`

There is no model router, provider registry, API adapter, launcher, run-state
machine, or automated harness.

That was intentional. Before building infrastructure, I wanted to know whether
the loop itself produced useful evidence.

The thesis was:

> Weak models do not mainly need a smarter router. They need judgment moved out
> of the model and into artifacts: briefs, gates, reviews, and lessons.

## The Tasks

I used three public tasks:

| Task | Repository | Why it mattered |
|---|---|---|
| `jc-685` | `kellyjonbrazil/jc` | Parser fix, runtime compatibility risk |
| `jc-687` | `kellyjonbrazil/jc` | Related parser fix, same-repo lesson transfer |
| `pflow-389` | `spinje/pflow` | Cross-repo boundary run |

The main ablation was `jc-687`.

| Arm | Prompt shape | Result |
|---|---|---|
| A | Raw weak, no lessons, no brief | 1 accepted, 1 protocol violation |
| B | Weak + prior lessons only | 2 accepted |
| C | Weak + prior lessons + Mentor Brief | 2 accepted |
| D | Strong direct | 1 accepted |

Do not over-read this table. "2 accepted vs 1 accepted" at this sample size is
not a benchmark claim.

The useful question is not "which arm won statistically?"

The useful question is:

> What changed the model's behavior, and what became reusable?

## The Surprise

I expected the Mentor Brief to be the star.

It was not.

On `jc-687`, lessons-only and lessons-plus-brief both went 2 for 2. The brief
did not show obvious success-rate lift over lessons-only.

But the brief did buy something real: auditability.

The brief made it easier to see whether the model had:

- checked the baseline,
- reproduced the bug,
- read the relevant files,
- respected stop conditions,
- stayed inside the blast radius,
- and given the reviewer enough evidence to judge the patch.

That made the runs easier to inspect. It does not establish a product outcome
claim.

Mentor Briefs are not primarily "make weak models smarter" artifacts. They are
audit artifacts. They make model work easier to inspect, reproduce, and block.

The bigger leverage came from lessons and gates.

## Failure 1: The Runtime Floor Catch

One weak run on `jc-685` passed focused tests but used:

```python
str.removeprefix()
```

That looked fine locally. But the project supported Python 3.6, and
`removeprefix()` is newer than that.

The strong review blocked the patch.

That became a lesson:

> Before using newer language APIs, check the project's runtime floor:
> `python_requires`, `engines`, or equivalent metadata.

On later `jc` runs, lessons-only models explicitly checked `setup.py` before
choosing an implementation.

That is the first step down the ladder:

```text
strong review caught it
  -> lesson tells the next weak model to check first
```

## Failure 2: The Gate That Missed Untracked Files

One raw weak `jc-687` run functionally fixed the bug, but it also created an
untracked `.surgical-fix/` directory.

The original blast-radius gate missed it because it read:

```text
git diff --name-only
```

That only sees tracked-file diffs. It misses untracked artifacts.

The gate changed to read:

```text
git status --porcelain
```

Now the same kind of failure is blocked mechanically.

That is the next step down the ladder:

```text
review/gate missed a class of artifact drift
  -> gate got stronger
  -> later checks are deterministic
```

This is the reusable engineering sequence the cases produced:

```text
review catches mistake
  -> lesson prevents repeat
    -> gate repeats a specific check mechanically
```

## The pflow Boundary Run

After `jc-687`, I ran a cheap cross-repo boundary test on `pflow-389`.

I intentionally did not run the full four-arm experiment again.

The shape was:

- raw weak x1
- weak + transferred lessons x2

All three weak runs produced the same plausible patch shape:

- Handle YAML continuation before markdown heading and code-fence detection.
- Add focused parser regression tests.
- Touch only:
  - `src/pflow/core/markdown_parser.py`
  - `tests/test_core/test_markdown_parser.py`
- Pass the blast-radius gate.

But the environment lacked `uv`, `pytest`, and `PyYAML`, so I counted all three
rows as:

```text
verification_incomplete
```

That matters. A plausible patch is not an accepted patch.

The pflow result says only this:

- Cross-repo lesson transfer did not produce a measurable success-rate lift.
- Both lessons-only prompts referenced "preserve nested parser context before
  checking surface syntax," but verification never established an accepted result.
- Neither the same-repo nor cross-repo observations establish a product-level
  lesson-transfer claim.

## Historical Author-Run Dogfooding Notes

The next day of use changed the story again.

Across ten author-run cases on three codebases — one public library and two
private application contexts — the artifacts also exposed mistakes made by
strong models. This is an anecdotal engineering observation, not an independent
product result.

First, the strong model's context bill shrank too - but the honest
decomposition matters more than the headline. The drop was visible on the
quota meter by evening, and the causes rank like this: within-conversation
working memory was the largest (the evening script was pasted once at the
start of run 7 and runs 8-10 reused that context with no re-reading; any long
chat session gets this for free - it is not the ledger, and it did not carry
over from the afternoon, which was a different file in a different project);
the evening tasks were intrinsically easier (line-targeted edits instead of
multi-path UI diagnosis); and process overhead reduction was real but
smallest (template reuse, artifacts in files instead of in-conversation,
tail-line reads, one-line fix orders - this saves expression and transport
cost, not judgment cost). Deliberately shorter replies confounded it further.
The genuine "ledger compounds" claim belongs to cross-task eval data, not to
one evening on one file - and overclaiming the anecdote would itself be the
"strong model serving the metric" failure this loop exists to catch.
Prospectively this becomes measurable: per-session usage accounting (ccusage)
plus a session-per-chapter habit can compare loop chapters against non-loop
chapters going forward; the evening anecdote itself cannot be decomposed
retroactively.

Second, the process caught strong models repeatedly. The reviewer skipped an
apprentice log until the verification-summary artifact forced the issue. The
mentor invented a "past midnight" narrative while run IDs showed 20:38. The
mentor's verbose output became one of the user's biggest usability complaints.
A non-template Blast Radius section was blocked because it produced no
`allowed_files`. A performance acceptance test compared different semantics
and different workloads, making it inconclusive by construction. Another review
only caught an inverted clamp comparison after substituting concrete values.

That matters because it reframes the product. Gates and protocols are not
"weak-model training wheels." They are ways to make model judgment inspectable
even when the model is strong.

Third, one private-application run introduced a persistent slowdown in an
incremental refresh path. The user diagnosed the root cause from observed
behavior, and a later run bounded the refresh window and added a human-visible
annotation. Runtime moved back toward the prior range. This private anecdote is
retained only at the mechanism level; it is not independently reproducible
evidence. The recorded arc was:

```text
mentor design flaw
  -> field data
  -> user diagnosis
  -> evidence-pinned fix
  -> quantitative acceptance
```

The artifacts made this correction traceable. The case does not establish a
general cost or reliability advantage.

Fourth, some tasks need design briefs, not just repair briefs. For "find the
optimal logic" work, the mentor should make the design decisions explicitly in
the brief and number them. The apprentice should implement those decisions, not
invent the strategy. A useful scope rule emerged: existing behavior with
invariants to protect belonged in the prototype with a design brief; greenfield
build mode was outside its historical scope.

Fifth, verification is not one thing. Three regimes appeared in the author-run
cases: automatic tests, human review of a private browser-based workflow, and a
paste-and-run environment with machine syntax checks plus application-provided
measurements. Private services, account details, and screenshots are not part of
this public repository. The durable rule is to state the verification boundary
and say "I cannot verify this here" instead of manufacturing proof.

## Why the Lesson File Needs Depreciation

The long-term problem is not capturing lessons.

It is preventing the lesson file from rotting.

Anyone who has used a big `CLAUDE.md` or `AGENTS.md` has seen this failure
mode: stale rules, duplicated warnings, contradictions, and context bloat.

An archived v1 proposal therefore included lesson depreciation.

Every lesson should carry metadata:

- created date,
- source failure,
- hit count,
- last hit date,
- status: active, candidate gate, retired.

Under that archived proposal, a periodic consolidation would:

- merge duplicates,
- delete stale or contradictory rules,
- promote repeatedly-hit lessons into gate candidates,
- keep only rules that still change model behavior.

After an execution-model change, that proposal would run a retirement audit:

- disable a sample of older lessons,
- rerun representative tasks,
- retire lessons the new model no longer needs,
- promote deterministic mistakes into gates.

The asset is not "a long prompt."

The asset is a judgment balance sheet that gets reconciled.

## What The Author-Run Cases Observed

These observations are bounded to the recorded cases and do not establish causal
product benefit:

- A tiny same-repo sequence produced accepted lesson-seeded runs, with confounds.
- Review caught failures that the focused tests in those runs missed.
- Specific observed failures were encoded into deterministic gates.
- Mentor Briefs made required inputs and evidence more inspectable.
- Narrow patches were produced under tightly specified prompts; this is not a
  general weak-versus-strong model result.

## What It Does Not Prove

It does not prove:

- statistical uplift,
- cost reduction,
- cross-repo lesson transfer as a product claim,
- Mentor Briefs alone improving success rate,
- or that this should be automated yet.

The cost ratio is still unmeasured:

```text
(strong brief + strong review + weak execution) / strong direct
```

Subagent token counts were unavailable, so I am not claiming cost arbitrage.

## The Reframe

I started with:

> strong model mentors weak model

I ended with:

> judgment distillation for coding agents

That is a better frame.

A model router tries to guess whether the weak model can handle a task.

This workflow assumes the weak model will miss judgment, then gives it judgment
in forms it can actually use:

- context files,
- work orders,
- gates,
- review,
- lessons,
- and eventually checks that no model has to remember.

The goal is not to make weak models magical.

The historical design goal was to make selected judgments explicit and reusable.
The study did not prove that doing so improves weak-model outcomes.

## Final Disposition

The prototype and its evidence are preserved, but there is no active publication-
then-automation plan. The A′ measurement design was falsified; the underlying
thesis remains unproven, not disproven. Further product-level validation is not
being pursued. Any restart would require an explicit owner decision and a new
measurement contract.
