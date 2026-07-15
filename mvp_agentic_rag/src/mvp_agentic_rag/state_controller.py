from __future__ import annotations

from dataclasses import dataclass, field

from .slot_execution_state import SlotExecutionState


STATE_ACTIONS = {
    "answer",
    "repair_missing_hop",
    "disambiguate_conflict",
    "abstain",
    "no_state_action",
}

FUSION_LANES = {
    "strict_certificate",
    "generic_compatibility",
    "no_fallback",
}

_STRICT_CERTIFICATE_REASONS = {
    "deterministic_named_after_player_signing_binding",
    "deterministic_shared_saint_constraint_topology",
    "deterministic_shared_saint_chain_binding",
    "deterministic_partial_country_network_topology",
    "deterministic_country_network_chain_binding",
    "deterministic_partial_geographic_race_topology",
    "deterministic_geographic_race_chain_binding",
}

_UNSAFE_TOPOLOGY_REASONS = {
    "required_hops_malformed",
    "verifier_parse_failure",
}


@dataclass(frozen=True)
class StateControllerDecision:
    action: str
    target_hop_id: str = ""
    reason: str = ""
    allowed_actions: tuple[str, ...] = ()
    blocked: bool = False
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "action": self.action,
            "target_hop_id": self.target_hop_id,
            "reason": self.reason,
            "allowed_actions": list(self.allowed_actions),
            "blocked": self.blocked,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class StateActionValidation:
    valid: bool
    action: str
    target_hop_id: str = ""
    reasons: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "valid": self.valid,
            "action": self.action,
            "target_hop_id": self.target_hop_id,
            "reasons": list(self.reasons),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FusionLaneDecision:
    lane: str
    reason: str
    strict_certificate_reason: str = ""
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "lane": self.lane,
            "reason": self.reason,
            "strict_certificate_reason": self.strict_certificate_reason,
            "metadata": dict(self.metadata),
        }


class FusionLaneRouter:
    """Select strict state enforcement without consulting sample identity.

    The router consumes only the canonical runtime state and its verifier
    topology diagnostic.  Existing deterministic certificate adapters remain
    provenance sources for the phase-1 fusion gate; no sample ID, question,
    answer, decomposition, or gold support field is available to this class.
    """

    def __init__(self, *, allow_strict_certificate: bool = True):
        self.allow_strict_certificate = bool(allow_strict_certificate)

    def classify(self, state: SlotExecutionState) -> FusionLaneDecision:
        diagnostic = dict(state.topology_diagnostic or {})
        primary = str(diagnostic.get("primary_reason") or "").strip()
        secondary = {
            str(value or "").strip()
            for value in diagnostic.get("secondary_reasons", [])
            if str(value or "").strip()
        }
        certificate_reason = str(
            diagnostic.get("deterministic_binding_applied") or ""
        ).strip()
        common = {
            "topology_status": state.topology_status,
            "topology_primary_reason": primary,
            "topology_secondary_reasons": sorted(secondary),
            "conflict_hop_ids": list(state.conflict_hop_ids),
            "evidence_certificate_binding": bool(
                diagnostic.get("evidence_certificate_binding", False)
            ),
            "strict_certificate_enabled": self.allow_strict_certificate,
        }

        if primary in _UNSAFE_TOPOLOGY_REASONS:
            return FusionLaneDecision(
                lane="no_fallback",
                reason=primary,
                metadata=common,
            )
        if state.conflict_hop_ids:
            return FusionLaneDecision(
                lane="no_fallback",
                reason="hard_conflict",
                metadata=common,
            )
        if (
            state.topology_status == "ready"
            and primary == "required_hops_present"
            and (
                bool(diagnostic.get("evidence_certificate_binding", False))
                or certificate_reason in _STRICT_CERTIFICATE_REASONS
            )
        ):
            if not self.allow_strict_certificate:
                return FusionLaneDecision(
                    lane="generic_compatibility",
                    reason="strict_certificate_disabled_for_generic_only",
                    strict_certificate_reason=certificate_reason,
                    metadata=common,
                )
            return FusionLaneDecision(
                lane="strict_certificate",
                reason="trusted_runtime_certificate",
                strict_certificate_reason=certificate_reason,
                metadata=common,
            )
        if primary == "required_hops_present" or state.topology_status == "ready":
            return FusionLaneDecision(
                lane="generic_compatibility",
                reason="valid_topology_without_strict_certificate",
                metadata=common,
            )
        return FusionLaneDecision(
            lane="no_fallback",
            reason=primary or "topology_unavailable",
            metadata=common,
        )


