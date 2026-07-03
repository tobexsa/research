# Error Analysis: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline

## Run Shape
- total records: 135
- paired samples with both methods: 45

## agentic_rag_baseline
- count: 45
- mean_f1: 0.190794
- median_f1: 0.000000
- f1_zero: 35 (77.8%)
- f1_positive: 10 (22.2%)
- f1_ge_0_5: 9 (20.0%)
- final_action_counts: {'abstain': 30, 'answer': 15}
- retrieval_call_counts: {1: 9, 2: 5, 3: 31}
- trajectory_round_counts: {1: 9, 2: 5, 3: 31}

## claim_risk
- count: 45
- mean_f1: 0.263443
- median_f1: 0.000000
- f1_zero: 31 (68.9%)
- f1_positive: 14 (31.1%)
- f1_ge_0_5: 13 (28.9%)
- final_action_counts: {'abstain': 24, 'answer': 21}
- retrieval_call_counts: {1: 11, 2: 18, 3: 16}
- trajectory_round_counts: {1: 11, 2: 18, 3: 16}

## prompt_verifier
- count: 45
- mean_f1: 0.122222
- median_f1: 0.000000
- f1_zero: 39 (86.7%)
- f1_positive: 6 (13.3%)
- f1_ge_0_5: 6 (13.3%)
- final_action_counts: {'abstain': 36, 'answer': 9}
- retrieval_call_counts: {1: 45}
- trajectory_round_counts: {1: 45}

## Pairwise Comparison
- agentic_rag_baseline wins: 4
- agentic_rag_baseline losses: 0
- ties: 41
- agentic_rag_baseline answer / prompt abstain: 6
- agentic_rag_baseline abstain / prompt answer: 0
- both answer: 9
- both abstain: 30

## agentic_rag_baseline Retrieval Behavior
- extra_retrieval_records: 36 (80.0%)
- no_new_evidence_records: 32 (71.1%)
- no_new_evidence_and_abstain: 29
- no_new_evidence_and_answer: 3
- mean_f1_with_no_new_evidence: 0.056250
- mean_f1_without_no_new_evidence: 0.521978

## agentic_rag_baseline Verifier Decision Signals
- need_more_evidence_counts_by_step: {'True': 97, 'False': 15}
- overall_sufficiency_counts_by_step: {'insufficient': 95, 'sufficient': 15, 'unclear': 1, 'conflicting': 1}
- risk_score_mean: 0.421429
- risk_score_max: 0.800000
- suggested_query_nonempty_steps: 97
- suggested_query_empty_steps: 15

## Cases: agentic_rag_baseline wins over prompt_verifier
1. id=2hop__194469_83289
   - question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
   - gold: Matt Bennett
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=Matt Bennett
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
2. id=3hop1__140786_2053_52946
   - question: When is Celebrity Big Brother coming to the broadcast company that, along with the network of Just Men!?, and ABC, is one of the major broadcasters based in New York?
   - gold: February 7, 2018
   - agentic_rag_baseline: action=answer f1=1.000 calls=2 answer=February 7, 2018
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
3. id=3hop1__145194_160545_62931
   - question: The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?
   - gold: island Koh Phi Phi
   - agentic_rag_baseline: action=answer f1=0.800 calls=2 answer=Koh Phi Phi
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
4. id=3hop1__103751_24918_24991
   - question: What went down after the Soviet President visiting the country of origin of Ethella Chupryk while the protests were taking place departed from the Kremlin?
   - gold: Soviet flag
   - agentic_rag_baseline: action=answer f1=0.286 calls=3 answer=Dissolution of the Soviet Union
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=

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
6. id=3hop1__103881_443779_52195
   - question: Who is the president of the newly declared independent country that is part of the Commission of Truth and Friendship with the country that Tony Gunawan is from?
   - gold: Francisco Guterres
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.8 suggested=Who is the current president of East Timor?
7. id=3hop1__104996_160713_77246
   - question: What is the meaning of the word that is also a majority religion in the area that became India when the country that release Ankahi was created in Arabic dictionary?
   - gold: the country of India
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.6666666666666666 suff=insufficient need_more=True risk=0.6 suggested=What was the majority religion in India at the time of its creation in 1947?
8. id=3hop1__105767_443779_52195
   - question: Who is the president of the newly declared independent country that is part of the commission of truth and friendship with the country that eats Kemplang?
   - gold: Francisco Guterres
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Who is the current president of East Timor?
9. id=3hop1__108833_720914_41132
   - question: How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?
   - gold: 22
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.5 suggested=Where did Titian die?
10. id=3hop1__129499_33897_81096
   - question: Who won the 1993 Indy Car race in the city with the largest population in the state where Poachie Range is located?
   - gold: Mario Andretti
   - agentic_rag_baseline: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - agentic_rag_baseline_last: round=3 evidence_gain=0.3333333333333333 suff=insufficient need_more=True risk=0.5 suggested=What is the largest city in Arizona by population?
