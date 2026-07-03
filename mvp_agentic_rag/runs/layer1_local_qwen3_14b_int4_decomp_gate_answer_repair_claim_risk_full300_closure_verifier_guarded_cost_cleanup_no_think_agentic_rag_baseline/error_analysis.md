# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline

## Run Shape
- total records: 900
- paired samples with both methods: 300

## agentic_rag_baseline
- count: 300
- mean_f1: 0.205312
- median_f1: 0.000000
- f1_zero: 225 (75.0%)
- f1_positive: 75 (25.0%)
- f1_ge_0_5: 66 (22.0%)
- final_action_counts: {'abstain': 178, 'answer': 122}
- retrieval_call_counts: {1: 58, 2: 50, 3: 192}
- trajectory_round_counts: {1: 58, 2: 50, 3: 192}

## claim_risk
- count: 300
- mean_f1: 0.243961
- median_f1: 0.000000
- f1_zero: 209 (69.7%)
- f1_positive: 91 (30.3%)
- f1_ge_0_5: 80 (26.7%)
- final_action_counts: {'abstain': 157, 'answer': 143}
- retrieval_call_counts: {1: 67, 2: 138, 3: 95}
- trajectory_round_counts: {1: 67, 2: 138, 3: 95}

## prompt_verifier
- count: 300
- mean_f1: 0.092413
- median_f1: 0.000000
- f1_zero: 265 (88.3%)
- f1_positive: 35 (11.7%)
- f1_ge_0_5: 30 (10.0%)
- final_action_counts: {'abstain': 243, 'answer': 57}
- retrieval_call_counts: {1: 300}
- trajectory_round_counts: {1: 300}

## Pairwise Comparison
- agentic_rag_baseline wins: 40
- agentic_rag_baseline losses: 0
- ties: 260
- agentic_rag_baseline answer / prompt abstain: 65
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 57
- both abstain: 178

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 242 (80.7%)
- no_new_evidence_records: 188 (62.7%)
- no_new_evidence_and_abstain: 171
- no_new_evidence_and_answer: 17
- mean_f1_with_no_new_evidence: 0.036086
- mean_f1_without_no_new_evidence: 0.489371

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 599, 'False': 135}
- overall_sufficiency_counts_by_step: {'insufficient': 572, 'sufficient': 122, 'conflicting': 33, 'unclear': 7}
- risk_score_mean: 0.393120
- risk_score_max: 1.000000
- suggested_query_nonempty_steps: 601
- suggested_query_empty_steps: 133

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__194469_83289
   - question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
   - gold: Matt Bennett
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Matt Bennett
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Sir Robert Peel, 1st Baronet
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Maria Shriver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
4. id=2hop__341176_711757
   - question: What other district is found in the same county as Gmina Stężyca?
   - gold: Gmina Ryki
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Gmina Ryki
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__351045_47134
   - question: What is the mascot of the operator of RV Wecoma?
   - gold: Benny Beaver
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Benny Beaver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
6. id=2hop__424294_19033
   - question: Where did the author of A Lion's Tale: Around the World in Spandex win in 2008?
   - gold: Great American Bash
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Great American Bash
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
7. id=2hop__446324_620302
   - question: The author of Elizabeth and After attended which university?
   - gold: University of Toronto
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=University of Toronto
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
8. id=2hop__472486_97805
   - question: Which war did the operator of the Fabian Wrede-class training ship serve in?
   - gold: Winter War
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Winter War
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
9. id=2hop__547045_131879
   - question: What body of water is by the headquarters location of Wipac?
   - gold: River Great Ouse
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=River Great Ouse
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
10. id=2hop__622637_120171
   - question: What year did the company that published Starship Command end?
   - gold: 1986
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=1986
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline loses to prompt_verifier

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__10620_49084
   - question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
   - gold: Liam Thomas Garrigan
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Which legendary figure from Historia Regum Britanniae is portrayed by Liam Garrigan in Once Upon a Time?
2. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is Mohammed Atta's association with the Datsun Type 12 or its manufacturer?
3. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the name of the television show that was named after a character from Mickey's Safari in Letterland?
4. id=2hop__167577_31122
   - question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
   - gold: 18th
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What were the birth and death years of George Berkeley?
5. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What movement was Robert Mills associated with?
6. id=2hop__370564_71701
   - question: What year did the japanese get to the current administrative territorial entity of the Century Lotus Stadium and the rest of the guangdong province?
   - gold: November 5
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.8 suggested=What was the exact year when Japan completed its control over Guangdong province, including Foshan where the Century ...
7. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=conflicting need_more=True risk=0.5 suggested=Who is the football star who backed out of the 2008 Summer Olympics torch relay and was signed by Barcelona?
8. id=2hop__39063_593388
   - question: Who is the father of the person who came up with the concept of the "new" police?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.75 suggested=Who is the person who came up with the concept of the 'new' police?
9. id=2hop__46550_85990
   - question: Who were the leaders of the opposition of the party that controlled the house of representatives in 2002?
   - gold: anti-slavery activists, modernizers, ex Whigs and ex Free Soilers
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.75 suggested=Who was the Minority Leader of the United States House of Representatives in 2002?
10. id=2hop__496792_392646
   - question: A participant of the Battle of Brechin is an instance of?
   - gold: Scottish clan
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the classification of a participant in a battle such as the Battle of Brechin?
