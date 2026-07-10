from __future__ import annotations


def _record(record_id: str, risk_type: str = "supported_answer", oracle_action: str = "answer", hop: int = 2) -> dict:
    claim_support = "supported"
    evidence_sufficiency = "sufficient"
    candidate_answer = "Ada"
    wrong_target = risk_type == "wrong_target"
    final_answer_supported = True
    should_abstain = False
    repair_target = {}

    if risk_type == "answer_extraction_failure":
        candidate_answer = ""
        final_answer_supported = False
    elif risk_type == "repairable_missing_hop":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        repair_target = {"suggested_query": "Ada founded X"}
    elif risk_type == "critical_gap":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
    elif risk_type == "no_new_evidence":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        should_abstain = oracle_action == "abstain"
    elif risk_type == "insufficient_evidence":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        should_abstain = oracle_action == "abstain"
    elif risk_type == "contradiction":
        claim_support = "contradicted"
        evidence_sufficiency = "conflicting"
        final_answer_supported = False

    if oracle_action == "repair_missing_hop" and not repair_target:
        repair_target = {"suggested_query": "Ada founded X"}
    if oracle_action == "abstain":
        should_abstain = True

    return {
        "id": record_id,
        "dataset": "musique",
        "source_run": "run-a",
        "sample_id": record_id,
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "candidate_answer": candidate_answer,
        "hop": hop,
        "claims": [{"claim_id": "c1", "text": "Ada founded X.", "role": "final_answer", "source": "final_answer"}],
        "evidence": [{"id": f"{record_id}::p1", "title": "T", "text": "Ada founded X."}],
        "claim_support": {"c1": claim_support},
        "evidence_sufficiency": evidence_sufficiency,
        "critical_missing_claims": ["c1"] if claim_support == "unclear" else [],
        "noncritical_missing_claims": [],
        "contradicted_claims": ["c1"] if claim_support == "contradicted" else [],
        "wrong_target": wrong_target,
        "bridge_as_final": False,
        "final_answer_supported": final_answer_supported,
        "should_abstain": should_abstain,
        "oracle_action": oracle_action,
        "oracle_repair_target": repair_target,
        "risk_type": risk_type,
        "state": {"round": 1, "max_rounds": 3, "budget_remaining": 2, "allowed_actions": ["answer", "repair_missing_hop"]},
        "metadata": {"claims_source": "final_answer", "risk_type": risk_type},
        "mining_reason": {"rule": risk_type, "matched_fields": ["final_action"], "confidence": "strong"},
        "label_provenance": {
            "uses_gold_answer": False,
            "uses_gold_chain": False,
            "uses_model_output": True,
            "uses_human_review": False,
            "runtime_available": True,
        },
        "annotation_status": "pending_review",
    }
