# Claim-Risk Selective Agentic RAG

## Motivation

Verifier-guided iterative RAG can enter low-yield retrieval loops when evidence-gap signals trigger additional retrieval but the retriever repeatedly fails to surface new supporting evidence. In the original full300 run, 76.7% of `agentic_rag_baseline` records triggered extra retrieval and also had no-new-evidence behavior, while mean F1 on those records was 0.002820 versus 0.181985 without no-new-evidence behavior.

The revised method treats iterative RAG as a selective answering problem. The controller should decide whether to answer, abstain, or continue retrieval under claim-level evidence uncertainty.

## Difference From FAIR-RAG

FAIR-RAG focuses on structured evidence assessment and adaptive gap filling. This work does not make structured evidence checklist refinement the main contribution. It instead focuses on claim-level selective answering: deciding whether to answer, abstain, or continue when evidence remains uncertain and retrieval may be low-yield.

## Difference From Stop-RAG

Stop-RAG frames iterative retrieval control as a value-based STOP/CONTINUE problem for answer quality. This work uses explicit claim-level risk signals and includes ABSTAIN as a first-class action, so stopping can mean either answering safely or refusing to answer. The current implementation is a rule-based claim-risk controller; it does not claim to reproduce Stop-RAG.

## Controller Signals

- verifier sufficiency
- critical unsupported claims
- evidence gain
- retrieval novelty
- budget remaining
- generated answer validity, including `UNKNOWN`

## Actions

- `answer`
- `abstain`
- `continue_search`
- `refine_query`

## Evaluation

- answer F1
- coverage
- selective answer F1
- unsupported claim rate
- answered unsupported rate
- abstention precision
- average retrieval calls
- wasted retrieval rate
- cost-normalized F1

## Current Subset Evidence

On `layer1_api_balanced300_dense_bge_claim_risk_subset30`, `claim_risk` reduced average retrieval calls relative to original `agentic_rag_baseline` while lowering answered unsupported risk:

| method | answer_f1 | coverage | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | cost_normalized_f1 |
|---|---:|---:|---:|---:|---:|---:|
| prompt_verifier | 0.3111 | 0.5667 | 1.0000 | 0.0000 | 0.0588 | 0.3111 |
| agentic_rag_baseline | 0.3611 | 0.6000 | 1.8333 | 0.4333 | 0.0556 | 0.1970 |
| claim_risk | 0.3444 | 0.4667 | 1.4000 | 0.4000 | 0.0000 | 0.2460 |

This supports the intended tradeoff: `claim_risk` is more conservative than `agentic_rag_baseline`, answering fewer cases while avoiding answered unsupported claims and reducing retrieval cost. The full300 run is still needed before making a stable claim.
