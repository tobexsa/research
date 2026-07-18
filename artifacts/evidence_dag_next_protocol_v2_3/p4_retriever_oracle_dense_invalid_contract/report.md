# V2.3 P4 Retriever Oracle Gate

Gold queries are teacher-forced from Gold decomposition questions and prior Gold answers. No Planner output, Gold passage text, or Confirmation sample enters query construction.

| Metric | Result | Gate |
|---|---:|---:|
| Step Recall@10 | 9/200 (4.5%) | >=75% |
| All-Steps Recall | 1/60 (1.7%) | >=60% |
| Timeout | 0/200 | 0 |
| Merge Joint Recall | 1/30 (3.3%) | Dev descriptive freeze |

Overall gate passed: **false**. MRR@10: **0.0297**.

The target retriever is the repository's frozen BGE-base-en-v1.5 FAISS dense configuration at top-k 10.
