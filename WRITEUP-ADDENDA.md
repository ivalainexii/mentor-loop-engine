# Writeup Addenda — evening of 2026-06-11 (fold into writeup-draft.md)

From the mentor session, after a full day of live dogfooding (10 runs across
3 codebases: a Python library, an Electron+Playwright app, a Google Apps
Script). These are findings the current draft predates.

## 1. Discipline cuts the STRONG model's context bill too

Observation (NOT yet evidence — state it honestly or not at all): the user
noticed the mentor's token burn drop over the day. Decomposed honestly, the
causes rank:
1. Within-conversation working memory (largest): the evening script was
   pasted once at run #7; runs #8-#10 reused that context with no re-reading.
   Any long session gets this free. NOT carried over from the afternoon —
   the afternoon file (.mjs app) and evening file (.gs script) are different
   projects (her correction). This is not the ledger — it's working memory.
2. Easier tasks: #7-#10 were delete-a-function / add-a-clamp / flip-an-
   operator edits; briefs could point at exact lines. The afternoon TDCA work
   was multi-path UI diagnosis, intrinsically context-heavy.
3. Process overhead reduction (real but smallest): template reuse, artifacts
   in files instead of in-conversation, one-line fix orders. This saves
   EXPRESSION and TRANSPORT cost, not judgment cost.
Plus deliberately shorter replies (output is 5x input price).
The genuine "ledger compounds" claim belongs to CROSS-TASK eval data (lessons
help the NEXT different task; a gate saves a whole execute round), NOT to this
single-file evening. Do not sell the evening anecdote as proof of compounding
— it is at best a hypothesis-generating observation, and overclaiming it is
itself the "strong model serving the metric" failure the loop is meant to
catch.

## 2. The process caught STRONG models six times in one day

Worth a section — the gates/protocol are not weak-model babysitting:
1. Reviewer (strong) skipped the apprentice log; the verification-summary
   artifact caught it.
2. Mentor declared "it's past midnight" while holding run IDs saying 20:38 —
   narrative inertia vs data.
3. Mentor's own verbose output was the user's #2 pain (glance-first thesis
   applied to its author).
4. Mentor wrote a non-template Blast Radius section; the gate fail-closed
   BLOCKED the run on a formatting error (allowed_files: none).
5. Mentor designed a performance acceptance comparing timings across
   different code semantics AND workloads — inconclusive by construction.
6. Reviewer round 1 caught an inverted clamp comparison only by substituting
   concrete values (floor T-5 vs latest T-10).

## 3. A regression introduced, diagnosed, and fixed inside the loop

Run #8 (per-tab incremental refresh) introduced a permanent slowdown:
dormant accounts' windows never advance, so every run re-scans from their
ancient latest date (40/47s → 69/80s). The USER diagnosed the root cause
from observed behavior; run #10 clamped the window to max(latest, today-5)
with a human-visible "clamped from" annotation (→ 48/61s, validation 14→5s).
Full arc: design flaw by the mentor → field data → user diagnosis →
evidence-pinned fix → quantitative acceptance. The loop's value is not
"no mistakes"; it is that every mistake left artifacts that made the next
step cheap.

## 4. Design-type briefs

Run #8 established the pattern for "find the optimal logic" tasks: the
MENTOR makes the design decisions (enumerated, numbered, in the brief); the
apprentice implements exactly. "Think out the best solution" is never
delegated to the cheap model — that is the judgment the loop exists to
supply. Scope rule of thumb: existing behavior with invariants to protect →
loop with a design brief; greenfield → out of scope (build mode, future).

## 5. Verification-tier taxonomy held up

Three verification regimes all worked in one day: full-automatic (Python
library with test suite), human-in-the-loop (real bank portals, screenshots
as decisive evidence), and paste-and-run (Apps Script — syntax check is the
only machine gate; quantitative acceptance via the script's own timing
columns). The brief's job is to pick the regime honestly, and the apprentice
must say "I cannot verify this here" rather than claim proof.
