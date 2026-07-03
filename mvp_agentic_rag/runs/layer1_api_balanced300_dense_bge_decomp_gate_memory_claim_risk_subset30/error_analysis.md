# Error Analysis: layer1_api_balanced300_dense_bge_decomp_gate_memory_claim_risk_subset30

## Run Shape
- total records: 90
- paired samples with both methods: 30

## claim_risk
- count: 30
- mean_f1: 0.448889
- median_f1: 0.416667
- f1_zero: 14 (46.7%)
- f1_positive: 16 (53.3%)
- f1_ge_0_5: 15 (50.0%)
- final_action_counts: {'abstain': 11, 'answer': 19}
- retrieval_call_counts: {1: 15, 2: 9, 3: 6}
- trajectory_round_counts: {1: 15, 2: 9, 3: 6}

## ours
- count: 30
- mean_f1: 0.471111
- median_f1: 0.500000
- f1_zero: 14 (46.7%)
- f1_positive: 16 (53.3%)
- f1_ge_0_5: 16 (53.3%)
- final_action_counts: {'answer': 21, 'abstain': 9}
- retrieval_call_counts: {1: 16, 2: 5, 3: 9}
- trajectory_round_counts: {1: 16, 2: 5, 3: 9}

## prompt_verifier
- count: 30
- mean_f1: 0.348889
- median_f1: 0.000000
- f1_zero: 17 (56.7%)
- f1_positive: 13 (43.3%)
- f1_ge_0_5: 12 (40.0%)
- final_action_counts: {'answer': 17, 'abstain': 13}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- ours wins: 4
- ours losses: 1
- ties: 25
- ours answer / prompt abstain: 5
- ours abstain / prompt answer: 1
- both answer: 16
- both abstain: 8

## Ours Retrieval Behavior
- extra_retrieval_records: 14 (46.7%)
- no_new_evidence_records: 10 (33.3%)
- no_new_evidence_and_abstain: 9
- no_new_evidence_and_answer: 1
- mean_f1_with_no_new_evidence: 0.000000
- mean_f1_without_no_new_evidence: 0.706667

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 23, 'True': 30}
- overall_sufficiency_counts_by_step: {'sufficient': 23, 'insufficient': 30}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 30
- suggested_query_empty_steps: 23

## Cases: Ours wins over prompt_verifier
1. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - ours: action=answer f1=1.000 calls=2 answer=Sir Robert Peel, 1st Baronet
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - ours: action=answer f1=1.000 calls=2 answer=Maria Shriver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__341176_711757
   - question: What other district is found in the same county as Gmina Stężyca?
   - gold: Gmina Ryki
   - ours: action=answer f1=1.000 calls=2 answer=Gmina Ryki
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
4. id=2hop__351045_47134
   - question: What is the mascot of the operator of RV Wecoma?
   - gold: Benny Beaver
   - ours: action=answer f1=1.000 calls=2 answer=Benny Beaver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=

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
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who did the Huguenots in Aiken County, South Carolina purchase land from to establish the area around Zubly Cemetery?
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
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Does Mohammed Atta own or have any connection to a Datsun model or Nissan?
4. id=2hop__167577_31122
   - question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
   - gold: 18th
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.000 calls=1 answer=18世纪
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What century did George Berkeley, the author of A Treatise Concerning the Principles of Human Knowledge, live in?
5. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What political or ideological movement did Robert Mills, the creator of the Washington Monument, belong to?
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
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What administrative territorial entity includes the location of The Judd School and the University of South Bank wher...
9. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find evidence about a football star who backed out of signing with Barcelona due to a relay controversy.
