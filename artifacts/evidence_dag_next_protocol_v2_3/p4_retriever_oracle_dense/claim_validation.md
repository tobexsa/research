# P4 Claim Validation

| Claim | Gate | Observed | Verdict |
|---|---:|---:|---|
| Gold-query target retrieval is adequate | Recall@10 >=75% | 182/200 (91.0%) | supported |
| Complete multi-step retrieval is adequate | All-Steps Recall >=60% | 44/60 (73.3%) | supported |
| Retriever has no timeout loss | timeout = 0 | 0/200 | supported |
| Merge retrieval is uniformly solved | descriptive | 21/30 (70.0%) joint recall | partial |

The result supports only a teacher-forced Gold-query retriever upper bound. It does not rescue failed Planner, relation, span, binding, or generated-query routes.
