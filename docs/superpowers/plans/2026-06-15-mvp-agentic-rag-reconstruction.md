# MVP Agentic RAG Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable, test-covered MVP Agentic RAG reconstruction under `D:\research\mvp_agentic_rag`.

**Architecture:** A standard-library Python package with structured schemas, local JSONL data, lexical/oracle retrieval, five agent methods, unified trajectory logs, metrics, and table generation. The implementation uses smoke data by default and keeps API/dense retrieval as future-compatible extension points.

**Tech Stack:** Python 3 standard library, `unittest`, JSONL, CSV, minimal YAML-like config parser.

---

### Task 1: Project Skeleton and Data Loading

**Files:**
- Create: `mvp_agentic_rag/pyproject.toml`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/__init__.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/schemas.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/data_loader.py`
- Test: `mvp_agentic_rag/tests/test_data_loader.py`

- [ ] Write failing tests for loading samples and passages from JSONL.
- [ ] Run `python -m unittest tests.test_data_loader -v` and verify failure.
- [ ] Implement dataclasses and JSONL loading.
- [ ] Run the test and verify pass.

### Task 2: Retrieval

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/retriever.py`
- Test: `mvp_agentic_rag/tests/test_retriever.py`

- [ ] Write failing tests for lexical ranking and oracle supporting passage ranking.
- [ ] Run `python -m unittest tests.test_retriever -v` and verify failure.
- [ ] Implement lexical and oracle retrievers.
- [ ] Run the test and verify pass.

### Task 3: Verifier and Policy

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/evidence_ledger.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/verifier.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/policy.py`
- Test: `mvp_agentic_rag/tests/test_policy.py`

- [ ] Write failing tests for answer/refine/continue/abstain decisions.
- [ ] Run `python -m unittest tests.test_policy -v` and verify failure.
- [ ] Implement weak claim verifier and rule policy.
- [ ] Run the test and verify pass.

### Task 4: Agents and Runner

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/answer_generator.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/agents/`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/layer1_runner.py`
- Test: `mvp_agentic_rag/tests/test_runner.py`

- [ ] Write failing tests that run all methods and then resume without duplicating trajectories.
- [ ] Run `python -m unittest tests.test_runner -v` and verify failure.
- [ ] Implement agents and runner.
- [ ] Run the test and verify pass.

### Task 5: Metrics, Tables, Scripts, Configs, Data

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/evaluator.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/eval/table_builder.py`
- Create: `mvp_agentic_rag/scripts/*.py`
- Create: `mvp_agentic_rag/configs/*.yaml`
- Create: `mvp_agentic_rag/data/*.jsonl`
- Create: `mvp_agentic_rag/runs/mvp_decision.md`
- Create: `mvp_agentic_rag/README.md`
- Test: `mvp_agentic_rag/tests/test_tables.py`

- [ ] Write failing tests for table generation.
- [ ] Run `python -m unittest tests.test_tables -v` and verify failure.
- [ ] Implement metrics, table builder, scripts, configs, smoke data, README, and decision note.
- [ ] Run table tests and verify pass.

### Task 6: Full Verification

**Files:**
- All project files.

- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python scripts\run_layer1_skeleton.py --config configs\offline_bm25_smoke_all_methods.yaml`.
- [ ] Run `python scripts\make_mvp_tables.py --dataset data\challenge_smoke.jsonl --output-dir tables`.
- [ ] Inspect generated `runs/offline_bm25_smoke_all_methods/metrics.json` and `tables/mvp_tables_summary.json`.
