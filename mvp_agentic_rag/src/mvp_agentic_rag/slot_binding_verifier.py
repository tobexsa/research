from __future__ import annotations

import json
from dataclasses import dataclass, field

from .llm_client import LLMClient, make_llm_client
from .prompts import format_evidence
from .schemas import Passage, Sample
from .slot_ledger import SlotLedger
from .target_slot_binder import build_target_slot_spec


@dataclass(frozen=True)
class QuestionSlotParserResult:
    answer_type: str = ""
    target_relation: str = ""
    final_slot_description: str = ""
    subject_chain: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    forbidden_roles: list[str] = field(default_factory=list)
    decomposition_confidence: float = 0.0

    def to_record(self) -> dict:
        return {
            "answer_type": self.answer_type,
            "target_relation": self.target_relation,
            "subject_chain": list(self.subject_chain),
            "constraints": list(self.constraints),
            "forbidden_roles": list(self.forbidden_roles),
        }

    def to_v1_2_record(self) -> dict:
        record = self.to_record()
        record["final_slot_description"] = self.final_slot_description
        record["decomposition_confidence"] = self.decomposition_confidence
        return record


@dataclass(frozen=True)
class CandidateRoleLabel:
    candidate: str = ""
    normalized_candidate: str = ""
    role: str = ""
    evidence_span: str = ""
    answer_type_match: bool = True
    relation_to_question: str = ""
    role_error_type: str = "none"

    def to_record(self) -> dict:
        return {
            "candidate": self.candidate,
            "role": self.role,
            "evidence_span": self.evidence_span,
            "relation_to_question": self.relation_to_question,
        }

    def to_v1_2_record(self) -> dict:
        return {
            "candidate": self.candidate or None,
            "normalized_candidate": self.normalized_candidate or (self.candidate.strip().lower() or None),
            "candidate_role": self.role or "unknown",
            "answer_type_match": self.answer_type_match,
            "relation_to_question": self.relation_to_question or "ambiguous",
            "role_error_type": self.role_error_type or "none",
        }


