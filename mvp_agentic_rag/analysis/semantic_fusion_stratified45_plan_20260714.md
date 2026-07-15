# Semantic Fusion Stratified45 Plan

Date: 2026-07-14

## Objective

Phase 2 asks whether the R24 fixed-gate success survives on the original
45-case stratified set, and whether strict-certificate activation adds value
over a matched generic-only system.

Run order is fixed:

1. Fusion R25.
2. Generic-only R26.
3. Compare both with R12 and R20.

Phase 3 is not authorized until both phase-2 runs are complete and audited.

## Comparability Contract

- Dataset: `data/musique_mvp_stratified45.jsonl`
- Dataset SHA-256: `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`
- Corpus, dense index, embedding model, Qwen3-14B backends, top-k 5,
  three-round budget, answer/verifier token budgets, evaluator, and metric
  definitions are identical between R25 and R26.
- Both use the 2304-token slot-binding verifier budget.
- R25 enables R24 Fusion and deterministic certificate adapters.
- R26 disables strict-certificate activation and deterministic certificate
  adapters only.
- R26 still uses `no_fallback` for malformed topology, parse failure, real
  canonical conflict, sentinel candidates, and invalid/non-local evidence.
- Runs are sequential and use distinct output directories; no rows are
  shared or resumed across variants.

## Research Questions

1. Does Fusion improve Answer F1 or coverage over the matched generic-only
   variant without increasing final answered unsupported?
2. Does Fusion retain or improve the five known strict-certificate gains on
   the full 45-case surface?
3. Are any differences driven by lane activation rather than token budget,
   retriever, dataset, or evaluator drift?

## Required Outputs

- 45 unique trajectory rows per run.
- Complete finite metrics for accuracy/EM, Answer F1, coverage, selective
  accuracy/F1, retrieval cost, wasted retrieval rate, final unsupported, and
  per-hop slices.
- Fusion lane counts and reasons for R25.
- Explicit proof that R26 has zero strict-certificate lane steps and zero
  deterministic binding markers.
- Per-sample paired correctness deltas versus R12, R20, and between R25/R26.
- Safety replay with zero unsafe failure-candidate transitions.

## Stop Conditions

- Missing or duplicate rows.
- Configuration drift beyond the two generic-only switches.
- Non-finite or incomplete metrics.
- Final answered unsupported above zero.
- R26 entering the strict-certificate lane or applying a deterministic
  binding adapter.

An endpoint failure is recorded as infrastructure failure and may resume only
the same frozen config. A methodological failure does not authorize phase 3.

## Runtime

- Run focused and full tests before R25.
- Launch R25 and monitor rows/logs to completion.
- Validate R25 before launching R26.
- Launch R26 and monitor rows/logs to completion.
- Aggregate only from complete durable outputs.

## Decision Rule

After both runs, report the paired result honestly. Phase 3 may begin only
after this comparison is complete; a fixed-12 pass alone is insufficient.
