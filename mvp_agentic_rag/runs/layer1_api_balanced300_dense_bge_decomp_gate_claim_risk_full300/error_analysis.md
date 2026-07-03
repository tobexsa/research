# Error Analysis: layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_full300

## Run Shape
- total records: 900
- paired samples with both methods: 300

## claim_risk
- count: 300
- mean_f1: 0.223532
- median_f1: 0.000000
- f1_zero: 219 (73.0%)
- f1_positive: 81 (27.0%)
- f1_ge_0_5: 72 (24.0%)
- final_action_counts: {'abstain': 203, 'answer': 97}
- retrieval_call_counts: {1: 67, 2: 71, 3: 162}
- trajectory_round_counts: {1: 67, 2: 71, 3: 162}

## ours
- count: 300
- mean_f1: 0.217057
- median_f1: 0.000000
- f1_zero: 222 (74.0%)
- f1_positive: 78 (26.0%)
- f1_ge_0_5: 70 (23.3%)
- final_action_counts: {'answer': 114, 'abstain': 186}
- retrieval_call_counts: {1: 65, 2: 43, 3: 192}
- trajectory_round_counts: {1: 65, 2: 43, 3: 192}

## prompt_verifier
- count: 300
- mean_f1: 0.123239
- median_f1: 0.000000
- f1_zero: 254 (84.7%)
- f1_positive: 46 (15.3%)
- f1_ge_0_5: 39 (13.0%)
- final_action_counts: {'answer': 71, 'abstain': 229}
- retrieval_call_counts: {1: 300}
- trajectory_round_counts: {1: 300}

## Pairwise Comparison
- ours wins: 35
- ours losses: 2
- ties: 263
- ours answer / prompt abstain: 47
- ours abstain / prompt answer: 4
- both answer: 67
- both abstain: 182

## Ours Retrieval Behavior
- extra_retrieval_records: 235 (78.3%)
- no_new_evidence_records: 201 (67.0%)
- no_new_evidence_and_abstain: 183
- no_new_evidence_and_answer: 18
- mean_f1_with_no_new_evidence: 0.031620
- mean_f1_without_no_new_evidence: 0.593552

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 118, 'True': 609}
- overall_sufficiency_counts_by_step: {'sufficient': 117, 'insufficient': 603, 'unclear': 7}
- risk_score_mean: 0.003301
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 610
- suggested_query_empty_steps: 117

## Cases: Ours wins over prompt_verifier
1. id=2hop__194469_83289
   - question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
   - gold: Matt Bennett
   - ours: action=answer f1=1.000 calls=1 answer=Matt Bennett
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - ours: action=answer f1=1.000 calls=2 answer=Sir Robert Peel, 1st Baronet
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - ours: action=answer f1=1.000 calls=2 answer=Maria Shriver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
4. id=2hop__341176_711757
   - question: What other district is found in the same county as Gmina Stężyca?
   - gold: Gmina Ryki
   - ours: action=answer f1=1.000 calls=2 answer=Gmina Ryki
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__351045_47134
   - question: What is the mascot of the operator of RV Wecoma?
   - gold: Benny Beaver
   - ours: action=answer f1=1.000 calls=2 answer=Benny Beaver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
6. id=2hop__446324_620302
   - question: The author of Elizabeth and After attended which university?
   - gold: University of Toronto
   - ours: action=answer f1=1.000 calls=2 answer=University of Toronto
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
7. id=2hop__622637_120171
   - question: What year did the company that published Starship Command end?
   - gold: 1986
   - ours: action=answer f1=1.000 calls=2 answer=1986
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
8. id=2hop__645448_77615
   - question: When did military instruction start at the place where Larry Alcala was educated?
   - gold: 1912
   - ours: action=answer f1=1.000 calls=1 answer=1912
   - prompt: action=answer f1=0.000 calls=1 answer=1922
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
9. id=2hop__677929_696450
   - question: Who founded the publisher of The Final Testament of the Holy Bible?
   - gold: Larry Gagosian
   - ours: action=answer f1=1.000 calls=2 answer=Larry Gagosian
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
10. id=2hop__728969_131890
   - question: Which is the body of water near George Mills' place of birth?
   - gold: River Thames
   - ours: action=answer f1=1.000 calls=2 answer=River Thames
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours loses to prompt_verifier
1. id=3hop1__145194_160545_62931
   - question: The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?
   - gold: island Koh Phi Phi
   - ours: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - prompt: action=answer f1=0.857 calls=1 answer=Thai island Koh Phi Phi
   - ours_last: round=1 evidence_gain=0.6666666666666666 suff=sufficient need_more=False risk=0.0 suggested=
2. id=3hop2__91678_90098_10557
   - question: What was the form of the language that the last name Sylvester comes from, used in the era of the first Holy Roman Emperor, later known as?
   - gold: Medieval Latin
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.667 calls=1 answer=Latin
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What was the form of the language used during the era of the first Holy Roman Emperor and how did it relate to the sp...

## Cases: Ours no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Identify the original landowner from whom the Huguenots purchased land in the area of Zubly Cemetery.
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
4. id=2hop__167577_31122
   - question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
   - gold: 18th
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__20268_42014
   - question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
   - gold: 2
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=How many members of the Scottish Government were in the seats of the Scottish Parliament when the Directory of Public...
6. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What movement or political affiliation did Robert Mills, the creator of the Washington Monument, belong to?
7. id=2hop__247353_55227
   - question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
   - gold: Maria Bello
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the wife of Here Comes the Boom's screenwriter in the movie Grown Ups?
8. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find a show named for a Politically Incorrect cast member and its new season premiere date.
9. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find evidence about a football star who backed out of signing with Barcelona due to a relay controversy.
10. id=2hop__37656_36240
   - question: What specific part of the document that is the highest authority in Protestantism for morals reference Mary?
   - gold: Genesis 3:15
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - ours_last: round=3 evidence_gain=0.5 suff=insufficient need_more=True risk=0.0 suggested=Find specific references to Mary in the Bible as the highest authority in Protestantism for morals.
