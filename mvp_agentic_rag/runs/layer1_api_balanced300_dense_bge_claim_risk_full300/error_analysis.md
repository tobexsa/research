# Error Analysis: layer1_api_balanced300_dense_bge_claim_risk_full300

## Run Shape
- total records: 900
- paired samples with both methods: 300

## claim_risk
- count: 300
- mean_f1: 0.122239
- median_f1: 0.000000
- f1_zero: 253 (84.3%)
- f1_positive: 47 (15.7%)
- f1_ge_0_5: 39 (13.0%)
- final_action_counts: {'answer': 60, 'abstain': 240}
- retrieval_call_counts: {1: 66, 2: 234}
- trajectory_round_counts: {1: 66, 2: 234}

## ours
- count: 300
- mean_f1: 0.118622
- median_f1: 0.000000
- f1_zero: 253 (84.3%)
- f1_positive: 47 (15.7%)
- f1_ge_0_5: 39 (13.0%)
- final_action_counts: {'answer': 66, 'abstain': 234}
- retrieval_call_counts: {1: 64, 2: 6, 3: 230}
- trajectory_round_counts: {1: 64, 2: 6, 3: 230}

## prompt_verifier
- count: 300
- mean_f1: 0.118289
- median_f1: 0.000000
- f1_zero: 254 (84.7%)
- f1_positive: 46 (15.3%)
- f1_ge_0_5: 38 (12.7%)
- final_action_counts: {'answer': 63, 'abstain': 237}
- retrieval_call_counts: {1: 300}
- trajectory_round_counts: {1: 300}

## Pairwise Comparison
- ours wins: 3
- ours losses: 5
- ties: 292
- ours answer / prompt abstain: 6
- ours abstain / prompt answer: 3
- both answer: 60
- both abstain: 231

## Ours Retrieval Behavior
- extra_retrieval_records: 236 (78.7%)
- no_new_evidence_records: 236 (78.7%)
- no_new_evidence_and_abstain: 234
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.005234
- mean_f1_without_no_new_evidence: 0.536740

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 69, 'True': 697}
- overall_sufficiency_counts_by_step: {'sufficient': 69, 'insufficient': 692, 'unclear': 5}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 697
- suggested_query_empty_steps: 69

## Cases: Ours wins over prompt_verifier
1. id=2hop__20268_42014
   - question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
   - gold: 2
   - ours: action=answer f1=1.000 calls=2 answer=2
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
2. id=3hop1__617062_127905_54974
   - question: What is the farthest home run ever hit in the league where the team that Jim Wilson plays for?
   - gold: about 575 feet
   - ours: action=answer f1=0.571 calls=1 answer=575 feet (175 m)
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=
3. id=3hop1__103751_24918_24991
   - question: What went down after the Soviet President visiting the country of origin of Ethella Chupryk while the protests were taking place departed from the Kremlin?
   - gold: Soviet flag
   - ours: action=answer f1=0.235 calls=3 answer=The Soviet flag was lowered for the last time, and the Russian tricolor was raised in its place.
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours loses to prompt_verifier
1. id=3hop1__695430_831637_91775
   - question: What does SEAL stand for in the military group that is part of the branch that operates the USS Chillicothe?
   - gold: Sea, Air, and Land
   - ours: action=abstain f1=0.000 calls=2 answer=
   - prompt: action=answer f1=1.000 calls=1 answer=Sea, Air, and Land
   - ours_last: round=2 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Does the USS Chillicothe operate under the branch of the military that includes the SEALs?
2. id=2hop__5658_25002
   - question: How long did the pact last between Kravchuk and the person who signed the decree suspending the Communist Party of the Russian SFSR?
   - gold: 10-year
   - ours: action=answer f1=0.667 calls=1 answer=10-year bilateral pact
   - prompt: action=answer f1=1.000 calls=1 answer=10-year
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
3. id=4hop1__88342_49853_128008_89859
   - question: When does the regular season of the league where the team with the most titles from the series after which the MLB MVP award is given out plays?
   - gold: March 29, 2018
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.200 calls=1 answer=late March / early April to late September / early October
   - ours_last: round=3 evidence_gain=0.0 suff=unclear need_more=True risk=0.0 suggested=Which team has the most titles from the series after which the MLB MVP award is given out, and what are the regular s...
4. id=3hop2__92991_27069_76291
   - question: When did the party Oklahoma's US Senators come from take control of the body determining the rules of the US House and US Senate?
   - gold: January 2015
   - ours: action=answer f1=0.667 calls=1 answer=2015
   - prompt: action=answer f1=0.800 calls=1 answer=January 3, 2015
   - ours_last: round=1 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__370564_71701
   - question: What year did the japanese get to the current administrative territorial entity of the Century Lotus Stadium and the rest of the guangdong province?
   - gold: November 5
   - ours: action=answer f1=0.042 calls=1 answer=2005 is not the correct answer based on the provided evidence. The correct year when the Japanese got to the Century Lotus Stadium and the rest of Guangdong province is 1941 (ba...
   - prompt: action=answer f1=0.082 calls=1 answer=2005 is not the correct answer based on the provided evidence. The correct year when the Japanese got to the Century Lotus Stadium and the rest of Guangdong province is 1941 (ba...
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Identify the specific individuals or entities from whom the Huguenots in the state encompassing Zubly Cemetery purcha...
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
7. id=2hop__249867_557232
   - question: Which country is the Desert Forest Golf Club located in?
   - gold: Maricopa County
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.000 calls=1 answer=UNKNOWN
   - ours_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
8. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find a show named after a Politically Incorrect cast member and its new season premiere date.
9. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the administrative territorial entity that includes the location of The Judd School?
10. id=2hop__341176_711757
   - question: What other district is found in the same county as Gmina Stężyca?
   - gold: Gmina Ryki
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find another district in Ryki County, Lublin Voivodeship, Poland
