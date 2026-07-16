# Source And Local-Mechanism Audit

Date: 2026-07-15

| Candidate | Primary source | Defining mechanism | Exact matched reproduction? | Route |
|---|---|---|---|---|
| FLARE | arXiv:2305.06983 | Upcoming-sentence prediction and low-confidence-token active retrieval | No: short-answer/API logprob mismatch | reject exact reproduction |
| Self-RAG | arXiv:2310.11511 | Trained reflection-token LM retrieves and critiques on demand | No: requires a specialized model, violating fixed Qwen3 backend | reject exact reproduction |
| CRAG | arXiv:2401.15884 | Retrieval evaluator, corrective actions, web search, decompose/recompose | No: full method violates fixed corpus | reject exact reproduction |
| Adaptive-RAG | arXiv:2403.14403 | Trained question-complexity classifier selects no/single/iterative retrieval | No: trained classifier is unavailable and cannot be silently replaced | reject exact reproduction |
| Local verifier-guided adaptive RAG | repository `agentic_rag_baseline_agent.py` | Iterative retrieve/generate/verify; verifier and evidence gain decide answer, refine, or abstain under three rounds | Yes for the local named mechanism; a closed-corpus CRAG-style corrective-core approximation, not full CRAG | primary matched comparator |
| Local prompt verifier | repository `prompt_verifier_agent.py` | One retrieval/generation plus verifier answer/abstain | Yes | secondary infrastructure comparator |
| Local fixed budget RAG | repository `fixed_k_agent.py` | Three fixed retrieval rounds then answer | Yes | secondary infrastructure comparator |

The local primary comparator may be described as a modern-pattern adaptive or
agentic RAG baseline. It must not be described as an implementation or
reproduction of any rejected exact paper method.
