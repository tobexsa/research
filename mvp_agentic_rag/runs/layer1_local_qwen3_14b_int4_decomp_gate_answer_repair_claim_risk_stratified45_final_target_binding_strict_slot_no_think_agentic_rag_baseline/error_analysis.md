# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think_agentic_rag_baseline

## Run Shape
- total records: 135
- paired samples with both methods: 45

## agentic_rag_baseline
- count: 45
- mean_f1: 0.253016
- median_f1: 0.000000
- f1_zero: 32 (71.1%)
- f1_positive: 13 (28.9%)
- f1_ge_0_5: 12 (26.7%)
- final_action_counts: {'answer': 19, 'abstain': 26}
- retrieval_call_counts: {1: 13, 2: 3, 3: 29}
- trajectory_round_counts: {1: 13, 2: 3, 3: 29}

## claim_risk
- count: 45
- mean_f1: 0.174554
- median_f1: 0.000000
- f1_zero: 35 (77.8%)
- f1_positive: 10 (22.2%)
- f1_ge_0_5: 9 (20.0%)
- final_action_counts: {'answer': 15, 'abstain': 30}
- retrieval_call_counts: {1: 11, 2: 19, 3: 15}
- trajectory_round_counts: {1: 11, 2: 19, 3: 15}

## prompt_verifier
- count: 45
- mean_f1: 0.202222
- median_f1: 0.000000
- f1_zero: 35 (77.8%)
- f1_positive: 10 (22.2%)
- f1_ge_0_5: 10 (22.2%)
- final_action_counts: {'answer': 13, 'abstain': 32}
- retrieval_call_counts: {1: 45}
- trajectory_round_counts: {1: 45}

## Pairwise Comparison
- agentic_rag_baseline wins: 3
- agentic_rag_baseline losses: 0
- ties: 42
- agentic_rag_baseline answer / prompt abstain: 6
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 13
- both abstain: 26

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 32 (71.1%)
- no_new_evidence_records: 28 (62.2%)
- no_new_evidence_and_abstain: 26
- no_new_evidence_and_answer: 2
- mean_f1_with_no_new_evidence: 0.035714
- mean_f1_without_no_new_evidence: 0.610924

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 19, 'True': 87}
- overall_sufficiency_counts_by_step: {'sufficient': 19, 'insufficient': 85, 'conflicting': 2}
- risk_score_mean: 0.217925
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 87
- suggested_query_empty_steps: 19

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__167577_31122
   - question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
   - gold: 18th
   - agentic_rag_baseline: action=answer f1=1.000 calls=3 answer=18th
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
2. id=4hop1__161810_583746_457883_650651
   - question: Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser?
   - gold: NBC
   - agentic_rag_baseline: action=answer f1=1.000 calls=3 answer=NBC
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.25 suff=sufficient need_more=False risk=0.0 suggested=
3. id=3hop1__103751_24918_24991
   - question: What went down after the Soviet President visiting the country of origin of Ethella Chupryk while the protests were taking place departed from the Kremlin?
   - gold: Soviet flag
   - agentic_rag_baseline: action=answer f1=0.286 calls=3 answer=Dissolution of the Soviet Union
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: agentic_rag_baseline loses to prompt_verifier

## Cases: agentic_rag_baseline no-new-evidence abstentions
1. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the relationship between Mohammed Atta and Nissan or Alghanim Industries?
2. id=2hop__153573_44085
   - question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
   - gold: The Mickey Mouse Club
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the name of the television show that was named after a character from Mickey's Safari in Letterland?
3. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What architectural movement was Robert Mills associated with?
4. id=3hop1__103881_443779_52195
   - question: Who is the president of the newly declared independent country that is part of the Commission of Truth and Friendship with the country that Tony Gunawan is from?
   - gold: Francisco Guterres
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=conflicting need_more=True risk=0.5 suggested=Who is the current president of East Timor?
5. id=3hop1__104996_160713_77246
   - question: What is the meaning of the word that is also a majority religion in the area that became India when the country that release Ankahi was created in Arabic dictionary?
   - gold: the country of India
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.3333333333333333 suff=insufficient need_more=True risk=0.5 suggested=What is the majority religion in the area that became India after the Partition of India?
6. id=3hop1__105767_443779_52195
   - question: Who is the president of the newly declared independent country that is part of the commission of truth and friendship with the country that eats Kemplang?
   - gold: Francisco Guterres
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Who is the current president of East Timor?
7. id=3hop1__108833_720914_41132
   - question: How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?
   - gold: 22
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Where did Titian die?
8. id=3hop1__129499_33897_81096
   - question: Who won the 1993 Indy Car race in the city with the largest population in the state where Poachie Range is located?
   - gold: Mario Andretti
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.3333333333333333 suff=insufficient need_more=True risk=0.5 suggested=What is the largest city in Arizona by population?
9. id=3hop1__135659_87694_64412
   - question: When did the place where St for whom the Mantua Cathedral was named for basilica the head of the catholic religion is located in become its own country?
   - gold: 11 February 1929
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the saint for whom Mantua Cathedral is named, and when did the place where this saint was located become its o...
10. id=3hop1__144439_443779_52195
   - question: who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin–Timor Leste Commission of Truth and Friendship?
   - gold: Francisco Guterres
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.8 suggested=Who is the current president of Timor-Leste?
11. id=3hop1__159803_89752_75165
   - question: What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts?
   - gold: 1,335,907
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=What is the region of the U.S. where trading practices were once threatened by the Navigation Acts, and what is its l...
12. id=3hop1__222497_309482_27537
   - question: Why did Roncalli leave the place where the composer of Al gran sole carico d'amore worked?
   - gold: for the conclave in Rome
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Where did Luigi Nono work?
