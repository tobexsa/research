# Error Analysis: layer1_api_balanced300_dense_bge_claim_risk_subset30

## Run Shape
- total records: 90
- paired samples with both methods: 30

## claim_risk
- count: 30
- mean_f1: 0.344444
- median_f1: 0.000000
- f1_zero: 17 (56.7%)
- f1_positive: 13 (43.3%)
- f1_ge_0_5: 12 (40.0%)
- final_action_counts: {'abstain': 16, 'answer': 14}
- retrieval_call_counts: {1: 18, 2: 12}
- trajectory_round_counts: {1: 18, 2: 12}

## ours
- count: 30
- mean_f1: 0.361111
- median_f1: 0.000000
- f1_zero: 16 (53.3%)
- f1_positive: 14 (46.7%)
- f1_ge_0_5: 13 (43.3%)
- final_action_counts: {'answer': 18, 'abstain': 12}
- retrieval_call_counts: {1: 17, 2: 1, 3: 12}
- trajectory_round_counts: {1: 17, 2: 1, 3: 12}

## prompt_verifier
- count: 30
- mean_f1: 0.311111
- median_f1: 0.000000
- f1_zero: 18 (60.0%)
- f1_positive: 12 (40.0%)
- f1_ge_0_5: 11 (36.7%)
- final_action_counts: {'answer': 17, 'abstain': 13}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- ours wins: 3
- ours losses: 1
- ties: 26
- ours answer / prompt abstain: 1
- ours abstain / prompt answer: 0
- both answer: 17
- both abstain: 12

## Ours Retrieval Behavior
- extra_retrieval_records: 13 (43.3%)
- no_new_evidence_records: 13 (43.3%)
- no_new_evidence_and_abstain: 12
- no_new_evidence_and_answer: 1
- mean_f1_with_no_new_evidence: 0.051282
- mean_f1_without_no_new_evidence: 0.598039

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 19, 'True': 36}
- overall_sufficiency_counts_by_step: {'sufficient': 19, 'insufficient': 36}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 36
- suggested_query_empty_steps: 19

## Cases: Ours wins over prompt_verifier
1. id=2hop__20268_42014
   - question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
   - gold: 2
   - ours: action=answer f1=1.000 calls=1 answer=2
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__10620_49084
   - question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
   - gold: Liam Thomas Garrigan
   - ours: action=answer f1=0.800 calls=1 answer=Liam Garrigan
   - prompt: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - ours_last: round=1 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__370564_71701
   - question: What year did the japanese get to the current administrative territorial entity of the Century Lotus Stadium and the rest of the guangdong province?
   - gold: November 5
   - ours: action=answer f1=0.033 calls=1 answer=2005 is not the correct answer based on the provided evidence. The correct year when the Japanese got to the Century Lotus Stadium and the rest of Guangdong province is related ...
   - prompt: action=answer f1=0.000 calls=1 answer=1938
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours loses to prompt_verifier
1. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - ours: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - prompt: action=answer f1=0.333 calls=1 answer=Metal Mickey
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

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
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the participant in The Listening Sessions and what is the identity of the 'guy' in the One Last Time video?
5. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What movement does Robert Mills, the creator of the Washington Monument, belong to?
6. id=2hop__247353_55227
   - question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
   - gold: Maria Bello
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the wife of Here Comes the Boom's screenwriter in the movie Grown Ups?
7. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find a show named after a Politically Incorrect cast member and its new season premiere date.
8. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What administrative territorial entity includes the place where Bill Cockcroft was educated?
