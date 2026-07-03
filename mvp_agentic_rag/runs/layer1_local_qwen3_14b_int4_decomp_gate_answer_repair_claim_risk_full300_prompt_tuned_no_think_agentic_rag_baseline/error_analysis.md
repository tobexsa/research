# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_prompt_tuned_no_think_agentic_rag_baseline

## Run Shape
- total records: 900
- paired samples with both methods: 300

## agentic_rag_baseline
- count: 300
- mean_f1: 0.220159
- median_f1: 0.000000
- f1_zero: 220 (73.3%)
- f1_positive: 80 (26.7%)
- f1_ge_0_5: 72 (24.0%)
- final_action_counts: {'answer': 120, 'abstain': 180}
- retrieval_call_counts: {1: 71, 2: 38, 3: 191}
- trajectory_round_counts: {1: 71, 2: 38, 3: 191}

## claim_risk
- count: 300
- mean_f1: 0.230159
- median_f1: 0.000000
- f1_zero: 217 (72.3%)
- f1_positive: 83 (27.7%)
- f1_ge_0_5: 75 (25.0%)
- final_action_counts: {'answer': 120, 'abstain': 180}
- retrieval_call_counts: {1: 70, 2: 50, 3: 180}
- trajectory_round_counts: {1: 70, 2: 50, 3: 180}

## prompt_verifier
- count: 300
- mean_f1: 0.126413
- median_f1: 0.000000
- f1_zero: 252 (84.0%)
- f1_positive: 48 (16.0%)
- f1_ge_0_5: 42 (14.0%)
- final_action_counts: {'answer': 70, 'abstain': 230}
- retrieval_call_counts: {1: 300}
- trajectory_round_counts: {1: 300}

## Pairwise Comparison
- agentic_rag_baseline wins: 32
- agentic_rag_baseline losses: 0
- ties: 268
- agentic_rag_baseline answer / prompt abstain: 50
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 70
- both abstain: 180

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 229 (76.3%)
- no_new_evidence_records: 189 (63.0%)
- no_new_evidence_and_abstain: 174
- no_new_evidence_and_answer: 15
- mean_f1_with_no_new_evidence: 0.038750
- mean_f1_without_no_new_evidence: 0.529043

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 124, 'True': 596}
- overall_sufficiency_counts_by_step: {'sufficient': 120, 'insufficient': 580, 'conflicting': 9, 'unclear': 11}
- risk_score_mean: 0.249097
- risk_score_max: 1.000000
- suggested_query_nonempty_steps: 597
- suggested_query_empty_steps: 123

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
4. id=2hop__424294_19033
   - question: Where did the author of A Lion's Tale: Around the World in Spandex win in 2008?
   - gold: Great American Bash
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Great American Bash
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__446324_620302
   - question: The author of Elizabeth and After attended which university?
   - gold: University of Toronto
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=University of Toronto
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
6. id=2hop__547045_131879
   - question: What body of water is by the headquarters location of Wipac?
   - gold: River Great Ouse
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=River Great Ouse
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
7. id=2hop__622637_120171
   - question: What year did the company that published Starship Command end?
   - gold: 1986
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=1986
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
8. id=2hop__678516_179720
   - question: Who was married to the creator of Ruby Loftus Screwing a Breech Ring?
   - gold: Harold Knight
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Harold Knight
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
9. id=2hop__763840_144857
   - question: What city was the author of Neighbors born in?
   - gold: Clatskanie
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Clatskanie
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
10. id=2hop__770487_494646
   - question: What administrative territorial entity contains the headquarters of the Mono Lake Committee?
   - gold: Mono County
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Mono County
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
7. id=2hop__38030_23241
   - question: According to Pew, in 2010, what percent of Nigeria's population practiced the religion dominant in the countries surrounding Armenia?
   - gold: 48.8 percent
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the dominant religion in the countries surrounding Armenia, and what percentage of Nigeria's population pract...
8. id=2hop__39063_593388
   - question: Who is the father of the person who came up with the concept of the "new" police?
   - gold: Sir Robert Peel, 1st Baronet
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.8 suggested=Who was the father of Sir Robert Peel, 1st Baronet?
9. id=2hop__40270_11402
   - question: According to the agency that considers if Los Angeles County is to be a separate metropolitan area, what is the total area in square miles?
   - gold: 17.037 square miles
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the total area in square miles of Los Angeles County according to the U.S. Census Bureau or other official ag...
10. id=2hop__433694_20273
   - question: In what year did Margaret Knox's spouse pass away?
   - gold: 1572
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What year did John Knox, Margaret Knox's spouse, pass away?
