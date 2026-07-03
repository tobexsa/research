# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_no_think

## Run Shape
- total records: 45
- paired samples with both methods: 0

## claim_risk
- count: 45
- mean_f1: 0.321962
- median_f1: 0.000000
- f1_zero: 27 (60.0%)
- f1_positive: 18 (40.0%)
- f1_ge_0_5: 16 (35.6%)
- final_action_counts: {'answer': 27, 'abstain': 18}
- retrieval_call_counts: {1: 12, 2: 27, 3: 6}
- trajectory_round_counts: {1: 12, 2: 27, 3: 6}

## Pairwise Comparison
- agentic_rag_baseline wins: 0
- agentic_rag_baseline losses: 0
- ties: 0
- agentic_rag_baseline answer / prompt abstain: 0
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 0
- both abstain: 0

## Cases: agentic_rag_baseline wins over prompt_verifier

## Cases: agentic_rag_baseline loses to prompt_verifier

## Cases: agentic_rag_baseline no-new-evidence abstentions
