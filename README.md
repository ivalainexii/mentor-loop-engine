# mentor-loop-engine

**English** · [中文](README.zh.md)

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

## Two substrates, one methodology

This is the **engine** substrate. Its sibling, the
[**mentor-loop skill**](https://github.com/ivalainexii/mentor-loop), packages the same methodology as
a Claude-Code-native skill (`/mentor-loop <task>` + a subagent).

|              | skill (`mentor-loop`)            | engine (`mentor-loop-engine`)         |
| ------------ | -------------------------------- | ------------------------------------- |
| substrate    | Claude Code skill + subagent     | Python CLI driver that shells `codex` |
| entry        | `/mentor-loop <task>` in-session | `python tools/mentor-loop.py …`       |

They are **siblings, not versions** — the skill is not superseded by this engine. **Which one?**
Working inside a Claude Code session → use the skill. Want a scriptable CLI, or to drive non-Claude
models → use this engine.

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

## Honest status: a working tool vs. an open research claim

Everything above is a **working, tested mechanism you can run today**. What is *not* settled is the
research question this project started from — and this repo is deliberate about saying which is which
(measuring your own tooling honestly is part of the point, and part of what it's meant to demonstrate).

> **The open question:** does packaging judgment this way make a cheap model perform *closer to* a
> strong one — and does the architect layer's benefit **compound** as its decision ledger grows?

**Established (in this repo, verifiable by running it):** the loop runs end-to-end and produces the
full artifact set; the gates are real deterministic code exercised by tests; the
guard / escalation / architect-loop / failure-review round-trips behave as specified; 149 tests pass
and the package self-check is green.

**Still open (stated plainly so it can't be quietly skipped):**

- **The compounding claim** is a *pre-registered, open measurement*, not a finding (see below); it has
  not cleanly fallen yet.
- Recent zero-correction datapoints are **weak** — the apprentice's slice was nearly fully specified
  from the author's own validated run, not an independent execution.
- All datapoints are **author-run**: no baseline comparison (cheap-model-alone vs. full-loop), and no
  independent third-party run of this engine.
- **No cost measurement** yet — treat this as discipline tooling and a case study, not cost arbitrage.

### A read fixed in advance

This is a **tiny, single-author sample (n ≈ 7)** — nowhere near enough to conclude anything, and I
won't dress it up as if it were. But the read was written down *before* the result, so it can't be
quietly moved later:

> If the correction rate has **not clearly fallen by ~n = 8**, the "compounding" claim is recorded as an
> **honest negative** — and the pitch narrows to: judgment can be *rationed* to an architect, but is not
> shown to *compound* as the ledger grows.

The raw series lives in a target repo's `.mentor-loop/decisions.md`.

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
