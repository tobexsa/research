# Decision: launch semantic-certificate stratified45

Date: 2026-07-14

- Verdict: `good`
- Action: `launch_experiment`
- Target run: `layer1_siliconflow_qwen3_14b_semantic_certificate_stratified45_20260714_r20`

## Decision question

Has the semantic-certificate controller passed the user-defined targeted8 gate
strongly enough to justify the fixed 45-sample generalization run?

## Evidence

- R19 completes 8/8 with 0.750 accuracy/F1/coverage, selective accuracy 1.0,
  wasted retrieval 0.25, and final unsupported zero.
- All structural gates pass: 18/18 verifier rounds invoked, 18/18 structured
  attempts stop normally, and length/parse/malformed are zero.
- Sentinel values produce six ignored diagnostics but zero candidate
  transitions and zero candidate state.
- The three 2-hop samples are retained, `1952` is restored, and two 4-hop
  samples answer correctly.
- R17 and R18 are preserved as valid failure/intermediate evidence; R19 is the
  first run satisfying every predeclared scale gate.

Evidence paths:

- `analysis/typed_hop_identity_targeted8_results_20260714_r19.md`
- `runs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r19`
- `analysis/typed_hop_identity_and_hint_resolver_plan_20260713.md`

## Alternatives

- Repeat targeted8 again: rejected because R19 already exercises every gate
  and another stochastic repeat adds less information than distribution-level
  evaluation.
- Stop at targeted8: rejected because deterministic certificates could still
  overfit the eight selected cases.
- Change verifier arbitration before scaling: rejected for this run because it
  would mix the proven R19 package with a new Arizona-specific intervention.
  Arizona remains a documented limitation for later analysis.

## Run contract

Use the established 45-sample dataset and change only dataset plus unique
run/output identity relative to R19. The run must complete 45 unique rows with
finite metrics and final unsupported zero. Compare against R12 on accuracy,
F1, coverage, selective accuracy, retrieval calls, wasted retrieval, per-hop
metrics, topology diagnostics, and the seven binding-failure categories.

If the run is interrupted, resume only the identical frozen config from its
durable completed keys. Do not reuse the run ID for changed code or settings.
