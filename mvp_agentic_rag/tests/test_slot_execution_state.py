import json
from dataclasses import replace

import pytest

from mvp_agentic_rag.slot_execution_state import (
    SlotExecutionState,
    SlotStateUpdate,
    extract_canonical_runtime_category,
    hypothetical_state_action,
    reduce_slot_execution_state,
)


def ordered_hop(
    index: int,
    subject: str,
    relation: str,
    object_value: str = "",
    *,
    final: bool = False,
    status: str = "missing",
    evidence_ids: tuple[str, ...] = (),
) -> dict:
    return {
        "hop_index": index,
        "subject": subject,
        "relation": relation,
        "object": object_value,
        "status": status,
        "is_final_hop": final,
        "supporting_evidence_ids": list(evidence_ids),
        "confidence": 0.9,
    }


def binding_record(
    required_hops: list[dict],
    *,
    bound_value: str = "",
    evidence_ids: tuple[str, ...] = (),
    category: str = "",
    chain_complete: bool = False,
    all_required_hops_covered: bool = False,
    conflict_on_final_slot: bool = False,
    conflict_on_bridge: bool | None = None,
    missing_critical_hops: tuple[str, ...] = (),
    candidate_is_final_relation_object: bool = False,
    filled_hop_index: int = 0,
) -> dict:
    set_level = {
        "final_slot_covered": bool(bound_value),
        "all_required_hops_covered": all_required_hops_covered,
        "missing_critical_hops": list(missing_critical_hops),
        "conflict_on_final_slot": conflict_on_final_slot,
    }
    if conflict_on_bridge is not None:
        set_level["conflict_on_bridge"] = conflict_on_bridge
    return {
        "supports_slot": bool(bound_value),
        "bound_value": bound_value,
        "evidence_ids": list(evidence_ids),
        "typed_reject_category": category,
        "candidate_role_labeler": {"candidate": bound_value},
        "ordered_hop_binding": {
            "required_hops": required_hops,
            "filled_hop_index": filled_hop_index,
            "missing_critical_hops": list(missing_critical_hops),
            "bound_bridge_values": [],
            "candidate_is_final_relation_object": candidate_is_final_relation_object,
            "chain_complete": chain_complete,
        },
        "set_level_sufficiency": set_level,
        "slot_bound_entailment": {
            "candidate": bound_value,
            "evidence_ids": list(evidence_ids),
            "contradicted": False,
        },
        "decision_head": {},
        "structured_output": {},
    }


def make_update(
    sample_id: str,
    round_idx: int,
    record: dict,
    *,
    runtime_metadata: dict | None = None,
    verifier_record: dict | None = None,
    local_evidence_ids: tuple[str, ...] = (),
    legacy_slot_ledger_record: dict | None = None,
) -> SlotStateUpdate:
    return SlotStateUpdate(
        sample_id=sample_id,
        round_idx=round_idx,
        slot_binding_record=record,
        runtime_metadata=runtime_metadata or {},
        legacy_slot_ledger_record=legacy_slot_ledger_record or {},
        verifier_record=verifier_record or {"claims": [], "overall_sufficiency": "insufficient"},
        local_evidence_ids=local_evidence_ids,
    )


def trusted_revision_record(
    required_hops: list[dict],
    *,
    candidate: str,
    evidence_ids: tuple[str, ...],
    reason: str,
) -> dict:
    record = binding_record(
        required_hops,
        bound_value=candidate,
        evidence_ids=evidence_ids,
        chain_complete=True,
        all_required_hops_covered=True,
        candidate_is_final_relation_object=True,
        filled_hop_index=len(required_hops),
    )
    record.update(
        {
            "slot_relation_match": True,
            "answer_type_match": True,
            "reason": reason,
            "structured_output": {
                "parse_status": "parsed",
                "deterministic_binding_applied": reason,
            },
            "topology_diagnostic": {
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            },
        }
    )
    ordered = record["ordered_hop_binding"]
    ordered.update(
        {
            "final_hop_index": len(required_hops),
            "final_relation": required_hops[-1]["relation"],
            "final_relation_object": candidate,
            "missing_requirements": [],
        }
    )
    record["set_level_sufficiency"].update(
        {
            "final_slot_covered": True,
            "all_required_hops_covered": True,
            "conflict_on_final_slot": False,
            "conflict_on_bridge": False,
            "evidence_set_sufficient": True,
        }
    )
    record["slot_bound_entailment"].update(
        {
            "candidate": candidate,
            "evidence_ids": list(evidence_ids),
            "entails_answer": True,
            "contradicted": False,
        }
    )
    return record


def two_hop_record(
    *,
    first_status: str = "bound",
    second_status: str = "missing",
    first_object: str = "B",
    second_object: str = "",
    first_evidence: tuple[str, ...] = ("p1",),
    second_evidence: tuple[str, ...] = (),
    **kwargs,
) -> dict:
    return binding_record(
        [
            ordered_hop(
                1,
                "A",
                "relation_a",
                first_object,
                status=first_status,
                evidence_ids=first_evidence,
            ),
            ordered_hop(
                2,
                "B",
                "relation_b",
                second_object,
                final=True,
                status=second_status,
                evidence_ids=second_evidence,
            ),
        ],
        **kwargs,
    )


def test_empty_state_starts_without_topology() -> None:
    state = SlotExecutionState.empty("s1")

    assert state.sample_id == "s1"
    assert state.topology_status == "topology_unavailable"
    assert state.hops == ()
    assert state.candidates == ()
    assert state.state_fingerprint
    json.dumps(state.to_record())


def test_initializes_frozen_linear_topology() -> None:
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )

    assert result.state.topology_status == "ready"
    assert [hop.hop_id for hop in result.state.hops] == ["required_hop_1", "required_hop_2"]
    assert result.state.hops[0].status == "verified"
    assert result.state.hops[1].dependency_hop_ids == ("required_hop_1",)
    assert result.state.hops[1].is_final_hop is True
    assert result.state.first_critical_missing_hop_id == "required_hop_2"
    assert result.progress is True


