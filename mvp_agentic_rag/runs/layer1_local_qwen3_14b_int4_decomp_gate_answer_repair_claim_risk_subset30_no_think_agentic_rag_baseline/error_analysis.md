# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_no_think_agentic_rag_baseline

## Run Shape
- total records: 90
- paired samples with both methods: 30

## agentic_rag_baseline
- count: 30
- mean_f1: 0.464286
- median_f1: 0.464286
- f1_zero: 13 (43.3%)
- f1_positive: 17 (56.7%)
- f1_ge_0_5: 15 (50.0%)
- final_action_counts: {'answer': 22, 'abstain': 8}
- retrieval_call_counts: {1: 17, 2: 5, 3: 8}
- trajectory_round_counts: {1: 17, 2: 5, 3: 8}

## claim_risk
- count: 30
- mean_f1: 0.464286
- median_f1: 0.464286
- f1_zero: 13 (43.3%)
- f1_positive: 17 (56.7%)
- f1_ge_0_5: 15 (50.0%)
- final_action_counts: {'answer': 22, 'abstain': 8}
- retrieval_call_counts: {1: 17, 2: 6, 3: 7}
- trajectory_round_counts: {1: 17, 2: 6, 3: 7}

## prompt_verifier
- count: 30
- mean_f1: 0.361111
- median_f1: 0.000000
- f1_zero: 16 (53.3%)
- f1_positive: 14 (46.7%)
- f1_ge_0_5: 12 (40.0%)
- final_action_counts: {'answer': 18, 'abstain': 12}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- agentic_rag_baseline wins: 4
- agentic_rag_baseline losses: 1
- ties: 25
- agentic_rag_baseline answer / prompt abstain: 5
- agentic_rag_baseline abstain / prompt answer: 1
- both answer: 17
- both abstain: 7

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 13 (43.3%)
- no_new_evidence_records: 10 (33.3%)
- no_new_evidence_and_abstain: 8
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.100000
- mean_f1_without_no_new_evidence: 0.646429

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 26, 'True': 25}
- overall_sufficiency_counts_by_step: {'sufficient': 26, 'insufficient': 25}
- risk_score_mean: 0.129412
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 25
- suggested_query_empty_steps: 26

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__20268_42014
   - question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
   - gold: 2
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=2
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Maria Shriver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__351045_47134
   - question: What is the mascot of the operator of RV Wecoma?
   - gold: Benny Beaver
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Benny Beaver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
4. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - agentic_rag_baseline: action=answer f1=0.667 calls=2 answer=Kent
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline loses to prompt_verifier
1. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.571 calls=1 answer=Robert Peel
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the relationship between Mohammed Atta and Nissan, or any other company that produces Datsun Type 12?
2. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the name of the television show named after the character featured in the video game Mickey's Safari in Lette...
3. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What political or cultural movement was Robert Mills associated with?
4. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.571 calls=1 answer=Robert Peel
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the name of a show named after a cast member from Politically Incorrect, and when does its new season air?
6. id=2hop__370564_71701
   - question: What year did the japanese get to the current administrative territorial entity of the Century Lotus Stadium and the rest of the guangdong province?
   - gold: November 5
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What specific year did Japanese forces occupy Foshan, where the Century Lotus Stadium is located, and the rest of Gua...
7. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the football star who backed out due to the relay controversy, and when was he signed by Barcelona?
8. id=2hop__374495_68633
   - question: Who is the president of the organization that Avery Brundage is a member of?
   - gold: Thomas Bach
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
