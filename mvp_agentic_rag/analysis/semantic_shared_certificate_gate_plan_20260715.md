# Shared-Certificate Deterministic Gate Plan

Date: 2026-07-15

## Objective

- Run id: `semantic_shared_certificate_gate_20260715`.
- Tier: offline auxiliary/dev mechanism and safety gate.
- Parent decision: `analysis/semantic_terminal_safety_r31_next_decision_20260715.md`.
- Research question: on byte-identical frozen certificate inputs, does terminal
  authorization behave deterministically, preserve safety invariants, and
  expose the actual action-level contribution of strict routing?
- Null: strict-on/off differences cannot be isolated from LLM certificate
  generation, or replayed actions violate terminal safety.
- Alternative: one pure replay path can hold certificates fixed and vary only
  strict acceptance policy.

## Non-Negotiable Boundaries

- No API, model, retrieval, dataset, evaluator, or prompt call.
- No sample ID, gold answer, decomposition, or gold support may affect routing.
- The replay may report sample IDs for audit, but action logic consumes only
  frozen runtime state, verifier output, slot binding, proposal action, budget,
  repair metadata, and retrieved evidence IDs.
- Evidence locality and R28 fail-closed behavior remain unchanged.
- Existing R24-R31 run outputs are read-only.

## Code And Test Plan

| Path | Change | Purpose |
|---|---|---|
| `scripts/replay_shared_certificate_terminal.py` | Reconstruct gold-free terminal inputs; replay strict on/off twice; audit invariants; write JSON/Markdown | Deterministic code gate and action attribution |
| `tests/test_replay_shared_certificate_terminal.py` | Positive, negative, deterministic, and strict on/off action-delta controls | Prevent replay or policy confounds |

## Frozen Inputs And Outputs

- Fixed-12 safety stream: R31 trajectories.
- Attribution stream: R25 full-Fusion adapter-on stratified45 trajectories.
- Required R31 outputs: 12 unique inputs, deterministic replay, nonzero strict
  eligibility, zero accepted-answer invariant violations.
- Required R25 outputs: 45 unique inputs, deterministic replay, eligibility and
  strict-on/off action deltas reported without new sampling, zero violations
  for every accepted counterfactual action.

## Implementation Sequence

1. Add red tests for identical input digest, deterministic repeat, safe local
   positive, non-local negative, and one synthetic strict-policy action delta.
2. Implement minimal record-to-dataclass translation and replay.
3. Run focused tests, wider state/replay tests, full tests, compileall, and
   source scan for gold/sample-specific routing.
4. Replay R31, then R25; hash and report outputs.

## Success And Abandonment

Success:

- replay is byte-stable across repeated executions;
- strict on/off share one input digest per case;
- no replayed answer violates terminal invariants;
- strict eligibility and action-change counts are explicit;
- no runtime gold/sample branch is introduced.

Abandon/narrow strict claim if the valid shared stream has nonzero strict
eligibility but strict-on changes no terminal action relative to strict-off, or
if its only changes are unsafe.

## Runtime Degradation

Managed `bash_exec`, artifact, and memory interfaces are unavailable. Use
PowerShell plus repository-local tests, JSON, and Markdown as explicit
fallback evidence.

## Checklist

- `analysis/semantic_shared_certificate_gate_checklist_20260715.md`
