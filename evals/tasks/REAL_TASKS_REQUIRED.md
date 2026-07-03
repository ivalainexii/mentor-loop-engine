# Real GitHub Tasks Required

The eval runner is built and mock-verified. The live benchmark still needs
10-15 real GitHub tasks before the suite can be used for claims.

Each task must satisfy all rules:

- Closed GitHub issue with a merged fix PR.
- Ground-truth fix diff under 100 changed lines.
- Repo has runnable focused and regression verification commands.
- Suite covers at least Python plus one more language.
- Prefer issues closed after the cheap model's training cutoff; if the cutoff
  is unknown, record `training_cutoff_relation: unknown`.

## JSON Template

```json
{
  "id": "owner-repo-issue-number-short-slug",
  "language": "Python",
  "repo": {
    "url": "https://github.com/owner/repo.git",
    "base_ref": "<commit before fix PR>",
    "checkout_commands": [
      "git clone https://github.com/owner/repo.git",
      "git checkout <base_ref>"
    ]
  },
  "ground_truth": {
    "issue_url": "https://github.com/owner/repo/issues/123",
    "fix_pr_url": "https://github.com/owner/repo/pull/456",
    "close_date": "YYYY-MM-DD",
    "fix_diff_lines": 42,
    "training_cutoff_relation": "after cutoff | before cutoff | unknown"
  },
  "issue": {
    "title": "Issue title",
    "body": "Issue body or concise reproduction copied from the issue."
  },
  "verification": {
    "focused": [
      {
        "name": "focused test",
        "command": ["python", "-m", "pytest", "path/to/test.py::test_name"]
      }
    ],
    "regression": [
      {
        "name": "regression suite",
        "command": ["python", "-m", "pytest"]
      }
    ]
  },
  "env": {
    "required_files": ["pyproject.toml"],
    "preflight_commands": [
      {
        "name": "python available",
        "command": ["python", "--version"]
      }
    ],
    "required_deps": ["python", "pytest"]
  }
}
```

## Collection Status

Real tasks are not yet checked in. Run `evals/collect-tasks.py` from an
unrestricted terminal to generate `evals/candidates.json`, then use the
template above to solidify selected candidates only after verifying issue URL,
merged PR URL, close date, base ref, diff size, verification commands, and env
deps.
