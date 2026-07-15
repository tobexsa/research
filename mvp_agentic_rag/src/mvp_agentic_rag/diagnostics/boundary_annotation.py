from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from typing import Any, Iterable, Mapping


CONTRACT_VERSION = "boundary_annotation_contract_v1"
DEFAULT_SPLIT_RATIOS = {"train": 0.6, "dev": 0.2, "test": 0.2}
BOUNDARY_VALUES = ("E", "C_form", "C_align", "V", "P", "O", "none", "ambiguous")
EVIDENCE_VALUES = ("incomplete", "complete", "ambiguous")
CANDIDATE_VALUES = ("none", "correct_present", "wrong_only", "mixed")
CONFLICT_VALUES = ("none", "resolvable", "irreconcilable", "unclear")
CANDIDATE_FAILURE_VALUES = (
    "none",
    "not_formed",
    "malformed",
    "wrong_target",
    "bridge_as_final",
    "unsupported",
    "other",
)
ACTION_VALUES = (
    "answer",
    "repair_missing_hop",
    "read_more",
    "disambiguate_conflict",
    "abstain",
)
REQUIRED_REVIEWED_FIELDS = (
    "first_loss_boundary",
    "evidence_state",
    "candidate_state",
    "candidate_failure_subtype",
    "conflict_state",
    "wrong_target",
    "recommended_action",
)


