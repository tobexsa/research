# Matched Baseline Verification

Completed: 2026-07-16
Verdict: `verified_close` for the local matched contract
Feasibility: `degraded_but_acceptable`
Downstream trust: `verified_for_local_matched_contract`

## Outcome

The run completed all 135 method/sample rows with 135 unique keys, 45 unique
sample IDs per method, zero skipped rows, and no remaining lock. The frozen
config, data, corpus, index, implementation, evaluator, trajectories, and
metrics are hashed in `manifest.json`.

The primary local comparator is `agentic_rag_baseline`, a verifier-guided
iterative retrieve/generate/refine/answer/abstain policy. It is a fair
closed-corpus corrective-RAG pattern comparison under the repository contract,
but not a full CRAG reproduction and not an Adaptive-RAG/Self-RAG reproduction.

## Metrics

| Method | EM | Answer F1 | Coverage | Selective F1 | Avg retrievals | Wasted retrieval | Final unsupported |
|---|---:|---:|---:|---:|---:|---:|---:|
| `agentic_rag_baseline` | 0.1111 | 0.1511 | 0.2667 | 0.5667 | 2.4889 | 0.6667 | 0 |
| `fixed_k` | 0.1556 | 0.2493 | 1.0000 | 0.2493 | 3.0000 | 1.0000 | 0 |
| `prompt_verifier` | 0.0889 | 0.1111 | 0.2000 | 0.5556 | 1.0000 | 0.0000 | 0 |

All three have zero 4-hop Answer F1. The primary comparator's 2-hop/3-hop/4-hop
F1 is `0.3333 / 0.1200 / 0.0000`.

## Incumbent Comparison

The incumbent reference is the mean of the two valid adapter-only repeats A1
and A2, using the same targeted45 evaluator contract.

| Metric | Adapter incumbent mean | Primary matched comparator | Incumbent - comparator |
|---|---:|---:|---:|
| EM | 0.4111 | 0.1111 | +0.3000 |
| Answer F1 | 0.4285 | 0.1511 | +0.2774 |
| Coverage | 0.4556 | 0.2667 | +0.1889 |
| Selective F1 | 0.9407 | 0.5667 | +0.3740 |
| Avg retrieval calls | 2.3556 | 2.4889 | -0.1333 |
| Wasted retrieval rate | 0.6000 | 0.6667 | -0.0667 |

The incumbent is better on answer quality, selective quality, coverage, and
the recorded retrieval-cost measures. The fixed-k comparator's coverage of 1.0
comes from always answering; its F1 and selective F1 remain far below the
incumbent.

## Safety And Cost Caveats

- Every method's repository-defined `final_answered_unsupported_rate` is zero.
- `agentic_rag_baseline` nevertheless has intermediate
  `answered_unsupported_rate=0.25`. This supports the narrower claim that its
  final policy abstains from those unsupported proposals, not that it produces
  certificate-backed answers throughout.
- `fixed_k` has no verifier/certificate layer. Its zero final-unsupported
  metric must not be interpreted as equivalent to the incumbent's explicit
  certificate safety audit.
- The repository `llm_calls` counter does not include every answer-generation
  or slot-verification call uniformly across agents. Only retrieval-call and
  wasted-retrieval metrics are treated as directly reliable cost comparisons.

## Source And Protocol Caveats

- This is a targeted stratified45 development surface, not standard MuSiQue
  dev/test and not comparable to published paper numbers.
- The primary comparator is a local modern-pattern approximation. Exact
  Self-RAG requires a reflection-token model; exact Adaptive-RAG requires a
  trained complexity classifier; full CRAG adds web retrieval; FLARE targets
  low-confidence-token long-form generation.
- Therefore the baseline package clears the phase-3 local matched-comparison
  gate, but does not replace the later non-leaking standard evaluation or a
  future exact-paper reproduction if a paper claim requires one.

## Decision

Accept the package as `degraded_but_acceptable` and locally verified. The
incumbent remains decisively stronger on this matched 45-case contract. Phase
3 may close and the next authorized stage is non-leaking standard MuSiQue
dev/test construction. A 300-sample or paper main experiment remains blocked.
