# Real Embedding and Reranker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real local BGE embedding and reranker support while preserving hashing fallback and existing runs.

**Architecture:** Add `embeddings.py` for backend-neutral text encoders and `reranker.py` for backend-neutral reranking. Extend `dense_index.py`, `retriever.py`, `build_index.py`, config parsing, and runner wiring so dense retrieval can use either hashing or `sentence_transformers`, and optional reranking can reorder a dense top-N candidate set before returning top-k passages.

**Tech Stack:** Python, FAISS, NumPy, torch, sentence_transformers, transformers, unittest.

---

### Task 1: Embedding Backend

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/embeddings.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/dense_index.py`
- Test: `mvp_agentic_rag/tests/test_embeddings.py`

- [ ] Write failing tests for hashing encoder shape and backend factory.
- [ ] Run the tests and verify failure.
- [ ] Implement `HashingTextEncoder`, `SentenceTransformerTextEncoder`, and `make_text_encoder`.
- [ ] Update dense index build/load metadata to record backend/model.
- [ ] Run tests and verify pass.

### Task 2: Dense Retriever Wiring

**Files:**
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/retriever.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/layer1_runner.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/config.py`
- Test: `mvp_agentic_rag/tests/test_dense_retriever.py`

- [ ] Write failing tests for loading backend metadata and returning dense candidates.
- [ ] Run tests and verify failure.
- [ ] Update `DenseRetriever` to read encoder backend/model from metadata and support config-supplied paths.
- [ ] Update `make_retriever` and runner config pass-through.
- [ ] Run tests and verify pass.

### Task 3: Reranker

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/reranker.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/retriever.py`
- Test: `mvp_agentic_rag/tests/test_reranker.py`

- [ ] Write failing tests using a lightweight lexical/fake reranker to prove reranking changes order.
- [ ] Run tests and verify failure.
- [ ] Implement `LexicalReranker`, `TransformersSequenceReranker`, and `make_reranker`.
- [ ] Wire optional reranking into `DenseRetriever`.
- [ ] Run tests and verify pass.

### Task 4: CLI and Configs

**Files:**
- Modify: `mvp_agentic_rag/scripts/build_index.py`
- Add: `mvp_agentic_rag/configs/layer1_api_balanced300_dense_bge_scoped_prompt_v3_all_methods.yaml`
- Add: `mvp_agentic_rag/configs/layer1_api_balanced300_dense_bge_rerank_scoped_prompt_v3_all_methods.yaml`
- Modify: `mvp_agentic_rag/README.md`

- [ ] Add CLI args for embedding backend/model/batch size.
- [ ] Add configs for BGE dense and BGE dense+reranker.
- [ ] Document exact local model snapshot paths.
- [ ] Run full tests.

### Task 5: Build and Run

**Files:**
- Generated index/run/table artifacts.

- [ ] Build BGE FAISS index.
- [ ] Run BGE dense balanced-300.
- [ ] Smoke-test reranker on a small config or capped run if CPU runtime is high.
- [ ] Regenerate tables.
- [ ] Run final tests and summarize remaining gaps.