def test_topology_diagnostic_preserves_deterministic_certificate_provenance() -> None:
    record = two_hop_record()
    record["structured_output"] = {
        "parse_status": "parsed",
        "deterministic_binding_applied": (
            "deterministic_shared_saint_constraint_topology"
        ),
    }

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1",)),
    )

    assert result.state.topology_diagnostic["deterministic_binding_applied"] == (
        "deterministic_shared_saint_constraint_topology"
    )


def test_equivalent_century_surface_does_not_create_hop_conflict() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(
                second_status="bound",
                second_object="18th century",
                second_evidence=("p2",),
                bound_value="18th century",
                evidence_ids=("p2",),
                chain_complete=True,
                all_required_hops_covered=True,
                candidate_is_final_relation_object=True,
                filled_hop_index=2,
            ),
            local_evidence_ids=("p1", "p2"),
        ),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "s1",
            2,
            two_hop_record(
                second_status="bound",
                second_object="18th",
                second_evidence=("p2",),
                bound_value="18th",
                evidence_ids=("p2",),
                chain_complete=True,
                all_required_hops_covered=True,
                candidate_is_final_relation_object=True,
                filled_hop_index=2,
            ),
            local_evidence_ids=("p1", "p2"),
        ),
    )

    assert second.state.conflict_hop_ids == ()
    assert not any(
        event.get("event") == "competing_bound_object_conflict"
        for event in second.transition_events
    )


def test_unverified_prior_object_can_be_corrected_without_conflict() -> None:
    first_record = two_hop_record(
        second_status="missing",
        second_object="Wrong Person",
        second_evidence=(),
        bound_value="",
        evidence_ids=(),
        chain_complete=False,
        all_required_hops_covered=False,
        candidate_is_final_relation_object=False,
        filled_hop_index=1,
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, first_record, local_evidence_ids=("p1",)),
    )
    second_record = two_hop_record(
        second_status="bound",
        second_object="Correct Person",
        second_evidence=("p2",),
        bound_value="Correct Person",
        evidence_ids=("p2",),
        chain_complete=True,
        all_required_hops_covered=True,
        candidate_is_final_relation_object=True,
        filled_hop_index=2,
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, second_record, local_evidence_ids=("p1", "p2")),
    )

    final_hop = next(hop for hop in second.state.hops if hop.is_final_hop)
    assert first.state.hops[-1].status == "support_incomplete"
    assert final_hop.status == "verified"
    assert final_hop.object_value == "Correct Person"
    assert second.state.conflict_hop_ids == ()


def test_candidate_scoped_entailment_contradiction_does_not_conflict_bridge_hops() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    record = two_hop_record()
    record["slot_bound_entailment"] = {
        "candidate": "Wrong President",
        "contradicted": True,
        "evidence_ids": ["p1"],
        "hypothesis": "The answer to the question is Wrong President.",
        "failure_reason": "The evidence names another country's president.",
    }
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, record, local_evidence_ids=("p1",)),
    )

    assert second.state.conflict_hop_ids == ()
    assert any(
        event.get("event") == "candidate_contradiction_not_hop_conflict"
        for event in second.transition_events
    )


def test_entailment_failure_explanation_cannot_scope_indonesia_timor_bridge() -> None:
    record = binding_record(
        [
            ordered_hop(1, "Tony Gunawan", "from", "Indonesia", status="bound", evidence_ids=("p17",)),
            ordered_hop(
                2,
                "Indonesia",
                "commission_partner",
                "East Timor",
                status="bound",
                evidence_ids=("p7",),
            ),
            ordered_hop(3, "East Timor", "president", final=True),
        ],
        missing_critical_hops=("president_of",),
        filled_hop_index=2,
    )
    record["slot_bound_entailment"] = {
        "candidate": "Susilo Bambang Yudhoyono",
        "contradicted": True,
        "evidence_ids": ["p7", "p17"],
        "hypothesis": (
            "The answer to the question is Susilo Bambang Yudhoyono."
        ),
        "reason": (
            "The evidence identifies the president of Indonesia, not the "
            "president of East Timor."
        ),
        "failure_reason": (
            "Indonesia and East Timor are distinct countries in the commission."
        ),
    }

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            record,
            local_evidence_ids=("p7", "p17"),
        ),
    )

    assert result.state.conflict_hop_ids == ()
    assert result.state.first_critical_missing_hop_id == "required_hop_3"
    event = next(
        event
        for event in result.transition_events
        if event.get("event") == "candidate_contradiction_not_hop_conflict"
    )
    assert "Indonesia" in event["reason"]
    assert "East Timor" in event["failure_reason"]


def test_invalid_topology_can_be_followed_by_valid_topology() -> None:
    invalid = binding_record(
        [ordered_hop(1, "A", "r1"), ordered_hop(3, "B", "r2", final=True)]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, invalid),
    )

    assert first.state.topology_status == "topology_unavailable"
    assert any(event["event"] == "topology_invalid" for event in first.transition_events)

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, two_hop_record(), local_evidence_ids=("p1",)),
    )
    assert second.state.topology_status == "ready"


def test_duplicate_or_invalid_final_marker_rejects_entire_topology() -> None:
    duplicate = binding_record(
        [ordered_hop(1, "A", "r1"), ordered_hop(1, "B", "r2", final=True)]
    )
    misplaced_final = binding_record(
        [ordered_hop(1, "A", "r1", final=True), ordered_hop(2, "B", "r2")]
    )

    for record in (duplicate, misplaced_final):
        result = reduce_slot_execution_state(
            SlotExecutionState.empty("s1"),
            make_update("s1", 1, record),
        )
        assert result.state.hops == ()
        assert any(event["event"] == "topology_invalid" for event in result.transition_events)


def test_malformed_required_hop_rejects_entire_topology_and_allows_later_valid_record() -> None:
    malformed = binding_record(
        [
            ordered_hop(1, "A", "relation_a", "B", final=True, status="bound", evidence_ids=("p1",)),
            "not-a-hop-record",
        ]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, malformed, local_evidence_ids=("p1",)),
    )

    assert first.state.topology_status == "topology_unavailable"
    assert first.state.hops == ()
    assert any(
        event["event"] == "topology_invalid"
        and event["reason"] == "required_hop_must_be_object"
        for event in first.transition_events
    )

    valid = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, two_hop_record(), local_evidence_ids=("p1",)),
    )
    assert valid.state.topology_status == "ready"
    assert len(valid.state.hops) == 2


