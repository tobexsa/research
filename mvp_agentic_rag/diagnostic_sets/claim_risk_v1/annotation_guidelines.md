# Claim-Risk Annotation Guidelines

Review each record as a decision point, not as a final QA score only.

Use `answer` only when all critical final-answer claims are supported, the final target is correct, and there is no unresolved contradiction.

Use `answer_extraction_failure` when the evidence and critical claims are sufficient for an answer, but the runtime candidate answer is empty or the final answer was not extracted. Such records should normally use `oracle_action=answer`, `evidence_sufficiency=sufficient`, and `final_answer_supported=false` to preserve the distinction between evidence diagnosis and answer extraction.

Use `repair_missing_hop` when a verified prefix exists and the missing hop, anchor entity, target relation, or suggested repair query is available.

Use `read_more` when the next step should inspect nearby or same-document evidence rather than rewrite the query.

Use `refine_query` when evidence is insufficient but no reliable repair target exists.

Use `disambiguate_conflict` when contradictory evidence, entity ambiguity, or source/time ambiguity blocks a safe answer.

Use `abstain` only when evidence is insufficient and no reliable repair or read-more action remains.

Mark `bridge_as_final=true` only when the candidate answer is an intermediate chain value used as the final answer. Such records should normally also set `wrong_target=true`.

Records that cannot be judged from the exported evidence should use `annotation_status=adjudication_needed`.
