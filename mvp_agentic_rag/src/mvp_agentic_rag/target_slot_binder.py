from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .schemas import Passage, Sample
from .slot_ledger import SlotLedger, evidence_ids_are_local

if TYPE_CHECKING:
    from .slot_binding_verifier import SlotBindingResult


@dataclass(frozen=True)
class TargetSlotSpec:
    target_type: str
    expected_granularity: str = ""
    final_slot: str = "span"
    final_slot_description: str = ""
    relation_cues: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        return {
            "target_type": self.target_type,
            "expected_granularity": self.expected_granularity,
            "final_slot": self.final_slot,
            "final_slot_description": self.final_slot_description,
            "relation_cues": list(self.relation_cues),
        }


@dataclass(frozen=True)
class TargetSlotBindingDecision:
    accepted: bool
    reason: str
    target_type: str
    expected_granularity: str = ""

    def to_record(self) -> dict:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "target_type": self.target_type,
            "expected_granularity": self.expected_granularity,
        }


def build_target_slot_spec(sample: Sample) -> TargetSlotSpec:
    question = _normalize(sample.question)
    target_type = _classify_target_type(question)
    return TargetSlotSpec(
        target_type=target_type,
        expected_granularity=_expected_granularity(question, target_type),
        final_slot=_final_slot_name(target_type),
        final_slot_description=_final_slot_description(question, target_type),
        relation_cues=_relation_cues(question, target_type),
    )


def validate_slot_binding_result(
    sample: Sample,
    evidence: list[Passage],
    slot_ledger: SlotLedger,
    binding_result: "SlotBindingResult",
    structured_acceptance: bool = False,
    ordered_hop_gate: bool = False,
) -> TargetSlotBindingDecision:
    spec = build_target_slot_spec(sample)
    target_type = slot_ledger.plan.final_target_type or spec.target_type
    expected_granularity = spec.expected_granularity

    def reject(reason: str) -> TargetSlotBindingDecision:
        return TargetSlotBindingDecision(False, reason, target_type, expected_granularity)

    structured_final_slot = structured_acceptance and _structured_final_slot_supported(binding_result)

    if not binding_result.supports_slot and not structured_final_slot:
        return reject("binding_verifier_rejected")
    if binding_result.slot_name != slot_ledger.plan.final_slot:
        return reject("non_final_slot")
    if not binding_result.bound_value.strip():
        return reject("empty_bound_value")
    if not binding_result.slot_relation_match and not structured_final_slot:
        return reject("slot_relation_mismatch")
    if not binding_result.answer_type_match and not structured_final_slot:
        return reject("answer_type_mismatch")
    if not binding_result.evidence_ids:
        return reject("missing_evidence_ids")
    retrieved_ids = {passage.passage_id for passage in evidence}
    if not set(binding_result.evidence_ids).issubset(retrieved_ids):
        return reject("unretrieved_evidence")
    if not evidence_ids_are_local(binding_result.evidence_ids, sample.sample_id):
        return reject("nonlocal_evidence")
    if ordered_hop_gate:
        ordered_fallback_reason = _ordered_hop_nonfatal_reason(binding_result)
        ordered_rejection = _ordered_hop_rejection_reason(sample, evidence, binding_result)
        if ordered_rejection:
            return reject(ordered_rejection)
    else:
        ordered_fallback_reason = ""

    value = binding_result.bound_value.strip()
    cited_text = _cited_text(evidence, binding_result.evidence_ids)
    weak_match_reason = ""
    if target_type == "date":
        value_kind = _date_value_kind(value)
        if expected_granularity == "day" and value_kind == "year":
            return reject("date_granularity_mismatch")
        if value_kind == "none":
            return reject("date_type_mismatch")
    elif target_type == "year":
        if not _contains_year(value):
            return reject("year_type_mismatch")
    elif target_type == "century":
        if not (_contains_century(value) or _contains_year(value)):
            return reject("century_type_mismatch")
    elif target_type in {"count", "population", "number"}:
        if not _contains_number(value):
            return reject("number_type_mismatch")
        if not _has_count_relation_cue(sample.question, cited_text, value):
            if not _allows_weak_count_match(sample.question, value, binding_result):
                return reject("count_relation_mismatch")
            weak_match_reason = "count_relation_weak_match"

    if structured_final_slot:
        return TargetSlotBindingDecision(
            True,
            "structured_final_slot_acceptance",
            target_type,
            expected_granularity,
        )
    if weak_match_reason:
        return TargetSlotBindingDecision(True, weak_match_reason, target_type, expected_granularity)
    if ordered_fallback_reason:
        return TargetSlotBindingDecision(True, ordered_fallback_reason, target_type, expected_granularity)
    return TargetSlotBindingDecision(True, "accepted", target_type, expected_granularity)


