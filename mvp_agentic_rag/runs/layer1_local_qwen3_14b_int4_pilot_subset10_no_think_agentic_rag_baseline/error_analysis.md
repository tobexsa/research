# Error Analysis: layer1_local_qwen3_14b_int4_pilot_subset10_no_think_agentic_rag_baseline

## Run Shape
- total records: 20
- paired samples with both methods: 10

## agentic_rag_baseline
- count: 10
- mean_f1: 0.496667
- median_f1: 0.583333
- f1_zero: 4 (40.0%)
- f1_positive: 6 (60.0%)
- f1_ge_0_5: 6 (60.0%)
- final_action_counts: {'answer': 7, 'abstain': 3}
- retrieval_call_counts: {1: 6, 2: 1, 3: 3}
- trajectory_round_counts: {1: 6, 2: 1, 3: 3}

## prompt_verifier
- count: 10
- mean_f1: 0.416667
- median_f1: 0.250000
- f1_zero: 5 (50.0%)
- f1_positive: 5 (50.0%)
- f1_ge_0_5: 5 (50.0%)
- final_action_counts: {'abstain': 4, 'answer': 6}
- retrieval_call_counts: {1: 10}
- trajectory_round_counts: {1: 10}

## Pairwise Comparison
- agentic_rag_baseline wins: 1
- agentic_rag_baseline losses: 0
- ties: 9
- agentic_rag_baseline answer / prompt abstain: 1
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 6
- both abstain: 3

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 4 (40.0%)
- no_new_evidence_records: 4 (40.0%)
- no_new_evidence_and_abstain: 3
- no_new_evidence_and_answer: 1
- mean_f1_with_no_new_evidence: 0.200000
- mean_f1_without_no_new_evidence: 0.694444

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 10, 'False': 7}
- overall_sufficiency_counts_by_step: {'insufficient': 10, 'sufficient': 7}
- risk_score_mean: 0.132353
- risk_score_max: 0.750000
- suggested_query_nonempty_steps: 10
- suggested_query_empty_steps: 7

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
3. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the name of a television show named after the character featured in the video game Mickey's Safari in Letterl...
