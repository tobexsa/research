# Semantic Fusion Gain/Loss-12 R21 Blocked Launch

Date: 2026-07-14

## Status

- Outcome: `blocked_before_execution`
- Failure layer: environment / external-data-transfer approval
- Completed trajectories: 0/12
- Metrics: absent
- Run lock: absent
- Methodological verdict: inconclusive
- Next stage authorized: none; phase 2 remains gated

## What Completed Before The Block

- Immutable 12-row dataset created and hash-verified.
- Runtime-only strict/generic/no-fallback router implemented.
- Legacy-first, certificate-escalated verifier protocol implemented.
- Stored R20 structural replay completed on all 12 samples.
- Focused tests: 214 passed, 25 subtests.
- Full tests: 617 passed, 27 subtests.
- Compileall and scoped diff check passed.
- Unique R21 config frozen with only run/data/output and fusion-flag deltas
  versus R20.

## Blocker

The normal sandbox denied the first SiliconFlow socket connection. The
unsandboxed escalation was then rejected because the run transmits experiment
inputs to an external service: MuSiQue questions plus the passages retrieved
from the local corpus. No sample completed before either failure.

## Required Resolution

The user must explicitly approve sending those experiment inputs and retrieved
passage texts to the external SiliconFlow API. If approved, resume the exact
frozen R21 config; do not modify the dataset, model, retriever, budget, metrics,
or output identity. If not approved, the comparable external run cannot be
performed; a local-model substitute would be a new, non-comparable experiment
and would require a revised plan.