def test_malformed_required_hop_does_not_mutate_frozen_state() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    malformed = binding_record(
        [
            ordered_hop(1, "A", "relation_a", "Changed", status="bound", evidence_ids=("p2",)),
            None,
        ],
        bound_value="Untrusted Candidate",
        evidence_ids=("p2",),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, malformed, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops == first.state.hops
    assert second.state.candidates == first.state.candidates
    assert any(event["event"] == "incoming_topology_invalid" for event in second.transition_events)


def test_schema_malformed_diagnostic_cannot_create_candidate_transition() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    malformed = two_hop_record(
        bound_value="Untrusted Candidate",
        evidence_ids=("p2",),
        chain_complete=True,
        all_required_hops_covered=True,
        candidate_is_final_relation_object=True,
    )
    malformed["topology_diagnostic"] = {
        "primary_reason": "required_hops_malformed",
        "required_hops_error": "required_hop_schema_invalid",
        "secondary_reasons": [],
    }

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, malformed, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops == first.state.hops
    assert second.state.candidates == first.state.candidates
    assert [event["event"] for event in second.transition_events] == [
        "incoming_topology_invalid"
    ]


def test_verifier_parse_failure_cannot_initialize_topology_and_valid_record_can_follow() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(category="verifier_parse_failure"),
            local_evidence_ids=("p1",),
        ),
    )

    assert first.state.topology_status == "topology_unavailable"
    assert first.state.hops == ()
    assert first.state.candidates == ()
    assert first.progress is False

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, two_hop_record(), local_evidence_ids=("p1",)),
    )
    assert second.state.topology_status == "ready"
    assert len(second.state.hops) == 2


def test_empty_required_hops_is_diagnosed_and_bootstraps_only_from_missing_hints() -> None:
    record = binding_record(
        [],
        missing_critical_hops=("parent company",),
    )
    record["ordered_hop_binding"]["final_relation"] = "parent company"
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record),
    )

    assert result.state.topology_status == "ready"
    assert result.state.topology_diagnostic["primary_reason"] == "required_hops_missing"
    assert result.state.topology_diagnostic["bootstrap_applied"] is True
    assert result.state.first_critical_missing_hop_id == "required_hop_1"
    assert any(event["event"] == "topology_bootstrap_applied" for event in result.transition_events)


def test_unknown_candidate_is_not_added_to_state_bookkeeping() -> None:
    record = binding_record([], bound_value="UNKNOWN")
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record),
    )

    assert result.state.candidates == ()
    assert any(
        event["event"] == "sentinel_candidate_ignored"
        for event in result.transition_events
    )


def test_ambiguous_target_mapping_is_exposed_as_secondary_topology_diagnosis() -> None:
    record = two_hop_record()
    record["candidate_role_labeler"] = {
        "candidate": "B",
        "candidate_role": "unknown",
        "relation_to_question": "ambiguous",
        "role_error_type": "ambiguous_target",
    }
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record),
    )

    assert "ambiguous_target_mapping" in result.state.topology_diagnostic["secondary_reasons"]


def test_verifier_parse_failure_cannot_update_existing_state() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(bound_value="Alice", evidence_ids=("p2",)),
            local_evidence_ids=("p1", "p2"),
        ),
    )
    parse_failure = two_hop_record(
        first_object="Changed",
        first_evidence=("p3",),
        bound_value="Untrusted Candidate",
        evidence_ids=("p3",),
        category="verifier_parse_failure",
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, parse_failure, local_evidence_ids=("p1", "p2", "p3")),
    )

    assert second.state.hops == first.state.hops
    assert second.state.candidates == first.state.candidates
    assert second.progress is False
    assert second.state.no_progress_count == first.state.no_progress_count + 1


def test_same_index_changed_semantic_key_is_drift_not_merge() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    changed = two_hop_record()
    changed["ordered_hop_binding"]["required_hops"][1]["relation"] = "changed_relation"
    changed["ordered_hop_binding"]["required_hops"][1]["status"] = "bound"
    changed["ordered_hop_binding"]["required_hops"][1]["object"] = "C"
    changed["ordered_hop_binding"]["required_hops"][1]["supporting_evidence_ids"] = ["p2"]

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, changed, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops[1].relation == "relation_b"
    assert "p2" not in second.state.hops[1].evidence_ids
    assert any(event["event"] == "hop_schema_drift_ignored" for event in second.transition_events)


def test_verified_hop_unions_local_evidence() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    record = two_hop_record(first_evidence=("p2", "p1"))
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, record, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops[0].evidence_ids == ("p1", "p2")


def test_verified_hop_cannot_silently_regress() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    missing = two_hop_record(first_status="missing", first_object="", first_evidence=())
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, missing, local_evidence_ids=("p1",)),
    )

    assert second.state.hops[0].status == "verified"
    assert second.regression_blocked is True
    assert any(event["event"] == "state_regression_blocked" for event in second.transition_events)


def test_scoped_contradiction_can_mark_verified_hop_conflicted() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    verifier = {
        "overall_sufficiency": "conflicting",
        "claims": [{"status": "contradicted", "evidence_ids": ["p1"]}],
    }
    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "s1",
            2,
            two_hop_record(),
            verifier_record=verifier,
            local_evidence_ids=("p1",),
        ),
    )

    assert second.state.hops[0].status == "conflicted"
    assert second.state.conflict_hop_ids == ("required_hop_1",)


def test_competing_supported_objects_mark_hop_conflicted_without_overwrite() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    competing = two_hop_record(first_object="Different B", first_evidence=("p2",))
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, competing, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops[0].status == "conflicted"
    assert second.state.hops[0].object_value == "B"
    assert second.state.hops[0].evidence_ids == ("p1", "p2")
    assert any(event["event"] == "competing_bound_object_conflict" for event in second.transition_events)


