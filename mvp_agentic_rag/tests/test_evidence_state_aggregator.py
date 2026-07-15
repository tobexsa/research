from __future__ import annotations

from mvp_agentic_rag.evidence_state_aggregator import aggregate_evidence_state
from mvp_agentic_rag.slot_execution_state import HopExecutionState, SlotExecutionState


def _state(*, conflict: bool = False) -> SlotExecutionState:
    hops = (
        HopExecutionState(
            "required_hop_1",
            "1|company a|located in|bridge",
            1,
            "Company A",
            "located in",
            "City A",
            "verified",
            False,
            True,
            (),
            ("p1",),
            (),
            1.0,
            "test",
            1,
        ),
        HopExecutionState(
            "required_hop_2",
            "2|city a|founded by|final",
            2,
            "City A",
            "founded by",
            "",
            "conflicted" if conflict else "unresolved",
            True,
            True,
            ("required_hop_1",),
            (),
            ("founded_by",),
            0.0,
            "test",
            1,
        ),
    )
    return SlotExecutionState(
        "sample-1",
        "ready",
        1,
        hops,
        (),
        "",
        "required_hop_2",
        ("required_hop_1",),
        ("required_hop_2",) if conflict else (),
        0,
        "",
        "state",
        {},
    )


def test_aggregator_exposes_repairable_gap_and_uncertainty() -> None:
    features = aggregate_evidence_state(_state())

    assert features.state_label == "repairable_gap"
    assert features.critical_hop_count == 2
    assert features.verified_critical_hop_count == 1
    assert features.support_coverage == 0.5
    assert features.uncertainty >= 0.5


def test_aggregator_prioritizes_conflict() -> None:
    features = aggregate_evidence_state(_state(conflict=True))

    assert features.state_label == "conflict"
    assert features.conflict is True
    assert features.uncertainty == 1.0