def _ordered_hop_rejection_reason(
    sample: Sample,
    evidence: list[Passage],
    binding_result: "SlotBindingResult",
) -> str:
    value = binding_result.bound_value.strip().lower()
    candidate_roles = list(binding_result.candidate_roles)
    ordered = binding_result.ordered_hop_binding
    if ordered.has_signal():
        if _mouth_watercourse_bridge_evidence_only(sample, evidence, binding_result):
            return "mouth_watercourse_bridge_evidence_only"
        if _ordered_relation_depth_mismatch(sample, binding_result):
            return "ordered_relation_depth_mismatch"
        if not ordered.candidate_is_final_relation_object:
            if _ordered_hop_nonfatal_reason(binding_result):
                return ""
            return "candidate_not_final_relation_object"
        if not ordered.chain_complete:
            return "ordered_chain_incomplete"
    if not candidate_roles:
        return "missing_candidate_role"
    final_role = any(
        role.role == "final_answer"
        and role.relation_to_question == "fills_final_slot"
        and (not value or role.candidate.strip().lower() == value)
        for role in candidate_roles
    )
    if not final_role:
        return "candidate_role_not_final_answer"
    if not binding_result.slot_entailment.entails_answer:
        return "slot_bound_entailment_failed"
    if not binding_result.set_level_sufficiency.final_slot_covered:
        return "final_slot_not_covered"
    if binding_result.set_level_sufficiency.conflict_on_final_slot:
        return "final_slot_conflict"
    return ""


def _mouth_watercourse_bridge_evidence_only(
    sample: Sample,
    evidence: list[Passage],
    binding_result: "SlotBindingResult",
) -> bool:
    question = _normalize(sample.question)
    if "mouth" not in question or "watercourse" not in question:
        return False
    if "body of water" not in question and "river" not in question:
        return False
    value = binding_result.bound_value.strip()
    if not value:
        return False
    cited = _normalize(_cited_text(evidence, binding_result.evidence_ids))
    if _normalize(value) not in cited:
        return False
    final_relation = _normalize(binding_result.ordered_hop_binding.final_relation)
    if "mouth" not in final_relation and "watercourse" not in final_relation:
        return False
    bridge_only_cues = [
        "bounded by",
        "in the north",
        "in the south",
        "in the east",
        "in the west",
        "located",
        "situated",
        "by the",
    ]
    final_watercourse_cues = [
        "mouth",
        "flows",
        "flows from",
        "flows west",
        "flows east",
        "confluence",
        "continues as",
        "tributary",
        "delta",
    ]
    return any(cue in cited for cue in bridge_only_cues) and not any(
        cue in cited for cue in final_watercourse_cues
    )


def _ordered_relation_depth_mismatch(sample: Sample, binding_result: "SlotBindingResult") -> bool:
    question = _normalize(sample.question)
    ordered = binding_result.ordered_hop_binding
    relation = _normalize(ordered.final_relation)
    if "mouth" in question and ("watercourse" in question or "body of water" in question):
        return not any(cue in relation for cue in ["mouth", "name", "called"])
    return False


def _ordered_hop_nonfatal_reason(binding_result: "SlotBindingResult") -> str:
    ordered = binding_result.ordered_hop_binding
    if not ordered.has_signal():
        return ""
    if ordered.candidate_is_final_relation_object:
        return ""
    if not ordered.chain_complete or ordered.missing_critical_hops:
        return ""
    if not _strong_final_slot_signal(binding_result):
        return ""
    return "ordered_hop_schema_conflict_fallback"


def _strong_final_slot_signal(binding_result: "SlotBindingResult") -> bool:
    value = binding_result.bound_value.strip().lower()
    if not value:
        return False
    has_final_role = any(
        role.role == "final_answer"
        and role.relation_to_question == "fills_final_slot"
        and (not role.candidate.strip() or role.candidate.strip().lower() == value)
        for role in binding_result.candidate_roles
    )
    if not has_final_role:
        return False
    if not binding_result.slot_entailment.entails_answer:
        return False
    if not binding_result.set_level_sufficiency.final_slot_covered:
        return False
    if not binding_result.set_level_sufficiency.all_required_hops_covered:
        return False
    if binding_result.set_level_sufficiency.conflict_on_final_slot:
        return False
    return True


def _structured_final_slot_supported(binding_result: "SlotBindingResult") -> bool:
    if binding_result.slot_name != "final_target":
        return False
    value = binding_result.bound_value.strip().lower()
    has_final_role = any(
        role.role == "final_answer"
        and role.relation_to_question == "fills_final_slot"
        and (not value or role.candidate.strip().lower() == value)
        for role in binding_result.candidate_roles
    )
    if not has_final_role:
        return False
    if not binding_result.slot_entailment.entails_answer:
        return False
    if binding_result.slot_entailment.candidate.strip().lower() != value:
        return False
    if not binding_result.set_level_sufficiency.final_slot_covered:
        return False
    if binding_result.set_level_sufficiency.conflict_on_final_slot:
        return False
    return True


