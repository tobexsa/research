from __future__ import annotations

from dataclasses import dataclass, field

from .semantic_hop_resolver import is_generic_entity
from .slot_execution_state import HopExecutionState, SlotExecutionState


@dataclass(frozen=True)
class CompiledRepairQuery:
    valid: bool
    query: str = ""
    target_hop_id: str = ""
    anchor_entity: str = ""
    target_relation: str = ""
    canonical_relation: str = ""
    expected_object_type: str = ""
    reasons: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "valid": self.valid,
            "query": self.query,
            "target_hop_id": self.target_hop_id,
            "anchor_entity": self.anchor_entity,
            "target_relation": self.target_relation,
            "canonical_relation": self.canonical_relation,
            "expected_object_type": self.expected_object_type,
            "reasons": list(self.reasons),
            "metadata": dict(self.metadata),
        }


class RepairQueryCompiler:
    """Compile exactly one state-derived missing-hop query."""

    def compile(
        self,
        state: SlotExecutionState,
        *,
        query_history: list[str] | None = None,
        original_question: str = "",
        suggested_query: str = "",
    ) -> CompiledRepairQuery:
        target_id = state.first_critical_missing_hop_id
        hop = next((item for item in state.hops if item.hop_id == target_id), None)
        if hop is None:
            return CompiledRepairQuery(False, reasons=("no_critical_missing_hop",))

        anchor = self._anchor_for_hop(state, hop)
        canonical_relation = " ".join(str(hop.relation_id or "").split())
        relation = " ".join(str(hop.relation or "").split())
        if not relation:
            relation = canonical_relation.replace("_", " ")
        query = " ".join(str(suggested_query or "").split())
        normalized_query = self._normalize(query)
        normalized_anchor = self._normalize(anchor)
        relation_tokens = [
            token
            for token in self._normalize(relation.replace("_", " ")).split()
            if token
        ]
        relation_bound = bool(relation_tokens) and any(token in normalized_query for token in relation_tokens)
        if (
            not query
            or self._normalize(query) == self._normalize(original_question)
            or not normalized_anchor
            or normalized_anchor not in normalized_query
            or not relation_bound
        ):
            query = " ".join(part for part in (anchor, relation) if part)

        reasons: list[str] = []
        if hop.status in {"verified", "conflicted"}:
            reasons.append("target_hop_not_repairable")
        if target_id in set(state.completed_hop_ids):
            reasons.append("completed_hop_repair_forbidden")
        if not anchor:
            reasons.append("missing_anchor_entity")
        if not relation:
            reasons.append("missing_target_relation")
        if not query:
            reasons.append("empty_compiled_query")
        if original_question and self._normalize(query) == self._normalize(original_question):
            reasons.append("repair_query_repeats_full_question")
        history = {self._normalize(item) for item in (query_history or []) if self._normalize(item)}
        if self._normalize(query) in history:
            reasons.append("repair_query_repeated")
        if self._is_compound(query):
            reasons.append("compound_repair_query")

        return CompiledRepairQuery(
            valid=not reasons,
            query=query if not reasons else "",
            target_hop_id=target_id,
            anchor_entity=anchor,
            target_relation=relation,
            canonical_relation=canonical_relation,
            expected_object_type=str(hop.expected_object_type or "entity"),
            reasons=tuple(sorted(set(reasons))),
            metadata={
                "compiler": "state_derived_single_hop_v1",
                "topology_version": state.topology_version,
                "topology_fingerprint": state.topology_fingerprint,
                "subject_entity_id": hop.subject_entity_id,
                "object_entity_id": hop.object_entity_id,
                "completed_hop_ids": list(state.completed_hop_ids),
                "no_progress_count": state.no_progress_count,
            },
        )

    @staticmethod
    def _anchor_for_hop(state: SlotExecutionState, hop: HopExecutionState) -> str:
        if hop.subject and hop.subject.strip() and not is_generic_entity(hop.subject):
            return " ".join(hop.subject.split())
        by_id = {item.hop_id: item for item in state.hops}
        for dependency_id in reversed(hop.dependency_hop_ids):
            dependency = by_id.get(dependency_id)
            if dependency and dependency.object_value.strip():
                return " ".join(dependency.object_value.split())
        prior = [item for item in state.hops if item.hop_index < hop.hop_index and item.object_value.strip()]
        if prior:
            return " ".join(prior[-1].object_value.split())
        return " ".join(hop.subject.split()) if hop.subject and not is_generic_entity(hop.subject) else ""

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value or "").lower().split())

    @classmethod
    def _is_compound(cls, query: str) -> bool:
        normalized = cls._normalize(query)
        return bool(normalized and (" and who " in f" {normalized} " or " and what " in f" {normalized} "))
