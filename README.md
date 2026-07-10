# mentor-loop-engine

**English** · [中文](README.zh.md)

> **Project status (2026-07-10): preserved research prototype; superseded as the
> default system architecture.** The CLI, tests, experiments, and reports remain available
> as evidence and reusable primitives. This repository has no active product roadmap; new
> work is limited to evidence-backed defects or explicitly chosen reuse. The rollback baseline
> is the annotated tag `mentor-loop-v2-preserved-20260710`.

| Claim / commitment | Close-out status | Evidence-bounded reading |
| --- | --- | --- |
| Deterministic engine, artifact trail, and fail-closed package/runtime checks | **completed** | 206 unit tests and the package verifier pass at the preserved baseline |
| Auditability and prevention of specific observed failure modes | **partially answered** | Author-run cases found real failures and produced gates; no third-party engine cold-start |
| A′ registered metric could measure the intended compounding effect | **falsified** | The metric was structurally unable to produce the intended signal; see the postmortem |
| Further product-level validation of cheap-model outcome uplift, cost advantage, or judgment compounding | **not pursued** | Earlier author-run experiments were insufficient for a trustworthy baseline/cost result; this repo makes no product claim |

Keep a cheap coding agent on a short leash. It executes a strong model's work order **inside a
deterministic scope gate** (edits to files the plan didn't list are blocked), under a review that reads
only the diff — and every run is written to disk so you can audit exactly what happened.

`mentor-loop-engine` is a small CLI that runs a **three-tier code-change loop**:

- **mentor** (strong) writes the work order — the *Mentor Brief* — and reviews the diff;
- **apprentice** (cheap) executes strictly inside the brief's declared blast radius;
- **gates** (deterministic code, no model judgment) check the change against that blast radius;
- **architect** (strong) is consulted, and its ruling recorded, whenever a change touches an
  architecture decision — so decisions don't silently drift.

It's **model-agnostic**: the engine drives a CLI (shipped configured for `codex`), so *strong*,
*cheap*, and *architect* are simply whichever models you point it at.

## Why you'd want it

- **Scope control.** A deterministic blast-radius gate blocks edits to any file the brief didn't list —
  an out-of-scope change is stopped before it lands. (It bounds *which files* change, not whether the
  logic inside them is correct — see the honest status below.)
- **Diff-only review.** A strong review reads only the diff, the brief, and the evidence, then returns
  Approved / Needs-fixes / Stop-and-re-plan.
- **A local audit trail.** Brief, apprentice log, gate outputs, diff, review, and final report — every
  run lands under `.mentor-loop/runs/<id>/`, so you can reconstruct any change after the fact.
- **Guards that escalate instead of guessing.** A brief must declare each guard's fail-direction; a
  guard left *fail-open* is routed to an architect **before** the cheap model runs, and the ruling is
  recorded and enforced on the next run.
- **Optional cross-vendor advisory.** Have a second-vendor model read the brief for gaps the mentor
  missed — before any code is written. Advisory only, off by default.
- **Covered by tests.** The gates and stages are exercised by unit tests, and a package self-check runs
  green — real execution, not "OK by inspection": `python -m unittest discover -s tests` and
  `python tools/verify-package.py` both pass.

## How it works in 60 seconds

A strong model (mentor) writes a work order — the Mentor Brief; a cheap model
(apprentice) executes it inside a declared blast radius; deterministic gates check
scope before a strong review ever reads the diff. Repeated failure on the same
target escalates to an architect audit of the brief, not another blind retry. Full
walkthrough, with real commands and artifacts: [docs/architecture-tour.md](docs/architecture-tour.md).

## Two substrates, one methodology

This is the **engine** substrate. Its sibling, the
[**mentor-loop skill**](https://github.com/ivalainexii/mentor-loop), packages the same methodology as
a Claude-Code-native skill (`/mentor-loop <task>` + a subagent).

|              | skill (`mentor-loop`)            | engine (`mentor-loop-engine`)         |
| ------------ | -------------------------------- | ------------------------------------- |
| substrate    | Claude Code skill + subagent     | Python CLI driver that shells `codex` |
| entry        | `/mentor-loop <task>` in-session | `python tools/mentor-loop.py …`       |

Within the preserved v2 line they are **siblings, not versions** — one did not replace the other.
The product line itself is now superseded as the default architecture. For historical or explicit
reuse: work inside Claude Code → use the skill; need a scriptable CLI or non-Claude driver → use
this engine.

## Quickstart

Requirements: Python 3.10+, a target **git** repo with a clean worktree, and a `codex` CLI on `PATH`
(the shipped `mentor-loop.config.json` calls `codex exec`; point it at your own model). A copyable
template is in `mentor-loop.config.json.example`.

Staged workflow — the mentor session writes `mentor-brief.md` and `review.md`; the engine runs the
deterministic stages and the cheap apprentice shell-out:

```powershell
python path\to\mentor-loop-engine\tools\mentor-loop.py init        --repo path\to\target-repo "fix <bug>"
python path\to\mentor-loop-engine\tools\mentor-loop.py brief-check  --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py apprentice   --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py gates        --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py snapshot     --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py capture-lesson --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py report       --repo path\to\target-repo --run <run-id>
```

When a brief escalates a fail-open guard, the architect-loop stages assemble a consult packet and
record the ruling back to the ledger:

```powershell
python path\to\mentor-loop-engine\tools\mentor-loop.py architect-packet --repo path\to\target-repo --run <run-id>
# take the packet to a strong architect, save its verdict under .mentor-loop/runs/<run-id>/, then:
python path\to\mentor-loop-engine\tools\mentor-loop.py architect-ratify --repo path\to\target-repo --run <run-id> --verdict <file> --ref <ref>
```

A one-shot `run` path and a `--dry-run` flag also exist. When the **same target** keeps failing
(repeated failure, not a fail-open guard), the engine escalates to a direction-only architect
review instead of retrying blind; a narrowed or re-routed retry inherits the same failure history
via `--target`:

```powershell
python path\to\mentor-loop-engine\tools\mentor-loop.py run --repo path\to\target-repo --target <parent-target-id> "<narrowed task>"
```

See `operator-runbook.md` ("Failure-Review Loop") for the full trigger/verdict/park behavior, and
`quickstart.md` for the full manual workflow.

## How the loop is wired

```
architect (strong, consulted at decision points)  ── rules on architecture; ruling recorded to a ledger
     │
mentor (strong, per task)  ── writes the Mentor Brief (the work order) and reviews the diff
     │
apprentice (cheap, per run)  ── executes strictly inside the brief's blast radius
     │
gates (deterministic code)  ── blast-radius + runtime-floor checks; no model judgment
```

The engine carries four guard/escalation mechanisms beyond the base loop: a **brief-honesty gate**
(every guard must declare a fail-direction + reason), **architect escalation** (a fail-open/unsure
guard is routed to the architect before the apprentice runs; the mentor may not self-approve it),
**architect-loop closure** (the engine assembles the consult packet, injects prior decisions into
future briefs, and records the ruling back to the ledger — no ruling, no unlock), and a
**failure-review loop** (the sibling POST-execution escalation: the same target failing repeatedly
routes to a direction-only architect audit — never a code review — instead of a blind retry; see
`operator-runbook.md`).

## Honest status: a working tool and a closed research program

Everything above is a **working, tested mechanism you can run today**. The research program that
produced it is now closed rather than left as an implied product obligation. Its historical question
was whether packaging judgment this way made a cheap model perform *closer to* a strong one, and
whether the architect layer's benefit **compounded** as its decision ledger grew.

**Established (in this repo, verifiable by running it):** the loop runs end-to-end and produces the
full artifact set; the gates are real deterministic code exercised by tests; the
guard / escalation / architect-loop / failure-review round-trips behave as specified; 206 tests pass
and the package self-check is green.

**Final research disposition:**

- The preregistered A′ **measurement design was falsified**: the harness structurally could not produce
  the intended metric. The pilot therefore closed **uninformative**, providing zero evidence in either
  direction about the underlying compounding thesis.
- The cheap-model uplift, cost-advantage, and compounding theses remain **unproven, not disproven**.
  Earlier datapoints were author-run, tiny, and confounded by an apprentice slice largely specified
  from the author's validated run; there was no trustworthy cheap-model-alone baseline, cost measure,
  or independent third-party engine run.
- Further product-level validation is **not pursued**. There is no remaining `n ≈ 8` obligation or
  active roadmap. Treat this as discipline tooling and a case study, not cost arbitrage. Reopening the
  research would require an explicit decision and a new measurement contract.

The historical raw series lives in a target repo's `.mentor-loop/decisions.md`. The full A′
postmortem, including how two independent adjudications caught the invalid metric, is in
[docs/aprime-postmortem.md](docs/aprime-postmortem.md).

## Current limitations

- **No third-party cold-start of this engine.** The sibling *skill* had one interactive cold-start;
  this engine has not. Installing/running from these docs on a fresh machine is an untested path —
  reports welcome.
- **Windows-first.** Developed and tested on Windows; the `codex` sandbox has real platform limits
  (see `reports/codex-cli-limitation-report.md`).
- **The research log is raw.** `experiments/`, `evals/`, and `reports/` are dated internal notes and
  evidence, superseded in places. The claims that stand are the ones in *this README*; where an older
  note reads as a stronger claim, this README overrides it.

## Repository layout

- `tools/mentor-loop.py` — the stage engine (loop + gates + architect-loop closure).
- `tools/verify-package.py` — release self-check (manifest, gates, tests, optional zip).
- `gates/` — the two deterministic gates (blast-radius, runtime-floor).
- `tests/` — unit tests (`unittest discover -s tests`).
- `*-template.md`, `subagents/`, `skills/`, `.claude/` — the loop's prompt artifacts and Claude-Code wiring.
- `evals/`, `experiments/`, `reports/` — the (raw) research log and evidence.

## License

MIT — see `LICENSE`.
