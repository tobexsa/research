# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_no_think_agentic_rag_baseline

## Run Shape
- total records: 90
- paired samples with both methods: 30

## agentic_rag_baseline
- count: 30
- mean_f1: 0.516667
- median_f1: 0.583333
- f1_zero: 13 (43.3%)
- f1_positive: 17 (56.7%)
- f1_ge_0_5: 16 (53.3%)
- final_action_counts: {'abstain': 7, 'answer': 23}
- retrieval_call_counts: {1: 15, 2: 7, 3: 8}
- trajectory_round_counts: {1: 15, 2: 7, 3: 8}

## claim_risk
- count: 30
- mean_f1: 0.583333
- median_f1: 1.000000
- f1_zero: 11 (36.7%)
- f1_positive: 19 (63.3%)
- f1_ge_0_5: 18 (60.0%)
- final_action_counts: {'abstain': 6, 'answer': 24}
- retrieval_call_counts: {1: 15, 2: 9, 3: 6}
- trajectory_round_counts: {1: 15, 2: 9, 3: 6}

## prompt_verifier
- count: 30
- mean_f1: 0.327778
- median_f1: 0.000000
- f1_zero: 19 (63.3%)
- f1_positive: 11 (36.7%)
- f1_ge_0_5: 10 (33.3%)
- final_action_counts: {'abstain': 15, 'answer': 15}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- agentic_rag_baseline wins: 6
- agentic_rag_baseline losses: 0
- ties: 24
- agentic_rag_baseline answer / prompt abstain: 8
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 15
- both abstain: 7

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 15 (50.0%)
- no_new_evidence_records: 9 (30.0%)
- no_new_evidence_and_abstain: 7
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.000000
- mean_f1_without_no_new_evidence: 0.738095

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 30, 'False': 23}
- overall_sufficiency_counts_by_step: {'insufficient': 27, 'sufficient': 23, 'conflicting': 3}
- risk_score_mean: 0.286792
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 30
- suggested_query_empty_steps: 23

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
6. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - agentic_rag_baseline: action=answer f1=0.667 calls=2 answer=Kent
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