class StateAwareController:
    """Deterministic safety controller over the canonical execution state.

    This is intentionally small and model-independent. A larger planning model
    can propose an action later, but it must be checked against this contract.
    """

    def __init__(self, no_progress_limit: int = 2):
        self.no_progress_limit = max(1, int(no_progress_limit))

    def decide(self, state: SlotExecutionState, budget_remaining: int) -> StateControllerDecision:
        if state.topology_status == "topology_unavailable":
            return StateControllerDecision(
                action="no_state_action",
                reason="topology_unavailable",
                metadata={"state_controller_available": False},
            )

        budget = max(0, int(budget_remaining))
        if state.conflict_hop_ids:
            action = "disambiguate_conflict" if budget > 0 else "abstain"
            return StateControllerDecision(
                action=action,
                reason="hard_conflict_blocks_repair_and_answer",
                allowed_actions=("disambiguate_conflict", "abstain"),
                blocked=True,
                metadata={"conflict_hop_ids": list(state.conflict_hop_ids)},
            )

        if state.first_critical_missing_hop_id:
            if state.no_progress_count >= self.no_progress_limit:
                return StateControllerDecision(
                    action="abstain",
                    target_hop_id=state.first_critical_missing_hop_id,
                    reason="no_progress_limit_reached",
                    allowed_actions=("repair_missing_hop", "abstain"),
                    blocked=True,
                    metadata={"no_progress_count": state.no_progress_count},
                )
            if budget > 0:
                return StateControllerDecision(
                    action="repair_missing_hop",
                    target_hop_id=state.first_critical_missing_hop_id,
                    reason="first_critical_missing_hop",
                    allowed_actions=("repair_missing_hop", "abstain"),
                    metadata={"budget_remaining": budget},
                )
            return StateControllerDecision(
                action="abstain",
                target_hop_id=state.first_critical_missing_hop_id,
                reason="critical_gap_budget_exhausted",
                allowed_actions=("repair_missing_hop", "abstain"),
                blocked=True,
            )

        critical_hops = [hop for hop in state.hops if hop.is_critical]
        active = next(
            (candidate for candidate in state.candidates if candidate.normalized_value == state.active_candidate_key),
            None,
        )
        if critical_hops and all(hop.status == "verified" for hop in critical_hops):
            if active is not None and active.status == "verified":
                return StateControllerDecision(
                    action="answer",
                    reason="critical_chain_complete_and_candidate_verified",
                    allowed_actions=("answer", "abstain"),
                )
            return StateControllerDecision(
                action="no_state_action",
                reason="chain_complete_but_no_verified_final_candidate",
                allowed_actions=("answer", "abstain"),
                metadata={"active_candidate_key": state.active_candidate_key},
            )

        return StateControllerDecision(
            action="no_state_action",
            reason="state_has_no_executable_transition",
            allowed_actions=("abstain",),
        )


class StateActionValidator:
    """Validates controller output before it can change runtime behavior."""

    def validate(
        self,
        decision: StateControllerDecision,
        state: SlotExecutionState,
        *,
        budget_remaining: int,
        query: str = "",
        query_history: list[str] | None = None,
        original_question: str = "",
    ) -> StateActionValidation:
        reasons: list[str] = []
        history = {self._normalize(value) for value in (query_history or []) if self._normalize(value)}
        action = decision.action
        target = decision.target_hop_id

        if action not in STATE_ACTIONS:
            reasons.append("unknown_action")
        if action == "repair_missing_hop":
            if int(budget_remaining) <= 0:
                reasons.append("budget_exhausted")
            if not target:
                reasons.append("missing_target_hop")
            if target in set(state.completed_hop_ids):
                reasons.append("completed_hop_repair_forbidden")
            if target in set(state.conflict_hop_ids):
                reasons.append("conflicted_hop_repair_forbidden")
            if target != state.first_critical_missing_hop_id:
                reasons.append("target_is_not_first_critical_missing_hop")
            if not self._normalize(query):
                reasons.append("missing_repair_query")
            if self._normalize(query) in history:
                reasons.append("repair_query_repeated")
            if original_question and self._normalize(query) == self._normalize(original_question):
                reasons.append("repair_query_repeats_full_question")
            if self._is_compound(query):
                reasons.append("compound_repair_query")
        elif action == "answer":
            if state.conflict_hop_ids:
                reasons.append("conflict_blocks_answer")
            if state.first_critical_missing_hop_id:
                reasons.append("critical_gap_blocks_answer")

        return StateActionValidation(
            valid=not reasons,
            action=action if not reasons else "abstain",
            target_hop_id=target,
            reasons=tuple(sorted(set(reasons))),
            metadata={"state_controller_validation": True},
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value or "").lower().split())

    @classmethod
    def _is_compound(cls, query: str) -> bool:
        normalized = cls._normalize(query)
        return bool(normalized and (" and who " in f" {normalized} " or " and what " in f" {normalized} "))
