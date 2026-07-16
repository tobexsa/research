# MuSiQue 2-Hop Proxy Frozen Held-Out Report

## Scope

This report records the single held-out evaluation for the frozen MuSiQue
2-hop proxy configuration selected on dev.

- Branch: `performance-musique-2hop-retrieval`
- Dataset: `data/musique_2hop_proxy/test.jsonl`
- Corpus: `data/musique_2hop_proxy/corpus.jsonl` (9,600 passages)
- Methods: `agentic_rag_baseline`, `claim_risk`
- Frozen config:
  `configs/musique_2hop_proxy_frozen_dense_bge_top100_rerank_top10_test_agentic_rag_baseline_c1.yaml`
- Frozen config SHA-256:
  `C5DA1379D57005495130DD4009DD96952E1E4F5E648690898C9D2BE2CD9A07EC`
- Output:
  `runs/musique_2hop_proxy_frozen_dense_bge_top100_rerank_top10_test_agentic_rag_baseline_c1`

The selected configuration is dense BGE retrieval with top100 candidates,
BGE reranking, final top10 evidence, and ordinary checklist C1. The held-out
test was not used for selection.

## Important Caveat

These are retrieval/control proxy metrics. The run uses
`answer_backend: heuristic` and `verifier_backend: weak`; the weak verifier and
heuristic answer path can access gold-related fields. These numbers must not be
reported as standard non-leaking open-domain QA or SOTA results.

## Dev Candidate Summary

| Candidate | Baseline EM/F1 | C1 EM/F1 | Decision |
| --- | ---: | ---: | --- |
| BM25 top10 | 0.3133 / 0.3183 | 0.4267 / 0.4316 | rejected |
| BM25 top20 | 0.4467 / 0.4506 | 0.5200 / 0.5240 | rejected |
| Dense BGE top10 | 0.5800 / 0.5869 | 0.6267 / 0.6336 | rejected |
| Hybrid top10 | 0.5533 / 0.5591 | 0.6600 / 0.6658 | rejected |
| Hybrid top10 + targeted C1 | 0.5533 / 0.5591 | 0.6667 / 0.6724 | rejected |
| Dense top100 + reranker top10 | 0.6133 / 0.6202 | 0.6800 / 0.6869 | selected |
| Hybrid top100 + reranker + targeted C1 | 0.6067 / 0.6141 | 0.6667 / 0.6741 | rejected |

The selected dense reranker configuration had the best dev C1 EM/F1, finite
metrics, 300 unique dev trajectories, and `final_answered_unsupported_rate = 0`.
A separate non-targeted hybrid top100 + reranker dev run was not executed; the
evaluated targeted hybrid reranker package already underperformed the dense
reranker winner.

## Held-Out Validation

The frozen held-out run produced:

- `trajectories.jsonl`: 600 rows
- unique `(id, method)` keys: 600
- `agentic_rag_baseline`: 300 records
- `claim_risk`: 300 records
- `metrics.json`: present
- `run_summary.md`: present
- all numeric metric values: finite
- frozen config hash after run: unchanged

## Held-Out Metrics

| Method | Count | EM | F1 | Coverage | Selective Acc | Selective F1 | Avg Calls | Wasted Rate | Final Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 300 | 0.5233 | 0.5332 | 0.7600 | 0.6886 | 0.7015 | 1.5067 | 0.2467 | 0 |
| claim_risk | 300 | 0.6100 | 0.6200 | 0.8433 | 0.7233 | 0.7352 | 1.4100 | 0.1700 | 0 |

Strict target:

- Required: `overall_em > 0.433`, `answer_f1 > 0.565`
- C1 observed: `overall_em = 0.6100`, `answer_f1 = 0.6200`
- Verdict: pass

Against the matched held-out baseline, C1 improves:

- EM: `+0.0867`
- F1: `+0.0869`
- Coverage: `+0.0833`
- Average retrieval calls: `-0.0967`
- Wasted retrieval rate: `-0.0767`

## Support Retrieval

Support metrics use cumulative retrieved passage IDs across the recorded
trajectory and compare them with each sample's gold support IDs.

| Method | Avg Cumulative Support Recall | Any-Support Hit | All-Support Hit |
| --- | ---: | ---: | ---: |
| agentic_rag_baseline | 0.6883 | 0.9567 | 0.4200 |
| claim_risk | 0.7283 | 0.9667 | 0.4900 |

The C1 gain is consistent with improved support acquisition and lower wasted
retrieval, but this remains within the proxy evaluation setting.

## Decision

The dense top100 + BGE reranker top10 + checklist C1 configuration passes the
strict held-out proxy target on MuSiQue 2-hop proxy test and should be treated
as the current fixed performance branch result.

Do not retune on this held-out output. The next valid step is either to package
this as a proxy result with caveats, or start a new dev-only line for a
non-leaking answer/verifier backend before making open-domain QA claims.
