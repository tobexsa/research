# MVP Decision

Historical reconstruction decision:

```text
Conditional GO for offline MVP infrastructure;
NO-GO for final MVP claim table until balanced-300 API runs are executed.
```

This repository now provides offline smoke infrastructure plus a generated MuSiQue-Ans dev balanced-300 dataset:

```text
data/musique_mvp_300.jsonl
data/musique_corpus.jsonl
```

The balanced dataset contains 100 two-hop, 100 three-hop, and 100 four-hop answerable samples. The flattened corpus contains 6000 passages.

Completed local runs:

```text
runs/layer1_api_balanced300_bm25_scoped_prompt_v3_all_methods
runs/layer1_api_balanced300_dense_scoped_prompt_v3_all_methods
runs/layer1_api_balanced300_dense_bge_scoped_prompt_v3_all_methods
runs/layer1_api_balanced300_dense_bge_rerank_subset2_scoped_prompt_v3_all_methods
```

Dense index files:

```text
indexes/faiss_musique.index
indexes/faiss_musique_meta.pkl
indexes/faiss_musique_bge_base_en_v1_5.index
indexes/faiss_musique_bge_base_en_v1_5_meta.pkl
```

The first dense index is a local 768-dimensional hashing embedding index built with FAISS `IndexFlatIP`. The BGE index uses the local `bge-base-en-v1.5` sentence-transformers model.

The local `bge-reranker-v2-m3` model is wired and verified on smoke and subset runs. Full reranker balanced-300 CPU execution is slow and currently incomplete; run it on GPU or with smaller `rerank_top_n` / method sets.

OpenAI-compatible LLM answer generation and claim verification are wired behind config flags. The default runs still use heuristic generation/verification. Real API execution requires setting an API key environment variable such as `SILICONFLOW_API_KEY`.

Still missing: completed real LLM/API runs, learned verifier/controller, and official Stop-RAG/FAIR-RAG/A2RAG reproductions.

Next gates:

1. Run `configs/layer1_api_balanced300_dense_bge_llm_verifier_subset2.yaml` after setting `SILICONFLOW_API_KEY`.
2. Finish full BGE reranker balanced-300 on GPU or with a reduced reranker protocol.
3. Add Stop-RAG-style and FAIR-RAG-style baselines.
4. Generate final MVP tables from balanced-300 complete runs only.
