# Monotonic Slot State Stratified45 Run Contract

Date: 2026-07-12

## Contract

- Run ID: `layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_r1`
- Tier: main/stratified45
- Question: Does the reviewed monotonic slot-state observation layer execute on all 45 samples without changing the established runtime contract or introducing unsafe final answers?
- Hypothesis: State snapshots and transitions are emitted consistently; final unsupported rate remains zero; aggregate metrics should remain near the latest historical 45 reference, but metric deltas are not attributable solely to this observation feature.
- Dataset: `data/musique_mvp_stratified45.jsonl`, unchanged 45-sample split.
- Method: `claim_risk`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Primary metrics: overall accuracy, answer F1, coverage, selective accuracy, final answered unsupported rate.
- State acceptance: all trajectory steps contain JSON-safe before/after snapshots; all 45 records complete; state fingerprints are non-empty; no runtime exception.
- Stop condition: smoke API/config/state validation fails, output lock conflict, repeated API failure, or missing state metadata.
- Budget: one 1-sample smoke followed by one 45-sample run.

## Historical Reference

- Run: `layer1_siliconflow_qwen3_14b_stratified45_v1_3_5_20260710_r1_after_targeted7_gate`
- overall accuracy: 0.3333
- answer F1: 0.3511
- coverage: 0.3778
- selective accuracy: 0.8824
- final answered unsupported rate: 0

The historical derived config was not preserved as a standalone file. The new config is based on the full Targeted7 r2 package with the stratified45 dataset and the monotonic observation flag. Comparability is therefore medium, and no causal metric-improvement claim will be made.

## Commands

```powershell
python scripts/run_layer1_skeleton.py --config configs/layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_smoke1.yaml
python scripts/run_layer1_skeleton.py --config configs/layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_r1.yaml
```

## Status

- [x] Local tests and compile checks passed before network execution.
- [x] Smoke completed and state metadata validated.
- [x] Main 45 run completed (31 records in the initial process, then 14 records by safe resume after a SiliconFlow read timeout).
- [x] Metrics and trajectory state coverage validated.
- [x] Historical comparison and next decision recorded.

## Outcome

- Main run completed at 2026-07-12 15:04:16 Asia/Shanghai with 45 unique records and 110 trajectory steps.
- Runtime/state serialization acceptance passed: all 110 steps contain the feature marker, before/after snapshots, and non-empty fingerprints; adjacent snapshots have no chain mismatches.
- Safety acceptance passed narrowly: `final_answered_unsupported_rate` remained 0.
- Functional activation failed: all 110 steps reported `topology_unavailable`; all selected state actions were `no_state_action`; no first missing hop was identified.
- Headline quality regressed descriptively relative to the medium-comparability historical reference: accuracy 0.2444, F1 0.2556, coverage 0.2889, and selective accuracy 0.8462.
- Decision: do not scale this observation-only configuration to 300 samples. The next experiment must first make structured topology available on real SiliconFlow verifier outputs and demonstrate non-zero missing-hop/action activation on a small targeted gate.

Detailed evidence and the comparison table are in `analysis/monotonic_slot_state_stratified45_results_20260712.md`.
