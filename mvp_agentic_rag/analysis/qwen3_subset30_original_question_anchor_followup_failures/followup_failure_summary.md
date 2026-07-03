# Follow-Up Retrieval Failure Analysis

Run: `runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline`

Case definition: claim_risk follow-up step with evidence_gain <= 0

## Summary

- cases: 14
- support_in_raw_top50_rate: 1.0000
- support_in_original_question_top50_rate: 1.0000

## Category Counts

| category | count |
| --- | ---: |
| support_retrieved_but_no_evidence_gain | 14 |
| support_already_seen_before_followup | 14 |
| verifier_failed_despite_support_context | 13 |
| query_drops_question_constraints | 2 |
| top_k_too_small | 1 |
| per_subquery_or_total_top_k_too_small | 1 |

## Query Source Counts

| query_source | count |
| --- | ---: |
| memory | 14 |

## Representative Cases

### 2hop__10620_49084 round 2

- query_source: `memory`
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 5
- original_question_rank_first_support: 1
- support_seen_before: 2hop__10620_49084::p18
- support_in_current_retrieved: 2hop__10620_49084::p18
- new_support_in_current_retrieved: 
- question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
- query: Is the legendary figure featured in Historia Regum Britanniae King Arthur?
- supporting_ids: 2hop__10620_49084::p18, 2hop__10620_49084::p2

### 2hop__10620_49084 round 3

- query_source: `memory`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context, top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 13
- original_question_rank_first_support: 1
- support_seen_before: 2hop__10620_49084::p18
- support_in_current_retrieved: 2hop__10620_49084::p18
- new_support_in_current_retrieved: 
- question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
- query: Which legendary figure from Historia Regum Britanniae is portrayed in the show Once Upon a Time?
- supporting_ids: 2hop__10620_49084::p18, 2hop__10620_49084::p2

### 2hop__132854_417697 round 3

- query_source: `memory`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__132854_417697::p10, 2hop__132854_417697::p6
- support_in_current_retrieved: 2hop__132854_417697::p10
- new_support_in_current_retrieved: 
- question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
- query: What company is associated with producing the Datsun Type 12, and does Mohammed Atta have any connection to it?
- supporting_ids: 2hop__132854_417697::p10, 2hop__132854_417697::p6

### 2hop__153573_44085 round 2

- query_source: `memory`
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 2
- original_question_rank_first_support: 1
- support_seen_before: 2hop__153573_44085::p14, 2hop__153573_44085::p2
- support_in_current_retrieved: 2hop__153573_44085::p14, 2hop__153573_44085::p2
- new_support_in_current_retrieved: 
- question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
- query: What is the name of the show that features a character named Metal Mickey?
- supporting_ids: 2hop__153573_44085::p14, 2hop__153573_44085::p2

### 2hop__153573_44085 round 3

- query_source: `memory`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__153573_44085::p14, 2hop__153573_44085::p2
- support_in_current_retrieved: 2hop__153573_44085::p14, 2hop__153573_44085::p2
- new_support_in_current_retrieved: 
- question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
- query: What is the name of the television show that features the character from Mickey's Safari in Letterland?
- supporting_ids: 2hop__153573_44085::p14, 2hop__153573_44085::p2

### 2hop__167577_31122 round 2

- query_source: `memory`
- action: `answer`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, query_drops_question_constraints
- raw_rank_first_support: 2
- original_question_rank_first_support: 1
- support_seen_before: 2hop__167577_31122::p10
- support_in_current_retrieved: 2hop__167577_31122::p10
- new_support_in_current_retrieved: 
- question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
- query: What were the birth and death years of George Berkeley?
- supporting_ids: 2hop__167577_31122::p10, 2hop__167577_31122::p14

### 2hop__244193_461106 round 3

- query_source: `memory`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context, query_drops_question_constraints
- raw_rank_first_support: 1
- original_question_rank_first_support: 4
- support_seen_before: 2hop__244193_461106::p6
- support_in_current_retrieved: 2hop__244193_461106::p6
- new_support_in_current_retrieved: 
- question: What movement does the creator of the Washington Monument belong to?
- query: What movement was Robert Mills associated with?
- supporting_ids: 2hop__244193_461106::p3, 2hop__244193_461106::p6

### 2hop__247353_55227 round 2

- query_source: `memory`
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- support_in_current_retrieved: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- new_support_in_current_retrieved: 
- question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
- query: Who is the screenwriter of Here Comes the Boom, and who plays their wife in Grown Ups?
- supporting_ids: 2hop__247353_55227::p17, 2hop__247353_55227::p6

### 2hop__247353_55227 round 3

- query_source: `memory`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- support_in_current_retrieved: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- new_support_in_current_retrieved: 
- question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
- query: Who is the screenwriter of Here Comes the Boom, and who plays their wife in Grown Ups?
- supporting_ids: 2hop__247353_55227::p17, 2hop__247353_55227::p6

### 2hop__2682_577502 round 2

- query_source: `memory`
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__2682_577502::p9
- support_in_current_retrieved: 2hop__2682_577502::p9
- new_support_in_current_retrieved: 
- question: Who is the spouse of the famous governor signing legislation in honor of Donda West's death?
- query: Who was Arnold Schwarzenegger married to during the time he signed the 'Donda West Law'?
- supporting_ids: 2hop__2682_577502::p17, 2hop__2682_577502::p9
