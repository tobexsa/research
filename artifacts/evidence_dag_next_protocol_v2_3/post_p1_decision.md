# V2.3 Post-P1 Decision

- verdict: `bad` for all tested P1 Planner routes.
- action: `stop` Route A/B/C promotion; `branch` once into the independent P4 Gold×Gold Retriever Oracle Gate.

## Decisive evidence

- Route A: 0/60 topology match, 50/60 invalid, macro-F1 0.
- Route B C2P: 7/60 end-to-end topology, 18/60 invalid, macro-F1 0.0751, below the 10/60 majority baseline.
- C4A Oracle Pairwise: 85/250 pair accuracy, only 2/60 globally consistent and 1/60 exact graphs.
- P2A remains 68/90 (75.56%) versus the 98% span gates.
- P3 has no authorized exact strong-model comparator.

## Route choice

The P4 Gold×Gold Retriever gate is selected because it is independent of the failed Planner/Span path, has explicit preregistered thresholds, requires no new LLM calls, and can isolate whether retrieval is itself a blocker. The target BGE model, FAISS index, corpus, and CUDA runtime are locally available; an earlier 300-sample dense gate provides a credible operational baseline.

Rejected alternatives:

- promote a P1 candidate: contradicted by all full-denominator metrics;
- tune prompts or increase max tokens: violates the freeze and does not address 187 schema-valid semantic errors;
- run Query factorial: Predicted relation and Predicted binding prerequisites failed;
- substitute a strong model: explicitly forbidden;
- open Internal Holdout/Confirmation: no eligible candidate exists;
- finalize immediately: would leave the protocol's explicit Retriever Oracle question unanswered despite a bounded, locally feasible test.

After P4, stop model-dependent P5/Validator rollout unless a prerequisite unexpectedly becomes satisfied. Existing pure Oracle Engine fixtures remain supporting evidence only.

Compatibility: artifact/decision APIs are unavailable; this Git-tracked record is the durable decision surface.
