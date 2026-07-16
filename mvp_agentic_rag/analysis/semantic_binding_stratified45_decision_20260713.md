# Decision: launch semantic-binding stratified45

Date: 2026-07-13

- Verdict: `good`
- Action: `launch_experiment`
- Target run: `layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12`

## Decision question

Has the targeted semantic-binding line passed enough safety and functionality
gates to justify one 45-sample generalization run?

## Evidence

- R10 completed all seven targeted samples and all 11 verifier steps with
  canonical primary topology, zero malformed/missing/parse-failure primary
  reasons, and zero final unsupported answers.
- R10 improved over topology R8 from 0.2857 to 0.7143 accuracy and reduced
  wasted retrieval from 0.7143 to 0.1429.
- Five code-actionable cases pass in R10: Rotterdam, NBC, Liam, Mickey, Timor.
- The post-R10 R11 real API gate closes Nissan with the correct final answer,
  deterministic model-chain acceptance, separate topology-repair provenance,
  and zero final unsupported answers.
- Arizona is independently documented as a question/gold granularity mismatch
  and is not a clean controller-regression case.
- Final local verification passes 560 tests and 27 subtests, compileall, and
  relevant diff checks.

Evidence paths:

- `analysis/semantic_binding_targeted7_results_20260713_r10.md`
- `analysis/arizona_granularity_audit_20260713.md`
- `runs/layer1_siliconflow_qwen3_14b_semantic_binding_targeted7_20260713_r10`
- `runs/layer1_siliconflow_qwen3_14b_semantic_binding_nissan_targeted1_20260713_r11`

## Alternatives considered

- Repeat targeted7: rejected because R10 already validates the other six
  trajectories and R11 isolates the sole post-R10 Nissan code change. A repeat
  would spend API budget without adding a new discriminating condition.
- Stop at targeted evidence: rejected because narrow deterministic binders may
  overfit the gate and do not establish distribution-level improvement.
- Launch a larger-than-45 run: rejected because the 45-sample set is the next
  established comparison surface and is sufficient to test generalization and
  safety before any broader scale-up.

## Success and abandonment criteria

The run must complete 45 unique trajectories with finite metrics and retain
`final_answered_unsupported_rate=0`. Primary topology availability, coverage,
accuracy/F1, retrieval calls, wasted retrieval, and the seven diagnostic
reason categories will be compared with the 2026-07-12 monotonic-state R1
reference. Any incomplete run is resumed only from durable completed keys; a
repeat with a changed method is forbidden under the same run ID.

The run is a generalization check, not a pre-committed superiority claim.
Because the old R1 configuration contains additional legacy flags, aggregate
deltas are medium-comparability descriptive evidence unless a matched-config
reference is available.
