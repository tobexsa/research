# Error Analysis: layer1_local_qwen3_14b_int4_pilot_subset5_no_think_agentic_rag_baseline

## Run Shape
- total records: 10
- paired samples with both methods: 5

## agentic_rag_baseline
- count: 5
- mean_f1: 0.360000
- median_f1: 0.000000
- f1_zero: 3 (60.0%)
- f1_positive: 2 (40.0%)
- f1_ge_0_5: 2 (40.0%)
- final_action_counts: {'answer': 3, 'abstain': 2}
- retrieval_call_counts: {1: 2, 2: 1, 3: 2}
- trajectory_round_counts: {1: 2, 2: 1, 3: 2}

## prompt_verifier
- count: 5
- mean_f1: 0.200000
- median_f1: 0.000000
- f1_zero: 4 (80.0%)
- f1_positive: 1 (20.0%)
- f1_ge_0_5: 1 (20.0%)
- final_action_counts: {'abstain': 3, 'answer': 2}
- retrieval_call_counts: {1: 5}
- trajectory_round_counts: {1: 5}

## Pairwise Comparison
- agentic_rag_baseline wins: 1
- agentic_rag_baseline losses: 0
- ties: 4
- agentic_rag_baseline answer / prompt abstain: 1
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 2
- both abstain: 2

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 3 (60.0%)
- no_new_evidence_records: 3 (60.0%)
- no_new_evidence_and_abstain: 2
- no_new_evidence_and_answer: 1
- mean_f1_with_no_new_evidence: 0.266667
- mean_f1_without_no_new_evidence: 0.500000

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 7, 'False': 3}
- overall_sufficiency_counts_by_step: {'insufficient': 7, 'sufficient': 3}
- risk_score_mean: 0.075000
- risk_score_max: 0.750000
- suggested_query_nonempty_steps: 7
- suggested_query_empty_steps: 3

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__10620_49084
   - question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
   - gold: Liam Thomas Garrigan
   - agentic_rag_baseline: action=answer f1=0.800 calls=2 answer=Liam Garrigan
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline loses to prompt_verifier

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the historical record of land purchases by Huguenots in the area encompassing Zubly Cemetery, South Carolina?
2. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is Mohammed Atta's connection to the Datsun Type 12 or Nissan?
