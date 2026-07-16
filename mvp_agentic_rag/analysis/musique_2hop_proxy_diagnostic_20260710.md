# MuSiQue 2-Hop Proxy Diagnostic

Date: 2026-07-10

## Scope

This diagnostic explains why the first MuSiQue 2-hop proxy metrics were low,
identifies the current blocking issues, and sets a practical target for the
next proxy-stage experiment. All runs use `data/musique_2hop_proxy/dev.jsonl`
and do not touch the held-out `test.jsonl`.

## Current Issues

1. The initial dense index used `hashing` embeddings, not a semantic retriever.
   This is suitable for smoke testing FAISS I/O but not for quality claims.

2. The proxy corpus is a pooled 9,600-passage corpus, not a per-question
   20-paragraph oracle setting. This is useful for RAG-like stress testing but
   exposes weak retrieval immediately.

3. `top_k=5` is too tight for the current weak retriever on 2-hop questions.
   Hashing top5 retrieved all gold support for only 3 of 150 C1 dev samples.

4. The current `heuristic` answer generator reads `sample.gold_answer`. It is
   acceptable only as a retrieval/control proxy and is not a valid final
   performance setting.

5. The current `weak` verifier gives C2 very little usable state signal. In the
   hashing top5 setting, C1 and C1+C2 produced identical trajectories.

6. Current cost metrics emphasize retrieval-call count and do not sufficiently
   penalize larger `top_k`. For budget decisions, report average retrieved
   passages alongside `avg_retrieval_calls`.

7. Building a BGE index for the new 9,600-passage proxy corpus did not complete
   within the 300-second command timeout. No complete BGE proxy index artifacts
   were produced in this pass.

## Diagnostic Results

| Setting | Method | F1 | Acc | Coverage | Any support | Full support | Avg calls | Avg retrieved passages | Final unsupported |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hash top5 | C1 | 0.1411 | 0.1400 | 0.2067 | 55/150 | 3/150 | 2.6333 | 13.1667 | 0 |
| Hash top20 | C1 | 0.2800 | 0.2800 | 0.4333 | 84/150 | 10/150 | 2.3600 | 47.2000 | 0 |
| BM25 top5 | C1 | 0.2787 | 0.2733 | 0.4400 | 100/150 | 8/150 | 2.0933 | 10.4667 | 0 |
| BM25 top10 | C1 | 0.4316 | 0.4267 | 0.6133 | 118/150 | 26/150 | 1.8600 | 18.6000 | 0 |
| BM25 top20 | C1 | 0.5240 | 0.5200 | 0.7533 | 134/150 | 40/150 | 1.5867 | 31.7333 | 0 |
| Oracle top5 | C1 | 0.9733 | 0.9733 | 0.9733 | 150/150 | 150/150 | 1.0267 | 5.1333 | 0 |

## Interpretation

The oracle run shows that the sample format, evaluator, and control flow can
produce high scores when the correct evidence is available. Therefore the low
initial score is primarily a retrieval and query-budget problem, not an
evaluator failure.

BM25 top10 is the best current operating point for a low-cost proxy run. It
more than triples the initial hashing top5 F1 while keeping the average
retrieved passage budget under 20. BM25 top20 is stronger but should be treated
as a stretch or upper-budget setting because it retrieves about 32 passages per
sample on average.

The C2-only line should not be promoted yet. Under weak verifier signals, it
does not change behavior enough to justify a claim. C2 should be revisited only
after either a stronger verifier/reasoner or a stronger conflict/gap diagnostic
signal is available.

## Recommended Targets

### Current Low-Cost Proxy Target

Use BM25 top10 + C1 as the current acceptable dev target:

- `answer_f1 >= 0.40`
- `overall_acc >= 0.40`
- `coverage >= 0.60`
- `final_answered_unsupported_rate = 0`
- `avg_retrieved_passages <= 20`
- `C1 answer_f1 - baseline answer_f1 >= 0.10`

This target is achieved on dev:

- `answer_f1 = 0.4316`
- `overall_acc = 0.4267`
- `coverage = 0.6133`
- `final_answered_unsupported_rate = 0`
- `avg_retrieved_passages = 18.6000`
- baseline F1 in the same setting is `0.3183`, so C1 improves by `+0.1133`

### Stretch Proxy Target

Use BM25 top20 only as a high-budget reference:

- `answer_f1 >= 0.50`
- `coverage >= 0.70`
- `final_answered_unsupported_rate = 0`
- report `avg_retrieved_passages` explicitly

This is achieved on dev with C1:

- `answer_f1 = 0.5240`
- `coverage = 0.7533`
- `avg_retrieved_passages = 31.7333`

### Valid Performance Target

For a real non-leaking performance run, replace heuristic answer generation and
weak verifier with a real reasoner/verifier. A reasonable first non-leaking dev
target is:

- `answer_f1 >= 0.35`
- `coverage >= 0.50`
- `final_answered_unsupported_rate <= 0.02`, preferably `0`
- `avg_retrieved_passages <= 20`
- C1 or C1+C2 improves over matched baseline by at least `+0.05 F1`

## Next Action

Run the held-out `test.jsonl` only after choosing one non-test operating point.
The recommended next operating point is:

- retriever: `bm25`
- top_k: `10`
- max_rounds: `3`
- method promoted from dev: `C1`
- report C1+C2 only as a research-label-compatible wrapper unless a stronger
  verifier makes C2 behavior observably different.
