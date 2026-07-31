# ADR 0001: Record Architecture Decisions

## Status
Accepted

## Context
MediBridge AI is built incrementally across many sessions by an AI coding agent with no memory
beyond files on disk (see `AGENT_INSTRUCTIONS.md`). Decisions that deviate from, or add detail
beyond, `docs/BLUEPRINT.md` need a durable record so future sessions don't silently re-litigate
or contradict them.

## Decision
We will use Architecture Decision Records, stored in `docs/ADRs/`, numbered sequentially
(`NNNN-title.md`). Each ADR captures: Status, Context, Decision, Consequences. A new ADR is
added whenever a phase introduces a decision not already fully specified in `BLUEPRINT.md`
(new dependency, changed service boundary, changed schema contract, etc.), per
`AGENT_INSTRUCTIONS.md` Section 5.4.

## Consequences
- Every phase that deviates from or extends the blueprint gets a corresponding ADR.
- `docs/PROGRESS.md` links to the relevant ADR number instead of re-explaining the decision.
