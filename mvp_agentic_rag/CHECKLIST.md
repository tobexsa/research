# MuSiQue 2-Hop Retrieval Performance Checklist

> Active checklist (2026-07-15):
> `analysis/semantic_fusion_phase3_campaign_checklist_20260715.md`. This
> checklist remains the historical record for the completed 2-hop proxy
> retrieval line.

## Preflight

- [x] Confirm proxy split and shared 9,600-passage corpus.
- [x] Confirm BM25 top10/top20 reference metrics.
- [x] Confirm local BGE embedding and reranker model paths.
- [x] Confirm current 9,600-passage dense index is hashing-only.
- [x] Confirm old real BGE index covers a different 6,000-passage corpus.
- [x] Confirm current Python is CPU-only and record GPU limitation.
- [x] Check for an existing CUDA-capable local Python environment.
- [x] Verify model loading with bounded embedding/reranker probes.

Notes:

- Active branch: `performance-musique-2hop-retrieval`.
- Default Python has a stable CPU model stack.
- Conda base has CUDA PyTorch but currently has a NumPy/scikit-learn binary
  incompatibility; do not use it until repaired or isolated.
- The BGE CPU probe encoded 128 short queries in about 1.55 seconds.
- The CPU reranker probe scored relevant evidence above an unrelated passage.

## BGE Index

- [x] Build the 9,600-passage BGE index.
- [x] Verify document count is exactly 9,600.
- [x] Verify metadata backend/model/dimension.
- [x] Verify index passage IDs match the proxy corpus.
- [x] Run bounded dense retrieval smoke.

Index evidence (2026-07-11):

- Build completed in 659.2 seconds on CPU.
- FAISS contains 9,600 vectors with dimension 768.
- Metadata records `sentence_transformers` and the local BGE-base-en-v1.5 snapshot.
- All 9,600 metadata passage IDs are unique and exactly match sorted corpus IDs.
- Dense top10 smoke completed 10 trajectories for 5 dev samples in 37.9 seconds.
- CPU top100 reranker smoke completed 4 trajectories in 409 seconds, projecting
  roughly 8.5 hours for the full dev run without acceleration.
- A process-local package-path override yields a compatible CUDA stack without
  installing dependencies: NumPy 1.26.3, Torch 2.6.0+cu126, Transformers 4.57.6,
  SentenceTransformers 5.1.2, and CUDA available.

## Dev Candidates

Reranker runtime evidence:

- CUDA reduced the identical 4-trajectory reranker smoke from 409 to 62.8 seconds.
- Exact-query caching passed focused/regression tests and reduced it to 49 seconds;
  cached and uncached CUDA trajectory JSON records are exactly equal.

- [x] Run dense-only dev.
- [x] Record dense-only metrics and support recall.
- [x] Run dense top100 + reranker smoke and runtime estimate.
- [x] Run dense top100 + reranker dev.
- [x] Record reranked metrics and support recall.
- [x] Add failing hybrid retriever tests.
- [x] Implement BM25+BGE hybrid retrieval.
- [x] Pass focused and regression retrieval tests.
- [x] Run hybrid dev.
- [ ] Run non-targeted hybrid top100 + reranker dev separately.
- [x] Add failing targeted multi-hop query tests.
- [x] Implement bounded C1 targeted multi-hop query fallback.
- [x] Pass focused and regression controller tests.
- [x] Run targeted C1 dev candidate.
- [x] Run hybrid top100 + reranker + targeted C1 dev candidate.

Current dev evidence:

- Dense top10: baseline EM/F1 0.5800/0.5869; C1 0.6267/0.6336.
- Hybrid top10: baseline EM/F1 0.5533/0.5591; C1 0.6600/0.6658.
- Hybrid top10 + targeted C1: baseline unchanged; C1 0.6667/0.6724.
- Targeted C1 changed correctness for one sample: one improvement, zero regressions.
- All three candidates have `final_answered_unsupported_rate = 0`.
- C1 average cumulative support recall: dense 0.6767, hybrid 0.6800,
  hybrid + targeted 0.6867.
- C1 any-support hit: 0.9400, 0.9400, 0.9533 respectively; all-support hit:
  0.4133, 0.4200, 0.4200.
- Dense top100 + reranker top10 C1: EM/F1 0.6800/0.6869, cumulative
  support recall 0.7333, any-support hit 0.9733, all-support hit 0.4933.
- Dense reranker run has 300 unique trajectory keys, 150 records per method,
  finite metrics, and `final_answered_unsupported_rate = 0`.
- Hybrid top100 + reranker + targeted C1: baseline EM/F1 0.6067/0.6141;
  C1 EM/F1 0.6667/0.6741. It underperformed dense top100 + reranker C1, so it
  was rejected before held-out testing.
- A separate non-targeted hybrid top100 + reranker dev run was not executed;
  this is not needed for the frozen selection because the stronger targeted
  hybrid reranker package still underperformed the dense reranker winner.

## Selection

- [x] Compare all candidates using the unchanged evaluator.
- [x] Verify all metric values are finite.
- [x] Verify no run used held-out test for selection.
- [x] Verify C1 improvement against matched baseline.
- [x] Select exactly one configuration: dense top100 + BGE reranker top10.
- [x] Freeze the config and record its hash.
- [x] Confirm dev gate: EM >= 0.46, F1 >= 0.59, final unsupported = 0.

Selection decision (2026-07-11):

- Winner C1: `dense_reranker`, EM/F1 `0.6800/0.6869`.
- Rejected `hybrid_reranker_targeted`: EM/F1 `0.6667/0.6741`.
- Rejected `hybrid_targeted` without reranker: EM/F1 `0.6667/0.6724`.
- All candidates had final unsupported rate 0; winner had 300 unique trajectories,
  150 per method, and finite metrics.
- Frozen test config SHA-256:
  `C5DA1379D57005495130DD4009DD96952E1E4F5E648690898C9D2BE2CD9A07EC`.

## Held-Out Test

- [x] Run the frozen configuration on `test.jsonl` exactly once.
- [x] Verify 300 samples per configured method and no duplicate keys.
- [x] Verify metrics, trajectories, and run summary exist.
- [x] Check strict acceptance: EM > 0.433 and F1 > 0.565.
- [x] Write final comparison and limitations report.

Held-out evidence (2026-07-11):

- Frozen config SHA-256 remained
  `C5DA1379D57005495130DD4009DD96952E1E4F5E648690898C9D2BE2CD9A07EC`.
- `trajectories.jsonl`: 600 rows, 600 unique `(id, method)` keys.
- Method counts: `agentic_rag_baseline = 300`, `claim_risk = 300`.
- `metrics.json` and `run_summary.md` exist; all metric values are finite.
- Baseline held-out: EM/F1 `0.5233/0.5332`, coverage `0.7600`,
  final unsupported `0`.
- C1 held-out: EM/F1 `0.6100/0.6200`, coverage `0.8433`,
  final unsupported `0`.
- C1 support recall: average cumulative `0.7283`, any-support hit `0.9667`,
  all-support hit `0.4900`.
- C1 passes the strict held-out target. These are still proxy metrics because
  `answer_backend: heuristic` and `verifier_backend: weak` are active.
