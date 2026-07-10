# Work Order 3: two small runner fixes from the full probe rerun

> **Archived work order (2026-07-10):** retained as historical runner context,
> not as a pending instruction. No command or next step in this file is currently
> authorized or awaiting execution. Further product-level validation is not being
> pursued; `README.md` controls current status and claims.

Work orders 1-2 are DONE and live-verified. Probe rerun results (jc-694, new
classifier): raw-weak=accepted, lessons-only=verification_failure, full-loop=
crashed. Note raw-weak and lessons-only SWAPPED outcomes vs the previous
rerun — single-run arm differences are pure spark variance; record this
observation in eval-suite report (it justifies multi-run aggregation).

## FIX 1 (blocking full-loop): {package} placeholder not substituted

codex-live.config.json has `"mentor_loop_config": "{package}/mentor-loop.config.json"`.
run-task.py passes this string to the engine UNRENDERED → FileNotFoundError
(evidence: artifacts\jc-694-lsattr-spaces\full-loop\20260611-200816-907765\full-loop.txt).
Render {package} (and any other placeholders) on the mentor_loop_config value
before use, same substitution map as the command templates.

## FIX 2: infra crashes are not protocol violations

The crash above was classified `protocol_violation` — that label must be
reserved for the MODEL breaking rules (out-of-scope edits etc.). Add an
`infra_error` outcome_type for runner/engine exceptions (or classify them as
env_failure); update README outcome list + verifier.

## FIX 3 (blocking ALL non-jc tasks): source clone cache is not keyed per repo

The runner caches the base clone in a single `<work-root>/source` directory.
The probe cloned jc there; every subsequent task from a DIFFERENT repo then
ran `git worktree add` against the jc clone and died instantly with
`fatal: invalid reference: <sha>^1` (live evidence: 22/22 batch runs
env_failure in 9 seconds total; `git -C source remote get-url origin` returns
kellyjonbrazil/jc). Fix: key source clones per repository, e.g.
`<work-root>/source/<sanitized-repo-slug>/`, creating each on first use.
Ensure clones are full (not shallow) so `<merge_sha>^1` always resolves.
Migrate: existing `source` dir can be moved to its jc slug or simply
re-cloned. Also add a verifier case: two mock tasks with different repo URLs
must produce two distinct source clones.

## DO NOT BUILD anything else. Verifier + zip as usual.

DONE WHEN: mock full-loop dry-run passes with a {package}-style config value;
a forced runner exception classifies as infra_error; verifier green; zip
refreshed.
