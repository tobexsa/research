# Matched Verifier-Guided Adaptive RAG Baseline Plan

Date: 2026-07-15
Baseline id: `matched_verifier_adaptive_rag_stratified45_v1`
Route: local reproduce-and-verify fast path
Status: `verified_complete`

## Objective And User Boundary

Establish at least one fairly matched modern-pattern baseline after the frozen
adapter/generic repeats passed. Keep the user's order: this package must finish
before non-leaking standard MuSiQue dev/test; 300 samples and paper-facing main
experiments remain later.

The primary comparator is the repository's verifier-guided iterative retrieval
agent, reported as `agentic_rag_baseline`. It is not labeled as an exact
reproduction of Adaptive-RAG, Self-RAG, CRAG, or FLARE.

Secondary infrastructure comparators in the same run are:

- `prompt_verifier`: one retrieval/generation followed by evidence sufficiency
  verification and answer/abstain.
- `fixed_k`: fixed three-round retrieval followed by answer generation.

## Comparability Contract

Held fixed against the online-stability incumbent:

- dataset: `data/musique_mvp_stratified45.jsonl`, 45 rows;
- corpus: `data/musique_corpus.jsonl`;
- dense BGE index and metadata;
- heuristic query decomposition, max four subqueries, per-subquery top-k 3;
- Qwen3-14B answer and verifier backends with reasoning disabled;
- top-k 5 and maximum three retrieval rounds;
- answer style, timeouts, retry settings, and repository evaluator;
- EM, Answer F1, coverage, selective metrics, retrieval cost, wasted retrieval,
  and final answered-unsupported metrics.

Changed factor: agent/control policy only. Method-inherent LLM-call counts may
differ and must be reported, not normalized away.

This targeted stratified45 surface is not a standard published MuSiQue split.
Published paper numbers are provenance context only and are not direct numeric
comparators.

## Source And Naming Boundary

Primary-source identities audited through the official arXiv API:

- FLARE, arXiv `2305.06983`: iterative retrieval triggered by low-confidence
  upcoming tokens; long-form and token-confidence contract mismatch.
- Self-RAG, arXiv `2310.11511`: specially trained reflection-token model;
  incompatible with a Qwen3 method-only comparison.
- CRAG, arXiv `2401.15884`: retrieval evaluator plus corrective actions,
  including web search; full method violates the fixed-corpus contract.
- Adaptive-RAG, arXiv `2403.14403`: trained complexity classifier routes among
  no-, single-, and iterative-retrieval strategies; the local agent has no such
  trained classifier.

Accordingly, no exact paper name is attached to the local comparator. Its
trust claim is limited to a matched verifier-guided adaptive/agentic RAG
pattern under this repository's evaluator.

## Command And Outputs

Config:

`configs/layer1_siliconflow_qwen3_14b_matched_verifier_adaptive_baselines_stratified45_20260715_v1.yaml`

Frozen config SHA-256:
`D456B238A5147D7CBA14F72B94A8813F6E92FE6C870FE62F84E7983C471991D2`.

Command:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_matched_verifier_adaptive_baselines_stratified45_20260715_v1.yaml
```

Expected output:

`runs/layer1_siliconflow_qwen3_14b_matched_verifier_adaptive_agentic_rag_baseline_stratified45_20260715_v1`

Expected rows: `45 × 3 = 135`, with 45 unique sample IDs for each method.

## Smoke And Real-Run Gate

Before launch:

1. parse the frozen YAML and verify exact method list;
2. prove dataset/config/source identities and output non-existence;
3. run focused agent/runner/evaluator tests;
4. use deterministic fake-backend tests as the bounded smoke; do not spend a
   new online sample outside the frozen 45-case run;
5. confirm no Python experiment process.

The real run is accepted only if it completes 135 unique method/sample keys,
has zero skipped rows and no remaining lock, writes finite required metrics,
uses the frozen config, and can be evaluated by the same evaluator. Safety and
coverage differences remain results, not reasons to alter the comparator.

## Trust Classes And Stop Rules

- Intended feasibility: `full_reproducible` locally.
- Intended downstream trust: `verified` for this repository's matched
  stratified45 comparison only.
- Hard stop: config/output collision, missing or duplicate method/sample rows,
  non-finite metrics, evaluator drift, source/data mismatch, or fatal endpoint
  failure.
- Do not repair a poor metric result; only repair implementation/environment
  invalidity.
- One concrete fix-and-retry is the maximum for a repeated failure class.

## Runtime Degradation

Managed `bash_exec`, artifact, and memory services are unavailable. PowerShell,
repository-local configs, run directories, reports, and SHA-256 hashes are the
explicit durable substitute.