@dataclass(frozen=True)
class SlotBoundEntailmentResult:
    question: str = ""
    final_slot: str = "final_target"
    candidate: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    entails_answer: bool = False
    contradicted: bool = False
    entailment_confidence: float = 0.0
    hypothesis: str = ""
    reason: str = ""
    failure_reason: str = "unknown"

    def to_record(self) -> dict:
        return {
            "question": self.question,
            "final_slot": self.final_slot,
            "candidate": self.candidate,
            "evidence_ids": list(self.evidence_ids),
            "entails_answer": self.entails_answer,
            "hypothesis": self.hypothesis,
            "reason": self.reason,
        }

    def to_v1_2_record(self) -> dict:
        return {
            "hypothesis": self.hypothesis,
            "entailed": self.entails_answer,
            "contradicted": self.contradicted,
            "evidence_ids": list(self.evidence_ids),
            "entailment_confidence": self.entailment_confidence,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class RequiredHopBinding:
    hop_index: int = 0
    subject: str = ""
    relation: str = ""
    object: str = ""
    status: str = "missing"
    is_final_hop: bool = False
    supporting_evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_record(self) -> dict:
        return {
            "hop_index": self.hop_index,
            "subject": self.subject,
            "relation": self.relation,
            "object": self.object or None,
            "status": self.status,
            "is_final_hop": self.is_final_hop,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class OrderedHopBindingResult:
    required_hops: list[RequiredHopBinding] = field(default_factory=list)
    filled_hop_index: int = 0
    final_hop_index: int = 0
    final_relation: str = ""
    final_relation_object: str = ""
    candidate_is_final_relation_object: bool = False
    missing_critical_hops: list[str] = field(default_factory=list)
    bound_bridge_values: list[str] = field(default_factory=list)
    chain_complete: bool = False

    def to_record(self) -> dict:
        return {
            "required_hops": [hop.to_record() for hop in self.required_hops],
            "filled_hop_index": self.filled_hop_index,
            "final_hop_index": self.final_hop_index,
            "final_relation": self.final_relation,
            "final_relation_object": self.final_relation_object or None,
            "candidate_is_final_relation_object": self.candidate_is_final_relation_object,
            "missing_critical_hops": list(self.missing_critical_hops),
            "bound_bridge_values": list(self.bound_bridge_values),
            "chain_complete": self.chain_complete,
        }

    def has_signal(self) -> bool:
        return bool(
            self.required_hops
            or self.filled_hop_index
            or self.final_hop_index
            or self.final_relation
            or self.final_relation_object
            or self.missing_critical_hops
            or self.bound_bridge_values
            or self.chain_complete
        )

@dataclass(frozen=True)
class SetLevelSufficiencyResult:
    final_slot_covered: bool = False
    all_required_hops_covered: bool = False
    missing_critical_hops: list[str] = field(default_factory=list)
    noncritical_gaps: list[str] = field(default_factory=list)
    missing_noncritical_hops: list[str] = field(default_factory=list)
    conflict_on_final_slot: bool = False
    conflict_on_bridge: bool = False
    evidence_set_sufficient: bool = False
    sufficiency_confidence: float = 0.0
    uncertainty: float = 1.0

    def to_record(self) -> dict:
        return {
            "final_slot_covered": self.final_slot_covered,
            "all_required_hops_covered": self.all_required_hops_covered,
            "missing_critical_hops": list(self.missing_critical_hops),
            "noncritical_gaps": list(self.noncritical_gaps),
            "conflict_on_final_slot": self.conflict_on_final_slot,
            "uncertainty": self.uncertainty,
        }

    def to_v1_2_record(self) -> dict:
        return {
            "final_slot_covered": self.final_slot_covered,
            "all_required_hops_covered": self.all_required_hops_covered,
            "missing_critical_hops": list(self.missing_critical_hops),
            "missing_noncritical_hops": list(self.missing_noncritical_hops or self.noncritical_gaps),
            "conflict_on_final_slot": self.conflict_on_final_slot,
            "conflict_on_bridge": self.conflict_on_bridge,
            "evidence_set_sufficient": self.evidence_set_sufficient or (
                self.final_slot_covered
                and self.all_required_hops_covered
                and not self.conflict_on_final_slot
            ),
            "sufficiency_confidence": self.sufficiency_confidence,
        }


@dataclass(frozen=True)
class CalibratedDecisionResult:
    action: str = "abstain"
    risk: float | dict = 1.0
    expected_gain: float = 0.0
    reason: str = ""
    abstain_reason: str = "none"

    def to_record(self) -> dict:
        return {
            "action": self.action,
            "risk": self.risk,
            "expected_gain": self.expected_gain,
            "reason": self.reason,
        }

    def to_v1_2_record(self) -> dict:
        risk = self.risk
        if not isinstance(risk, dict):
            risk = {
                "unsupported_risk": float(risk),
                "wrong_target_risk": 0.0,
                "bridge_binding_risk": 0.0,
                "relation_direction_risk": 0.0,
                "candidate_extraction_risk": 0.0,
                "conflict_risk": 0.0,
                "insufficient_evidence_risk": 0.0,
            }
        return {
            "action": self.action,
            "risk": risk,
            "expected_gain": self.expected_gain,
            "abstain_reason": self.abstain_reason,
        }


@dataclass(frozen=True)
class SlotBindingResult:
    slot_name: str = "final_target"
    supports_slot: bool = False
    bound_value: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    slot_relation_match: bool = False
    answer_type_match: bool = False
    reason: str = ""
    question_slot: QuestionSlotParserResult = field(default_factory=QuestionSlotParserResult)
    candidate_roles: list[CandidateRoleLabel] = field(default_factory=list)
    ordered_hop_binding: OrderedHopBindingResult = field(default_factory=OrderedHopBindingResult)
    slot_entailment: SlotBoundEntailmentResult = field(default_factory=SlotBoundEntailmentResult)
    set_level_sufficiency: SetLevelSufficiencyResult = field(default_factory=SetLevelSufficiencyResult)
    decision: CalibratedDecisionResult = field(default_factory=CalibratedDecisionResult)

    def to_record(self) -> dict:
        candidate_role = self.candidate_roles[0] if self.candidate_roles else CandidateRoleLabel(
            candidate=self.bound_value,
            role="final_answer" if self.supports_slot else "unknown",
            relation_to_question="fills_final_slot" if self.supports_slot else "ambiguous",
            answer_type_match=self.answer_type_match,
        )
        decision_head = self.decision.to_v1_2_record()
        if _needs_ordered_hop_repair(self.ordered_hop_binding):
            decision_head = {
                **decision_head,
                "action": "ordered_hop_repair",
            }
        if _decision_can_be_normalized_to_repair(decision_head["action"]) and _needs_answer_extraction_repair(
            self.bound_value,
            self.set_level_sufficiency,
        ):
            decision_head = {
                **decision_head,
                "action": "answer_extraction_repair",
                "abstain_reason": "candidate_extraction_failure",
            }
        return {
            "slot_name": self.slot_name,
            "supports_slot": self.supports_slot,
            "bound_value": self.bound_value,
            "evidence_ids": list(self.evidence_ids),
            "slot_relation_match": self.slot_relation_match,
            "answer_type_match": self.answer_type_match,
            "reason": self.reason,
            "question_slot": self.question_slot.to_record(),
            "candidate_roles": [item.to_record() for item in self.candidate_roles],
            "ordered_hop_binding": self.ordered_hop_binding.to_record(),
            "slot_entailment": self.slot_entailment.to_record(),
            "set_level_sufficiency": self.set_level_sufficiency.to_record(),
            "decision": self.decision.to_record(),
            "question_slot_parser": self.question_slot.to_v1_2_record(),
            "candidate_role_labeler": candidate_role.to_v1_2_record(),
            "slot_bound_entailment": self.slot_entailment.to_v1_2_record(),
            "decision_head": decision_head,
        }


def _decision_can_be_normalized_to_repair(action: str) -> bool:
    return str(action or "") in {
        "abstain",
        "continue_search",
        "read_more_chunks",
        "refine_query",
        "refine_missing_hop",
    }


def _needs_ordered_hop_repair(ordered_hop_binding: OrderedHopBindingResult) -> bool:
    return bool(
        ordered_hop_binding.has_signal()
        and not ordered_hop_binding.chain_complete
        and not ordered_hop_binding.candidate_is_final_relation_object
        and (
            ordered_hop_binding.bound_bridge_values
            or ordered_hop_binding.missing_critical_hops
            or ordered_hop_binding.final_relation
        )
    )


def _needs_answer_extraction_repair(
    bound_value: str,
    set_level_sufficiency: SetLevelSufficiencyResult,
) -> bool:
    return bool(
        not str(bound_value or "").strip()
        and set_level_sufficiency.final_slot_covered
        and (
            set_level_sufficiency.evidence_set_sufficient
            or set_level_sufficiency.all_required_hops_covered
        )
        and not set_level_sufficiency.conflict_on_final_slot
    )


class LLMSlotBindingVerifier:
    def __init__(self, client: LLMClient):
        self.client = client

    def bind_final_slot(
        self,
        sample: Sample,
        evidence: list[Passage],
        slot_ledger: SlotLedger,
    ) -> SlotBindingResult:
        content = self.client.complete(_build_slot_binding_prompt(sample, evidence, slot_ledger))
        try:
            return _parse_slot_binding_result(content)
        except Exception:
            return SlotBindingResult(reason="Slot binding verifier returned non-JSON")


def _build_slot_binding_prompt(
    sample: Sample,
    evidence: list[Passage],
    slot_ledger: SlotLedger,
) -> list[dict[str, str]]:
    target_slot_spec = build_target_slot_spec(sample)
    schema = _slot_binding_schema(sample, target_slot_spec)
    return [
        {
            "role": "system",
            "content": (
                "You are a slot-level evidence binder and slot-aware verifier. Return strict JSON only. "
                "You are a slot-level evidence binder. "
                "Use the five-stage contract exactly: "
                "A. Question Slot Parser, B. Candidate Role Labeler, "
                "C. Slot-Bound Entailment, D. Set-Level Sufficiency Aggregator, "
                "E. Calibrated Decision Head. "
                "Do not directly answer 'candidate supported?' in one step. "
                "First identify the final target slot, then label candidate roles, then test whether "
                "question + final_slot + evidence entails 'the answer to the question is candidate', "
                "then aggregate coverage/disagreement/conflict over the full evidence set, and only then emit an action. "
                "Do not answer from a bridge slot, intermediate entity, container/location, date component, or "
                "related but non-final fact. If the evidence only supports a bridge slot or an intermediate fact, "
                "the final slot must not be marked supported. If expected_granularity is day, a bare year is not a "
                "valid final answer; if the target is a count, bridge years or dates are not valid counts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n\n"
                "A. Question Slot Parser\n"
                f"{json.dumps(target_slot_spec.to_record(), ensure_ascii=False)}\n\n"
                "B. Candidate Role Labeler\n"
                "Label every candidate by role. Role must distinguish final_answer, bridge_entity, evidence_date, "
                "evidence_location, distractor.\n\n"
                "C. Slot-Bound Entailment\n"
                "Evaluate whether question + final_slot + evidence entails: "
                "\"the answer to the question is candidate\".\n\n"
                "D. Set-Level Sufficiency Aggregator\n"
                "Aggregate all evidence; do not average passage scores.\n\n"
                "E. Calibrated Decision Head\n"
                "Output action, risk, expected_gain, and reason only after the previous stages.\n\n"
                f"Target slot spec:\n{json.dumps(target_slot_spec.to_record(), ensure_ascii=False)}\n\n"
                f"Slot ledger:\n{json.dumps(slot_ledger.to_record(), ensure_ascii=False)}\n\n"
                f"Retrieved evidence:\n{format_evidence(evidence)}\n\n"
                f"Return JSON with this schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        },
    ]


def _parse_slot_binding_result(content: str) -> SlotBindingResult:
    payload = _extract_json(content)
    question_slot = _parse_question_slot_parser_result(payload.get("question_slot", {}))
    candidate_roles = [
        _parse_candidate_role_label(item) for item in payload.get("candidate_roles", []) if isinstance(item, dict)
    ]
    if not candidate_roles and isinstance(payload.get("candidate_role_labeler"), dict):
        candidate_roles = [_parse_candidate_role_label(payload.get("candidate_role_labeler", {}))]
    ordered_hop_binding = _parse_ordered_hop_binding_result(payload.get("ordered_hop_binding", {}))
    slot_entailment = _parse_slot_entailment_result(payload.get("slot_entailment", {}))
    if not slot_entailment.entails_answer and isinstance(payload.get("slot_bound_entailment"), dict):
        slot_entailment = _parse_slot_entailment_result(payload.get("slot_bound_entailment", {}))
    set_level_sufficiency = _parse_set_level_sufficiency_result(payload.get("set_level_sufficiency", {}))
    decision = _parse_calibrated_decision_result(payload.get("decision", {}))
    if decision.action == "abstain" and isinstance(payload.get("decision_head"), dict):
        decision = _parse_calibrated_decision_result(payload.get("decision_head", {}))
    return SlotBindingResult(
        slot_name=str(payload.get("slot_name", "final_target")),
        supports_slot=bool(payload.get("supports_slot", False)),
        bound_value=str(payload.get("bound_value", "")),
        evidence_ids=[str(value) for value in payload.get("evidence_ids", [])],
        slot_relation_match=bool(payload.get("slot_relation_match", False)),
        answer_type_match=bool(payload.get("answer_type_match", False)),
        reason=str(payload.get("reason", "")),
        question_slot=question_slot,
        candidate_roles=candidate_roles,
        ordered_hop_binding=ordered_hop_binding,
        slot_entailment=slot_entailment,
        set_level_sufficiency=set_level_sufficiency,
        decision=decision,
    )


def _slot_binding_schema(sample: Sample, target_slot_spec) -> dict:
    question = sample.question
    return {
        "question_slot": {
            "answer_type": target_slot_spec.target_type,
            "target_relation": "final requested target",
            "subject_chain": ["entity_0", "bridge_entity_1"],
            "constraints": list(target_slot_spec.relation_cues),
            "forbidden_roles": ["intermediate_entity", "date_component", "container_location", "related_number"],
        },
        "candidate_roles": [
            {
                "candidate": "short answer candidate",
                "normalized_candidate": "normalized short answer candidate",
                "role": "final_answer|bridge_entity|subject_entity|evidence_date|evidence_location|container_location|related_number|distractor|unknown",
                "evidence_span": "supporting span",
                "answer_type_match": True,
                "relation_to_question": "fills_final_slot|supports_bridge|local_support_only|unrelated|ambiguous",
                "role_error_type": "none|bridge_as_final|subject_as_final|container_as_final|date_component_as_final|related_number_as_final|relation_direction_error|local_support_only|unknown",
            }
        ],
        "candidate_role_labeler": {
            "candidate": "short answer candidate or null",
            "normalized_candidate": "normalized short answer candidate or null",
            "candidate_role": "final_answer|bridge_entity|subject_entity|evidence_date|evidence_location|container_location|related_number|distractor|unknown",
            "answer_type_match": True,
            "relation_to_question": "fills_final_slot|supports_bridge|local_support_only|unrelated|ambiguous",
            "role_error_type": "none|bridge_as_final|subject_as_final|container_as_final|date_component_as_final|related_number_as_final|relation_direction_error|local_support_only|unknown",
        },
        "ordered_hop_binding": {
            "required_hops": [
                {
                    "hop_index": 1,
                    "subject": "string",
                    "relation": "string",
                    "object": "string or null",
                    "status": "bound|missing|contradicted|ambiguous",
                    "is_final_hop": False,
                    "supporting_evidence_ids": [],
                    "confidence": 0.0,
                }
            ],
            "filled_hop_index": 0,
            "final_hop_index": 0,
            "final_relation": "string",
            "final_relation_object": "string or null",
            "candidate_is_final_relation_object": False,
            "missing_critical_hops": [],
            "bound_bridge_values": [],
            "chain_complete": False,
        },
        "slot_entailment": {
            "question": question,
            "final_slot": "final_target",
            "candidate": "candidate answer",
            "evidence_ids": ["passage id"],
            "entails_answer": True,
            "contradicted": False,
            "entailment_confidence": 0.0,
            "hypothesis": "the answer to the question is candidate",
            "reason": "brief reason",
            "failure_reason": "unsupported|wrong_target|missing_bridge|relation_direction_error|conflict|no_candidate|unknown",
        },
        "slot_bound_entailment": {
            "hypothesis": "The answer to the question is <candidate>.",
            "entailed": False,
            "contradicted": False,
            "evidence_ids": [],
            "entailment_confidence": 0.0,
            "failure_reason": "unsupported|wrong_target|missing_bridge|relation_direction_error|conflict|no_candidate|unknown",
        },
        "set_level_sufficiency": {
            "final_slot_covered": True,
            "all_required_hops_covered": True,
            "missing_critical_hops": [],
            "noncritical_gaps": [],
            "missing_noncritical_hops": [],
            "conflict_on_final_slot": False,
            "conflict_on_bridge": False,
            "evidence_set_sufficient": True,
            "sufficiency_confidence": 0.0,
            "uncertainty": 0.0,
        },
        "decision": {
            "action": "answer|answer_extraction_repair|ordered_hop_repair|refine_missing_hop|continue_search|read_more_chunks|disambiguate_conflict|abstain",
            "risk": 0.0,
            "expected_gain": 0.0,
            "reason": "final slot supported; only non-critical gap remains",
            "abstain_reason": "none|insufficient_evidence|unresolved_conflict|ambiguous_entity|candidate_extraction_failure|budget_exhausted|verifier_low_confidence",
        },
        "decision_head": {
            "action": "answer|answer_extraction_repair|ordered_hop_repair|refine_missing_hop|continue_search|read_more_chunks|disambiguate_conflict|abstain",
            "risk": {
                "unsupported_risk": 0.0,
                "wrong_target_risk": 0.0,
                "bridge_binding_risk": 0.0,
                "relation_direction_risk": 0.0,
                "candidate_extraction_risk": 0.0,
                "conflict_risk": 0.0,
                "insufficient_evidence_risk": 0.0,
            },
            "expected_gain": 0.0,
            "abstain_reason": "none|insufficient_evidence|unresolved_conflict|ambiguous_entity|candidate_extraction_failure|budget_exhausted|verifier_low_confidence",
        },
        "slot_name": "final_target",
        "supports_slot": True,
        "bound_value": "short value that fills final_target, or empty string",
        "evidence_ids": ["passage id"],
        "slot_relation_match": True,
        "answer_type_match": True,
        "reason": "brief evidence-grounded reason",
    }


def _parse_question_slot_parser_result(payload: dict) -> QuestionSlotParserResult:
    return QuestionSlotParserResult(
        answer_type=str(payload.get("answer_type", "")),
        target_relation=str(payload.get("target_relation", "")),
        final_slot_description=str(payload.get("final_slot_description", "")),
        subject_chain=[str(value) for value in payload.get("subject_chain", [])],
        constraints=[str(value) for value in payload.get("constraints", [])],
        forbidden_roles=[str(value) for value in payload.get("forbidden_roles", [])],
        decomposition_confidence=float(payload.get("decomposition_confidence", 0.0) or 0.0),
    )


def _parse_candidate_role_label(payload: dict) -> CandidateRoleLabel:
    return CandidateRoleLabel(
        candidate=str(payload.get("candidate", "")),
        normalized_candidate=str(payload.get("normalized_candidate", "")),
        role=str(payload.get("role") or payload.get("candidate_role", "")),
        evidence_span=str(payload.get("evidence_span", "")),
        answer_type_match=bool(payload.get("answer_type_match", True)),
        relation_to_question=str(payload.get("relation_to_question", "")),
        role_error_type=str(payload.get("role_error_type", "none")),
    )


def _parse_slot_entailment_result(payload: dict) -> SlotBoundEntailmentResult:
    return SlotBoundEntailmentResult(
        question=str(payload.get("question", "")),
        final_slot=str(payload.get("final_slot", "final_target")),
        candidate=str(payload.get("candidate", "")),
        evidence_ids=[str(value) for value in payload.get("evidence_ids", [])],
        entails_answer=bool(payload.get("entails_answer", payload.get("entailed", False))),
        contradicted=bool(payload.get("contradicted", False)),
        entailment_confidence=float(payload.get("entailment_confidence", 0.0) or 0.0),
        hypothesis=str(payload.get("hypothesis", "")),
        reason=str(payload.get("reason", "")),
        failure_reason=str(payload.get("failure_reason", "unknown")),
    )


def _parse_ordered_hop_binding_result(payload: dict) -> OrderedHopBindingResult:
    return OrderedHopBindingResult(
        required_hops=[
            _parse_required_hop_binding(item) for item in payload.get("required_hops", []) if isinstance(item, dict)
        ],
        filled_hop_index=int(payload.get("filled_hop_index", 0) or 0),
        final_hop_index=int(payload.get("final_hop_index", 0) or 0),
        final_relation=str(payload.get("final_relation", "")),
        final_relation_object=str(payload.get("final_relation_object") or ""),
        candidate_is_final_relation_object=bool(payload.get("candidate_is_final_relation_object", False)),
        missing_critical_hops=[str(value) for value in payload.get("missing_critical_hops", [])],
        bound_bridge_values=[str(value) for value in payload.get("bound_bridge_values", [])],
        chain_complete=bool(payload.get("chain_complete", False)),
    )


def _parse_required_hop_binding(payload: dict) -> RequiredHopBinding:
    return RequiredHopBinding(
        hop_index=int(payload.get("hop_index", 0) or 0),
        subject=str(payload.get("subject", "")),
        relation=str(payload.get("relation", "")),
        object=str(payload.get("object") or ""),
        status=str(payload.get("status", "missing")),
        is_final_hop=bool(payload.get("is_final_hop", False)),
        supporting_evidence_ids=[str(value) for value in payload.get("supporting_evidence_ids", [])],
        confidence=float(payload.get("confidence", 0.0) or 0.0),
    )


def _parse_set_level_sufficiency_result(payload: dict) -> SetLevelSufficiencyResult:
    return SetLevelSufficiencyResult(
        final_slot_covered=bool(payload.get("final_slot_covered", False)),
        all_required_hops_covered=bool(payload.get("all_required_hops_covered", False)),
        missing_critical_hops=[str(value) for value in payload.get("missing_critical_hops", [])],
        noncritical_gaps=[str(value) for value in payload.get("noncritical_gaps", [])],
        missing_noncritical_hops=[str(value) for value in payload.get("missing_noncritical_hops", [])],
        conflict_on_final_slot=bool(payload.get("conflict_on_final_slot", False)),
        conflict_on_bridge=bool(payload.get("conflict_on_bridge", False)),
        evidence_set_sufficient=bool(payload.get("evidence_set_sufficient", False)),
        sufficiency_confidence=float(payload.get("sufficiency_confidence", 0.0) or 0.0),
        uncertainty=float(payload.get("uncertainty", 1.0) or 0.0),
    )


def _parse_calibrated_decision_result(payload: dict) -> CalibratedDecisionResult:
    return CalibratedDecisionResult(
        action=str(payload.get("action", "abstain")),
        risk=payload.get("risk", 1.0),
        expected_gain=float(payload.get("expected_gain", 0.0) or 0.0),
        reason=str(payload.get("reason", "")),
        abstain_reason=str(payload.get("abstain_reason", "none")),
    )


def validate_ordered_hop_record(record: dict) -> list[str]:
    errors: list[str] = []
    required = [
        "question_slot_parser",
        "candidate_role_labeler",
        "ordered_hop_binding",
        "slot_bound_entailment",
        "set_level_sufficiency",
        "decision_head",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing:{key}")
    ordered = record.get("ordered_hop_binding", {})
    for key in [
        "required_hops",
        "filled_hop_index",
        "final_hop_index",
        "final_relation",
        "final_relation_object",
        "candidate_is_final_relation_object",
        "missing_critical_hops",
        "bound_bridge_values",
        "chain_complete",
    ]:
        if key not in ordered:
            errors.append(f"missing:ordered_hop_binding.{key}")
    role = record.get("candidate_role_labeler", {})
    for key in ["candidate", "candidate_role", "relation_to_question", "role_error_type"]:
        if key not in role:
            errors.append(f"missing:candidate_role_labeler.{key}")
    decision = record.get("decision_head", {})
    if "action" not in decision:
        errors.append("missing:decision_head.action")
    if "risk" not in decision:
        errors.append("missing:decision_head.risk")
    return errors


def _extract_json(content: str) -> dict:
    stripped = str(content or "").strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end >= start:
        stripped = stripped[start : end + 1]
    return json.loads(stripped)


def make_slot_binding_verifier(config: dict) -> LLMSlotBindingVerifier:
    return LLMSlotBindingVerifier(make_llm_client(config, prefix="slot_binding_verifier"))
