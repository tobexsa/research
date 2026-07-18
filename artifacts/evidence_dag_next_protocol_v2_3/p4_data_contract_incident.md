# P4 Data-Contract Incident

- status: first P4 run invalidated before interpretation.
- failure type: `data_contract_mismatch`.
- observed misleading metric: 9/200 Recall@10, 1/60 All-Steps Recall.

## Root cause

The initial freeze referenced the older `data/musique_corpus.jsonl` and its 6,000-passage FAISS index. Diagnostic-Dev-60 was constructed from a different frozen corpus at `data/evidence_dag_planner_protocol_v1/retrieval_corpus.jsonl`.

Contract audit:

- Gold targets: 200 unique passages.
- targets in Diagnostic corpus: 200/200.
- targets in old 6,000-passage corpus/index: 11/200.
- Diagnostic corpus IDs represented in old index: 220/3,720.

The run had no fair opportunity to retrieve 189 targets and therefore says nothing about BGE retrieval quality.

## Repair

Build one new FAISS index using the unchanged local BGE snapshot and the exact 3,720-passage Diagnostic corpus. Before rerun, require:

- index metadata count = 3,720;
- corpus/index ID equality;
- Gold target coverage = 200/200;
- new manifest/freeze hashes and a clean-tree Preflight.

Only one corrected rerun is allowed. The invalid raw records remain retained under `p4_retriever_oracle_dense_invalid_contract` and are excluded from final gate metrics.
