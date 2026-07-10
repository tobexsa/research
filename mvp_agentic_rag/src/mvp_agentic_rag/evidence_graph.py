from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import Sample, VerifierOutput


@dataclass(frozen=True)
class EvidenceGraphNode:
    node_id: str
    node_type: str
    status: str
    query: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceGraphState:
    nodes: list[EvidenceGraphNode] = field(default_factory=list)
    chain_complete: bool = False
    chain_incomplete: bool = False
    final_supported: bool = False
    hard_conflict: bool = False
    hard_wrong_target: bool = False
    soft_final_target_mismatch: bool = False
    supported_bridge_not_final: bool = False
    next_missing_node_id: str = ""
    next_missing_query: str = ""
    recommended_policy_action: str = ""
    reason: str = ""

    def to_record(self) -> dict[str, Any]:
        return {
            "evidence_graph_lite_v1": True,
            "evidence_graph_chain_complete": self.chain_complete,
            "evidence_graph_chain_incomplete": self.chain_incomplete,
            "evidence_graph_final_supported": self.final_supported,
            "evidence_graph_hard_conflict": self.hard_conflict,
            "evidence_graph_hard_wrong_target": self.hard_wrong_target,
            "evidence_graph_soft_final_target_mismatch": self.soft_final_target_mismatch,
            "evidence_graph_supported_bridge_not_final": self.supported_bridge_not_final,
            "evidence_graph_next_missing_node_id": self.next_missing_node_id,
            "evidence_graph_next_missing_query": self.next_missing_query,
            "evidence_graph_recommended_policy_action": self.recommended_policy_action,
            "evidence_graph_reason": self.reason,
            "evidence_graph_nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "status": node.status,
                    "query": node.query,
                    "evidence_ids": node.evidence_ids,
                    "depends_on": node.depends_on,
                }
                for node in self.nodes
            ],
        }


def build_evidence_graph_state(
    sample: Sample,
    verifier_output: VerifierOutput,
    slot_metadata: dict,
    repair_metadata: dict,
    budget_remaining: int,
) -> EvidenceGraphState:
    hard_conflict = _has_hard_conflict(verifier_output, slot_metadata)
    hard_wrong_target = _has_hard_wrong_target(slot_metadata)
    soft_final_target_mismatch = (
        verifier_output.final_target_match is False
        and not hard_conflict
        and not hard_wrong_target
    )
    supported_bridge_not_final = (
        _has_supported_bridge_signal(slot_metadata)
        and not hard_conflict
        and not hard_wrong_target
    )
    valid_repair_query = _valid_repair_query(repair_metadata)
    final_supported = (
        verifier_output.overall_sufficiency == "sufficient"
        and not verifier_output.need_more_evidence
        and verifier_output.final_target_match is not False
        and not hard_conflict
        and not hard_wrong_target
    )
    chain_incomplete = bool(
        verifier_output.need_more_evidence
        or soft_final_target_mismatch
        or supported_bridge_not_final
        or valid_repair_query
    ) and not final_supported
    chain_complete = final_supported and not chain_incomplete
    next_missing_query = str(repair_metadata.get("repair_next_query") or "").strip()
    next_missing_node_id = "repair_target" if next_missing_query else ("next_missing_hop" if chain_incomplete else "")
    action, reason = _recommend_action(
        hard_conflict=hard_conflict,
        hard_wrong_target=hard_wrong_target,
        final_supported=final_supported,
        valid_repair_query=valid_repair_query,
        chain_incomplete=chain_incomplete,
        budget_remaining=budget_remaining,
    )

    return EvidenceGraphState(
        nodes=_nodes_for_state(sample, final_supported, chain_incomplete, next_missing_query),
        chain_complete=chain_complete,
        chain_incomplete=chain_incomplete,
        final_supported=final_supported,
        hard_conflict=hard_conflict,
        hard_wrong_target=hard_wrong_target,
        soft_final_target_mismatch=soft_final_target_mismatch,
        supported_bridge_not_final=supported_bridge_not_final,
        next_missing_node_id=next_missing_node_id,
        next_missing_query=next_missing_query,
        recommended_policy_action=action,
        reason=reason,
    )


