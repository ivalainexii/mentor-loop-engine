# Experiment Task: jc-687

Repository: `kellyjonbrazil/jc`

Issue: `dir parser: lstrip strips D: drive letter from parent directory path`

Why this task:

- Similar string-prefix bug with a different parser.
- Useful check for whether lessons transfer after `jc-685`.

Verification:

```powershell
python -m unittest tests.test_dir
```

Known readiness:

- Context files were found in the public checkout.
- Baseline tests showed Windows epoch differences in this environment, so run
  this task where the project baseline passes.
