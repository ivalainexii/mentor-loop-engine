# We Preregistered an Experiment. The Instrument Couldn't Measure Its Claim.

*2026-07-08*

We run a small workshop building agent tooling — most recently a "mentor-loop" engine
pairing a stronger model (mentor) with a cheaper one (apprentice) to get reliable work
out of weak models without babysitting every step. The core bet is a thesis we've
never proven: that an agent's judgment can *compound* — a running ledger of past
decisions and mistakes, fed back into future work, makes the model make fewer
mistakes over time.

Nice story. We wanted to know if it was true, so we preregistered an experiment to
test it. This is why that experiment couldn't answer the question we asked, how we
caught that, and why the research line was later closed.

> **Archive note (2026-07-10):** this is a historical postmortem, not an active
> experiment announcement. The A′ measurement design was falsified because
> the instrument could not emit its registered metric. The underlying judgment-
> compounding thesis remains unproven, not disproven, and further product-level
> validation is not being pursued. Where the narrative below describes a successor
> design, read it as an archived attempt rather than a promise of future results.

## Why we preregistered before running anything

The claim, plainly: inject a real decisions ledger — nine architecture decisions, at
the time — into a cheap model's task brief, and the correction rounds needed to reach
an acceptable result should go down, versus the same task with no ledger.

We had a handful of promising internal data points, but all weak by design — small
samples, self-run, no baseline comparison, no cold-start on unfamiliar code. Our own
guardrail rules already held this thesis **UNPROVEN**, banned language that overstated
it, and flagged zero third-party cold-start evidence. We wanted a real test, not
another anecdote.

So before running anything we wrote down the exact metric, the two arms, the task
set, and the win/loss/null decision rule — plus three standing prohibitions: no
adding a third arm mid-run, no padding the sample size to chase significance, no
placebo arm in this first pass. We also separated a small plumbing pilot from any
larger run so an invalid instrument would be detected before a full batch. The
records do not support a reliable dollar-cost comparison, so this postmortem does
not attach dollar claims to either phase.

