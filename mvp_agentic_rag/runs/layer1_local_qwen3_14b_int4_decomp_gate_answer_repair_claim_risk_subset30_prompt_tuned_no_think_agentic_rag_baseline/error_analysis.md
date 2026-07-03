# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_prompt_tuned_no_think_agentic_rag_baseline

## Run Shape
- total records: 90
- paired samples with both methods: 30

## agentic_rag_baseline
- count: 30
- mean_f1: 0.560000
- median_f1: 0.733333
- f1_zero: 11 (36.7%)
- f1_positive: 19 (63.3%)
- f1_ge_0_5: 18 (60.0%)
- final_action_counts: {'answer': 24, 'abstain': 6}
- retrieval_call_counts: {1: 19, 2: 4, 3: 7}
- trajectory_round_counts: {1: 19, 2: 4, 3: 7}

## claim_risk
- count: 30
- mean_f1: 0.560000
- median_f1: 0.733333
- f1_zero: 11 (36.7%)
- f1_positive: 19 (63.3%)
- f1_ge_0_5: 18 (60.0%)
- final_action_counts: {'answer': 24, 'abstain': 6}
- retrieval_call_counts: {1: 19, 2: 4, 3: 7}
- trajectory_round_counts: {1: 19, 2: 4, 3: 7}

## prompt_verifier
- count: 30
- mean_f1: 0.437778
- median_f1: 0.166667
- f1_zero: 15 (50.0%)
- f1_positive: 15 (50.0%)
- f1_ge_0_5: 14 (46.7%)
- final_action_counts: {'answer': 19, 'abstain': 11}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- agentic_rag_baseline wins: 4
- agentic_rag_baseline losses: 0
- ties: 26
- agentic_rag_baseline answer / prompt abstain: 5
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 19
- both abstain: 6

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 11 (36.7%)
- no_new_evidence_records: 8 (26.7%)
- no_new_evidence_and_abstain: 6
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.125000
- mean_f1_without_no_new_evidence: 0.718182

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 24, 'True': 24}
- overall_sufficiency_counts_by_step: {'sufficient': 24, 'insufficient': 24}
- risk_score_mean: 0.125000
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 24
- suggested_query_empty_steps: 24

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__25396_593388
   - question: Who was the father of the person who issued the Tamworth manifesto?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Sir Robert Peel, 1st Baronet
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - agentic_rag_baseline: action=answer f1=1.000 calls=3 answer=Maria Shriver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
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

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the connection between Mohammed Atta and the company that makes Datsun Type 12?
2. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the name of the show that features a character from the video game 'Mickey's Safari in Letterland'?
3. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What historical or political movement was Robert Mills associated with?
4. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What show is named after a cast member from Politically Incorrect, and when does its new season air?
5. id=2hop__370564_71701
   - question: What year did the japanese get to the current administrative territorial entity of the Century Lotus Stadium and the rest of the guangdong province?
   - gold: November 5
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.8 suggested=What year did Japan occupy Foshan, where Century Lotus Stadium is located, and the rest of Guangdong province?
6. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Was Diego Maradona ever officially signed by FC Barcelona?
