# Follow-Up Retrieval Failure Analysis

Run: `runs\layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline`

Case definition: claim_risk follow-up step with evidence_gain <= 0

## Summary

- cases: 16
- support_in_raw_top50_rate: 1.0000
- support_in_original_question_top50_rate: 1.0000

## Category Counts

| category | count |
| --- | ---: |
| support_already_seen_before_followup | 16 |
| verifier_failed_despite_support_context | 15 |
| support_retrieved_but_no_evidence_gain | 14 |
| query_drops_question_constraints | 1 |

## Query Source Counts

| query_source | count |
| --- | ---: |
| missing | 16 |

## Representative Cases

### 2hop__129721_40482 round 2

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__129721_40482::p14, 2hop__129721_40482::p18
- support_in_current_retrieved: 2hop__129721_40482::p14, 2hop__129721_40482::p18
- new_support_in_current_retrieved: 
- question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
- query: Native American tribes or colonial authorities from whom Huguenots in South Carolina purchased land near Zubly Cemetery
- supporting_ids: 2hop__129721_40482::p14, 2hop__129721_40482::p18

### 2hop__131951_643670 round 2

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__131951_643670::p10, 2hop__131951_643670::p6
- support_in_current_retrieved: 2hop__131951_643670::p10, 2hop__131951_643670::p6
- new_support_in_current_retrieved: 
- question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
- query: name of the mouth of the watercourse by Rotterdam Centrum
- supporting_ids: 2hop__131951_643670::p10, 2hop__131951_643670::p6

### 2hop__132854_417697 round 2

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__132854_417697::p10
- support_in_current_retrieved: 2hop__132854_417697::p10
- new_support_in_current_retrieved: 
- question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
- query: Does Mohammed Atta own or have a Datsun Type 12 or any other Datsun model?
- supporting_ids: 2hop__132854_417697::p10, 2hop__132854_417697::p6

### 2hop__20268_42014 round 2

- query_source: ``
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__20268_42014::p1, 2hop__20268_42014::p8
- support_in_current_retrieved: 2hop__20268_42014::p1, 2hop__20268_42014::p8
- new_support_in_current_retrieved: 
- question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
- query: How many members of the Scottish Government were part of the organization that enacted the Directory of Public Worship into law?
- supporting_ids: 2hop__20268_42014::p1, 2hop__20268_42014::p8

### 2hop__20268_42014 round 3

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__20268_42014::p1, 2hop__20268_42014::p8
- support_in_current_retrieved: 2hop__20268_42014::p1, 2hop__20268_42014::p8
- new_support_in_current_retrieved: 
- question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
- query: number of Scottish Government members in organization that enacted Directory of Public Worship
- supporting_ids: 2hop__20268_42014::p1, 2hop__20268_42014::p8

### 2hop__244193_461106 round 3

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 4
- support_seen_before: 2hop__244193_461106::p6
- support_in_current_retrieved: 2hop__244193_461106::p6
- new_support_in_current_retrieved: 
- question: What movement does the creator of the Washington Monument belong to?
- query: movement of Robert Mills, creator of the Washington Monument
- supporting_ids: 2hop__244193_461106::p3, 2hop__244193_461106::p6

### 2hop__247353_55227 round 2

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- support_in_current_retrieved: 2hop__247353_55227::p17, 2hop__247353_55227::p6
- new_support_in_current_retrieved: 
- question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
- query: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
- supporting_ids: 2hop__247353_55227::p17, 2hop__247353_55227::p6

### 2hop__286621_84856 round 2

- query_source: ``
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__286621_84856::p17
- support_in_current_retrieved: 2hop__286621_84856::p17
- new_support_in_current_retrieved: 
- question: When does the new season of the show named for the Politically Incorrect cast member?
- query: show named after Politically Incorrect cast member new season release date
- supporting_ids: 2hop__286621_84856::p12, 2hop__286621_84856::p17

### 2hop__286621_84856 round 3

- query_source: ``
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__286621_84856::p17
- support_in_current_retrieved: 2hop__286621_84856::p17
- new_support_in_current_retrieved: 
- question: When does the new season of the show named for the Politically Incorrect cast member?
- query: show named after Politically Incorrect cast member new season release date
- supporting_ids: 2hop__286621_84856::p12, 2hop__286621_84856::p17

### 2hop__315267_277284 round 2

- query_source: ``
- action: `refine_query`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 1
- original_question_rank_first_support: 1
- support_seen_before: 2hop__315267_277284::p18
- support_in_current_retrieved: 2hop__315267_277284::p18
- new_support_in_current_retrieved: 
- question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
- query: Bill Cockcroft education location administrative territorial entity
- supporting_ids: 2hop__315267_277284::p15, 2hop__315267_277284::p18