The registered metric: **correction rounds per accepted task** — how many times a task
got kicked back for rework before it was accepted. Two arms: **L+** (real ledger
injected into the brief) and **L0** (no ledger, otherwise identical). Ten held-out
tasks the ledger had never seen — real GitHub issues on libraries like tenacity, zod,
jc, and tqdm, all closed after our task collector's cutoff, chosen to reduce the
chance the model was simply recalling solutions (we can't fully rule out training
overlap — the models' exact training cutoffs are unknown, and our records say so).

## The pilot: 11 runs, 0 accepted

We ran the pilot: eleven runs against a planned eight (retries included). Condensed
(gate column omitted — all ten `gate_blocked` rows were the same blast-radius false
positive, explained below; every row's logged arm = `full-loop`, also explained
below):

| Task | Outcome | Review verdict |
|---|---|---|
| tenacity-420 | protocol_violation | — |
| tenacity-420 | gate_blocked | Approved |
| tenacity-420 | gate_blocked | Approved |
| tenacity-420 | gate_blocked | Needs fixes (lint only) |
| zod-5273 | gate_blocked | Approved |
| zod-5273 | gate_blocked | Approved |
| zod-5273 | gate_blocked | — |
| jc-694 | gate_blocked | — |
| jc-694 | gate_blocked | Approved |
| tqdm-1701 | gate_blocked | Needs fixes (lint only) |
| tqdm-1701 | gate_blocked | — |

Zero of eleven runs reached `accepted`. Ten hit `gate_blocked`, one hit
`protocol_violation`. And every row's arm column says `full-loop` — not L+, not L0
(treatment and control).
The independent variable never made it into the primary data file. We could
reconstruct which runs were which arm from working-directory artifacts (was the
ledger file present or not), but the comparison the experiment existed to make wasn't
recoverable from the data we actually logged.

The gate blocks weren't real scope violations, either. One review verdict said it
outright: the blast-radius gate's BLOCKED status was a **false positive** — the brief
had written its touched-file list as prose instead of the one-path-per-line format
the gate's parser expects, so a deterministic gate choked on formatting, not actual
scope drift. Where reviews did reach a functional verdict, they were good: several
Approved outright, two more Needs-fixes for trivial lint only, functionally correct
per the reviewer.

Tempting surface read: "the model's doing fine, the harness is buggy, close enough to
evidence things work." We didn't take that read. Here's why.

## The twist: the metric couldn't exist, and the model was too good to test it

We sent the raw pilot data to adjudication twice, in parallel — each pass ran without
seeing the other's work, and the two were then compared head-to-head. Both converged
on the same finding, by different paths.

First: our harness runs each task in a **single pass** — a fact we only pinned down
after the pilot, which is the whole problem. (The "loop" in mentor-loop is the
mentor's brief-verify-review pass around the apprentice, not an iterate-until-accepted
retry loop — a naming trap we walked into ourselves.) The registered metric —
correction rounds per accepted task — requires observing a task get sent back for
rework, possibly repeatedly, until accepted. A single-pass harness cannot produce
that number, at any apprentice tier, no matter how the pilot had gone. We'd
preregistered a metric our own instrument was incapable of emitting — an
instrument-design flaw found at pilot cost, not a finding about whether ledgers help.

Second, independently: even setting the instrument problem aside, the model tier we
ran was too strong to generate the failures the metric needs. Where a functional
verdict came through, it was correct — under a stronger mentor tier than our baseline
eval batches use, on four held-out tasks — no bugs were showing up for a ledger to
help fix. A metric built on "how many mistakes get corrected" is silent when the model
isn't making mistakes to begin with: a ceiling effect. You can't measure a reduction
in errors from a baseline of zero errors.

Third, a construct-validity flag both adjudications caught: the ledger we injected
held decisions from our own internal build history; the held-out tasks were on
unrelated public libraries. Even a perfect version of this experiment would measure
whether priming a model with unrelated prior context helps it on a new codebase — not
whether judgment "compounds" project-over-project as the original thesis claims.
Different claims; only the narrower one would have been supportable.

## How it got caught: two adjudications, one retraction

Worth calling out, not hiding: we ran two independent read-outs of the same pilot
data, from separate sessions, blind to each other during the run and compared only
afterward — and the comparison is what did the catching. They didn't agree at first.

The first concluded the instrument couldn't produce the registered metric at any
tier, and that the honest disposition was to close the experiment as
**uninformative** — not evidence for the thesis, not against it, a null result from a
broken ruler.

The second, working independently, initially reasoned toward fixing the pilot's
plumbing bugs and rerunning at the original baseline model tier, on the theory that a
different (weaker) model combination had shown real outcome variance before, so the
metric might still have room to move. That reasoning rested on a misread of an
earlier, unrelated batch of results.

When the two were compared, the second adjudication retracted its own
recommendation and adopted the first's conclusion in full — in writing, with the
specific reasoning error named. We include that retraction here as a feature of the
process, not a footnote to skip past. The point of cross-checking a judgment call
with an independent second pass is to catch exactly this. It worked: one pass got it
right, the other got it wrong first and then caught itself against the first. Had we
run only one adjudication, we might have shipped a "let's rerun" plan that spent
budget on a metric that was never producible, regardless of which model ran it.

## The honest close: uninformative, not disproven

Stated the way our own rules require: the compounding-judgment thesis remains
**unproven** — exactly where it stood before this pilot. The experiment produced
**zero evidence in either direction**. Not weak evidence for the thesis, not against
it. The instrument that was supposed to measure the effect couldn't, full stop — a
ceiling-effect result and an absence-of-evidence result look identical from outside.

We're not calling this a failure of the underlying thesis — it is a failure of one
measurement design. The pilot did what a plumbing pilot should: it exposed the
structural problem before a larger batch reused the same invalid instrument. This
is a scope-control result, not evidence of cost savings.

## The archived successor design

We didn't patch the old metric. Preregistration only works if "the metric can't be
measured" triggers a new experiment, not a quietly loosened old one. A separately
preregistered successor design changed three things: a new primary metric
(first-pass review approval rate per task, a number our single-pass harness can
actually produce); a weaker, more error-prone apprentice tier with a documented
non-zero baseline failure rate, so there's room for a ledger to move the number
either way; and arm labels written directly into the scorecard's data columns, not
reconstructed after the fact from which working directory had a ledger file. It
would have reported direction and raw counts only — no p-values on an n of ten.

The successor attempt reached two scheduled rows before a subscription quota stopped
the batch. Both rows were voided before the mentor attempted a brief, so they carry no
signal about the ledger question. The batch did not resume and is now archived with
the rest of the research program. A subscription quota is a capacity constraint, not
evidence of zero marginal cost, so no dollar or cost-advantage conclusion is drawn.

## Practitioner lessons

Five things we wish we'd checked before locking the design:

1. **Verify your harness can actually emit the metric you're registering, before you
   register it.** We locked in "correction rounds" without confirming our
   single-pass runner could produce a number that requires multiple passes. Run one
   dry pass and check the field exists and means what you think.

2. **Watch for ceiling effects.** A model tier too strong for the task produces zero
   errors, leaving nothing for your treatment to reduce. A "fewer mistakes" metric
   needs a baseline where mistakes actually happen — pick a tier with a known
   non-zero failure rate, or you're measuring nothing.

3. **Arm labels belong in the primary data file**, not reconstructed from which
   working directory had which file present. If a human has to spelunk through run
   artifacts to figure out which row was which condition, the experiment's central
   comparison isn't actually in your data.

4. **Deterministic gates need spec-formatted inputs — fix the input, never loosen
   the gate.** Our blast-radius gate false-positived because a brief listed touched
   files as prose instead of the expected parseable format. Fix the input to conform
   to spec; a gate that can be talked past isn't a gate.

5. **Preregistration discipline bounded the invalid run.** Because we wrote the
   win/loss/null rules down before running anything and separated the plumbing pilot
   from the full batch, the design flaw was found after the pilot rather than after a
   completed batch. The records establish bounded exposure, not a dollar saving.

## Where this leaves us

The thesis that judgment compounds through a decisions ledger is still unproven,
not disproven. This round produced zero evidence either way. A successor instrument
was designed, but its incomplete rows produced no usable evidence and the batch is
archived rather than paused. Further product-level validation is not being pursued;
there is no pending result or promised follow-up. Reopening the question would
require an explicit new decision and measurement contract.

The mentor-loop harness is public:
[github.com/ivalainexii/mentor-loop-engine](https://github.com/ivalainexii/mentor-loop-engine).
(The private decision ledger is not part of this public repository.)