def test_category_extraction_uses_defined_precedence() -> None:
    assert extract_canonical_runtime_category(
        {"typed_reject_category": "wrong_target", "decision_head": {"typed_reject_category": "bridge_as_final"}},
        {},
    ) == "wrong_target"
    assert extract_canonical_runtime_category(
        {"decision_head": {"typed_reject_category": "bridge_as_final", "abstain_reason": "empty_binding"}},
        {},
    ) == "bridge_as_final"
    assert extract_canonical_runtime_category(
        {"decision_head": {"abstain_reason": "insufficient_bridge_evidence"}},
        {},
    ) == "insufficient_bridge_evidence"
    assert extract_canonical_runtime_category(
        {},
        {"final_candidate_preserved": True, "bridge_evidence_incomplete": True},
    ) == "insufficient_bridge_evidence"
    assert extract_canonical_runtime_category(
        {"decision_head": {"abstain_reason": "free-form missing bridge prose"}},
        {},
    ) == ""


def test_candidate_collection_preserves_nbc_during_bridge_repair() -> None:
    record = binding_record(
        [
            ordered_hop(1, "Sarangani Bay", "country", "Philippines", status="bound", evidence_ids=("p1",)),
            ordered_hop(2, "Country A", "same_country", "Philippines", status="bound", evidence_ids=("p2",)),
            ordered_hop(3, "Country A", "show_version", "", status="missing"),
            ordered_hop(4, "The Biggest Loser version", "network", "NBC", final=True, status="bound", evidence_ids=("p4",)),
        ],
        bound_value="NBC",
        evidence_ids=("p4",),
        missing_critical_hops=("3",),
        filled_hop_index=4,
        candidate_is_final_relation_object=True,
    )
    record["decision_head"] = {"abstain_reason": "insufficient_bridge_evidence"}
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("4hop1__161810_583746_457883_650651"),
        make_update(
            "4hop1__161810_583746_457883_650651",
            1,
            record,
            runtime_metadata={
                "final_candidate_preserved": True,
                "preserved_final_candidate": "NBC",
                "bridge_evidence_incomplete": True,
            },
            local_evidence_ids=("p1", "p2", "p4"),
        ),
    )

    candidate = next(item for item in result.state.candidates if item.value == "NBC")
    assert candidate.status == "support_incomplete"
    assert candidate.preserved is True
    assert candidate.source_hop_id == "required_hop_4"
    assert result.state.active_candidate_key == "nbc"
    assert result.state.completed_hop_ids == ("required_hop_1", "required_hop_2", "required_hop_4")
    assert result.state.first_critical_missing_hop_id == "required_hop_3"

    refreshed = reduce_slot_execution_state(
        result.state,
        make_update(
            "4hop1__161810_583746_457883_650651",
            2,
            record,
            runtime_metadata={
                "final_candidate_preserved": True,
                "preserved_final_candidate": "NBC",
                "bridge_evidence_incomplete": True,
            },
            local_evidence_ids=("p1", "p2", "p4"),
        ),
    )
    assert refreshed.state.state_fingerprint == result.state.state_fingerprint
    assert refreshed.progress is False


def test_arizona_non_final_slot_is_observed_as_bridge_as_final_reject() -> None:
    record = two_hop_record(
        bound_value="Arizona",
        evidence_ids=("2hop__249867_557232::p3",),
        category="bridge_as_final",
        candidate_is_final_relation_object=False,
        filled_hop_index=1,
    )
    record["decision_head"] = {
        "typed_target_slot_binder_reject_reason": "non_final_slot",
    }

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("2hop__249867_557232"),
        make_update(
            "2hop__249867_557232",
            1,
            record,
            local_evidence_ids=("p1", "2hop__249867_557232::p3"),
        ),
    )

    candidate = next(item for item in result.state.candidates if item.value == "Arizona")
    assert candidate.status == "rejected"
    assert candidate.typed_reject_category == "bridge_as_final"
    assert candidate.rejection_reason == "non_final_slot"
    assert result.state.active_candidate_key == ""


def test_het_scheur_wrong_target_keeps_downstream_continuation_reason() -> None:
    evidence_id = "2hop__131951_643670::p10"
    record = two_hop_record(
        bound_value="Het Scheur",
        evidence_ids=(evidence_id,),
        category="wrong_target",
        candidate_is_final_relation_object=False,
        filled_hop_index=1,
    )
    record["decision_head"] = {
        "typed_target_slot_binder_reject_reason": (
            "mouth_watercourse_downstream_continuation"
        ),
    }

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("2hop__131951_643670"),
        make_update(
            "2hop__131951_643670",
            1,
            record,
            local_evidence_ids=("p1", evidence_id),
        ),
    )

    candidate = next(item for item in result.state.candidates if item.value == "Het Scheur")
    assert candidate.status == "rejected"
    assert candidate.typed_reject_category == "wrong_target"
    assert candidate.rejection_reason == "mouth_watercourse_downstream_continuation"
    candidate_events = [
        event for event in result.transition_events if event.get("candidate") == "Het Scheur"
    ]
    assert len(candidate_events) == 1


def test_rejection_applies_only_to_named_candidate() -> None:
    topology = two_hop_record(bound_value="Alice", evidence_ids=("p2",))
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, topology, local_evidence_ids=("p1", "p2")),
    )
    rejected = two_hop_record(
        bound_value="Bob",
        evidence_ids=("p3",),
        category="wrong_target",
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, rejected, local_evidence_ids=("p1", "p2", "p3")),
    )

    candidates = {item.normalized_value: item for item in second.state.candidates}
    assert candidates["alice"].status == "observed"
    assert candidates["bob"].status == "rejected"
    assert second.state.active_candidate_key == "alice"


def test_rejected_candidate_recovers_only_with_explicit_clean_binding() -> None:
    rejected = two_hop_record(bound_value="Bob", evidence_ids=("p2",), category="wrong_target")
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, rejected, local_evidence_ids=("p1", "p2")),
    )
    legacy_only = two_hop_record()
    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "s1",
            2,
            legacy_only,
            runtime_metadata={
                "slot_ledger_candidate_answer": "Bob",
                "slot_ledger_final_target_evidence_ids": ["p3"],
            },
            local_evidence_ids=("p1", "p2", "p3"),
        ),
    )
    assert next(item for item in second.state.candidates if item.normalized_value == "bob").status == "rejected"

    clean = two_hop_record(bound_value="Bob", evidence_ids=("p4",))
    third = reduce_slot_execution_state(
        second.state,
        make_update("s1", 3, clean, local_evidence_ids=("p1", "p2", "p3", "p4")),
    )
    assert next(item for item in third.state.candidates if item.normalized_value == "bob").status == "observed"


