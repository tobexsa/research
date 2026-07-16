# Follow-Up Retrieval Failure Analysis

Run: `runs\musique_2hop_proxy_hybrid_bm25_bge_top10_dev_agentic_rag_baseline_c1`

Case definition: claim_risk follow-up step with evidence_gain <= 0

## Summary

- cases: 52
- support_in_raw_top50_rate: 0.9231
- support_in_original_question_top50_rate: 0.9615

## Category Counts

| category | count |
| --- | ---: |
| support_retrieved_but_no_evidence_gain | 34 |
| support_already_seen_before_followup | 34 |
| verifier_failed_despite_support_context | 29 |
| top_k_too_small | 14 |
| per_subquery_or_total_top_k_too_small | 14 |
| dense_recall_miss_top50 | 4 |

## Query Source Counts

| query_source | count |
| --- | ---: |
| checklist | 52 |

## Representative Cases

### 2hop__10620_49084 round 2

- query_source: `checklist`
- action: `refine_query`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 13
- original_question_rank_first_support: 14
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
- query: Need answer plays legendary figure featured Historia Regum Britanniae show Once Upon Time Eldol king Britain Geoffrey Monmouth's c
- supporting_ids: 2hop__10620_49084::p18, 2hop__10620_49084::p2

### 2hop__10620_49084 round 3

- query_source: `checklist`
- action: `abstain`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 13
- original_question_rank_first_support: 14
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
- query: Need answer plays legendary figure featured Historia Regum Britanniae show Once Upon Time Eldol king Britain Geoffrey Monmouth's c
- supporting_ids: 2hop__10620_49084::p18, 2hop__10620_49084::p2

### 2hop__10620_79092 round 2

- query_source: `checklist`
- action: `refine_query`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 13
- original_question_rank_first_support: 15
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: The volcano, named after the legendary King featured in Historia Regum Britanniae, last erupted when?
- query: Need answer volcano named after legendary King featured Historia Regum Britanniae last erupted Catellus Britons recounted Geoffrey Monmouth's work
- supporting_ids: 2hop__10620_79092::p12, 2hop__10620_79092::p18

### 2hop__10620_79092 round 3

- query_source: `checklist`
- action: `abstain`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 13
- original_question_rank_first_support: 15
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: The volcano, named after the legendary King featured in Historia Regum Britanniae, last erupted when?
- query: Need answer volcano named after legendary King featured Historia Regum Britanniae last erupted Catellus Britons recounted Geoffrey Monmouth's work
- supporting_ids: 2hop__10620_79092::p12, 2hop__10620_79092::p18

### 2hop__10900_21567 round 3

- query_source: `checklist`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 2
- original_question_rank_first_support: 17
- support_seen_before: 2hop__10900_21567::p19
- support_in_current_retrieved: 2hop__10900_21567::p19
- new_support_in_current_retrieved: 
- question: Who introduced a system of musical notation in the 14th century used in the area where the Ottoman slave trade flourished?
- query: Need answer introduced system musical notation 14th century used area Ottoman slave trade flourished first military unit State army organized Osman I tribesmen inhabiting
- supporting_ids: 2hop__10900_21567::p14, 2hop__10900_21567::p19

### 2hop__135652_669373 round 2

- query_source: `checklist`
- action: `abstain`
- categories: support_retrieved_but_no_evidence_gain, support_already_seen_before_followup, verifier_failed_despite_support_context
- raw_rank_first_support: 3
- original_question_rank_first_support: 3
- support_seen_before: 2hop__135652_669373::p4
- support_in_current_retrieved: 2hop__135652_669373::p4
- new_support_in_current_retrieved: 
- question: Who is the employer of the physicist who Mach number is named after?
- query: Need answer employer physicist Mach number named after Austrian philosopher Ernst designation proposed aeronautical engineer Jakob Ackeret
- supporting_ids: 2hop__135652_669373::p4, 2hop__135652_669373::p5

### 2hop__13592_49388 round 2

- query_source: `checklist`
- action: `refine_query`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 38
- original_question_rank_first_support: 20
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: How many games in a season of the league in which Barcelona won titles in 1948 and 1949?
- query: Need answer How many games season league Barcelona won titles 1948 1949 treble 2014 2015 winning La Liga Copa del Rey UEFA Champions became
- supporting_ids: 2hop__13592_49388::p15, 2hop__13592_49388::p2

### 2hop__13592_49388 round 3

- query_source: `checklist`
- action: `abstain`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 38
- original_question_rank_first_support: 20
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: How many games in a season of the league in which Barcelona won titles in 1948 and 1949?
- query: Need answer How many games season league Barcelona won titles 1948 1949 treble 2014 2015 winning La Liga Copa del Rey UEFA Champions became
- supporting_ids: 2hop__13592_49388::p15, 2hop__13592_49388::p2

### 2hop__13592_85544 round 2

- query_source: `checklist`
- action: `refine_query`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 29
- original_question_rank_first_support: 22
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: How many games do team in the league where Barcelona won titles in 1948 and 1949 play?
- query: Need answer How many games team league Barcelona won titles 1948 1949 play one three founding members Primera Divisi n never been relegated top
- supporting_ids: 2hop__13592_85544::p11, 2hop__13592_85544::p12

### 2hop__13592_85544 round 3

- query_source: `checklist`
- action: `abstain`
- categories: top_k_too_small, per_subquery_or_total_top_k_too_small
- raw_rank_first_support: 29
- original_question_rank_first_support: 22
- support_seen_before: 
- support_in_current_retrieved: 
- new_support_in_current_retrieved: 
- question: How many games do team in the league where Barcelona won titles in 1948 and 1949 play?
- query: Need answer How many games team league Barcelona won titles 1948 1949 play one three founding members Primera Divisi n never been relegated top
- supporting_ids: 2hop__13592_85544::p11, 2hop__13592_85544::p12
