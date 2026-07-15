# MuSiQue 2-Hop Retrieval Performance Plan

> Active experiment sequence (2026-07-15): phase-3 component ablations,
> independent repeated runs, then matched modern baselines. The active charter
> is `analysis/semantic_fusion_phase3_campaign_plan_20260715.md`. The material
> below is the completed 2-hop proxy retrieval plan and remains historical
> evidence.

## Objective

Build a valid semantic retrieval and reranking stack for the 9,600-passage
MuSiQue 2-hop proxy corpus, select one configuration on `dev.jsonl`, and run
the held-out `test.jsonl` exactly once after the configuration is frozen.

The strict held-out acceptance target is:

- `overall_em > 0.433`
- `answer_f1 > 0.565`

These are retrieval/control proxy metrics while `answer_backend: heuristic`
and `verifier_backend: weak` remain active. They must not be reported as
standard non-leaking open-domain QA results.

## Non-Negotiable Constraints

- Do not use `test.jsonl` for parameter selection.
- Do not change the dataset, split, gold fields, evaluator, or metric
  definitions during selection.
- Do not expose gold decomposition, gold support labels, or gold answer to
  retrieval/query generation.
- Preserve the existing BM25 top10 and top20 runs as read-only references.
- Do not revert unrelated changes in the dirty worktree.
- Record every dev candidate in a unique config and run directory.
- Run held-out test only after one dev configuration is selected and frozen.

## Baseline Contract

- Dataset: `data/musique_2hop_proxy/dev.jsonl`
- Held-out dataset: `data/musique_2hop_proxy/test.jsonl`
- Corpus: `data/musique_2hop_proxy/corpus.jsonl` (9,600 passages)
- Methods: `agentic_rag_baseline`, `claim_risk`
- Primary metrics: `overall_em`, `answer_f1`
- Supporting metrics: coverage, selective accuracy/F1, support recall,
  average retrieval calls, retrieved passages, unique passages, wasted rate
- Existing references:
  - BM25 top10 dev C1: EM 0.4267, F1 0.4316
  - BM25 top20 dev C1: EM 0.5200, F1 0.5240
  - BM25 top10 held-out C1: EM 0.2967, F1 0.3042

## Execution Sequence

1. Build a BGE-base-en-v1.5 FAISS index over all 9,600 proxy passages.
2. Validate index metadata, passage identity, dimension, and a bounded smoke
   retrieval.
3. Run dense-only dev.
4. Run dense candidate top100 plus BGE reranker dev.
5. Implement reciprocal-rank-fusion BM25+BGE hybrid retrieval with tests.
6. Run hybrid dev and hybrid top100 plus reranker dev.
7. Implement a bounded C1 targeted multi-hop query fallback with tests. It
   may use the question, retrieved passage titles/text, verifier state, and
   query history, but no gold fields.
8. Run the targeted C1 candidate on dev.
9. Select exactly one frozen configuration using dev evidence.
10. Run held-out test exactly once and validate the strict target.

## Candidate Retrieval Contract

- Dense encoder:
  `D:\research\model\models--BAAI--bge-base-en-v1.5\snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`
- Reranker:
  `D:\research\model\models--BAAI--bge-reranker-v2-m3\snapshots\953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`
- Dense index:
  `indexes/faiss_musique_2hop_proxy_bge_base_en_v1_5.index`
- Dense metadata:
  `indexes/faiss_musique_2hop_proxy_bge_base_en_v1_5_meta.pkl`
- Rerank candidate pool: 100
- Final top-k candidates to compare on dev: 10 and 20 when runtime permits
- Hybrid fusion: reciprocal-rank fusion over BM25 and dense rankings, with
  equal default source weights unless dev evidence justifies one bounded
  alternative.

## Runtime Plan

- Current Python uses CPU-only PyTorch. Index construction and reranking will
  therefore use CPU unless an already-installed CUDA-capable interpreter is
  found during preflight.
- Run a two-sample reranker smoke before the full dev reranker run.
- If top100 reranking is prohibitively slow, preserve top100 candidate
  retrieval but cache query-level candidate scores/results. Do not silently
  reduce the candidate pool.
- Long commands write stdout/stderr logs under `runs/logs/`.

## Dev Selection Gate

A candidate is eligible for the single held-out run only if:

- C1 `overall_em >= 0.46`
- C1 `answer_f1 >= 0.59`
- `final_answered_unsupported_rate = 0`
- C1 improves over its matched baseline
- metrics and trajectory files are complete and finite

If no candidate reaches this dev gate, do not consume the held-out test.

## Expected Code Touchpoints

- `src/mvp_agentic_rag/retriever.py`
- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- focused retrieval/query tests
- new configs under `configs/`
- new run outputs under `runs/`
- a final comparison report under `analysis/`

## Revision Log

- 2026-07-10: Replaced the stale v1.3.0 lifecycle plan with the user-approved
  MuSiQue semantic retrieval, reranking, hybrid, and targeted-query sequence.
- 2026-07-11: Selected dense top100 + BGE reranker top10 after dev C1 reached
  EM/F1 0.6800/0.6869. Hybrid + targeted + reranker reached 0.6667/0.6741
  and was rejected. Frozen held-out config hash is
  C5DA1379D57005495130DD4009DD96952E1E4F5E648690898C9D2BE2CD9A07EC.
- 2026-07-11: Completed the frozen held-out run on all 300 test samples with
  600 unique `(id, method)` trajectories. C1 passed the strict target with
  EM/F1 0.6100/0.6200; baseline reached 0.5233/0.5332. The result remains a
  heuristic/weak-verifier proxy result, not a non-leaking open-domain QA score.
