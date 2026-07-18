# G0 Holdout Feasibility Audit

Actual reserved level: **Compositional**.

## Feasibility search

| Level | Feasible | Minimum topology count | Total selected | Bounded search |
|---|---:|---:|---:|---|
| Strict | no | 1 | 61 | 200 deterministic greedy trials |
| Compositional | yes | 12 | 72 | 200 deterministic greedy trials |
| Lexical | yes | 12 | 72 | 200 deterministic greedy trials |

A and B each reserve 6 samples per topology (36 total). Strict non-feasibility is a bounded construction result, not a mathematical impossibility proof.

## Pairwise overlap totals

| Field | Pairwise overlap count |
|---|---:|
| answer_entity | 56 |
| base_subquestion_id | 174 |
| complete_decomposition | 0 |
| normalized_question_near_duplicate | 2 |
| sample_id | 0 |
| source_passage | 0 |

Detailed pairwise counts and examples are in `holdout_overlap_ledger.csv`. Answer-entity overlap is reported rather than silently treated as prohibited. Confirmation-120 was read only for exclusion/audit and was not sent to any model.