def test_rejected_candidate_recovers_on_strict_same_evidence_semantic_correction() -> None:
    rejected = binding_record(
        [
            ordered_hop(1, "A", "relation_a", "B", status="bound", evidence_ids=("p1",)),
            ordered_hop(2, "B", "relation_b", "Bob", final=True, status="bound", evidence_ids=("p2",)),
        ],
        bound_value="Bob",
        evidence_ids=("p2",),
        category="wrong_target",
        chain_complete=True,
        all_required_hops_covered=True,
        conflict_on_bridge=False,
        candidate_is_final_relation_object=True,
        filled_hop_index=2,
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, rejected, local_evidence_ids=("p1", "p2")),
    )
    clean = binding_record(
        [
            ordered_hop(1, "A", "relation_a", "B", status="bound", evidence_ids=("p1",)),
            ordered_hop(2, "B", "relation_b", "Bob", final=True, status="bound", evidence_ids=("p2",)),
        ],
        bound_value="Bob",
        evidence_ids=("p2",),
        chain_complete=True,
        all_required_hops_covered=True,
        conflict_on_bridge=False,
        candidate_is_final_relation_object=True,
        filled_hop_index=2,
    )

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, clean, local_evidence_ids=("p1", "p2")),
    )
    candidate = next(item for item in second.state.candidates if item.normalized_value == "bob")
    assert candidate.status == "verified"
    assert candidate.typed_reject_category == ""
    assert candidate.rejection_reason == ""
    assert {
        "event": "candidate_state_updated",
        "candidate": "Bob",
        "from": "rejected",
        "to": "verified",
        "reason": "strict_binding_clears_stale_rejection",
        "round_idx": 2,
    } in second.transition_events

    repeated = reduce_slot_execution_state(
        second.state,
        make_update("s1", 3, clean, local_evidence_ids=("p1", "p2")),
    )
    assert repeated.progress is False
    assert repeated.transition_events == ()
    assert repeated.state.candidates[0].status == "verified"


def test_all_rejected_candidates_leave_active_key_empty() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(bound_value="Alice", evidence_ids=("p2",), category="wrong_target"),
            local_evidence_ids=("p1", "p2"),
        ),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "s1",
            2,
            two_hop_record(bound_value="Bob", evidence_ids=("p3",), category="bridge_as_final"),
            local_evidence_ids=("p1", "p2", "p3"),
        ),
    )
    assert second.state.active_candidate_key == ""


@pytest.mark.parametrize(
    "category",
    (
        "answer_extraction_failure",
        "verifier_parse_failure",
        "empty_binding",
    ),
)
def test_non_authoritative_failure_categories_do_not_update_candidates(category: str) -> None:
    failure = two_hop_record(
        bound_value="Untrusted Candidate",
        evidence_ids=("p2",),
        category=category,
    )
    empty_result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, failure, local_evidence_ids=("p1", "p2")),
    )

    assert empty_result.state.candidates == ()
    assert empty_result.state.active_candidate_key == ""

    trusted = two_hop_record(bound_value="Alice", evidence_ids=("p2",))
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, trusted, local_evidence_ids=("p1", "p2")),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, failure, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.candidates == first.state.candidates
    assert second.state.active_candidate_key == first.state.active_candidate_key


def test_unknown_binding_reject_rejects_named_candidate() -> None:
    record = two_hop_record(
        bound_value="Untrusted Candidate",
        evidence_ids=("p2",),
        category="unknown_binding_reject",
    )

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1", "p2")),
    )

    candidate = next(item for item in result.state.candidates if item.value == "Untrusted Candidate")
    assert candidate.status == "rejected"
    assert candidate.typed_reject_category == "unknown_binding_reject"
    assert result.state.active_candidate_key == ""


def test_unscoped_typed_reject_emits_event_without_mutating_candidates() -> None:
    record = two_hop_record(category="wrong_target")

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1",)),
    )

    assert result.state.candidates == ()
    assert result.state.active_candidate_key == ""
    assert {
        "event": "unscoped_typed_reject_observed",
        "typed_reject_category": "wrong_target",
        "round_idx": 1,
    } in result.transition_events


def test_candidate_evidence_remains_scoped_to_its_source_candidate() -> None:
    record = two_hop_record(
        bound_value="Current Candidate",
        evidence_ids=("binding-evidence",),
    )

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            record,
            runtime_metadata={
                "preserved_final_candidate": "Preserved Candidate",
                "final_candidate_preserved": True,
                "slot_ledger_candidate_answer": "Legacy Candidate",
                "slot_ledger_final_target_evidence_ids": ["legacy-evidence"],
            },
            local_evidence_ids=("p1", "binding-evidence", "legacy-evidence"),
        ),
    )

    candidates = {candidate.value: candidate for candidate in result.state.candidates}
    assert candidates["Current Candidate"].evidence_ids == ("binding-evidence",)
    assert candidates["Preserved Candidate"].evidence_ids == ()
    assert candidates["Legacy Candidate"].evidence_ids == ("legacy-evidence",)


def test_same_candidate_unions_binding_and_legacy_scoped_evidence() -> None:
    record = two_hop_record(bound_value="Alice", evidence_ids=("binding-evidence",))

    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            record,
            runtime_metadata={
                "slot_ledger_candidate_answer": "Alice",
                "slot_ledger_final_target_evidence_ids": ["legacy-evidence"],
            },
            local_evidence_ids=("p1", "binding-evidence", "legacy-evidence"),
        ),
    )

    candidate = next(item for item in result.state.candidates if item.value == "Alice")
    assert candidate.evidence_ids == ("binding-evidence", "legacy-evidence")


def test_scoped_entailment_contradiction_emits_candidate_transition() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(bound_value="Alice", evidence_ids=("p2",)),
            local_evidence_ids=("p1", "p2"),
        ),
    )
    contradiction = {
        "slot_bound_entailment": {
            "candidate": "Alice",
            "contradicted": True,
            "evidence_ids": ["p3"],
        },
        "ordered_hop_binding": {},
    }

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, contradiction, local_evidence_ids=("p1", "p2", "p3")),
    )

    candidate = next(item for item in second.state.candidates if item.value == "Alice")
    assert candidate.status == "contradicted"
    assert second.state.active_candidate_key == ""
    assert {
        "event": "candidate_state_updated",
        "candidate": "Alice",
        "from": "observed",
        "to": "contradicted",
        "round_idx": 2,
    } in second.transition_events
    assert second.progress_reasons == ("candidate_state_updated",)

    repeated = reduce_slot_execution_state(
        second.state,
        make_update("s1", 3, contradiction, local_evidence_ids=("p1", "p2", "p3")),
    )
    assert repeated.progress is False
    assert repeated.transition_events == ()
    assert repeated.progress_reasons == ()