def _classify_target_type(normalized_question: str) -> str:
    if normalized_question.startswith("when ") or " what day " in f" {normalized_question} " or "what date" in normalized_question:
        return "date"
    if "what year" in normalized_question:
        return "year"
    if "what century" in normalized_question:
        return "century"
    if "population" in normalized_question:
        return "population"
    if normalized_question.startswith("how many ") or "how much" in normalized_question:
        return "count"
    if normalized_question.startswith("who ") or " who " in f" {normalized_question} ":
        return "person"
    if normalized_question.startswith("where ") or " located" in normalized_question:
        return "location"
    return "entity"


def _expected_granularity(question: str, target_type: str) -> str:
    normalized = _normalize(question)
    if target_type == "date":
        if "what day" in normalized or "what date" in normalized:
            return "day"
        return "date"
    if target_type == "year":
        return "year"
    if target_type == "century":
        return "century"
    return ""


def _final_slot_name(target_type: str) -> str:
    return {
        "date": "date_of_event",
        "year": "year_of_event",
        "century": "century_of_event",
        "count": "count_value",
        "population": "population_value",
        "number": "number_value",
        "person": "person_name",
        "location": "location_name",
        "organization": "organization_name",
        "boolean": "boolean_value",
    }.get(target_type, "answer_span")


def _final_slot_description(question: str, target_type: str) -> str:
    slot_name = _final_slot_name(target_type)
    return f"{slot_name} requested by the question: {question}"


def _relation_cues(question: str, target_type: str) -> list[str]:
    normalized = _normalize(question)
    cues: list[str] = []
    cue_groups = [
        (("death", "died", "die"), "death"),
        (("born", "birth"), "birth"),
        (("release", "released"), "release"),
        (("premiere", "premiered"), "premiere"),
        (("founded", "founding", "established"), "founding"),
        (("occur", "occurred", "times"), "occurrence"),
        (("mouth",), "mouth"),
        (("watercourse",), "watercourse"),
        (("population",), "population"),
    ]
    for triggers, label in cue_groups:
        if any(trigger in normalized for trigger in triggers):
            cues.append(label)
    if target_type in {"count", "population", "number"} and not cues:
        cues.extend(["count", "number", "total"])
    return list(dict.fromkeys(cues))


def _cited_text(evidence: list[Passage], evidence_ids: list[str]) -> str:
    target_ids = set(evidence_ids)
    return " ".join(
        f"{passage.title} {passage.text}" for passage in evidence if passage.passage_id in target_ids
    )


def _date_value_kind(value: str) -> str:
    text = str(value or "")
    month_names = (
        "january|february|march|april|may|june|july|august|september|october|november|december|"
        "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    )
    if re.search(rf"\b(?:{month_names})\.?\s+\d{{1,2}}(?:,\s*\d{{4}})?\b", text, flags=re.IGNORECASE):
        return "day"
    if re.search(rf"\b\d{{1,2}}\s+(?:{month_names})\.?(?:\s+\d{{4}})?\b", text, flags=re.IGNORECASE):
        return "day"
    if re.fullmatch(r"\s*(1[0-9]{3}|20[0-9]{2})\s*", text):
        return "year"
    if _contains_year(text):
        return "date"
    return "none"


def _contains_year(value: str) -> bool:
    return bool(re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(value or "")))


def _contains_century(value: str) -> bool:
    return bool(re.search(r"\b\d{1,2}(?:st|nd|rd|th)(?:\s*[- ]?\s*century)?\b", str(value or ""), flags=re.IGNORECASE))


def _contains_number(value: str) -> bool:
    return bool(re.search(r"\b\d[\d,]*(?:\.\d+)?\b", str(value or "")))


def _has_count_relation_cue(question: str, cited_text: str, value: str) -> bool:
    normalized_question = _normalize(question)
    if "population" in normalized_question:
        required = ["population"]
    elif "how many" in normalized_question and "times" in normalized_question:
        required = ["occur", "occurred", "occurs", "times"]
    else:
        required = ["count", "number", "total", "population", "times"]
    window = _value_window(cited_text, value)
    return any(cue in _normalize(window) for cue in required)


def _allows_weak_count_match(question: str, value: str, binding_result: "SlotBindingResult") -> bool:
    normalized_question = _normalize(question)
    if not (normalized_question.startswith("how many ") or " how many " in f" {normalized_question} "):
        return False
    if _looks_like_year(value):
        return False
    return _strong_final_slot_signal(binding_result) or (
        binding_result.supports_slot
        and binding_result.slot_relation_match
        and binding_result.answer_type_match
    )


def _looks_like_year(value: str) -> bool:
    return bool(re.fullmatch(r"\s*(1[0-9]{3}|20[0-9]{2})\s*", str(value or "")))


def _value_window(text: str, value: str, radius: int = 90) -> str:
    source = str(text or "")
    index = source.lower().find(str(value or "").lower())
    if index < 0:
        return source
    return source[max(0, index - radius) : min(len(source), index + len(str(value)) + radius)]


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())
