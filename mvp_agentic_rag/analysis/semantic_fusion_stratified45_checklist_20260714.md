# Semantic Fusion Stratified45 Checklist

## Preflight

- [x] R24 fixed-12 gate passed 5/5 gains, 7/7 losses, unsupported 0.
- [x] Define matched generic-only switches.
- [x] Test strict-lane disable while preserving no-fallback.
- [x] Test deterministic-adapter disable.
- [x] Run full test suite, compileall, and scoped diff checks: 640 passed, 27 subtests.
- [x] Freeze R25/R26 configs and record hashes.
- [x] Confirm configs differ only in identity and the two generic-only flags.

Frozen hashes:

- R25 Fusion: `194C75669E907A050C6817985FCA9F2E7DBEAC985C58D32C859B1CFBB6A88F72`
- R26 generic-only: `1D71BBE5C629E88448AEEE5F64E7F72A6F94070E00A90820C9A2FA2BE429A693`
- Dataset: `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`

## Fusion R25

- [x] Launch only after local preflight passes.
- [x] Complete 45 unique rows.
- [x] Verify complete finite metrics and unsupported 0.
- [x] Replay safety state.
- [x] Record lane counts, hashes, and result report.

R25 result: `analysis/semantic_fusion_stratified45_results_20260714_r25.md`.

## Generic-Only R26

- [x] Launch only after R25 is complete and valid.
- [x] Complete 45 unique rows.
- [x] Verify complete finite metrics and unsupported 0.
- [x] Verify zero strict-certificate lane steps.
- [x] Verify zero recognized deterministic certificate-adapter markers.
- [x] Replay safety state and record hashes.

R26 result: `analysis/semantic_generic_only_stratified45_results_20260714_r26.md`.
One topology-only `final_hop_order_canonicalization` compatibility marker is
reported separately and is not a certificate adapter.

## Comparison

- [x] Compare R12, R20, R25, and R26 metrics.
- [x] Compute paired correctness gains/losses.
- [x] State whether Fusion adds value over generic-only on this run.
- [x] Decide whether phase 3 is authorized.

Comparison:
`analysis/semantic_fusion_stratified45_comparison_20260714.md` and `.json`.

Decision: phase 3 is authorized in the user-specified order: component
ablations, repeated runs, then matched modern baselines.
