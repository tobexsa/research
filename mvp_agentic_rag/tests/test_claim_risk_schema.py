from mvp_agentic_rag.diagnostics.claim_risk_schema import validate_record


def _record() -> dict:
    return {
        "id": "rec-1",
        "dataset": "musique",
        "source_run": "run-a",
        "sample_id": "sample-1",
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "candidate_answer": "Ada",
        "hop": 2,
        "claims": [{"claim_id": "c1", "text": "Ada founded X.", "role": "final_answer", "source": "final_answer"}],
        "evidence": [{"id": "p1", "title": "T", "text": "Ada founded X."}],
        "claim_support": {"c1": "supported"},
        "evidence_sufficiency": "sufficient",
        "critical_missing_claims": [],
        "noncritical_missing_claims": [],
        "contradicted_claims": [],
        "wrong_target": False,
        "bridge_as_final": False,
        "final_answer_supported": True,
        "should_abstain": False,
        "oracle_action": "answer",
        "oracle_repair_target": {},
        "risk_type": "supported_answer",
        "state": {"round": 1, "max_rounds": 3, "budget_remaining": 2, "allowed_actions": ["answer"]},
        "metadata": {"claims_source": "final_answer", "risk_type": "supported_answer"},
        "mining_reason": {"rule": "final_answer_supported", "matched_fields": ["final_action"], "confidence": "strong"},
        "label_provenance": {
            "uses_gold_answer": False,
            "uses_gold_chain": False,
            "uses_model_output": True,
            "uses_human_review": False,
            "runtime_available": True,
        },
        "action_metadata": {"runtime_action": "answer", "diagnostic_action": "answer"},
        "annotation_status": "pending_review",
    }


def test_validates_complete_record() -> None:
    assert validate_record(_record()) == []


def test_reports_missing_provenance_and_state() -> None:
    record = _record()
    del record["label_provenance"]
    del record["state"]["allowed_actions"]

    errors = validate_record(record)

    assert "missing:label_provenance" in errors
    assert "missing:state.allowed_actions" in errors


def test_repair_action_requires_target() -> None:
    record = _record()
    record["oracle_action"] = "repair_missing_hop"
    record["risk_type"] = "repairable_missing_hop"
    record["metadata"]["risk_type"] = "repairable_missing_hop"
    record["oracle_repair_target"] = {}

    assert "invalid:repair_missing_hop_without_target" in validate_record(record)
