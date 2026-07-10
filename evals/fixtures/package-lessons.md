# Mentor Loop Eval Lesson Seed

- `seed_id`: mentor-loop-eval-lessons-2026-06-11-v1
- `frozen_for_release`: true

## 2026-06-11 windows-text-encoding

- `created_at`: 2026-06-11T00:00:00
- `source_run_id`: windows-encoding-third-case
- `source_failure`: report stdout crash and runtime-floor BOM false block
- `source_artifact`: reports/codex-native-v0-report.md
- `trigger`: reading/writing text files on Windows
- `mistake`: assuming UTF-8 text reads and platform stdout are enough on Windows; UTF-8 BOM files and cp1252/GBK consoles can break otherwise valid runs
- `rule_for_next_time`: read text files with utf-8-sig, write utf-8 without BOM, and reconfigure stdout/stderr to utf-8 with replacement errors
- `hit_count`: 3
- `last_hit_at`: 2026-06-11
- `status`: active
- `candidate_gate`: verifier Windows encoding smoke

## 2026-06-11 codex-command-resolution

- `created_at`: 2026-06-11T00:00:00
- `source_run_id`: jc-685-gui-live-run
- `source_failure`: codex npm .cmd shim was not found/executable through a bare command head
- `source_artifact`: reports/codex-native-v0-report.md
- `trigger`: launching codex exec from Python on Windows
- `mistake`: passing a bare command head directly to subprocess and surfacing FileNotFoundError as a naked traceback
- `rule_for_next_time`: resolve command heads with shutil.which before subprocess execution, and when resolution fails write result: ENV_FAILURE with a machine-readable tail line
- `hit_count`: 1
- `last_hit_at`: 2026-06-11
- `status`: active
- `candidate_gate`: verifier command-resolution smoke

## 2026-06-11 apprentice-shell-environment

- `created_at`: 2026-06-11T00:00:00
- `source_run_id`: jc-685-gui-live-run
- `source_failure`: apprentice codex exec sandbox could not find python, so the apprentice could not self-verify
- `source_artifact`: reports/codex-native-v0-report.md
- `trigger`: apprentice needs to run project verification commands
- `mistake`: assuming the apprentice codex exec environment has the same PATH/runtime availability as the mentor or host shell
- `rule_for_next_time`: run env-preflight before apprentice execution, and investigate codex shell_environment_policy or explicit runtime paths before relying on apprentice self-verification
- `hit_count`: 1
- `last_hit_at`: 2026-06-11
- `status`: active
- `candidate_gate`: gates/env-preflight-check.py

## 2026-06-11 apprentice-verification-summary-before-review

- `created_at`: 2026-06-11T00:00:00
- `source_run_id`: jc-685-gui-live-run
- `source_failure`: reviewer initially skipped the apprentice execution log and missed that apprentice verification did not actually run
- `source_artifact`: reports/codex-native-v0-report.md
- `trigger`: preparing artifacts for strong review
- `mistake`: generating apprentice verification summary only in the final report, after review had already happened
- `rule_for_next_time`: generate apprentice-verification-summary.md during snapshot and require reviewers to read it before writing review.md
- `hit_count`: 1
- `last_hit_at`: 2026-06-11
- `status`: active
- `candidate_gate`: verifier snapshot summary smoke

## 2026-06-11 baseline-relative-regression

- `created_at`: 2026-06-11T00:00:00
- `source_run_id`: jc-685-weak-direct-clean2
- `source_failure`: the broader regression suite was already red from known environment noise while focused verification remained clean
- `source_artifact`: experiments/jc-685-live-results.md
- `trigger`: classifying regression by absolute pass/fail in environments that do not match upstream CI
- `mistake`: pre-existing environmental failures condemn clean changes when regression checks are not pinned before editing
- `rule_for_next_time`: regression checks must be baseline-relative: pin the failing set before the change and count only new failures; this is surgical-fix Step 3 applied to eval tooling
- `hit_count`: 1
- `last_hit_at`: 2026-06-11
- `status`: active
- `candidate_gate`: eval runner baseline-relative regression check
