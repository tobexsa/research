from mvp_agentic_rag.semantic_hop_resolver import (
    canonical_entity_id,
    canonical_hop_id,
    canonical_relation_id,
    normalize_missing_requirement,
    resolve_hop_update,
    resolve_missing_requirement,
)


def hop(
    hop_id: str,
    relation_id: str,
    *,
    subject_entity_id: str,
    final: bool,
    status: str = "unresolved",
    dependencies: tuple[str, ...] = (),
    expected_object_type: str = "entity",
) -> dict:
    return {
        "hop_id": hop_id,
        "hop_index": int(hop_id.rsplit("_", 1)[-1]),
        "subject": subject_entity_id.replace("_", " "),
        "subject_entity_id": subject_entity_id,
        "subject_type": "entity",
        "relation": relation_id.replace("_", " "),
        "relation_id": relation_id,
        "expected_object_type": expected_object_type,
        "dependency_hop_ids": dependencies,
        "dependency_object_entity_ids": (),
        "is_final_hop": final,
        "status": status,
    }


def test_entity_and_relation_aliases_are_canonicalized_conservatively() -> None:
    assert canonical_entity_id("Mohamed Atta") == canonical_entity_id("Mohammed Atta")
    assert canonical_relation_id("company that makes") == "manufacturer"
    assert canonical_relation_id("produced by") == "manufacturer"
    assert canonical_relation_id("has model") == "owned_vehicle_model"
    assert canonical_relation_id("model of") == "owned_vehicle_model"
    assert canonical_relation_id("model") == "owned_vehicle_model"
    assert canonical_relation_id("changed relation") == "changed_relation"


def test_legacy_hop_index_variants_normalize_to_stable_hop_id() -> None:
    assert canonical_hop_id("2") == "required_hop_2"
    assert canonical_hop_id("hop_2") == "required_hop_2"
    assert canonical_hop_id("required_hop_2") == "required_hop_2"
    assert canonical_hop_id("hop_index: 2") == "required_hop_2"
    assert normalize_missing_requirement("hop_index 3")["target_hop_id"] == "required_hop_3"
    assert normalize_missing_requirement("hop_index: 4")["target_hop_id"] == "required_hop_4"
    assert normalize_missing_requirement("required_hop_2")["target_hop_id"] == "required_hop_2"
    assert normalize_missing_requirement({"target_hop_id": "hop_2"})["target_hop_id"] == "required_hop_2"


def test_explicit_hop_update_requires_identity_compatibility() -> None:
    hops = [
        hop(
            "required_hop_1",
            "manufacturer",
            subject_entity_id="datsun_type_12",
            final=False,
            expected_object_type="organization",
        )
    ]
    accepted = resolve_hop_update(
        hops,
        {
            "hop_id": "required_hop_1",
            "subject": "The Datsun Type 12",
            "relation": "produced by",
            "expected_object_type": "organization",
        },
        canonical_is_final_hop=False,
    )
    rejected = resolve_hop_update(
        hops,
        {
            "hop_id": "required_hop_1",
            "subject": "The Datsun Type 12",
            "relation": "headquarters location",
            "expected_object_type": "city",
        },
        canonical_is_final_hop=False,
    )

    assert accepted.status == "resolved"
    assert accepted.reason == "explicit_hop_id"
    assert rejected.status == "rejected"
    assert rejected.reason == "hop_identity_mismatch"


def test_explicit_hop_update_accepts_legacy_hop_id_alias() -> None:
    hops = [
        hop(
            "required_hop_2",
            "owned_vehicle_model",
            subject_entity_id="mohammed_atta",
            final=True,
            expected_object_type="vehicle_model",
        )
    ]

    resolution = resolve_hop_update(
        hops,
        {
            "hop_id": "hop_2",
            "subject": "Mohamed Atta",
            "relation": "model of",
            "expected_object_type": "vehicle_model",
        },
        canonical_is_final_hop=True,
    )

    assert resolution.status == "resolved"
    assert resolution.hop_id == "required_hop_2"


def test_missing_requirement_uses_dependency_frontier_and_rejects_guessing() -> None:
    hops = [
        hop(
            "required_hop_1",
            "record_label",
            subject_entity_id="desde_el_principio",
            final=False,
            status="verified",
        ),
        hop(
            "required_hop_2",
            "parent_organization",
            subject_entity_id="sony_music",
            final=False,
            dependencies=("required_hop_1",),
            expected_object_type="organization",
        ),
        hop(
            "required_hop_3",
            "headquarters_location",
            subject_entity_id="universal_music_group",
            final=False,
            dependencies=("required_hop_2",),
            expected_object_type="city",
        ),
        hop(
            "required_hop_4",
            "count",
            subject_entity_id="santa_monica",
            final=True,
            dependencies=("required_hop_3",),
            expected_object_type="count",
        ),
    ]
    resolved = resolve_missing_requirement(
        hops,
        {
            "target_hop_id": "required_hop_2",
            "anchor_entity": "Sony Music",
            "canonical_relation": "parent organization",
            "expected_object_type": "organization",
        },
    )
    blocked = resolve_missing_requirement(
        hops,
        {
            "target_hop_id": "required_hop_3",
            "anchor_entity": "Universal Music Group",
            "canonical_relation": "headquarters location",
            "expected_object_type": "city",
        },
    )

    assert resolved.status == "resolved"
    assert resolved.hop_id == "required_hop_2"
    assert blocked.status == "rejected"
    assert blocked.reason == "target_hop_dependencies_incomplete"


def test_ambiguous_typed_requirement_is_not_guessed() -> None:
    hops = [
        hop(
            "required_hop_1",
            "located_in",
            subject_entity_id="a",
            final=False,
            expected_object_type="location",
        ),
        hop(
            "required_hop_2",
            "located_in",
            subject_entity_id="b",
            final=True,
            expected_object_type="location",
        ),
    ]
    resolution = resolve_missing_requirement(
        hops,
        {"canonical_relation": "located in", "expected_object_type": "location"},
    )

    assert resolution.status == "ambiguous"
    assert set(resolution.candidate_hop_ids) == {"required_hop_1", "required_hop_2"}


def test_requirement_rejections_report_subject_relation_and_type_mismatches() -> None:
    base = hop(
        "required_hop_1",
        "performer",
        subject_entity_id="east_coasting",
        final=False,
        expected_object_type="person",
    )

    relation = resolve_missing_requirement(
        [base],
        {
            "target_hop_id": "required_hop_1",
            "anchor_entity": "East Coasting",
            "canonical_relation": "state_of_origin",
            "expected_object_type": "person",
        },
    )
    expected_type = resolve_missing_requirement(
        [base],
        {
            "target_hop_id": "required_hop_1",
            "anchor_entity": "East Coasting",
            "canonical_relation": "performer",
            "expected_object_type": "location",
        },
    )
    subject = resolve_missing_requirement(
        [base],
        {
            "target_hop_id": "required_hop_1",
            "anchor_entity": "Different Work",
            "canonical_relation": "performer",
            "expected_object_type": "person",
        },
    )

    assert relation.reason == "hop_binding_relation_mismatch"
    assert relation.metadata["binding_mismatch"]["component"] == "relation"
    assert expected_type.reason == "hop_binding_expected_type_mismatch"
    assert expected_type.metadata["binding_mismatch"]["component"] == "expected_object_type"
    assert subject.reason == "hop_binding_subject_mismatch"
    assert subject.metadata["binding_mismatch"]["component"] == "subject"
