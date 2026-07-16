# MuSiQue 2-Hop Proxy Held-Out Test: BM25 Top10 Baseline vs C1

Date: 2026-07-10

## Scope

This report records the fixed held-out test run selected from dev diagnostics.
No test-time tuning was performed in this pass.

Selected operating point:

- dataset: `data/musique_2hop_proxy/test.jsonl`
- corpus: `data/musique_2hop_proxy/corpus.jsonl`
- retriever: `bm25`
- `top_k`: `10`
- `max_rounds`: `3`
- methods: `agentic_rag_baseline`, `claim_risk`
- answer backend: `heuristic`
- verifier backend: `weak`
- query decomposition: `none`
- C1 switches: claim evidence checklist enabled

Important caveat: this is a retrieval/control proxy setting. The heuristic
answer generator uses gold-answer matching internally, so these numbers are not
valid final open-domain QA performance claims.

## Artifacts

- config: `configs/musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1.yaml`
- run directory: `runs/musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1`
- metrics: `runs/musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1/metrics.json`
- trajectories: `runs/musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1/trajectories.jsonl`
- summary table: `runs/musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1/run_summary.md`

Command:

```powershell
python scripts\run_layer1_skeleton.py --config configs\musique_2hop_proxy_test_bm25_top10_agentic_rag_baseline_c1.yaml
```

## Verification

Configuration and data-loader tests:

```powershell
python -m pytest tests/test_config_naming.py tests/test_musique_conversion.py tests/test_data_loader.py -q
```

Result:

```text
7 passed in 0.19s
```

Run-output verification:

- required files exist: `metrics.json`, `run_summary.md`, `trajectories.jsonl`
- trajectory rows: `600`
- methods: `agentic_rag_baseline`, `claim_risk`
- unique `(method, id)` pairs: `600`
- all rows use `subset == "test"`
- all rows use `hop == 2`
- required metric values are finite

## Test Results

| Method | Count | F1 | Acc | Coverage | Selective Acc | Avg calls | Avg retrieved passages | Avg unique retrieved passages | Wasted rate | Final unsupported | Any support | Full support |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 300 | 0.2009 | 0.1933 | 0.4167 | 0.4640 | 2.1733 | 21.7333 | 10.8600 | 0.5900 | 0 | 192/300 | 27/300 |
| claim_risk / C1 | 300 | 0.3042 | 0.2967 | 0.5333 | 0.5563 | 1.9733 | 19.7333 | 12.6200 | 0.4900 | 0 | 205/300 | 52/300 |

Delta, C1 minus baseline:

- F1: `+0.1033`
- Accuracy: `+0.1033`
- Coverage: `+0.1167`
- Avg retrieval calls: `-0.2000`
- Avg retrieved passages: `-2.0000`
- Full-support recall: `+25` samples, from `27/300` to `52/300`

## Acceptance Check

Held-out proxy target set before test:

- `answer_f1 >= 0.38`
- `overall_acc >= 0.38`
- `coverage >= 0.55`
- `final_answered_unsupported_rate = 0`
- `avg_retrieved_passages <= 20`
- C1 over matched baseline `>= +0.07 F1`

Observed C1:

- `answer_f1 = 0.3042` — fail
- `overall_acc = 0.2967` — fail
- `coverage = 0.5333` — near miss
- `final_answered_unsupported_rate = 0` — pass
- `avg_retrieved_passages = 19.7333` — pass
- C1 F1 delta over baseline = `+0.1033` — pass

Verdict: the mechanism-level delta survives on held-out test, but the absolute
score does not meet the held-out proxy target. This run supports "C1 improves
the current proxy controller over the matched baseline" but does not support
"BM25 top10 + current C1 is already strong enough as a final test setting."

## Dev-to-Test Shift

| Split | Method | F1 | Acc | Coverage | Avg retrieved passages | Any support | Full support |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | baseline | 0.3183 | 0.3133 | 0.5067 | 19.9333 | 110/150 | 19/150 |
| dev | C1 | 0.4316 | 0.4267 | 0.6133 | 18.6000 | 118/150 | 26/150 |
| test | baseline | 0.2009 | 0.1933 | 0.4167 | 21.7333 | 192/300 | 27/300 |
| test | C1 | 0.3042 | 0.2967 | 0.5333 | 19.7333 | 205/300 | 52/300 |

The largest practical issue is retrieval robustness. C1 test full-support rate
matches dev proportionally (`26/150 = 17.3%`; `52/300 = 17.3%`), but test
any-support recall is lower (`78.7%` on dev to `68.3%` on test). This means
more test questions fail before the controller has enough partial evidence to
converge.

## Current Problems

1. BM25 top10 is not robust enough on held-out 2-hop proxy questions.
   Any-support recall drops by about `10.3` percentage points from dev to test.

2. Full 2-hop support retrieval remains low at `52/300 = 17.3%` for C1. The
   heuristic can sometimes answer with partial evidence, but the evidence path
   is not strong enough for final RAG claims.

3. The current weak verifier gives no strong C2 signal, so C2 should not be
   promoted from this evidence.

4. Current proxy scores are not valid open-domain QA SOTA numbers because the
   heuristic answer generator uses gold-answer matching.

5. The cost metric alone is misleading. Baseline has fewer unique passages than
   C1 in some cases but more total retrieved passages due repeated calls, so
   reports must include both calls and retrieved-passage budget.

## Next Decision

Do not tune on `test.jsonl`.

Recommended next route:

1. Return to `dev.jsonl`.
2. Improve retrieval/query generation under the same no-leakage proxy
   constraints.
3. Keep the held-out target unchanged until a dev-side change is selected:
   - C1 dev F1 should be comfortably above `0.45`
   - C1 dev coverage should be at least `0.65`
   - average retrieved passages should remain near or below `20`
   - C1 should beat matched baseline by at least `+0.10 F1`
4. Only after selecting one improved dev operating point, run one new held-out
   test pass.

Best immediate candidates:

- better multi-hop query rewriting for BM25 top10, especially adding entity and
  relation constraints from the first retrieved hop;
- controlled BM25 top10 plus one targeted fallback query instead of blindly
  moving to top20;
- revisit dense retrieval only after a real semantic index can be built and
  verified.
