# Error Analysis: layer1_api_balanced300_oracle_claim_risk_subset30

## Run Shape
- total records: 90
- paired samples with both methods: 30

## claim_risk
- count: 30
- mean_f1: 0.526366
- median_f1: 0.666667
- f1_zero: 12 (40.0%)
- f1_positive: 18 (60.0%)
- f1_ge_0_5: 17 (56.7%)
- final_action_counts: {'abstain': 8, 'answer': 22}
- retrieval_call_counts: {1: 24, 2: 6}
- trajectory_round_counts: {1: 24, 2: 6}

## ours
- count: 30
- mean_f1: 0.586366
- median_f1: 0.733333
- f1_zero: 10 (33.3%)
- f1_positive: 20 (66.7%)
- f1_ge_0_5: 19 (63.3%)
- final_action_counts: {'answer': 24, 'abstain': 6}
- retrieval_call_counts: {1: 24, 3: 6}
- trajectory_round_counts: {1: 24, 3: 6}

## prompt_verifier
- count: 30
- mean_f1: 0.559700
- median_f1: 0.666667
- f1_zero: 11 (36.7%)
- f1_positive: 19 (63.3%)
- f1_ge_0_5: 18 (60.0%)
- final_action_counts: {'answer': 24, 'abstain': 6}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- ours wins: 1
- ours losses: 0
- ties: 29
- ours answer / prompt abstain: 0
- ours abstain / prompt answer: 0
- both answer: 24
- both abstain: 6

## Ours Retrieval Behavior
- extra_retrieval_records: 6 (20.0%)
- no_new_evidence_records: 6 (20.0%)
- no_new_evidence_and_abstain: 6
- no_new_evidence_and_answer: 0
- mean_f1_with_no_new_evidence: 0.000000
- mean_f1_without_no_new_evidence: 0.732958

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 24, 'True': 18}
- overall_sufficiency_counts_by_step: {'sufficient': 24, 'insufficient': 18}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 18
- suggested_query_empty_steps: 24

## Cases: Ours wins over prompt_verifier
1. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - ours: action=answer f1=0.800 calls=1 answer=Tonbridge, Kent, England
   - prompt: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours loses to prompt_verifier

## Cases: Ours no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who did the Huguenots in Aiken County, South Carolina purchase land from?
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
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What specific model of car did Mohammed Atta have that is made by the company that makes Datsun Type 12?
4. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What show, if any, was named after the character featured in the video game Mickey's Safari in Letterland?
5. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What movement or architectural school did Robert Mills belong to?
6. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find a show named for a Politically Incorrect cast member and its new season release date.