def test_ambiguous_hop_is_not_selected_as_missing_repair_target() -> None:
    initialized = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    ).state
    ambiguous_hop = replace(initialized.hops[1], status="ambiguous")
    ambiguous_state = replace(
        initialized,
        hops=(initialized.hops[0], ambiguous_hop),
        first_critical_missing_hop_id="",
        state_fingerprint="",
    )
    ambiguous_state = replace(
        ambiguous_state,
        state_fingerprint=ambiguous_state.semantic_fingerprint(),
    )

    result = reduce_slot_execution_state(
        ambiguous_state,
        make_update("s1", 2, {}, local_evidence_ids=("p1",)),
    )

    assert result.state.first_critical_missing_hop_id == ""
    assert hypothetical_state_action(result.state) == ("no_state_action", "")


def test_unscoped_typed_reject_is_not_a_progress_reason() -> None:
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(
            "s1",
            1,
            two_hop_record(category="wrong_target"),
            local_evidence_ids=("p1",),
        ),
    )

    assert result.progress is True
    assert any(
        event["event"] == "unscoped_typed_reject_observed"
        for event in result.transition_events
    )
    assert "topology_initialized" in result.progress_reasons
    assert "unscoped_typed_reject_observed" not in result.progress_reasons


def test_missing_conflict_on_bridge_does_not_verify_final_candidate() -> None:
    record = two_hop_record(
        second_status="bound",
        second_object="Answer",
        second_evidence=("p2",),
        bound_value="Answer",
        evidence_ids=("p2",),
        chain_complete=True,
        all_required_hops_covered=True,
        conflict_on_final_slot=False,
    )
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1", "p2")),
    )
    candidate = next(item for item in result.state.candidates if item.normalized_value == "answer")
    assert candidate.status == "support_incomplete"


def test_missing_critical_hints_use_typed_conservative_mapping() -> None:
    numeric = two_hop_record(missing_critical_hops=("2",))
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, numeric, local_evidence_ids=("p1",)),
    )
    assert result.state.hops[1].missing_requirements == ("required_hop_2",)
    assert any(event["event"] == "missing_requirement_resolved" for event in result.transition_events)

    relation = two_hop_record(missing_critical_hops=("relation_b",))
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s2"),
        make_update("s2", 1, relation, local_evidence_ids=("p1",)),
    )
    assert result.state.hops[1].missing_requirements == ("relation_b",)

    prose = two_hop_record(missing_critical_hops=("full claim mentioning relation_b in prose",))
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s3"),
        make_update("s3", 1, prose, local_evidence_ids=("p1",)),
    )
    assert result.state.hops[1].missing_requirements == (
        "full claim mentioning relation_b in prose",
    )
    assert any(
        event["event"] == "missing_requirement_resolved"
        and event["reason"] == "unique_dependency_frontier"
        for event in result.transition_events
    )

    indexed = two_hop_record(missing_critical_hops=("hop_index: 2",))
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s4"),
        make_update("s4", 1, indexed, local_evidence_ids=("p1",)),
    )
    assert result.state.hops[1].missing_requirements == ("required_hop_2",)


def test_relation_and_entity_aliases_update_the_same_frozen_hop() -> None:
    first_record = binding_record(
        [
            ordered_hop(
                1,
                "Datsun Type 12",
                "manufacturer",
                "Nissan",
                status="bound",
                evidence_ids=("p1",),
            ),
            ordered_hop(2, "Mohammed Atta", "has model", final=True),
        ]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, first_record, local_evidence_ids=("p1",)),
    )
    update_record = binding_record(
        [
            ordered_hop(
                1,
                "The Datsun Type 12",
                "produced by",
                "Nissan",
                status="bound",
                evidence_ids=("p1",),
            ),
            ordered_hop(
                2,
                "Mohamed Atta",
                "model of",
                "Nissan Altima",
                final=True,
                status="bound",
                evidence_ids=("p2",),
            ),
        ]
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, update_record, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops[1].status == "verified"
    assert second.state.hops[1].object_value == "Nissan Altima"
    assert any(
        event["event"] == "hop_update_resolved"
        and event["hop_id"] == "required_hop_2"
        for event in second.transition_events
    )
    assert not any(event["event"] == "hop_schema_drift_ignored" for event in second.transition_events)


def test_structured_missing_requirement_resolves_only_its_target_hop() -> None:
    record = two_hop_record()
    record["ordered_hop_binding"]["missing_requirements"] = [
        {
            "target_hop_id": "required_hop_2",
            "anchor_entity": "B",
            "canonical_relation": "relation_b",
            "expected_object_type": "entity",
            "missing_component": "object",
            "suggested_query": "B relation b",
        }
    ]
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1",)),
    )

    assert result.state.hops[0].missing_requirements == ()
    assert result.state.hops[1].missing_requirements == ("required_hop_2",)
    event = next(
        event for event in result.transition_events
        if event["event"] == "missing_requirement_resolved"
    )
    assert event["hop_id"] == "required_hop_2"
    assert event["reason"] == "explicit_target_hop_id"


def test_topology_fingerprint_mismatch_rejects_every_update_and_candidate() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    update_record = two_hop_record(
        second_status="bound",
        second_object="Answer",
        second_evidence=("p2",),
        bound_value="Answer",
        evidence_ids=("p2",),
    )
    update_record["ordered_hop_binding"].update(
        {
            "topology_version": first.state.topology_version,
            "topology_fingerprint": "wrong-fingerprint",
        }
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, update_record, local_evidence_ids=("p1", "p2")),
    )

    assert second.state.hops == first.state.hops
    assert second.state.candidates == first.state.candidates
    assert [event["event"] for event in second.transition_events] == [
        "topology_update_rejected"
    ]


