# Error Analysis: layer1_api_balanced300_dense_bge_short_answer_subset10

## Run Shape
- total records: 20
- paired samples with both methods: 10

## ours
- count: 10
- mean_f1: 0.296667
- median_f1: 0.000000
- f1_zero: 6 (60.0%)
- f1_positive: 4 (40.0%)
- f1_ge_0_5: 4 (40.0%)
- final_action_counts: {'answer': 6, 'abstain': 4}
- retrieval_call_counts: {1: 6, 3: 4}
- trajectory_round_counts: {1: 6, 3: 4}

## prompt_verifier
- count: 10
- mean_f1: 0.296667
- median_f1: 0.000000
- f1_zero: 6 (60.0%)
- f1_positive: 4 (40.0%)
- f1_ge_0_5: 4 (40.0%)
- final_action_counts: {'answer': 6, 'abstain': 4}
- retrieval_call_counts: {1: 10}
- trajectory_round_counts: {1: 10}

## Pairwise Comparison
- ours wins: 0
- ours losses: 0
- ties: 10
- ours answer / prompt abstain: 0
- ours abstain / prompt answer: 0
- both answer: 6
- both abstain: 4

## Ours Retrieval Behavior
- extra_retrieval_records: 4 (40.0%)
- no_new_evidence_records: 4 (40.0%)
- no_new_evidence_and_abstain: 4
- no_new_evidence_and_answer: 0
- mean_f1_with_no_new_evidence: 0.000000
- mean_f1_without_no_new_evidence: 0.494444

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 6, 'True': 12}
- overall_sufficiency_counts_by_step: {'sufficient': 6, 'insufficient': 12}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 12
- suggested_query_empty_steps: 6

## Cases: Ours wins over prompt_verifier

## Cases: Ours loses to prompt_verifier

## Cases: Ours no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who did the Huguenots in South Carolina purchase land from to establish the area around Zubly Cemetery?
2. id=2hop__131951_643670
   - question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
   - gold: Het Scheur
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the name of the mouth of the watercourse by Rotterdam Centrum?
3. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Does Mohammed Atta own or possess a Datsun model?
4. id=2hop__194469_83289
   - question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
   - gold: Matt Bennett
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the participant in The Listening Sessions and what is their connection to the 'guy' in the One Last Time video?
