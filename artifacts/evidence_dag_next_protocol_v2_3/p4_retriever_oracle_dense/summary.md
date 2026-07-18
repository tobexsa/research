# P4 Retriever Oracle Summary

The corrected, contract-matched BGE dense retriever passed the V2.3 Oracle gate: Recall@10 91.0%, All-Steps Recall 73.3%, timeout 0, MRR@10 0.6658. Performance is weakest on 4hop1/4hop2 All-Steps Recall (both 50%), so retrieval still contributes multi-step loss but is not the primary reason the Planner pipeline is unusable.

An earlier 9/200 run was invalidated because its old index contained only 11/200 Gold targets. It is retained separately with a data-contract incident; it is excluded from all final metrics.

Next action: run the zero-LLM R0 Oracle Engine attribution slice once, then stop remaining model-dependent P5 routes because their Planner/Span/strong-model prerequisites are unmet.