def test_same_round_refresh_does_not_reject_model_supplied_fingerprint() -> None:
    record = two_hop_record()
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1",)),
    )
    refresh = two_hop_record()
    refresh["ordered_hop_binding"].update(
        {
            "topology_version": 1,
            "topology_fingerprint": "A -> bridge -> model-generated-final-chain",
        }
    )

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 1, refresh, local_evidence_ids=("p1",)),
    )

    assert second.state.topology_fingerprint == first.state.topology_fingerprint
    assert second.state.topology_version == first.state.topology_version
    assert not any(
        event["event"] == "topology_update_rejected"
        for event in second.transition_events
    )


def test_trusted_model_chain_can_replace_wrong_frozen_topology() -> None:
    initial = two_hop_record(bound_value="Wrong", evidence_ids=("p0",))
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, initial, local_evidence_ids=("p0", "p1")),
    )
    revised = trusted_revision_record(
        [
            ordered_hop(
                1,
                "Datsun Type 12",
                "manufacturer",
                "Nissan",
                status="bound",
                evidence_ids=("p1",),
            ),
            ordered_hop(
                2,
                "Mohamed Atta",
                "model",
                "Nissan Altima",
                final=True,
                status="bound",
                evidence_ids=("p2",),
            ),
        ],
        candidate="Nissan Altima",
        evidence_ids=("p1", "p2"),
        reason="deterministic_model_chain_binding",
    )

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, revised, local_evidence_ids=("p0", "p1", "p2")),
    )

    assert second.state.topology_version == 2
    assert second.state.topology_fingerprint != first.state.topology_fingerprint
    assert [hop.relation_id for hop in second.state.hops] == [
        "manufacturer",
        "owned_vehicle_model",
    ]
    assert all(hop.status == "verified" for hop in second.state.hops)
    assert [candidate.value for candidate in second.state.candidates] == ["Nissan Altima"]
    assert second.state.candidates[0].status == "verified"
    assert any(
        event["event"] == "topology_revision_applied"
        and event["reason"] == "deterministic_model_chain_binding"
        for event in second.transition_events
    )


def test_trusted_country_network_chain_can_replace_wrong_five_hop_topology() -> None:
    initial = binding_record(
        [
            ordered_hop(1, "General Santos", "located_in", "South Cotabato", status="bound", evidence_ids=("old1",)),
            ordered_hop(2, "South Cotabato", "country", "Philippines", status="bound", evidence_ids=("old2",)),
            ordered_hop(3, "Philippines", "embassy country"),
            ordered_hop(4, "country A", "show"),
            ordered_hop(5, "show", "created by", final=True),
        ]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("nbc"),
        make_update("nbc", 1, initial, local_evidence_ids=("old1", "old2")),
    )
    revised = trusted_revision_record(
        [
            ordered_hop(1, "General Santos", "located_on_shores_of", "Sarangani Bay", status="bound", evidence_ids=("p18",)),
            ordered_hop(2, "Sarangani Bay", "located_in", "Philippines", status="bound", evidence_ids=("p11",)),
            ordered_hop(3, "Embassy of the Philippines, Bandar Seri Begawan", "country_a", "Brunei", status="bound", evidence_ids=("p8",)),
            ordered_hop(4, "The Biggest Loser Brunei", "created_by", "NBC", final=True, status="bound", evidence_ids=("p5",)),
        ],
        candidate="NBC",
        evidence_ids=("p18", "p11", "p8", "p5"),
        reason="deterministic_country_network_chain_binding",
    )

    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "nbc",
            2,
            revised,
            local_evidence_ids=("old1", "old2", "p18", "p11", "p8", "p5"),
        ),
    )

    assert len(second.state.hops) == 4
    assert second.state.hops[-1].object_value == "NBC"
    assert second.state.hops[-1].status == "verified"
    assert second.state.candidates[0].value == "NBC"
    assert second.state.candidates[0].status == "verified"
    assert any(event["event"] == "topology_revision_applied" for event in second.transition_events)


def test_incomplete_deterministic_revision_is_rejected_without_state_or_candidate_migration() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    incomplete = trusted_revision_record(
        [
            ordered_hop(1, "Datsun Type 12", "manufacturer", "Nissan", status="bound", evidence_ids=("p1",)),
            ordered_hop(2, "Mohamed Atta", "model", "", final=True, status="missing"),
        ],
        candidate="Nissan Altima",
        evidence_ids=("p1",),
        reason="deterministic_model_chain_binding",
    )
    incomplete["ordered_hop_binding"]["chain_complete"] = False
    incomplete["set_level_sufficiency"]["all_required_hops_covered"] = False

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, incomplete, local_evidence_ids=("p1",)),
    )

    assert second.state.hops == first.state.hops
    assert second.state.candidates == first.state.candidates
    assert [event["event"] for event in second.transition_events] == [
        "topology_revision_rejected"
    ]
    assert second.transition_events[0]["reason"] == "deterministic_chain_incomplete"


def test_non_deterministic_topology_drift_cannot_replace_frozen_topology() -> None:
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    drift = binding_record(
        [
            ordered_hop(1, "Different", "manufacturer", "Nissan", status="bound", evidence_ids=("p2",)),
            ordered_hop(2, "Another", "model", "Altima", final=True, status="bound", evidence_ids=("p3",)),
        ]
    )

    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, drift, local_evidence_ids=("p1", "p2", "p3")),
    )

    assert second.state.topology_version == first.state.topology_version
    assert second.state.topology_fingerprint == first.state.topology_fingerprint
    assert not any(event["event"] == "topology_revision_applied" for event in second.transition_events)
    assert any(event["event"] == "hop_schema_drift_ignored" for event in second.transition_events)


def test_verified_bridge_identity_becomes_next_hop_subject_identity() -> None:
    record = binding_record(
        [
            ordered_hop(
                1,
                "Datsun Type 12",
                "manufacturer",
                "Nissan",
                status="bound",
                evidence_ids=("p1",),
            ),
            ordered_hop(2, "company", "model", final=True),
        ]
    )
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1",)),
    )

    assert result.state.hops[0].object_entity_id == "nissan"
    assert result.state.hops[1].subject_entity_id == "nissan"
    assert result.state.topology_version == 1
    assert result.state.topology_fingerprint


