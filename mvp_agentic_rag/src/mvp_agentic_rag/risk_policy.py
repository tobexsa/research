from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import VerifierOutput


@dataclass(frozen=True)
class RiskPolicyInput:
    original_action: str
    verifier_output: VerifierOutput
    slot_metadata: dict = field(default_factory=dict)
    repair_metadata: dict = field(default_factory=dict)
    evidence_graph: dict = field(default_factory=dict)
    budget_remaining: int = 0
    round_idx: int = 0
    query_history: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RiskPolicyOutput:
    action: str
    reason: str
    risk_bucket: str = ""
    metadata: dict = field(default_factory=dict)


class RiskPolicy:
    def decide(self, policy_input: RiskPolicyInput) -> RiskPolicyOutput:
        repair_metadata = policy_input.repair_metadata
        evidence_graph = policy_input.evidence_graph
        planner_recommendation = str(repair_metadata.get("repair_planner_recommended_policy_action") or "")
        planner_blocked = bool(repair_metadata.get("repair_plan_risk_blocked"))
        conflict = _has_conflict(policy_input.verifier_output, policy_input.slot_metadata)
        wrong_target = _has_hard_wrong_target_signal(
            policy_input.verifier_output,
            policy_input.slot_metadata,
            evidence_graph,
        )
        soft_final_target_mismatch = _has_soft_final_target_mismatch(
            policy_input.verifier_output,
            policy_input.slot_metadata,
            evidence_graph,
        )
        chain_incomplete = bool(
            evidence_graph.get("evidence_graph_chain_incomplete")
            or evidence_graph.get("evidence_graph_supported_bridge_not_final")
            or soft_final_target_mismatch
        )
        supported_bridge_not_final = bool(evidence_graph.get("evidence_graph_supported_bridge_not_final"))
        repair_signal_present = _has_repair_signal(repair_metadata)
        budget_remaining = int(policy_input.budget_remaining or 0)

        if planner_recommendation == "abstain":
            return self._output(
                policy_input,
                action="abstain",
                reason="planner_recommended_abstain",
                risk_bucket="planner_blocked",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if planner_recommendation == "disambiguate_conflict":
            action = "disambiguate_conflict" if budget_remaining > 0 else "abstain"
            reason = "planner_recommended_disambiguation" if budget_remaining > 0 else "planner_disambiguation_budget_exhausted"
            return self._output(
                policy_input,
                action=action,
                reason=reason,
                risk_bucket="planner_blocked",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if conflict:
            action = "disambiguate_conflict" if budget_remaining > 0 else "abstain"
            reason = "conflict_signal" if budget_remaining > 0 else "conflict_budget_exhausted"
            return self._output(
                policy_input,
                action=action,
                reason=reason,
                risk_bucket="conflict",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if wrong_target:
            action = "disambiguate_conflict" if budget_remaining > 0 else "abstain"
            reason = "wrong_target_signal" if budget_remaining > 0 else "wrong_target_budget_exhausted"
            return self._output(
                policy_input,
                action=action,
                reason=reason,
                risk_bucket="wrong_target",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if _can_answer(policy_input.verifier_output):
            return self._output(
                policy_input,
                action="answer",
                reason="sufficient_no_conflict",
                risk_bucket="low",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if repair_signal_present and budget_remaining > 0:
            return self._output(
                policy_input,
                action="repair_missing_hop",
                reason="critical_repair_signal_valid",
                risk_bucket="critical_gap",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if chain_incomplete and budget_remaining > 0:
            return self._output(
                policy_input,
                action="read_more",
                reason="chain_incomplete_read_more",
                risk_bucket="evidence_gap",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        if policy_input.verifier_output.need_more_evidence and budget_remaining > 0:
            return self._output(
                policy_input,
                action="read_more",
                reason="insufficient_budget_available",
                risk_bucket="evidence_gap",
                conflict=conflict,
                wrong_target=wrong_target,
                soft_final_target_mismatch=soft_final_target_mismatch,
                chain_incomplete=chain_incomplete,
                supported_bridge_not_final=supported_bridge_not_final,
                repair_signal_present=repair_signal_present,
                planner_blocked=planner_blocked,
            )

        return self._output(
            policy_input,
            action="abstain",
            reason="insufficient_budget_exhausted",
            risk_bucket="terminal",
            conflict=conflict,
            wrong_target=wrong_target,
            soft_final_target_mismatch=soft_final_target_mismatch,
            chain_incomplete=chain_incomplete,
            supported_bridge_not_final=supported_bridge_not_final,
            repair_signal_present=repair_signal_present,
            planner_blocked=planner_blocked,
        )

    def _output(
        self,
        policy_input: RiskPolicyInput,
        *,
        action: str,
        reason: str,
        risk_bucket: str,
        conflict: bool,
        wrong_target: bool,
        soft_final_target_mismatch: bool,
        chain_incomplete: bool,
        supported_bridge_not_final: bool,
        repair_signal_present: bool,
        planner_blocked: bool,
    ) -> RiskPolicyOutput:
        metadata = {
            "risk_policy_v1_applied": True,
            "risk_policy_v1_action": action,
            "risk_policy_v1_original_action": policy_input.original_action,
            "risk_policy_v1_reason": reason,
            "risk_policy_v1_risk_bucket": risk_bucket,
            "risk_policy_v1_conflict_signal": conflict,
            "risk_policy_v1_wrong_target_signal": wrong_target,
            "risk_policy_v1_hard_wrong_target_signal": wrong_target,
            "risk_policy_v1_soft_final_target_mismatch": soft_final_target_mismatch,
            "risk_policy_v1_chain_incomplete_signal": chain_incomplete,
            "risk_policy_v1_supported_bridge_not_final": supported_bridge_not_final,
            "risk_policy_v1_evidence_graph_recommended_action": policy_input.evidence_graph.get(
                "evidence_graph_recommended_policy_action",
                "",
            ),
            "risk_policy_v1_budget_remaining": policy_input.budget_remaining,
            "risk_policy_v1_repair_signal_present": repair_signal_present,
            "risk_policy_v1_planner_blocked": planner_blocked,
            "risk_policy_v1_planner_recommended_action": policy_input.repair_metadata.get(
                "repair_planner_recommended_policy_action",
                "",
            ),
        }
        return RiskPolicyOutput(action=action, reason=reason, risk_bucket=risk_bucket, metadata=metadata)


def _can_answer(verifier_output: VerifierOutput) -> bool:
    return (
        verifier_output.overall_sufficiency == "sufficient"
        and not verifier_output.need_more_evidence
        and verifier_output.final_target_match is not False
    )


def _has_repair_signal(repair_metadata: dict) -> bool:
    action = str(repair_metadata.get("repair_query_action") or "")
    if action not in {
        "ordered_hop_repair",
        "partial_chain_next_hop_repair",
        "refine_missing_hop",
        "answer_extraction_repair",
    }:
        return False
    if repair_metadata.get("repair_plan_risk_blocked"):
        return False
    if repair_metadata.get("repair_target_valid") is False:
        return False
    criticality = str(repair_metadata.get("repair_target_criticality") or "critical").strip().lower()
    if criticality not in {"critical", "unknown", ""}:
        return False
    return bool(repair_metadata.get("repair_next_query") or action == "answer_extraction_repair")


def _has_conflict(verifier_output: VerifierOutput, slot_metadata: dict) -> bool:
    if verifier_output.overall_sufficiency == "conflicting":
        return True
    if any(claim.status == "contradicted" for claim in verifier_output.claims):
        return True
    record = slot_metadata.get("slot_binding_verifier_result") or {}
    if not isinstance(record, dict):
        return False
    set_level = record.get("set_level_sufficiency") or {}
    if set_level.get("conflict_on_final_slot") or set_level.get("conflict_on_bridge"):
        return True
    slot_entailment = record.get("slot_bound_entailment") or {}
    return bool(slot_entailment.get("contradicted"))


def _has_hard_wrong_target_signal(verifier_output: VerifierOutput, slot_metadata: dict, evidence_graph: dict) -> bool:
    if evidence_graph.get("evidence_graph_hard_wrong_target"):
        return True
    record = slot_metadata.get("slot_binding_verifier_result") or {}
    if not isinstance(record, dict):
        record = {}
    role_record = record.get("candidate_role_labeler") or {}
    if not isinstance(role_record, dict):
        role_record = {}
    candidate_role = str(role_record.get("candidate_role") or "").strip().lower()
    relation_to_question = str(role_record.get("relation_to_question") or "").strip().lower()
    role_error_type = str(role_record.get("role_error_type") or "").strip().lower()
    if candidate_role in {
        "distractor",
        "wrong_target",
    }:
        return True
    if relation_to_question in {"local_support_only", "unrelated"}:
        return True
    if role_error_type in {"wrong_target", "relation_direction_error", "bridge_as_final", "local_support_only"}:
        return True
    typed_category = str(record.get("typed_reject_category") or "").strip().lower()
    if typed_category in {"wrong_target", "bridge_as_final"}:
        return True
    typed_binding = slot_metadata.get("typed_target_slot_binder_result") or record.get("typed_target_slot_binder_result") or {}
    if isinstance(typed_binding, dict) and typed_binding.get("accepted") is False:
        reason = str(typed_binding.get("reason") or "").lower()
        category = str(typed_binding.get("category") or typed_binding.get("reject_category") or "").lower()
        return any(value in reason or value in category for value in ["wrong_target", "bridge_as_final"])
    return False


def _has_soft_final_target_mismatch(verifier_output: VerifierOutput, slot_metadata: dict, evidence_graph: dict) -> bool:
    if evidence_graph.get("evidence_graph_soft_final_target_mismatch"):
        return True
    if verifier_output.final_target_match is not False:
        return False
    if _has_conflict(verifier_output, slot_metadata):
        return False
    if _has_hard_wrong_target_signal(verifier_output, slot_metadata, evidence_graph):
        return False
    return True
