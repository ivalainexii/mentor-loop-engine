# pflow-389 Boundary Results

This run was deliberately smaller than the `jc-687` ablation:

- A: raw weak x1.
- B: weak plus transferred lessons x2.

No Mentor Brief arm and no strong-direct arm were run. The question was not
"does Mentor Loop win again?" The question was narrower:

> Do repo-level lessons transfer across repositories, or only same-repo?

## Result

All three weak runs produced the same plausible patch shape:

- Move YAML continuation handling before markdown heading and code-fence
  detection.
- Add focused parser regression tests for markdown-looking content inside a
  YAML block scalar.
- Touch only:
  - `src/pflow/core/markdown_parser.py`
  - `tests/test_core/test_markdown_parser.py`

All three runs passed the blast-radius gate.

Focused verification did not run because the environment lacked the requested
tooling:

- `uv` unavailable.
- `python` unavailable in the weak-model PATH.
- Coordinator bundled Python lacked `pytest` and `PyYAML`.

Because of that, the correct outcome type is:

`verification_incomplete`

## Interpretation

This boundary run does not show a success-rate difference:

- Raw weak produced a plausible scoped fix.
- Lessons-only also produced plausible scoped fixes.
- No arm could be functionally accepted without the parser test environment.

The useful signal is narrower:

- Cross-repo lessons did not create an obvious new advantage in this sample.
- The meta-level lesson did transfer conceptually: both lessons-only runs
  explicitly applied "preserve nested parser context before checking surface
  syntax."
- Repo-level lessons remain the durable product claim. Cross-repo transfer is a
  nice boundary note, not the main proof.

For the writeup, pflow should be one paragraph:

> I also tried a cheap cross-repo boundary run on `pflow-389`. All three weak
> runs found the same plausible parser-state fix and stayed inside the blast
> radius, but the environment lacked `uv`/`pytest`/`PyYAML`, so I counted the
> result as verification-incomplete. The lesson did transfer as a concept, not
> as a measurable success-rate lift.
