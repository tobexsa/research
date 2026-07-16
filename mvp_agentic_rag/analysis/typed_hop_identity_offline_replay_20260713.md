# Typed hop identity offline R12 replay

Date: 2026-07-13

## Purpose

Replay the 106 recorded R12 verifier/state observations through the new typed
hop resolver before spending API budget. This isolates reducer/addressing
behavior; it does not rerun answer generation or claim answer-quality gains.

## Contract

- Input: R12 `trajectories.jsonl`, 45 rows and 106 steps.
- State: rebuilt from empty for every sample.
- Evidence IDs: accumulated from recorded retrieval steps.
- Binding/verifier/runtime records: taken from the recorded trajectory only.
- No network, new retrieval, model call, gold field, or evaluator change.

## Results

| Structural signal | Original R12 | Typed replay | Delta |
| --- | ---: | ---: | ---: |
| Topology-ready steps | 105/106 | 105/106 | 0 |
| `hop_schema_drift_ignored` | 146 | 95 | -51 (-34.9%) |
| `unmapped_missing_critical_hint` | 104 | 65 | -39 (-37.5%) |
| `missing_requirement_resolved` | not available | 64 | +64 |
| `hop_update_resolved` | not available | 18 | +18 |
| Sentinel candidate transitions | 0 | 0 | 0 |

The resolver maps legacy forms such as `2`, `required_hop_2`, `hop_index 2`,
and `hop_index: 2` to one stable ID. It also resolves free-text/entity-only
hints only when the dependency frontier is unique; two ambiguous cases remain
explicitly ambiguous rather than guessed.

The replay reports 74 steps with a first missing hop versus 77 in the original
run. The difference comes from conservative rejection of requirements aimed at
verified or dependency-blocked hops. It is not an answer-quality regression,
but must be checked in the real targeted run.

## Interpretation

The mechanism addresses both diagnosed bottlenecks on fixed historical model
output without weakening topology or sentinel safety. The remaining 95 drift
events mostly represent genuine cross-round decomposition changes rather than
simple aliases; the real protocol now supplies frozen topology IDs and should
prevent the model from producing many of those changes.

Because historical R12 prompts did not contain frozen topology or structured
missing requirements, this replay is a lower-bound protocol test. Proceed to a
fixed targeted8 real API gate; do not infer stratified answer metrics from it.
