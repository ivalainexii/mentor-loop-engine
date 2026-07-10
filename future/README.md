# Future, Not v0

> **Archived proposal (2026-07-10):** this file preserves a historical design
> direction; it is not an active roadmap and has no pending action. Further
> product-level validation is not being pursued. `README.md` controls current
> status and claims. The original text below is retained for provenance only.

These components existed in the larger exploration package, but they are not in
the lean v0 path because the current evidence supports a publication case
study, not framework expansion.

Move back only after publication creates clear demand for one specific painful
step to automate.

## Parked Ideas

- Model router.
- Model policy resolver.
- Provider registry.
- OpenAI-compatible provider adapter.
- Handoff bundle builder.
- Run-state auditor.
- Next-step packet builder.
- Launcher adapter.
- Mock provider.
- Mock e2e runner.
- Public dogfood runner.
- Automatic GitHub task miner for eval task discovery and PR metadata checks.
- Patch runner.
- Response extractor.
- Response gate.
- Provider artifact gate.
- Automatic installer for copying `.claude/` into a target repo.
- Automatic retry/escalation loop after a failed review.
- Token accounting dashboard for strong brief, weak execution, and review.
- Multi-platform command launchers outside Claude Code.
- Claude Code port after the Codex-native driver is proven in the user's normal
  Codex workflow.

## V1 Priority

The first v1 feature should be a lesson ledger, not another agent framework.

The detailed design brief is `lesson-ledger-v1.md`.

It should preserve three mechanisms:

- Metadata: source failure, source artifact, hit count, last hit, status, and
  candidate gate.
- Consolidation: merge duplicates, remove contradictions, count repeated hits,
  and promote recurring lessons into gates.
- Retirement audit: when the execution model changes, remove a sample of old
  lessons and replay representative tasks so obsolete rules can disappear.

The goal is to stop `CLAUDE.md`-style memory from rotting. Durable memory should
get thinner when models improve, not only longer.

## Why Park Them

At validation time, a human copied prompts, pasted outputs, and ran the blast
radius gate manually. That preserved experiment validity while avoiding
framework work before the useful mechanism was clear.

The current mechanism worth preserving is:

`review -> lesson -> gate`

Future automation should serve that ladder, not recreate a general agent
framework.
