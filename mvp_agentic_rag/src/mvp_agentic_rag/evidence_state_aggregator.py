from __future__ import annotations

from dataclasses import dataclass, field

from .slot_execution_state import SlotExecutionState


@dataclass(frozen=True)
class EvidenceStateFeatures:
    """Auditable set/chain-level features derived from the canonical state."""

    critical_hop_count: int = 0
    verified_critical_hop_count: int = 0
    support_coverage: float = 0.0
    conflict: bool = False
    candidate_disagreement: int = 0
    uncertainty: float = 1.0
    state_label: str = "unknown"
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "critical_hop_count": self.critical_hop_count,
            "verified_critical_hop_count": self.verified_critical_hop_count,
            "support_coverage": self.support_coverage,
            "conflict": self.conflict,
            "candidate_disagreement": self.candidate_disagreement,
            "uncertainty": self.uncertainty,
            "state_label": self.state_label,
            "metadata": dict(self.metadata),
        }


def aggregate_evidence_state(state: SlotExecutionState) -> EvidenceStateFeatures:
    critical = [hop for hop in state.hops if hop.is_critical]
    verified = [hop for hop in critical if hop.status == "verified"]
    coverage = len(verified) / len(critical) if critical else 0.0
    viable = [
        candidate
        for candidate in state.candidates
        if candidate.status in {"observed", "support_incomplete", "verified"}
    ]
    candidate_values = {candidate.normalized_value for candidate in viable if candidate.normalized_value}
    disagreement = max(0, len(candidate_values) - 1)

    if state.conflict_hop_ids:
        label = "conflict"
    elif state.first_critical_missing_hop_id:
        label = "repairable_gap"
    elif critical and len(verified) == len(critical) and any(
        candidate.status == "verified" for candidate in viable
    ):
        label = "supported"
    elif state.topology_status == "topology_unavailable":
        label = "unknown"
    else:
        label = "insufficient"

    uncertainty = 1.0 - coverage
    if disagreement:
        uncertainty = min(1.0, uncertainty + 0.15 * disagreement)
    if state.no_progress_count:
        uncertainty = min(1.0, uncertainty + 0.1 * state.no_progress_count)
    if state.conflict_hop_ids:
        uncertainty = 1.0

    return EvidenceStateFeatures(
        critical_hop_count=len(critical),
        verified_critical_hop_count=len(verified),
        support_coverage=coverage,
        conflict=bool(state.conflict_hop_ids),
        candidate_disagreement=disagreement,
        uncertainty=uncertainty,
        state_label=label,
        metadata={
            "active_candidate_key": state.active_candidate_key,
            "first_critical_missing_hop_id": state.first_critical_missing_hop_id,
            "no_progress_count": state.no_progress_count,
        },
    )
