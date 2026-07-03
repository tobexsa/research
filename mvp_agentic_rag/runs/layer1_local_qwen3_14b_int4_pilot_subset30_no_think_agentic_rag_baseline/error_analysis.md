# Error Analysis: layer1_local_qwen3_14b_int4_pilot_subset30_no_think_agentic_rag_baseline

## Run Shape
- total records: 60
- paired samples with both methods: 30

## agentic_rag_baseline
- count: 30
- mean_f1: 0.420952
- median_f1: 0.414286
- f1_zero: 14 (46.7%)
- f1_positive: 16 (53.3%)
- f1_ge_0_5: 14 (46.7%)
- final_action_counts: {'answer': 21, 'abstain': 9}
- retrieval_call_counts: {1: 17, 2: 4, 3: 9}
- trajectory_round_counts: {1: 17, 2: 4, 3: 9}

## prompt_verifier
- count: 30
- mean_f1: 0.360952
- median_f1: 0.000000
- f1_zero: 16 (53.3%)
- f1_positive: 14 (46.7%)
- f1_ge_0_5: 12 (40.0%)
- final_action_counts: {'abstain': 13, 'answer': 17}
- retrieval_call_counts: {1: 30}
- trajectory_round_counts: {1: 30}

## Pairwise Comparison
- agentic_rag_baseline wins: 2
- agentic_rag_baseline losses: 0
- ties: 28
- agentic_rag_baseline answer / prompt abstain: 4
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 17
- both abstain: 9

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 13 (43.3%)
- no_new_evidence_records: 11 (36.7%)
- no_new_evidence_and_abstain: 9
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.072727
- mean_f1_without_no_new_evidence: 0.622556

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 29, 'False': 23}
- overall_sufficiency_counts_by_step: {'insufficient': 29, 'sufficient': 23}
- risk_score_mean: 0.160577
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 29
- suggested_query_empty_steps: 23

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__351045_47134
   - question: What is the mascot of the operator of RV Wecoma?
   - gold: Benny Beaver
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Benny Beaver
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=2hop__10620_49084
   - question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
   - gold: Liam Thomas Garrigan
   - agentic_rag_baseline: action=answer f1=0.800 calls=2 answer=Liam Garrigan
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline loses to prompt_verifier

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the historical record of land purchases by Huguenots in the area encompassing Zubly Cemetery, South Carolina?
2. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is Mohammed Atta's connection to the Datsun Type 12 or Nissan?
3. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the name of a television show named after the character featured in the video game Mickey's Safari in Letterl...
4. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What political or social movement was Robert Mills, the creator of the Washington Monument, associated with?
5. id=2hop__247353_55227
   - question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
   - gold: Maria Bello
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Who is the screenwriter of Here Comes the Boom, and who plays his wife in Grown Ups?
6. id=2hop__2682_577502
   - question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
   - gold: Maria Shriver
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Who was the governor who signed legislation in honor of Donda West's death, and who is their spouse?
7. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Are there any new television shows that are named after a cast member of Politically Incorrect? If so, when is the ne...
8. id=2hop__3739_13529
   - question: When was the football star who backed out due to relay controversy signed by Barcelona?
   - gold: June 1982
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the football star who backed out due to a relay controversy and when was he signed by Barcelona?
9. id=2hop__374495_68633
   - question: Who is the president of the organization that Avery Brundage is a member of?
   - gold: Thomas Bach
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
