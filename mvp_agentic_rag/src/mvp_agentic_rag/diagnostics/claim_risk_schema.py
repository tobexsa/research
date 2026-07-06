from __future__ import annotations

from .action_normalization import normalize_runtime_action


ALLOWED_SUPPORT = {"supported", "unsupported", "contradicted", "unclear"}
ALLOWED_SUFFICIENCY = {"sufficient", "insufficient", "conflicting", "unclear"}
ALLOWED_ACTIONS = {
    "answer",
    "refine_query",
    "repair_missing_hop",
    "disambiguate_conflict",
    "read_more",
    "abstain",
}
ALLOWED_RISK_TYPES = {
    "supported_answer",
    "critical_gap",
    "noncritical_gap",
    "wrong_target",
    "bridge_as_final",
    "contradiction",
    "insufficient_evidence",
    "no_new_evidence",
    "repairable_missing_hop",
}
PROVENANCE_KEYS = {
    "uses_gold_answer",
    "uses_gold_chain",
    "uses_model_output",
    "uses_human_review",
    "runtime_available",
}


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    required = [
        "id",
        "dataset",
        "source_run",
        "sample_id",
        "question",
        "candidate_answer",
        "claims",
        "evidence",
        "claim_support",
        "evidence_sufficiency",
        "oracle_action",
        "risk_type",
        "state",
        "metadata",
        "mining_reason",
        "label_provenance",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing:{key}")

    state = record.get("state") or {}
    for key in ["round", "max_rounds", "budget_remaining", "allowed_actions"]:
        if key not in state:
            errors.append(f"missing:state.{key}")

    metadata = record.get("metadata") or {}
    if "claims_source" not in metadata:
        errors.append("missing:metadata.claims_source")
    if "risk_type" not in metadata:
        errors.append("missing:metadata.risk_type")

    mining_reason = record.get("mining_reason")
    if not isinstance(mining_reason, dict):
        errors.append("missing:mining_reason")
    else:
        for key in ["rule", "matched_fields", "confidence"]:
            if key not in mining_reason:
                errors.append(f"missing:mining_reason.{key}")
        if mining_reason.get("confidence") not in {None, "weak", "medium", "strong"}:
            errors.append("invalid:mining_reason.confidence")

    provenance = record.get("label_provenance")
    if not isinstance(provenance, dict):
        errors.append("missing:label_provenance")
    else:
        for key in sorted(PROVENANCE_KEYS):
            if key not in provenance:
                errors.append(f"missing:label_provenance.{key}")
            elif not isinstance(provenance[key], bool):
                errors.append(f"invalid:label_provenance.{key}")

    claims = record.get("claims") or []
    claim_support = record.get("claim_support") or {}
    for claim in claims:
        claim_id = claim.get("claim_id")
        for key in ["claim_id", "text", "role", "source"]:
            if key not in claim:
                errors.append(f"missing:claim.{key}")
        if claim_id and claim_id not in claim_support:
            errors.append(f"missing:claim_support.{claim_id}")

    for claim_id, support in claim_support.items():
        if support not in ALLOWED_SUPPORT:
            errors.append(f"invalid:claim_support.{claim_id}")

    if record.get("evidence_sufficiency") not in ALLOWED_SUFFICIENCY:
        errors.append("invalid:evidence_sufficiency")
    if record.get("oracle_action") not in ALLOWED_ACTIONS:
        errors.append("invalid:oracle_action")
    if record.get("risk_type") not in ALLOWED_RISK_TYPES:
        errors.append("invalid:risk_type")

    if record.get("oracle_action") == "answer" and record.get("should_abstain") is True:
        errors.append("invalid:answer_with_should_abstain")
    if record.get("oracle_action") == "repair_missing_hop" and not _has_repair_target(record.get("oracle_repair_target")):
        errors.append("invalid:repair_missing_hop_without_target")
    if record.get("bridge_as_final") is True and record.get("wrong_target") is not True:
        if record.get("annotation_status") not in {"unclear", "adjudication_needed"}:
            errors.append("invalid:bridge_as_final_without_wrong_target")
    if record.get("final_answer_supported") is False and record.get("oracle_action") == "answer":
        if record.get("annotation_status") != "unclear":
            errors.append("invalid:unsupported_answer_action")

    action_metadata = record.get("action_metadata") or {}
    runtime_action = action_metadata.get("runtime_action", "")
    diagnostic_action = action_metadata.get("diagnostic_action")
    if diagnostic_action and diagnostic_action != normalize_runtime_action(runtime_action):
        errors.append("invalid:action_metadata.diagnostic_action")

    return errors


def _has_repair_target(target) -> bool:
    if not isinstance(target, dict):
        return False
    return any(bool(target.get(key)) for key in ["missing_hop", "anchor_entity", "target_relation", "suggested_query"])
