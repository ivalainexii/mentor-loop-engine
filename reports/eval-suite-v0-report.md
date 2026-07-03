# Eval Suite v0 Report

## Built

- `evals/env-preflight-check.py`
- `evals/collect-tasks.py`
- `evals/fixtures/collect-tasks.fixture.json`
- `evals/run-task.py`
- `evals/run-task`
- `evals/mock-codex.py`
- `evals/mock-codex.config.json`
- `evals/codex-live.config.json`
- `evals/scorecard-template.csv`
- `evals/tasks/mock-smoke.json`
- 12 real task definitions under `evals/tasks/`
- `evals/README.md`
- `evals/RUNBOOK.md`

## Verified Locally

- `env-preflight-check.py` passes on the mock task fixture.
- `run-task.py` dry-runs `raw-weak` with mock Codex and appends one scorecard
  row.
- `run-task.py` dry-runs `full-loop` with mock Codex through the one-shot
  engine path and appends one scorecard row.
- `collect-tasks.py` dry-runs against a mocked HTTP fixture and writes a
  candidate with repo, issue URL, PR URL, merge time, base commit expression,
  changed files, diff size, and verification hint.
- The package verifier includes the mock runner checks.
- The package verifier checks that real tasks count is 10-15, cover at least
  two languages, exclude polluted `jc-685`/`jc-687`, have diff size under 100,
  and include ground truth, checkout metadata, env deps, and focused/regression
  verification commands.

## Probe Rerun Notes

The first `jc-694` probe rerun under the baseline-relative classifier produced
single-run arm variance: `raw-weak` was accepted, `lessons-only` failed
verification, and `full-loop` exposed a runner infrastructure bug. This should
not be read as an arm-level conclusion. It is evidence that the baseline needs
multi-run aggregation, and that `infra_error` must be separated from model
protocol violations in the scorecard.

## Task Table

| Task | Language | Close date | Diff lines | Issue | PR | Cutoff note |
|---|---|---:|---:|---|---|---|
| `execa-1193-kill-zero-ci` | JavaScript/TypeScript | 2025-10-27 | 17 | [issue](https://github.com/sindresorhus/execa/issues/1193) | [PR](https://github.com/sindresorhus/execa/pull/1212) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `jc-694-lsattr-spaces` | Python | 2026-04-17 | 23 | [issue](https://github.com/kellyjonbrazil/jc/issues/694) | [PR](https://github.com/kellyjonbrazil/jc/pull/697) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `tenacity-420-loguru-traceback` | Python | 2026-03-05 | 27 | [issue](https://github.com/jd/tenacity/issues/420) | [PR](https://github.com/jd/tenacity/pull/622) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `tenacity-544-tryagain-cause` | Python | 2026-05-22 | 76 | [issue](https://github.com/jd/tenacity/issues/544) | [PR](https://github.com/jd/tenacity/pull/640) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `tenacity-554-logger-protocol` | Python | 2026-02-19 | 2 | [issue](https://github.com/jd/tenacity/issues/554) | [PR](https://github.com/jd/tenacity/pull/586) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `tenacity-613-retry-statistics` | Python | 2026-02-25 | 47 | [issue](https://github.com/jd/tenacity/issues/613) | [PR](https://github.com/jd/tenacity/pull/614) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `tqdm-1701-pandas-compat` | Python | 2026-01-30 | 53 | [issue](https://github.com/tqdm/tqdm/issues/1701) | [PR](https://github.com/tqdm/tqdm/pull/1703) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `yargs-2497-apply-extends-proto-pollution` | JavaScript/TypeScript | 2026-02-22 | 8 | [issue](https://github.com/yargs/yargs/issues/2497) | [PR](https://github.com/yargs/yargs/pull/2498) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `zod-5273-dynamic-catch-json-schema` | JavaScript/TypeScript | 2026-05-04 | 11 | [issue](https://github.com/colinhacks/zod/issues/5273) | [PR](https://github.com/colinhacks/zod/pull/5925) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `zod-5824-falsy-prefault-json-schema` | JavaScript/TypeScript | 2026-04-29 | 34 | [issue](https://github.com/colinhacks/zod/issues/5824) | [PR](https://github.com/colinhacks/zod/pull/5893) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `zod-5937-catch-absent-object-keys` | JavaScript/TypeScript | 2026-05-03 | 66 | [issue](https://github.com/colinhacks/zod/issues/5937) | [PR](https://github.com/colinhacks/zod/pull/5939) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |
| `zod-5944-cidrv6-json-schema` | JavaScript/TypeScript | 2026-05-04 | 10 | [issue](https://github.com/colinhacks/zod/issues/5944) | [PR](https://github.com/colinhacks/zod/pull/5945) | closed after 2025-09-01 collector cutoff; exact cheap-model training cutoff unknown |

## Known Gap

Live baseline execution is still pending by design. The task definitions are
ready for the human terminal runbook, but their setup and verification commands
should be treated as first-run candidates: if env-preflight cannot pass within
30 minutes, swap the task.

## Parked In Future

- CI.
- Dashboarding.
- Parallel execution framework.
- Automatic GitHub task miner.