def build_question_components(sample_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Build transitive question components from shared MuSiQue decomposition IDs."""
    questions = sorted({str(sample_id).strip() for sample_id in sample_ids if str(sample_id).strip()})
    parent = {sample_id: sample_id for sample_id in questions}

    def find(sample_id: str) -> str:
        while parent[sample_id] != sample_id:
            parent[sample_id] = parent[parent[sample_id]]
            sample_id = parent[sample_id]
        return sample_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    decomposition_owner: dict[str, str] = {}
    question_decomposition_ids: dict[str, list[str]] = {}
    for sample_id in questions:
        parts = _decomposition_ids(sample_id)
        question_decomposition_ids[sample_id] = parts
        for part in parts:
            owner = decomposition_owner.setdefault(part, sample_id)
            union(owner, sample_id)

    grouped: dict[str, list[str]] = defaultdict(list)
    for sample_id in questions:
        grouped[find(sample_id)].append(sample_id)

    components: list[dict[str, Any]] = []
    for members in sorted(grouped.values(), key=lambda values: tuple(sorted(values))):
        members = sorted(members)
        decomposition_ids = sorted(
            {
                decomposition_id
                for sample_id in members
                for decomposition_id in question_decomposition_ids[sample_id]
            }
        )
        digest = hashlib.sha256("\n".join(members).encode("utf-8")).hexdigest()[:12]
        components.append(
            {
                "component_group_id": f"decomp_cc::{digest}",
                "sample_ids": members,
                "decomposition_ids": decomposition_ids,
                "question_count": len(members),
                "grouping_rule": "transitive_shared_musique_decomposition_id",
            }
        )
    return components


def assign_component_splits(
    components: Iterable[dict[str, Any]],
    question_profiles: Mapping[str, dict[str, Any]],
    ratios: Mapping[str, float] | None = None,
) -> dict[str, str]:
    """Assign whole connected components to deterministic provisional splits."""
    component_rows = [deepcopy(component) for component in components]
    split_ratios = dict(ratios or DEFAULT_SPLIT_RATIOS)
    _validate_split_ratios(split_ratios)
    split_names = list(split_ratios)
    question_total = sum(len(component.get("sample_ids") or []) for component in component_rows)
    p0_total = sum(
        str(question_profiles.get(sample_id, {}).get("priority_tier") or "P3") == "P0"
        for component in component_rows
        for sample_id in component.get("sample_ids") or []
    )
    question_targets = {name: question_total * split_ratios[name] for name in split_names}
    p0_targets = {name: p0_total * split_ratios[name] for name in split_names}
    question_counts = {name: 0 for name in split_names}
    p0_counts = {name: 0 for name in split_names}

    def component_features(component: dict[str, Any]) -> tuple[int, int, int, str]:
        members = list(component.get("sample_ids") or [])
        tier_counts = Counter(
            str(question_profiles.get(sample_id, {}).get("priority_tier") or "P3")
            for sample_id in members
        )
        return (
            int(tier_counts.get("P0", 0)),
            int(tier_counts.get("P1", 0)),
            len(members),
            str(component.get("component_group_id") or ""),
        )

    ordered = sorted(
        component_rows,
        key=lambda component: (
            -component_features(component)[0],
            -component_features(component)[1],
            -component_features(component)[2],
            component_features(component)[3],
        ),
    )
    assignments: dict[str, str] = {}
    for component in ordered:
        component_id = str(component.get("component_group_id") or "")
        if not component_id:
            raise ValueError("Every component requires component_group_id")
        members = [str(value) for value in component.get("sample_ids") or []]
        component_p0 = sum(
            str(question_profiles.get(sample_id, {}).get("priority_tier") or "P3") == "P0"
            for sample_id in members
        )

        def assignment_cost(candidate_split: str) -> tuple[float, float, int]:
            projected_questions = dict(question_counts)
            projected_p0 = dict(p0_counts)
            projected_questions[candidate_split] += len(members)
            projected_p0[candidate_split] += component_p0
            question_cost = sum(
                ((projected_questions[name] - question_targets[name]) / max(question_targets[name], 1.0)) ** 2
                for name in split_names
            )
            rare_cost = 0.0
            if p0_total:
                rare_cost = sum(
                    ((projected_p0[name] - p0_targets[name]) / max(p0_targets[name], 1.0)) ** 2
                    for name in split_names
                )
            overflow = max(
                0.0,
                projected_questions[candidate_split] - max(question_targets[candidate_split], 1.0),
            )
            return (question_cost + 2.0 * rare_cost + overflow, overflow, split_names.index(candidate_split))

        selected_split = min(split_names, key=assignment_cost)
        assignments[component_id] = selected_split
        question_counts[selected_split] += len(members)
        p0_counts[selected_split] += component_p0
    return assignments


def build_question_profiles(
    ledger: Iterable[dict[str, Any]],
    interventions: Iterable[dict[str, Any]],
    human_verified: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Join all source events under the ledger's question-level grouping key."""
    ledger_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        sample_id = str(row.get("sample_id") or "").strip()
        if not sample_id:
            raise ValueError("Ledger rows require sample_id")
        ledger_groups[sample_id].append(deepcopy(row))

    intervention_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in interventions:
        sample_id = str(row.get("sample_id") or "").strip()
        if sample_id in ledger_groups:
            intervention_groups[sample_id].append(deepcopy(row))

    human_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in human_verified:
        sample_id = str(row.get("sample_id") or "").strip()
        if sample_id in ledger_groups:
            human_groups[sample_id].append(deepcopy(row))

    profiles: dict[str, dict[str, Any]] = {}
    for sample_id in sorted(ledger_groups):
        rows = sorted(
            ledger_groups[sample_id],
            key=lambda row: (
                str(row.get("source_id") or ""),
                int(row.get("round") or 0),
                str(row.get("ledger_id") or ""),
            ),
        )
        intervention_rows = sorted(
            intervention_groups.get(sample_id, []),
            key=lambda row: str(row.get("intervention_id") or ""),
        )
        human_rows = sorted(
            human_groups.get(sample_id, []),
            key=lambda row: (
                str(row.get("source_run") or ""),
                int(row.get("round") or 0),
                str(row.get("id") or ""),
            ),
        )
        transitions = _observed_e_to_c_transitions(rows, intervention_rows)
        reasons = _priority_reasons(rows, human_rows, transitions)
        priority_tier = _priority_tier(reasons)
        priority_score = _priority_score(priority_tier, reasons, rows, human_rows)
        profiles[sample_id] = {
            "sample_id": sample_id,
            "question": _first_text(rows, "question"),
            "gold_answer": _first_text(rows, "gold_answer"),
            "decomposition_ids": _decomposition_ids(sample_id),
            "boundary_events": [_boundary_event(row) for row in rows],
            "intervention_events": [_intervention_event(row) for row in intervention_rows],
            "human_verified_risk_events": [_human_risk_event(row) for row in human_rows],
            "observed_e_to_c_transitions": transitions,
            "priority_tier": priority_tier,
            "priority_score": priority_score,
            "priority_reasons": reasons,
        }
    return profiles


def build_annotation_packets(
    profiles: Mapping[str, dict[str, Any]],
    component_map: Mapping[str, str],
    split_map: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Build one self-contained review packet for every question."""
    packets: list[dict[str, Any]] = []
    for sample_id in sorted(profiles):
        profile = profiles[sample_id]
        component_id = str(component_map.get(sample_id) or "")
        if not component_id:
            raise ValueError(f"Missing component assignment for {sample_id}")
        proposed_split = str(split_map.get(component_id) or "")
        if proposed_split not in DEFAULT_SPLIT_RATIOS:
            raise ValueError(f"Missing provisional split for component {component_id}")
        boundary_events = deepcopy(profile.get("boundary_events") or [])
        human_events = deepcopy(profile.get("human_verified_risk_events") or [])
        packet = {
            "contract_version": CONTRACT_VERSION,
            "packet_id": f"boundary_packet::{sample_id}",
            "sample_id": sample_id,
            "question_group_id": sample_id,
            "component_group_id": component_id,
            "decomposition_ids": list(profile.get("decomposition_ids") or []),
            "proposed_split": proposed_split,
            "split_status": "provisional_not_publication_ready",
            "priority_tier": str(profile.get("priority_tier") or "P3"),
            "priority_score": int(profile.get("priority_score") or 0),
            "priority_reasons": list(profile.get("priority_reasons") or []),
            "question": str(profile.get("question") or ""),
            "gold_answer": str(profile.get("gold_answer") or ""),
            "boundary_events": boundary_events,
            "intervention_events": deepcopy(profile.get("intervention_events") or []),
            "observed_e_to_c_transitions": deepcopy(
                profile.get("observed_e_to_c_transitions") or []
            ),
            "human_verified_risk_events": human_events,
            "boundary_prefill": _boundary_prefill(profile),
            "boundary_annotations": [
                _pending_boundary_annotation(event) for event in boundary_events
            ],
            "boundary_annotation_status": "pending_review",
            "eligible_for_training": False,
            "review_contract": _review_contract(),
            "provenance": {
                "boundary_prefill": {
                    "derivation": "machine_derived_from_ecvpo_ledger_and_joined_source_signals",
                    "uses_human_review": False,
                    "is_human_gold": False,
                },
                "source_claim_risk_context": {
                    "record_count": len(human_events),
                    "has_human_verified_records": any(
                        event.get("source_annotation_status") == "human_verified"
                        for event in human_events
                    ),
                    "scope": (
                        "Human verification applies only to copied source claim-risk fields; "
                        "it does not verify any boundary annotation in this packet."
                    ),
                },
                "immutable_grouping_key": "sample_id",
                "component_grouping_rule": "transitive_shared_musique_decomposition_id",
            },
        }
        validate_annotation_packet(packet)
        packets.append(packet)
    return packets


def select_priority_batch(
    packets: Iterable[dict[str, Any]],
    *,
    target_count: int = 24,
) -> list[dict[str, Any]]:
    """Select a bounded review batch while making P0 inclusion non-negotiable."""
    if target_count < 0:
        raise ValueError("target_count must be non-negative")
    unique: dict[str, dict[str, Any]] = {}
    for packet in packets:
        sample_id = str(packet.get("sample_id") or "")
        if not sample_id:
            raise ValueError("Priority packets require sample_id")
        if sample_id in unique:
            raise ValueError(f"Duplicate question group in packet pool: {sample_id}")
        unique[sample_id] = packet
    p0_count = sum(str(packet.get("priority_tier") or "") == "P0" for packet in unique.values())
    if p0_count > target_count:
        raise ValueError(
            f"P0 packet count ({p0_count}) exceeds target_count ({target_count}); "
            "P0 packets must not be silently dropped"
        )
    tier_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    ordered = sorted(
        unique.values(),
        key=lambda packet: (
            tier_rank.get(str(packet.get("priority_tier") or "P3"), 4),
            -int(packet.get("priority_score") or 0),
            str(packet.get("sample_id") or ""),
        ),
    )
    return [deepcopy(packet) for packet in ordered[: min(target_count, len(ordered))]]


def validate_annotation_packet(packet: dict[str, Any]) -> None:
    required = {
        "contract_version",
        "packet_id",
        "sample_id",
        "question_group_id",
        "component_group_id",
        "proposed_split",
        "boundary_events",
        "boundary_annotations",
        "boundary_annotation_status",
        "eligible_for_training",
        "provenance",
    }
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError(f"Annotation packet missing required fields: {missing}")
    sample_id = str(packet.get("sample_id") or "")
    if not sample_id or packet.get("question_group_id") != sample_id:
        raise ValueError("question_group_id must equal the non-empty sample_id")
    if packet.get("proposed_split") not in DEFAULT_SPLIT_RATIOS:
        raise ValueError("proposed_split must be train, dev, or test")
    boundary_provenance = (packet.get("provenance") or {}).get("boundary_prefill") or {}
    if boundary_provenance.get("uses_human_review") is not False:
        raise ValueError("Machine-derived boundary prefill must not claim uses_human_review")

    events = list(packet.get("boundary_events") or [])
    annotations = list(packet.get("boundary_annotations") or [])
    event_ids = [str(event.get("ledger_id") or "") for event in events]
    annotation_event_ids = [str(item.get("ledger_id") or "") for item in annotations]
    if len(event_ids) != len(set(event_ids)) or "" in event_ids:
        raise ValueError("boundary_events require unique, non-empty ledger_id values")
    if event_ids != annotation_event_ids:
        raise ValueError("boundary_annotations must align one-to-one with boundary_events")
    if any(str(event.get("sample_id") or "") != sample_id for event in events):
        raise ValueError("All rounds and source events in a packet must share sample_id")

    status = str(packet.get("boundary_annotation_status") or "")
    eligible = bool(packet.get("eligible_for_training"))
    if status == "pending_review":
        if eligible:
            raise ValueError("Pending boundary annotations are not eligible for training")
        if any(item.get("annotation_status") != "pending_review" for item in annotations):
            raise ValueError("Pending packets require pending event annotations")
        if any(item.get("eligible_for_training") for item in annotations):
            raise ValueError("Pending event annotations are not eligible for training")
    elif status == "human_verified":
        for annotation in annotations:
            reviewer = annotation.get("reviewer_provenance") or {}
            if not all(
                str(reviewer.get(field) or "").strip()
                for field in ("reviewer_id", "reviewed_at", "review_protocol_version")
            ):
                raise ValueError(
                    "human_verified boundary labels require reviewer provenance for every event"
                )
            reviewed = annotation.get("reviewed_labels") or {}
            missing_reviewed = [
                field
                for field in REQUIRED_REVIEWED_FIELDS
                if field not in reviewed or reviewed[field] is None or reviewed[field] == ""
            ]
            if missing_reviewed:
                raise ValueError(
                    f"human_verified boundary labels missing reviewed fields: {missing_reviewed}"
                )
            if annotation.get("annotation_status") != "human_verified":
                raise ValueError("Verified packets require verified event annotations")
    else:
        raise ValueError("boundary_annotation_status must be pending_review or human_verified")
    if eligible and status != "human_verified":
        raise ValueError("Only human_verified boundary annotations may be training-eligible")


def summarize_annotation_contract(
    packets: Iterable[dict[str, Any]],
    batch: Iterable[dict[str, Any]],
    components: Iterable[dict[str, Any]],
    splits: Mapping[str, str],
) -> dict[str, Any]:
    packet_rows = list(packets)
    batch_rows = list(batch)
    component_rows = list(components)
    packet_ids = [str(packet.get("sample_id") or "") for packet in packet_rows]
    batch_ids = {str(packet.get("sample_id") or "") for packet in batch_rows}
    p0_ids = {
        str(packet.get("sample_id") or "")
        for packet in packet_rows
        if packet.get("priority_tier") == "P0"
    }
    component_split_sets: dict[str, set[str]] = defaultdict(set)
    decomposition_split_sets: dict[str, set[str]] = defaultdict(set)
    for component in component_rows:
        component_id = str(component.get("component_group_id") or "")
        split = str(splits.get(component_id) or "")
        component_split_sets[component_id].add(split)
        for decomposition_id in component.get("decomposition_ids") or []:
            decomposition_split_sets[str(decomposition_id)].add(split)
    question_split_sets: dict[str, set[str]] = defaultdict(set)
    split_priority_counts: dict[str, Counter[str]] = {
        split: Counter() for split in DEFAULT_SPLIT_RATIOS
    }
    for packet in packet_rows:
        split = str(packet.get("proposed_split") or "")
        question_split_sets[str(packet.get("sample_id") or "")].add(split)
        split_priority_counts.setdefault(split, Counter()).update(
            [str(packet.get("priority_tier") or "unknown")]
        )
    return {
        "contract_version": CONTRACT_VERSION,
        "packet_count": len(packet_rows),
        "unique_question_count": len(set(packet_ids)),
        "component_count": len(component_rows),
        "boundary_event_count": sum(len(packet.get("boundary_events") or []) for packet in packet_rows),
        "intervention_event_count": sum(
            len(packet.get("intervention_events") or []) for packet in packet_rows
        ),
        "human_verified_source_risk_event_count": sum(
            len(packet.get("human_verified_risk_events") or []) for packet in packet_rows
        ),
        "priority_tier_counts": dict(
            sorted(Counter(str(packet.get("priority_tier") or "unknown") for packet in packet_rows).items())
        ),
        "priority_reason_question_counts": dict(
            sorted(
                Counter(
                    reason
                    for packet in packet_rows
                    for reason in packet.get("priority_reasons") or []
                ).items()
            )
        ),
        "split_question_counts": dict(
            sorted(Counter(str(packet.get("proposed_split") or "unknown") for packet in packet_rows).items())
        ),
        "split_component_counts": dict(sorted(Counter(splits.values()).items())),
        "split_priority_tier_counts": {
            split: dict(sorted(counts.items()))
            for split, counts in split_priority_counts.items()
        },
        "priority_batch_count": len(batch_rows),
        "priority_batch_unique_question_count": len(batch_ids),
        "p0_question_count": len(p0_ids),
        "all_p0_in_priority_batch": p0_ids.issubset(batch_ids),
        "pending_review_packet_count": sum(
            packet.get("boundary_annotation_status") == "pending_review" for packet in packet_rows
        ),
        "training_eligible_packet_count": sum(
            bool(packet.get("eligible_for_training")) for packet in packet_rows
        ),
        "question_cross_split_count": sum(len(values) > 1 for values in question_split_sets.values()),
        "component_cross_split_count": sum(len(values) > 1 for values in component_split_sets.values()),
        "decomposition_id_cross_split_count": sum(
            len(values) > 1 for values in decomposition_split_sets.values()
        ),
        "split_is_leakage_safe": all(
            len(values) == 1
            for groups in (question_split_sets, component_split_sets, decomposition_split_sets)
            for values in groups.values()
        ),
    }


def _decomposition_ids(sample_id: str) -> list[str]:
    if "__" not in sample_id:
        return []
    return sorted({part for part in sample_id.split("__", 1)[1].split("_") if part})


def _validate_split_ratios(ratios: Mapping[str, float]) -> None:
    if set(ratios) != {"train", "dev", "test"}:
        raise ValueError("Split ratios must define train, dev, and test")
    if any(float(value) <= 0 for value in ratios.values()):
        raise ValueError("Split ratios must be positive")
    if abs(sum(float(value) for value in ratios.values()) - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")


def _first_text(rows: list[dict[str, Any]], key: str) -> str:
    return next((str(row.get(key) or "") for row in rows if row.get(key)), "")


def _boundary_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ledger_id": str(row.get("ledger_id") or ""),
        "sample_id": str(row.get("sample_id") or ""),
        "source_id": str(row.get("source_id") or ""),
        "source_kind": str(row.get("source_kind") or ""),
        "evidence_grade": str(row.get("evidence_grade") or ""),
        "round": int(row.get("round") or 0),
        "is_terminal": bool(row.get("is_terminal")),
        "observable_through": str(row.get("observable_through") or ""),
        "runtime_action": str(row.get("runtime_action") or ""),
        "budget_remaining": row.get("budget_remaining"),
        "first_loss_boundary": str(row.get("first_loss_boundary") or ""),
        "evidence_state": str(row.get("evidence_state") or ""),
        "ambiguity_reason": str(row.get("ambiguity_reason") or ""),
        "oracle_evidence": deepcopy(row.get("oracle_evidence") or {}),
        "candidate_state": str(row.get("candidate_state") or ""),
        "candidate_state_details": deepcopy(row.get("candidate_state_details") or {}),
        "candidate_records": deepcopy(row.get("candidate_records") or []),
        "cumulative_candidate_records": deepcopy(row.get("cumulative_candidate_records") or []),
        "verifier_state": str(row.get("verifier_state") or ""),
        "verifier_disposition": deepcopy(row.get("verifier_disposition") or {}),
        "policy_state": str(row.get("policy_state") or ""),
        "policy_disposition": deepcopy(row.get("policy_disposition") or {}),
        "outcome_state": str(row.get("outcome_state") or ""),
        "source_label_provenance": deepcopy(row.get("label_provenance") or {}),
    }


def _intervention_event(row: dict[str, Any]) -> dict[str, Any]:
    event = deepcopy(row)
    event["source_scope"] = "stored_observation_or_oracle_contract_probe"
    return event


def _human_risk_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_record_id": str(row.get("id") or ""),
        "sample_id": str(row.get("sample_id") or ""),
        "source_dataset": str(row.get("dataset") or ""),
        "source_run": str(row.get("source_run") or ""),
        "round": int(row.get("round") or 0),
        "candidate_answer": str(row.get("candidate_answer") or ""),
        "claims": deepcopy(row.get("claims") or []),
        "evidence": deepcopy(row.get("evidence") or []),
        "claim_support": deepcopy(row.get("claim_support") or {}),
        "evidence_sufficiency": str(row.get("evidence_sufficiency") or ""),
        "critical_missing_claims": deepcopy(row.get("critical_missing_claims") or []),
        "noncritical_missing_claims": deepcopy(row.get("noncritical_missing_claims") or []),
        "contradicted_claims": deepcopy(row.get("contradicted_claims") or []),
        "wrong_target": bool(row.get("wrong_target")),
        "bridge_as_final": bool(row.get("bridge_as_final")),
        "final_answer_supported": bool(row.get("final_answer_supported")),
        "should_abstain": bool(row.get("should_abstain")),
        "oracle_action": str(row.get("oracle_action") or ""),
        "oracle_repair_target": deepcopy(row.get("oracle_repair_target") or {}),
        "risk_type": str(row.get("risk_type") or ""),
        "source_annotation_status": str(row.get("annotation_status") or ""),
        "source_label_provenance": deepcopy(row.get("label_provenance") or {}),
        "source_notes": str(row.get("notes") or ""),
        "scope": "human_verified_source_claim_risk_context_not_boundary_gold",
    }


def _observed_e_to_c_transitions(
    rows: list[dict[str, Any]],
    interventions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[str(row.get("source_id") or "")].append(row)
    for source_id, source_rows in sorted(by_source.items()):
        source_rows.sort(key=lambda row: (int(row.get("round") or 0), str(row.get("ledger_id") or "")))
        for before, after in zip(source_rows, source_rows[1:]):
            if (
                str(before.get("first_loss_boundary") or "") == "E"
                and str(after.get("first_loss_boundary") or "") in {"C_form", "C_align"}
            ):
                transitions.append(
                    {
                        "transition_type": "natural_trajectory",
                        "source_id": source_id,
                        "from_ledger_id": str(before.get("ledger_id") or ""),
                        "to_ledger_id": str(after.get("ledger_id") or ""),
                        "from_round": int(before.get("round") or 0),
                        "to_round": int(after.get("round") or 0),
                        "before_boundary": "E",
                        "after_boundary": str(after.get("first_loss_boundary") or ""),
                        "evidence_grade": "observed_trajectory_transition",
                    }
                )
    for intervention in interventions:
        for field, transition_type in (
            ("observed_fixed_evidence", "fixed_evidence_probe"),
            ("observed_trajectory_transition", "intervention_trajectory_probe"),
        ):
            probe = intervention.get(field) or {}
            if (
                bool(probe.get("available"))
                and bool(probe.get("boundary_advanced"))
                and str(probe.get("before_boundary") or "") == "E"
                and str(probe.get("after_boundary") or "") in {"C_form", "C_align"}
            ):
                transitions.append(
                    {
                        "transition_type": transition_type,
                        "intervention_id": str(intervention.get("intervention_id") or ""),
                        "source_id": str(probe.get("source_id") or ""),
                        "from_round": probe.get("from_round"),
                        "to_round": probe.get("to_round"),
                        "before_boundary": "E",
                        "after_boundary": str(probe.get("after_boundary") or ""),
                        "evidence_grade": str(probe.get("evidence_grade") or ""),
                    }
                )
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    for transition in transitions:
        key = (
            transition.get("transition_type"),
            transition.get("source_id"),
            transition.get("from_ledger_id"),
            transition.get("to_ledger_id"),
            transition.get("intervention_id"),
            transition.get("from_round"),
            transition.get("to_round"),
            transition.get("after_boundary"),
        )
        if key not in seen:
            seen.add(key)
            unique.append(transition)
    return unique


def _priority_reasons(
    rows: list[dict[str, Any]],
    human_rows: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    if any(_is_human_wrong_target(row) for row in human_rows):
        reasons.append("human_verified_wrong_target")
    if any(_is_human_conflict(row) for row in human_rows):
        reasons.append("human_verified_conflict")
    if transitions:
        reasons.append("observed_e_to_c_transition")
    if any(
        bool(row.get("is_terminal"))
        and str(row.get("first_loss_boundary") or "") in {"C_form", "C_align"}
        for row in rows
    ):
        reasons.append("terminal_c_form_or_c_align")
    if any(
        str(row.get("candidate_state") or "") == "wrong_only"
        or "false_accept" in str(row.get("verifier_state") or "")
        for row in rows
    ):
        reasons.append("wrong_only_or_false_accept_candidate")
    if any(
        str(row.get("first_loss_boundary") or "") == "E"
        and float((row.get("oracle_evidence") or {}).get("coverage_rate") or 0.0) >= 0.5
        and str(row.get("candidate_state") or "") in {"none", "wrong_only"}
        for row in rows
    ):
        reasons.append("high_coverage_e_missing_or_wrong_candidate")
    return reasons or ["contextual_boundary_state"]


def _priority_tier(reasons: list[str]) -> str:
    if any(
        reason
        in {
            "human_verified_wrong_target",
            "human_verified_conflict",
            "observed_e_to_c_transition",
        }
        for reason in reasons
    ):
        return "P0"
    if any(
        reason in {"terminal_c_form_or_c_align", "wrong_only_or_false_accept_candidate"}
        for reason in reasons
    ):
        return "P1"
    if "high_coverage_e_missing_or_wrong_candidate" in reasons:
        return "P2"
    return "P3"


def _priority_score(
    tier: str,
    reasons: list[str],
    rows: list[dict[str, Any]],
    human_rows: list[dict[str, Any]],
) -> int:
    base = {"P0": 4000, "P1": 3000, "P2": 2000, "P3": 1000}[tier]
    weights = {
        "human_verified_wrong_target": 500,
        "human_verified_conflict": 450,
        "observed_e_to_c_transition": 400,
        "terminal_c_form_or_c_align": 300,
        "wrong_only_or_false_accept_candidate": 250,
        "high_coverage_e_missing_or_wrong_candidate": 200,
        "contextual_boundary_state": 0,
    }
    return base + sum(weights[reason] for reason in reasons) + min(len(rows), 99) + min(len(human_rows), 99)


def _is_human_wrong_target(row: dict[str, Any]) -> bool:
    return bool(row.get("wrong_target")) or "wrong_target" in str(row.get("risk_type") or "").lower()


def _is_human_conflict(row: dict[str, Any]) -> bool:
    risk_type = str(row.get("risk_type") or "").lower()
    return bool(row.get("contradicted_claims")) or str(row.get("oracle_action") or "") == "disambiguate_conflict" or any(
        marker in risk_type for marker in ("contradiction", "conflict")
    )


def _boundary_prefill(profile: dict[str, Any]) -> dict[str, Any]:
    events = list(profile.get("boundary_events") or [])
    human_events = list(profile.get("human_verified_risk_events") or [])
    return {
        "derivation_status": "machine_prefill_pending_human_review",
        "observed_first_loss_boundaries": sorted(
            {str(event.get("first_loss_boundary") or "") for event in events}
        ),
        "terminal_first_loss_boundaries": sorted(
            {
                str(event.get("first_loss_boundary") or "")
                for event in events
                if event.get("is_terminal")
            }
        ),
        "observed_e_to_c_transition_count": len(profile.get("observed_e_to_c_transitions") or []),
        "source_human_verified_conflict_event_count": sum(
            _is_human_conflict(event) for event in human_events
        ),
        "source_human_verified_wrong_target_event_count": sum(
            _is_human_wrong_target(event) for event in human_events
        ),
        "warning": (
            "Source human verification is contextual only; every boundary label below requires "
            "an independent boundary review."
        ),
    }


def _pending_boundary_annotation(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "annotation_id": f"boundary_review::{event.get('ledger_id', '')}",
        "ledger_id": str(event.get("ledger_id") or ""),
        "machine_prefill": {
            "first_loss_boundary": str(event.get("first_loss_boundary") or ""),
            "evidence_state": str(event.get("evidence_state") or ""),
            "candidate_state": str(event.get("candidate_state") or ""),
            "verifier_state": str(event.get("verifier_state") or ""),
            "policy_state": str(event.get("policy_state") or ""),
        },
        "reviewed_labels": {field: None for field in REQUIRED_REVIEWED_FIELDS},
        "annotation_status": "pending_review",
        "eligible_for_training": False,
        "reviewer_provenance": {
            "reviewer_id": None,
            "reviewed_at": None,
            "review_protocol_version": None,
        },
        "review_notes": "",
    }


def _review_contract() -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "annotation_unit": "ledger_boundary_event_within_question_grouped_packet",
        "required_reviewed_fields": list(REQUIRED_REVIEWED_FIELDS),
        "allowed_values": {
            "first_loss_boundary": list(BOUNDARY_VALUES),
            "evidence_state": list(EVIDENCE_VALUES),
            "candidate_state": list(CANDIDATE_VALUES),
            "candidate_failure_subtype": list(CANDIDATE_FAILURE_VALUES),
            "conflict_state": list(CONFLICT_VALUES),
            "wrong_target": [False, True],
            "recommended_action": list(ACTION_VALUES),
        },
        "reviewer_provenance_required": [
            "reviewer_id",
            "reviewed_at",
            "review_protocol_version",
        ],
        "completion_rule": (
            "A packet becomes human_verified only after every event is reviewed under this "
            "protocol. Human-verified source claim-risk fields do not satisfy this rule."
        ),
        "training_rule": (
            "pending_review and partially reviewed records are ineligible; training eligibility "
            "requires completed boundary review plus downstream split freeze."
        ),
    }
