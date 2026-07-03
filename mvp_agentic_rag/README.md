# MVP Agentic RAG

This is a functional reconstruction of the prior `mvp_agentic_rag` research MVP from recovered conversation history and local design documents.

It implements a small, offline-first version of claim-level risk-calibrated Agentic RAG:

- unified trajectory logs
- lexical and oracle retrieval
- baseline agents: `naive`, `fixed_k`, `self_stop`, `prompt_verifier`
- `agentic_rag_baseline`: weak claim verifier plus stop/refine/abstain policy
- metrics and MVP table generation
- smoke data that runs without external APIs

## What This Is Not

This is not a byte-for-byte restoration of the old `E:\research\mvp_agentic_rag` project. The old project, FAISS indexes, and real API run outputs are not available in this workspace.

MuSiQue data has been converted from `D:\research\datasets\data\musique_ans_v1.0_dev.jsonl` into a balanced 300-sample MVP dataset. Dense retrieval works through a local 768-dimensional hashing FAISS index. This restores the dense/FAISS run path without downloading an external embedding model, but it is not quality-equivalent to bge/e5 embeddings.

## Run Tests

```powershell
cd D:\research\mvp_agentic_rag
python -m unittest discover -s tests -v
```

## Run Offline Smoke Experiment

```powershell
python scripts\run_layer1_skeleton.py --config configs\offline_bm25_smoke_all_methods.yaml
```

Outputs:

```text
runs/offline_bm25_smoke_all_methods/trajectories.jsonl
runs/offline_bm25_smoke_all_methods/metrics.json
runs/offline_bm25_smoke_all_methods/metrics.md
```

## Progress Display

Experiment progress is controlled from config:

```yaml
progress_every: 1
progress_display: auto
```

Supported `progress_display` values:

- `auto`: show a live single-line TUI bar in an interactive terminal, and fall back to plain `progress:` log lines when stdout is redirected.
- `plain`: always write plain `progress:` log lines.
- `tui`: always write the carriage-return TUI progress bar.
- `none`: suppress progress lines while still writing summary paths such as `result_table:`.

For resumed runs, the TUI bar counts both newly completed rows and skipped existing rows toward the displayed total. Setting `progress_every: 0` without an explicit `progress_display` preserves the old behaviour and disables progress output.

## Build MVP Tables

```powershell
python scripts\make_mvp_tables.py --dataset data\challenge_smoke.jsonl --output-dir tables
```

Outputs:

```text
tables/mvp_main_results.csv
tables/mvp_process_metrics.csv
tables/mvp_stale_runs.csv
tables/mvp_tables_summary.json
```

## Build MuSiQue Balanced 300

```powershell
python scripts\sample_musique.py --source D:\research\datasets\data\musique_ans_v1.0_dev.jsonl --sample-output data\musique_mvp_300.jsonl --corpus-output data\musique_corpus.jsonl --per-hop 100 --seed 13
```

Expected output:

```text
samples_written: 300
corpus_written: 6000
hop_counts: 2=100, 3=100, 4=100
```

## Run Balanced-300 BM25

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_bm25_scoped_prompt_v3_all_methods.yaml
```

Output:

```text
runs/layer1_api_balanced300_bm25_scoped_prompt_v3_all_methods/
```

## Build Dense FAISS Index

```powershell
python scripts\build_index.py --corpus data\musique_corpus.jsonl --index indexes\faiss_musique.index --meta indexes\faiss_musique_meta.pkl --dimension 768
```

Expected output:

```text
documents: 6000
dimension: 768
```

## Run Balanced-300 Dense

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_scoped_prompt_v3_all_methods.yaml
```

Output:

```text
runs/layer1_api_balanced300_dense_scoped_prompt_v3_all_methods/
```

## Build BGE Dense FAISS Index

```powershell
python scripts\build_index.py --corpus data\musique_corpus.jsonl --index indexes\faiss_musique_bge_base_en_v1_5.index --meta indexes\faiss_musique_bge_base_en_v1_5_meta.pkl --embedding-backend sentence_transformers --embedding-model D:\research\model\models--BAAI--bge-base-en-v1.5\snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a --batch-size 32
```

Expected output:

```text
documents: 6000
dimension: 768
embedding_backend: sentence_transformers
```

## Run Balanced-300 BGE Dense

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_scoped_prompt_v3_all_methods.yaml
```

Output:

```text
runs/layer1_api_balanced300_dense_bge_scoped_prompt_v3_all_methods/
```

## Run BGE Reranker

The local reranker path is:

```text
D:\research\model\models--BAAI--bge-reranker-v2-m3\snapshots\953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
```

CPU inference for `bge-reranker-v2-m3` is slow. Use the small verification config first:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_rerank_subset2_scoped_prompt_v3_all_methods.yaml
```

The full reranker config exists, but should be run on GPU or with reduced `rerank_top_n` / methods:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_rerank_scoped_prompt_v3_all_methods.yaml
```

## Run OpenAI-Compatible LLM Verifier/Generator

The LLM path is optional and disabled by default. API keys are read only from environment variables, not from config files.

For SiliconFlow-compatible usage:

```powershell
$env:SILICONFLOW_API_KEY = "<your key>"
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_llm_verifier_subset2.yaml
```

The subset config uses:

```text
answer_backend: openai_compatible
verifier_backend: openai_compatible
answer_api_key_env: SILICONFLOW_API_KEY
verifier_api_key_env: SILICONFLOW_API_KEY
limit_samples: 2
methods: [prompt_verifier, agentic_rag_baseline]
```

Use a small subset first because each sample can trigger multiple answer and verifier calls.

## Historical Table Command

```powershell
python scripts\make_mvp_tables.py --dataset data\musique_mvp_300.jsonl --output-dir tables
```

The current decision note is in:

```text
runs/mvp_decision.md
```
