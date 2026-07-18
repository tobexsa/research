# Evidence-DAG V2.3 Campaign Summary

## Final recommendation

Stop and archive the current `Pro/Qwen/Qwen2.5-7B-Instruct` Planner candidate. Do not consume Internal-Holdout-A/B or Confirmation-120. Preserve the contract-matched dense retriever and Oracle engine path for a future Planner candidate.

## Strongest evidence

- P0 fixed decoder/schema envelope: P0A 216/216; P0B canonical/semantic 432/432; P0C 216/216.
- P2A span gate failed: normalized/alias 68/90 (75.56% vs 98%).
- P1 failed: Route A 0/60; C2P 7/60; C4A exact graph 1/60.
- P1 mechanism: 83/362 whitespace-loop length finishes plus 187 schema-valid semantic errors.
- P4 corrected retriever gate passed: Recall@10 182/200; All-Steps 44/60; timeout 0.
- P5 R0: 182/200 steps resolved; 50/60 Answer Ready/EM; 0 mix.
- Full regression: 829/829 passed.

## Boundary

Internal holdouts are reserved at Compositional independence only and remain unused. Confirmation-120 was exclusion/audit-only and was never queried by a model.

## Reopen condition

Reopen only with a newly frozen Planner/typed-DSL or exact strong-model route that passes real-question structure and span gates on Diagnostic-Dev-60. Grammar-constrained decoding may be tested for whitespace loops, but it is not sufficient evidence for semantic correctness.
