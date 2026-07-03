# MVP Agentic RAG Reconstruction Design

Date: 2026-06-15

## Goal

Reconstruct a functionally equivalent MVP project for claim-level, risk-calibrated Agentic RAG in `D:\research\mvp_agentic_rag`, based on the recovered session summary and the local planning documents:

- `mvp_agentic_rag_implementation_plan.docx`
- `new_agentic_rag_blueprint_ccfa.md`

The reconstruction is not byte-for-byte recovery of the former `E:\research\mvp_agentic_rag` project. The old project and MuSiQue data are not present. This version provides a runnable, testable MVP skeleton with smoke data, unified trajectory logs, baseline agents, the claim-level policy, and table generation.

## Scope

The MVP will implement:

- Local smoke data and corpus files.
- Structured sample, passage, claim, verifier, trajectory, and metric schemas.
- BM25-like lexical retrieval and oracle retrieval.
- Placeholder dense retrieval interface with an actionable dependency error.
- Baseline agents: naive RAG, fixed-k, weak self-stop, prompt-verifier stop.
- Ours agent: evidence ledger, weak claim-level verifier, stop/refine/abstain policy.
- A runner that executes all methods, writes incremental `trajectories.jsonl`, and supports resume.
- Evaluators for answer F1, retrieval calls, no-new-evidence calls, abstention, unsupported claims, and stale/missing run checks.
- CLI scripts matching the historical workflow names.
- Configs for offline smoke runs and future balanced-300 API runs.
- Unit tests for the core behavior.

Out of scope for this reconstruction:

- Downloading MuSiQue or building the original balanced 300 dataset.
- Real SiliconFlow/OpenAI API calls by default.
- Full FAIR-RAG, Stop-RAG, A2RAG, or DecEx-RAG reproductions.
- Trained verifier, trained controller, RL, or GraphRAG.

## Architecture

The project is a small Python package using only the standard library for default operation. Domain objects live in `schemas.py`; retrieval in `retriever.py`; claim state in `evidence_ledger.py`; verification in `verifier.py`; control in `policy.py`; answer generation in `answer_generator.py`; agents in `agents/`; orchestration in `layer1_runner.py`; and metrics/table output in `evaluator.py` plus `eval/table_builder.py`.

The runner reads YAML-like configs through a minimal parser that supports the simple key/value and list shapes used by the included configs. It writes one trajectory record per `(sample_id, method)` to allow resume without rerunning completed methods.

## Data Flow

1. `scripts/run_layer1_skeleton.py` loads a config.
2. `data_loader.py` reads the dataset and corpus JSONL files.
3. `retriever.py` builds a lexical or oracle retriever.
4. `layer1_runner.py` dispatches each sample to each configured agent.
5. Each agent produces a final answer/action and per-round trajectory steps.
6. `evaluator.py` computes metrics and writes `metrics.json` and `metrics.md`.
7. `scripts/make_mvp_tables.py` aggregates run directories into CSV and JSON summaries under `tables/`.

## Testing

Tests will cover:

- JSONL sample/corpus loading.
- Lexical and oracle retrieval behavior.
- Risk policy decisions for answer, refine, continue, and abstain.
- Runner output and resume behavior.
- Table generation from run outputs.

The default verification command is:

```powershell
python -m unittest discover -s tests -v
```

The default smoke run is:

```powershell
python scripts\run_layer1_skeleton.py --config configs\offline_bm25_smoke_all_methods.yaml
python scripts\make_mvp_tables.py --dataset data\challenge_smoke.jsonl --output-dir tables
```

## Risks

- Smoke data can only validate pipeline behavior, not research claims.
- Weak heuristic verification is not a substitute for a trained or LLM verifier.
- Dense/FAISS is intentionally a future extension unless dependencies and embeddings are supplied.
- Without the original project, exact previous implementation details are unrecoverable.
