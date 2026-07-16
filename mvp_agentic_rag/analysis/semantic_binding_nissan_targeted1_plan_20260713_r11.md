# Nissan model-chain provenance targeted1 plan (R11)

## Purpose

Verify the post-R10 provenance fix without changing the semantic-binding
method, retrieval stack, dataset item, evaluator, or metric definitions. R10
already produced a strictly bound `Nissan Altima` candidate, but topology
repair provenance masked the candidate-specific deterministic binding reason
and the controller abstained.

## Comparison contract

- Reference: semantic-binding targeted7 R10, Nissan trajectory only.
- Dataset: `data/musique_nissan_model_chain_targeted1_20260710.jsonl`.
- Method/config: identical to R10 except for the one-sample dataset, unique
  run name, and unique output directory.
- Model/API: SiliconFlow `Qwen/Qwen3-14B` for answer and verifier roles.
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_binding_nissan_targeted1_20260713_r11`.

## Acceptance gate

The run passes only if all of the following hold:

1. final answer is `Nissan Altima` and final action is `answer`;
2. `candidate_specific_binding_final_acceptance_reason` is
   `deterministic_model_chain_binding`;
3. structured binding output records
   `deterministic_binding_applied=deterministic_model_chain_binding`;
4. if final-hop order canonicalization occurs, it is separately recorded as
   `topology_repair_applied=final_hop_order_canonicalization`;
5. `final_answered_unsupported_rate=0`;
6. no malformed or missing primary required-hop topology is silently consumed.

If the gate fails, inspect the trajectory and fix the smallest discriminating
issue before considering another targeted7 run. Do not run stratified45.

## Verification sequence

1. Run the full local test suite, `compileall`, and diff checks.
2. Execute the isolated one-sample real API run once.
3. Parse metrics and trajectory fields programmatically.
4. Record the result in the R10 report and topology checklist.

## Revision log

- 2026-07-13: Created after R10 exposed topology-repair provenance masking.
