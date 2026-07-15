from __future__ import annotations

from mvp_agentic_rag.repair_query_compiler import RepairQueryCompiler
from mvp_agentic_rag.slot_execution_state import HopExecutionState, SlotExecutionState


def _state() -> SlotExecutionState:
    hop1 = HopExecutionState(
        hop_id="required_hop_1",
        semantic_key="1|company a|located in|bridge",
        hop_index=1,
        subject="Company A",
        relation="located in",
        object_value="City A",
        status="verified",
        is_final_hop=False,
        is_critical=True,
        dependency_hop_ids=(),
        evidence_ids=("p1",),
        missing_requirements=(),
        confidence=1.0,
        source="test",
        last_updated_round=1,
    )
    hop2 = HopExecutionState(
        hop_id="required_hop_2",
        semantic_key="2|city a|founded by|final",
        hop_index=2,
        subject="City A",
        relation="founded by",
        object_value="",
        status="unresolved",
        is_final_hop=True,
        is_critical=True,
        dependency_hop_ids=("required_hop_1",),
        evidence_ids=(),
        missing_requirements=("founded_by",),
        confidence=0.0,
        source="test",
        last_updated_round=1,
    )
    return SlotExecutionState(
        sample_id="sample-1",
        topology_status="ready",
        round_idx=1,
        hops=(hop1, hop2),
        candidates=(),
        active_candidate_key="",
        first_critical_missing_hop_id="required_hop_2",
        completed_hop_ids=("required_hop_1",),
        conflict_hop_ids=(),
        no_progress_count=0,
        last_repair_target_hop_id="",
        state_fingerprint="state",
        topology_diagnostic={},
    )


def test_compiler_targets_first_missing_hop_and_uses_anchor() -> None:
    result = RepairQueryCompiler().compile(
        _state(),
        original_question="Who founded City A?",
    )

    assert result.valid is True
    assert result.target_hop_id == "required_hop_2"
    assert result.anchor_entity == "City A"
    assert result.target_relation == "founded by"
    assert result.query == "City A founded by"


def test_compiler_rejects_repeated_or_compound_query() -> None:
    state = _state()
    repeated = RepairQueryCompiler().compile(
        state,
        query_history=["City A founded by"],
        original_question="Who founded City A?",
    )
    assert repeated.valid is False
    assert "repair_query_repeated" in repeated.reasons

    compound = RepairQueryCompiler().compile(
        state,
        suggested_query="Who founded City A and what is its population?",
        original_question="Who founded City A?",
    )
    assert compound.valid is False
    assert "compound_repair_query" in compound.reasons


def test_compiler_uses_verified_dependency_when_subject_is_generic() -> None:
    state = _state()
    generic_hop = state.hops[1]
    generic_hop = generic_hop.__class__(
        **{
            **generic_hop.__dict__,
            "subject": "company",
            "subject_entity_id": "city_a",
            "relation_id": "founded_by",
            "expected_object_type": "person",
        }
    )
    state = state.__class__(**{**state.__dict__, "hops": (state.hops[0], generic_hop)})

    result = RepairQueryCompiler().compile(state)

    assert result.valid is True
    assert result.anchor_entity == "City A"
    assert result.query == "City A founded by"
    assert result.canonical_relation == "founded_by"
    assert result.expected_object_type == "person"


def test_compiler_preserves_targeted_model_query_for_underscored_relation() -> None:
    state = _state()
    model_hop = state.hops[1].__class__(
        **{
            **state.hops[1].__dict__,
            "subject": "Mohammed Atta",
            "subject_entity_id": "mohammed_atta",
            "relation": "has_model",
            "relation_id": "owned_vehicle_model",
            "expected_object_type": "vehicle_model",
        }
    )
    state = state.__class__(
        **{
            **state.__dict__,
            "hops": (state.hops[0], model_hop),
        }
    )

    result = RepairQueryCompiler().compile(
        state,
        suggested_query="What model of Nissan does Mohammed Atta have?",
        original_question=(
            "Mohammed Atta has what kind of model of the company that makes Datsun Type 12?"
        ),
    )

    assert result.valid is True
    assert result.target_hop_id == "required_hop_2"
    assert result.query == "What model of Nissan does Mohammed Atta have?"
    assert result.anchor_entity == "Mohammed Atta"
    assert result.canonical_relation == "owned_vehicle_model"
