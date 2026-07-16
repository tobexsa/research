# Semantic Fusion Terminal Safety Repair Checklist

## Identity

- Run id: `semantic_fusion_terminal_safety_repair_20260715`
- Stage: implementation plus auxiliary/dev verification.

## Planning

- [x] Repair idea and non-negotiable constraints frozen.
- [x] R24/R25 safety references and R28 failure reference identified.
- [x] Code touchpoints, smoke plan, paid gate, and fallbacks written.

## Test-First Diagnosis

- [x] Add failing generic-terminal R28-state regression test.
- [x] Add complete supported generic positive control.
- [x] Add strict-certificate positive/non-regression control.
- [x] Add critical ancestor-closure tests.
- [x] Add replay terminal-invariant tests.

## Implementation

- [x] Generic answer path no longer bypasses the state controller.
- [x] Unclear/unsupported final verifier blocks answer.
- [x] Incomplete or non-local binding blocks answer.
- [x] Critical ancestor gaps block downstream final eligibility.
- [x] Safe candidate-conflict repair recovery remains unchanged.
- [x] No sample ID or gold-field logic introduced.

## Local Validation

- [x] Focused tests pass: 281 tests and 27 subtests.
- [x] Full tests pass with project-local basetemp: 645 tests and 27 subtests.
- [x] Compileall passes.
- [x] Diff and whitespace checks pass.
- [x] R25-R28 historical terminal replay completed and action deltas reported.

## Paid Gates

- [x] Offending-case probe passes: R29 safely abstained, unsupported 0, terminal
  invariant violations 0; stochastic path did not directly exercise the new
  downgrade because the original controller already abstained.
- [ ] Repaired fixed-12 gate retains 5/5 gains and 7/7 losses: R30 reached
  4/5 and 6/7 with zero safety violations; one identity-only full retry is
  authorized because neither abstention was caused by the new guard. R31
  reached 5/5 and 5/7; the old per-run 12/12 form is rejected as stochastically
  unstable and no further paid retry is authorized.
- [x] Final unsupported and all terminal invariant violations are zero in R31.

## Closeout

- [x] Repair result and claim validation written.
- [x] Activation-aware shared-certificate attribution and a deterministic
  frozen-certificate gate are explicitly selected next.
- [x] Shared-certificate gate completed: R25/R27 have five eligible terminal
  cases each but zero strict on/off action deltas; adapters are selected as the
  incumbent and the strict terminal claim is downgraded.
