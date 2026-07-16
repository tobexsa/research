# Matched Baseline Checklist

## Analysis

- [x] Frozen repeat package authorizes matched modern baselines.
- [x] Dataset/split/evaluator/metric boundary is explicit.
- [x] Local candidate implementations inventoried.
- [x] Self-RAG, Adaptive-RAG, CRAG, and FLARE source mechanisms audited.
- [x] Exact-paper-name overclaim rejected.
- [x] Primary and infrastructure comparators selected.

## Setup

- [x] PLAN.md written before the real run.
- [x] Metric-contract JSON written.
- [x] Dedicated frozen config created.
- [x] Config hash and output non-existence recorded:
  `D456B238A5147D7CBA14F72B94A8813F6E92FE6C870FE62F84E7983C471991D2`.
- [x] Focused smoke/tests pass: `27 passed`.
- [x] No concurrent experiment process.

## Execution

- [x] Run all 45 cases for `fixed_k`.
- [x] Run all 45 cases for `prompt_verifier`.
- [x] Run all 45 cases for `agentic_rag_baseline`.
- [x] Confirm 135 unique method/sample keys, zero skipped, no lock.

## Verification

- [x] Verify complete finite metrics and evaluator identity.
- [x] Compare primary baseline to the adapter-only repeat aggregate.
- [x] Report method-inherent cost differences.
- [x] Classify feasibility and downstream trust.
- [x] Write verification report and explicit phase-3 route decision.
- [x] Do not compare targeted45 numbers directly with published splits.
