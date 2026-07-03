# Experiment Task: jc-685

Repository: `kellyjonbrazil/jc`

Issue: `ifconfig parser: lstrip('0x') incorrectly strips hex mask digits`

Why this task:

- Small parser bug.
- Clear blast radius.
- Existing focused tests.
- Good first uplift check.

Verification:

```powershell
python -m unittest tests.test_ifconfig
```

Known readiness:

- Public checkout readiness passed in the larger research package.
- `tests.test_ifconfig` passed on this machine with 13 tests.
