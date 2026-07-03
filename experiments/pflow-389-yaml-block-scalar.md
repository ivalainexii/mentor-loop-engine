# Experiment Task: pflow-389

Repository: `spinje/pflow`

Issue: Parser heading and code-fence detection inside multi-line YAML block
scalars uses stripped text before continuation checks.

Why this task:

- Broader parser state-machine risk.
- Tests whether the brief prevents overbroad weak-model edits.

Verification:

```powershell
uv run pytest tests/test_core/test_markdown_parser.py -q
```

Known readiness:

- Context files were found in the public checkout.
- This environment lacked `uv` and `pytest`, so run this task where project
  dependencies are installed.