def test_same_round_refresh_is_idempotent() -> None:
    update = make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",))
    first = reduce_slot_execution_state(SlotExecutionState.empty("s1"), update)
    second = reduce_slot_execution_state(first.state, update)

    assert second.state.state_fingerprint == first.state.state_fingerprint
    assert second.state.no_progress_count == first.state.no_progress_count
    assert second.progress is False


def test_cross_round_identical_candidate_observation_emits_no_transition() -> None:
    record = two_hop_record(bound_value="Alice", evidence_ids=("p2",))
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1", "p2")),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, record, local_evidence_ids=("p1", "p2")),
    )

    assert second.progress is False
    assert second.progress_reasons == ()
    assert second.transition_events == ()
    assert second.state.no_progress_count == first.state.no_progress_count + 1
    candidate = next(item for item in second.state.candidates if item.value == "Alice")
    assert candidate.last_seen_round == 2

    new_evidence_record = two_hop_record(bound_value="Alice", evidence_ids=("p2", "p3"))
    third = reduce_slot_execution_state(
        second.state,
        make_update("s1", 3, new_evidence_record, local_evidence_ids=("p1", "p2", "p3")),
    )
    assert third.progress is True
    assert any(event["event"] == "candidate_state_updated" for event in third.transition_events)
    assert third.state.no_progress_count == 0


def test_stale_round_update_is_ignored() -> None:
    current = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 2, two_hop_record(), local_evidence_ids=("p1",)),
    )
    stale = reduce_slot_execution_state(
        current.state,
        make_update("s1", 1, two_hop_record(first_object="Changed"), local_evidence_ids=("p1",)),
    )
    assert stale.state == current.state
    assert stale.transition_events[0]["event"] == "stale_update_ignored"


def test_fingerprint_excludes_candidate_timestamps_and_bookkeeping() -> None:
    record = two_hop_record(bound_value="Answer", evidence_ids=("p2",))
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, record, local_evidence_ids=("p1", "p2")),
    )
    second = reduce_slot_execution_state(
        first.state,
        make_update("s1", 2, record, local_evidence_ids=("p1", "p2")),
    )
    assert second.state.candidates[0].last_seen_round == 2
    assert second.state.state_fingerprint == first.state.state_fingerprint
    assert second.state.no_progress_count == 1

    bookkeeping = replace(second.state, no_progress_count=99, last_repair_target_hop_id="required_hop_2")
    assert bookkeeping.semantic_fingerprint() == second.state.state_fingerprint


def test_fingerprint_is_stable_under_sequence_permutations() -> None:
    first_record = two_hop_record(
        first_evidence=("p2", "p1"),
        bound_value="Answer",
        evidence_ids=("p4", "p3"),
        missing_critical_hops=("relation_b", "2"),
    )
    first_record["ordered_hop_binding"]["required_hops"].reverse()
    second_record = two_hop_record(
        first_evidence=("p1", "p2"),
        bound_value="Answer",
        evidence_ids=("p3", "p4"),
        missing_critical_hops=("2", "relation_b"),
    )
    local_ids = ("p1", "p2", "p3", "p4")
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, first_record, local_evidence_ids=local_ids),
    )
    second = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, second_record, local_evidence_ids=tuple(reversed(local_ids))),
    )
    assert first.state.state_fingerprint == second.state.state_fingerprint


def test_hypothetical_action_reports_missing_hop_without_mutating_state() -> None:
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update("s1", 1, two_hop_record(), local_evidence_ids=("p1",)),
    )
    assert hypothetical_state_action(result.state) == ("repair_missing_hop", "required_hop_2")


def test_shared_saint_branch_mismatch_does_not_conflict_supported_foligno_facts() -> None:
    record = binding_record(
        [
            ordered_hop(
                1,
                "San Feliciano",
                "dedicated_to",
                "Foligno Cathedral",
                status="bound",
                evidence_ids=("p19",),
            ),
            ordered_hop(
                2,
                "Foligno Cathedral",
                "located_in",
                "Foligno",
                final=True,
                status="bound",
                evidence_ids=("p19",),
            ),
        ]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("saint"),
        make_update("saint", 1, record, local_evidence_ids=("p19",)),
    )
    verifier = {
        "overall_sufficiency": "conflicting",
        "claims": [
            {
                "claim": "The basilica in Foligno is named after the same saint as Mantua Cathedral",
                "status": "contradicted",
                "evidence_ids": ["p19"],
                "missing_evidence": "There is no evidence that the basilica concerns the same saint; it is not Saint Peter.",
            }
        ],
    }
    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "saint",
            2,
            record,
            verifier_record=verifier,
            local_evidence_ids=("p19",),
        ),
    )

    assert all(hop.status == "verified" for hop in second.state.hops)
    assert second.state.conflict_hop_ids == ()
    assert any(
        event["event"] == "branch_constraint_mismatch_observed"
        and event["reason"] == "shared_value_constraint_mismatch_not_fact_contradiction"
        for event in second.transition_events
    )


def test_nbc_bay_country_claim_cannot_conflict_shore_fact_by_shared_evidence() -> None:
    record = binding_record(
        [
            ordered_hop(
                1,
                "General Santos",
                "located_on_shores_of",
                "Sarangani Bay",
                final=True,
                status="bound",
                evidence_ids=("p18",),
            )
        ]
    )
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("nbc"),
        make_update("nbc", 1, record, local_evidence_ids=("p18",)),
    )
    verifier = {
        "overall_sufficiency": "conflicting",
        "claims": [
            {
                "claim": "The country that contains Sarangani Bay is South Cotabato.",
                "status": "contradicted",
                "evidence_ids": ["p18"],
                "missing_evidence": "The passage only says General Santos is on the shores of Sarangani Bay.",
            }
        ],
    }

    second = reduce_slot_execution_state(
        first.state,
        make_update(
            "nbc",
            2,
            record,
            verifier_record=verifier,
            local_evidence_ids=("p18",),
        ),
    )

    assert second.state.hops[0].status == "verified"
    assert second.state.conflict_hop_ids == ()
    assert any(
        event["event"] == "conflict_scope_mismatch_ignored"
        and event["evidence_ids"] == ["p18"]
        for event in second.transition_events
    )
