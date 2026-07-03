# Publication Assets

Use these after the writeup has a public URL. Keep the evidence modest: this is
a case study, not a benchmark.

## One-Line Positioning

I tested a "strong model mentors weak model" coding workflow. The surprising
result: briefs mostly bought auditability; the durable leverage came from
lessons and gates.

## Do Not Claim

- Do not claim statistical uplift.
- Do not claim cost savings.
- Do not claim cross-repo lesson transfer as proven.
- Do not claim Mentor Briefs alone improved success rate.
- Do not claim this is a general agent framework.

## Safe Claims

- Same-repo lessons transferred across related parser tasks in the `jc` repo.
- Strong review caught a runtime compatibility issue that focused tests missed.
- A real protocol failure improved the deterministic blast-radius gate.
- Mentor Briefs improved auditability: baseline, repro, context, stop
  conditions, and reviewer visibility.
- `pflow-389` was a verification-incomplete boundary run, not an accepted
  success.

## HN Titles

Recommended:

- I tested whether a strong model could mentor a weak model

Alternates:

- Strong model mentors weak model: a small coding-agent case study
- Lessons transferred, briefs bought auditability
- I tried to make weak coding models behave more like strong ones
- Judgment distillation for coding agents
- How to stop your CLAUDE.md from rotting

Avoid:

- "Weak models are as good as strong models"
- "I reduced AI coding cost by X%"
- "A new agent framework"
- "Benchmarks show..."

## HN Post Body

I ran a small public case study on whether a strong coding model can "mentor" a
weaker one.

The original idea was:

- strong model writes a detailed brief,
- weak model executes,
- deterministic gates check scope,
- strong model reviews only the diff,
- reusable mistakes become lessons.

The surprising result was not that the brief made the weak model dramatically
better. In the small `jc-687` ablation, lessons-only and lessons-plus-brief
both went 2/2. The Mentor Brief mostly bought auditability: baseline, repro,
context read, stop conditions, and reviewer visibility.

The stronger mechanism was:

`review -> lesson -> gate`

Two real examples:

- A weak run passed focused tests but used `str.removeprefix()` in a project
  supporting Python 3.6. Review caught it, and it became a runtime-floor lesson.
- Another weak run fixed the bug but left untracked `.surgical-fix/` artifacts.
  The blast-radius gate missed it because it used `git diff --name-only`; the
  gate now uses `git status --porcelain`.

This is not a benchmark. n is tiny, cost ratio is unmeasured, and one pflow
boundary run is verification-incomplete because the environment lacked
`uv`/`pytest`/`PyYAML`.

But the product insight feels real: the durable asset is not a smarter model
router. It is a judgment distillation loop for coding agents.

The part I now think deserves more attention is lesson rot. If lessons only
accumulate, they become another stale `CLAUDE.md`: duplicated warnings, old
model workarounds, contradictions, and context bloat.

So v1 should treat lessons like a judgment asset ledger: each lesson has a
source failure, hit count, last-hit date, and status. Repeated hits get promoted
into gates. Stale rules get retired when a newer model no longer needs them.

## X Thread

1.

I tested whether a strong coding model can "mentor" a weaker one.

The surprising answer:

Briefs mostly bought auditability.

The real leverage came from lessons + gates.

2.

The loop was deliberately manual:

- strong model writes brief
- weak model executes
- gate checks scope
- strong model reviews diff
- reusable mistake becomes lesson

No agent framework. Human glue first.

3.

The key ablation was small:

- raw weak: 1 accepted, 1 protocol violation
- weak + lessons: 2 accepted
- weak + lessons + brief: 2 accepted
- strong direct: 1 accepted

This is a case study, not a benchmark.

4.

The brief did not show clear success-rate lift over lessons-only.

But it did improve auditability:

- baseline
- repro
- context read
- stop conditions
- reviewer visibility

That is useful, just a different claim.

5.

The useful mechanism was:

review -> lesson -> gate

Example: review caught `str.removeprefix()` in a Python 3.6-compatible project.

That became a lesson: check runtime floor before using newer APIs.

6.

Another weak run fixed the bug but left untracked `.surgical-fix/` artifacts.

The gate missed it because it used `git diff --name-only`.

The gate now uses `git status --porcelain`.

One failure became a permanent check.