def _has_hard_conflict(verifier_output: VerifierOutput, slot_metadata: dict) -> bool:
    if verifier_output.overall_sufficiency == "conflicting":
        return True
    if any(claim.status == "contradicted" for claim in verifier_output.claims):
        return True
    record = _binding_record(slot_metadata)
    set_level = record.get("set_level_sufficiency") or {}
    if isinstance(set_level, dict) and (set_level.get("conflict_on_final_slot") or set_level.get("conflict_on_bridge")):
        return True
    slot_entailment = record.get("slot_bound_entailment") or {}
    return isinstance(slot_entailment, dict) and bool(slot_entailment.get("contradicted"))


def _has_hard_wrong_target(slot_metadata: dict) -> bool:
    record = _binding_record(slot_metadata)
    role_record = record.get("candidate_role_labeler") or {}
    if not isinstance(role_record, dict):
        role_record = {}
    candidate_role = _norm(role_record.get("candidate_role"))
    relation_to_question = _norm(role_record.get("relation_to_question"))
    role_error_type = _norm(role_record.get("role_error_type"))
    typed_category = _norm(record.get("typed_reject_category"))
    if candidate_role in {"distractor", "wrong_target"}:
        return True
    if relation_to_question in {"local_support_only", "unrelated"}:
        return True
    if role_error_type in {"wrong_target", "relation_direction_error", "bridge_as_final", "local_support_only"}:
        return True
    if typed_category in {"wrong_target", "bridge_as_final"}:
        return True
    typed_binding = slot_metadata.get("typed_target_slot_binder_result") or record.get("typed_target_slot_binder_result") or {}
    if isinstance(typed_binding, dict) and typed_binding.get("accepted") is False:
        reason = _norm(typed_binding.get("reason"))
        category = _norm(typed_binding.get("category") or typed_binding.get("reject_category"))
        return any(value in reason or value in category for value in ("wrong_target", "bridge_as_final"))
    return False


def _has_supported_bridge_signal(slot_metadata: dict) -> bool:
    record = _binding_record(slot_metadata)
    role_record = record.get("candidate_role_labeler") or {}
    if not isinstance(role_record, dict):
        role_record = {}
    return (
        _norm(role_record.get("candidate_role")) == "bridge_entity"
        or _norm(role_record.get("relation_to_question")) == "supports_bridge"
    )


def _valid_repair_query(repair_metadata: dict) -> bool:
    if repair_metadata.get("repair_plan_risk_blocked") is True:
        return False
    if repair_metadata.get("repair_target_valid") is False:
        return False
    return bool(str(repair_metadata.get("repair_next_query") or "").strip())


def _recommend_action(
    *,
    hard_conflict: bool,
    hard_wrong_target: bool,
    final_supported: bool,
    valid_repair_query: bool,
    chain_incomplete: bool,
    budget_remaining: int,
) -> tuple[str, str]:
    budget = int(budget_remaining or 0)
    if hard_conflict:
        return ("disambiguate_conflict", "hard_conflict") if budget > 0 else ("abstain", "hard_conflict_budget_exhausted")
    if hard_wrong_target:
        return ("disambiguate_conflict", "hard_wrong_target") if budget > 0 else ("abstain", "hard_wrong_target_budget_exhausted")
    if final_supported:
        return "answer", "final_supported"
    if valid_repair_query and budget > 0:
        return "repair_missing_hop", "valid_repair_query"
    if chain_incomplete and budget > 0:
        return "read_more", "chain_incomplete"
    return "abstain", "insufficient_budget_exhausted"


def _nodes_for_state(
    sample: Sample,
    final_supported: bool,
    chain_incomplete: bool,
    next_missing_query: str,
) -> list[EvidenceGraphNode]:
    nodes = [
        EvidenceGraphNode(
            node_id="question",
            node_type="question",
            status="observed",
            query=sample.question,
        )
    ]
    if next_missing_query:
        nodes.append(
            EvidenceGraphNode(
                node_id="repair_target",
                node_type="missing_hop",
                status="unresolved",
                query=next_missing_query,
                depends_on=["question"],
            )
        )
    else:
        nodes.append(
            EvidenceGraphNode(
                node_id="final_slot",
                node_type="final_slot",
                status="supported" if final_supported else ("unresolved" if chain_incomplete else "unknown"),
                depends_on=["question"],
            )
        )
    return nodes


def _binding_record(slot_metadata: dict) -> dict:
    record = slot_metadata.get("slot_binding_verifier_result") or {}
    return record if isinstance(record, dict) else {}


def _norm(value) -> str:
    return str(value or "").strip().lower()
