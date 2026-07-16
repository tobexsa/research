# Semantic certificate targeted8 R19 result

## Verdict

R19 passes every fixed targeted8 gate and authorizes the first post-certificate
stratified45 run. This is a go decision for scale, not a claim that every
targeted sample is solved.

## Run integrity

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r19.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r19`
- Completion: 8/8, metrics written, lock removed normally, stderr zero bytes.
- Verifier rounds invoked: 18/18.
- Slot structured attempts: 18/18 `finish_reason=stop`.

## Metrics

| Metric | R17 | R18 | R19 |
| --- | ---: | ---: | ---: |
| Accuracy | 0.250 | 0.625 | 0.750 |
| F1 | 0.250 | 0.625 | 0.750 |
| Coverage | 0.250 | 0.625 | 0.750 |
| Selective accuracy | 1.000 | 1.000 | 1.000 |
| Average retrieval calls | 2.250 | 2.375 | 2.250 |
| Wasted retrieval rate | 0.375 | 0.375 | 0.250 |
| Final answered unsupported | 0 | 0 | 0 |

Per-hop R19:

- 2-hop: 3/3 answered and correct.
- 3-hop: 1/2 answered and correct; `1952` restored.
- 4-hop: 2/3 answered and correct; NBC and East Coasting restored.

The two abstentions are Arizona `Mario Andretti` and `two`. No incorrect
answer was emitted.

## Fixed gate

| Requirement | R19 | Verdict |
| --- | ---: | --- |
| length / parse / malformed | 0 / 0 / 0 | pass |
| final unsupported | 0 | pass |
| sentinel candidate bad transition | 0 | pass |
| sentinel candidate state | 0 | pass |
| allowed `sentinel_candidate_ignored` diagnostics | 6 | pass |
| topology update/revision rejection | 0 | pass |
| 2-hop retained | 3/3 | pass |
| `1952` restored | correct in 2 rounds | pass |
| at least one 4-hop correct | 2/3 | pass |

## R19-specific evidence

`18th century` is role-rejected in round 1, then the round-2 strict complete
binding clears the stale rejection over the same evidence. The trajectory
records `strict_binding_clears_stale_rejection`; typed-reject metadata is
cleared and the final answer is canonicalized to `18th`. This is a real state
transition, while a following identical update remains transition-free in the
deterministic regression.

## Remaining limitations

- Arizona's deterministic hop certificate succeeds, but the generic verifier
  does not accept the negative-form largest-city evidence. This is a later
  certificate/final-sufficiency arbitration issue.
- The `two` sample remains a safe abstention.
- Targeted8 is a gate, not distribution-level evidence. Generalization and
  diagnostic frequencies require the authorized stratified45.

## Decision

Launch one uniquely named stratified45 using `data/musique_mvp_stratified45.jsonl`.
Keep R19's model, retriever, 2304-token slot-verifier budget, three-round limit,
safety gates, and evaluator unchanged. Preserve R12 as the matched dataset
reference and do not overwrite any prior run.