7.

That changed the product frame for me.

It is not "a model router."

A router guesses whether the weak model can handle the task.

This loop assumes weak models miss judgment, then moves judgment into artifacts
they can follow.

8.

The long-term trap is lesson rot.

Lessons need metadata:

- source failure
- created date
- hit count
- last hit
- status: active / candidate gate / retired

Otherwise your lessons file becomes another stale CLAUDE.md.

9.

What this does NOT prove:

- statistical uplift
- cost savings
- cross-repo transfer
- Mentor Briefs alone improving success rate

What it supports:

same-repo lessons + gates can make weak-model work more disciplined.

10.

My current framing:

judgment distillation for coding agents

review catches mistake
lesson prevents repeat
gate makes it cheap forever

11.

The v1 question is not "how do I capture more lessons?"

It is:

how do I stop my lessons file from becoming a stale CLAUDE.md?

Answer: metadata, consolidation, and retirement audits.

## Reddit / LocalLLaMA Post

Title:

I tested a strong-model/weak-model coding workflow. The useful part was not the
brief.

Body:

I ran a small case study on whether a strong coding model can mentor a cheaper
weak model.

The workflow:

- strong model writes a detailed brief,
- weak model executes,
- deterministic gate checks scope,
- strong model reviews the diff,
- reusable mistake becomes a lesson.

The result was more interesting than I expected. The Mentor Brief mostly bought
auditability, not obvious success-rate lift. In the main small ablation,
lessons-only and lessons-plus-brief both succeeded. The brief made it easier to
inspect the run: baseline, repro, context read, stop conditions, and review
evidence.

The real mechanism was `review -> lesson -> gate`.

Example 1: a weak run passed focused tests but used a Python API newer than the
project's supported runtime. Strong review caught it. That became a lesson:
check runtime floor before choosing APIs.

Example 2: another weak run fixed the bug but left untracked artifacts. The
gate missed it because it used `git diff --name-only`; now it uses
`git status --porcelain`.

Important caveats:

- This is not a benchmark.
- Sample size is tiny.
- Cost ratio is unmeasured.
- Cross-repo transfer is not proven.

The product idea I am left with is not a model router. It is a judgment
distillation loop: move judgment from strong review into lessons, then from
lessons into deterministic gates.

The maintenance problem matters as much as capture. A lesson file that only
grows becomes a stale `CLAUDE.md`. The next version needs metadata, hit counts,
consolidation, and retirement audits so old model workarounds can disappear.

## Launch Checklist

- Publish `writeup-draft.md` as the canonical article.
- Link raw CSVs:
  - `experiments/jc-685-live-results.csv`
  - `experiments/jc-687-ablation-results.csv`
  - `experiments/pflow-389-boundary-results.csv`
- Link the evidence index:
  - `evidence-index.md`
- Link the gate code:
  - `gates/blast-radius-check.py`
  - `gates/runtime-floor-check.py`
- Link the package verifier:
  - `tools/verify-package.py`
- Mention that `pflow-389` is verification-incomplete.
- Mention cost ratio is unmeasured.
- Mention lesson decay as v1 design guidance, not implemented v0 automation.
- Invite criticism on methodology, not model fan tribalism.

## Likely Criticism And Replies

Criticism: "n is tiny."

Reply: Correct. This is a case study with raw rows, not a benchmark.

Criticism: "You did not prove cost savings."

Reply: Correct. Token accounting was unavailable from subagent runs. The
current claim is discipline and auditability, not cost arbitrage.

Criticism: "Aider/Claude Code already do architect/editor."

Reply: Yes. The differentiator here is not strong/weak split by itself. It is
the `review -> lesson -> gate` distillation loop and the refusal to build a
framework before evidence.

Criticism: "Why not just use the strong model?"

Reply: That remains the right answer for high-stakes or one-off work. The loop
is interesting when the same repo is worked on repeatedly and lessons/gates can
compound.

Criticism: "Won't the lessons file become prompt bloat?"

Reply: Yes, if it is append-only. The v1 design treats lessons as a ledger:
metadata, hit counts, consolidation, promotion to gates, and retirement when
newer models no longer need the rule.

Criticism: "Your pflow run did not verify."

Reply: Correct. It is recorded as `verification_incomplete` and used only as a
boundary note.
