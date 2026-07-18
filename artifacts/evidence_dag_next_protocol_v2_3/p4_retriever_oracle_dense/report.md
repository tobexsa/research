# V2.3 P4 Retriever Oracle Gate

Gold queries are teacher-forced from Gold decomposition questions and prior Gold answers. No Planner output, Gold passage text, or Confirmation sample enters query construction.

| Metric | Result | Gate |
|---|---:|---:|
| Step Recall@10 | 182/200 (91.0%) | >=75% |
| All-Steps Recall | 44/60 (73.3%) | >=60% |
| Timeout | 0/200 | 0 |
| Merge Joint Recall | 21/30 (70.0%) | Dev descriptive freeze |

Overall gate passed: **true**. MRR@10: **0.6658**.

The target retriever is the repository's frozen BGE-base-en-v1.5 FAISS dense configuration at top-k 10.
