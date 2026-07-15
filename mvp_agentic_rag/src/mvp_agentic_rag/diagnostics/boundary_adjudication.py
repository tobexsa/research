from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


ADJUDICATION_PROTOCOL_VERSION = "boundary_assistant_adjudication_v1"
ADJUDICATED_LABEL_FIELDS = (
    "first_loss_boundary",
    "evidence_state",
    "candidate_state",
    "candidate_failure_subtype",
    "conflict_state",
    "wrong_target",
    "recommended_action",
)
HUMAN_REVIEWER_PROVENANCE_FIELDS = (
    "reviewer_id",
    "reviewed_at",
    "review_protocol_version",
)


def build_evidence_bundles(
    review_events: Iterable[dict[str, Any]],
    corpus_records: Iterable[dict[str, Any]],
    *,
    trajectory_sources: Mapping[str, Iterable[dict[str, Any]]],
    fixed_evidence_sources: Mapping[str, Iterable[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    corpus_index: dict[str, dict[str, Any]] = {}
    for record in corpus_records:
        passage_id = str(record.get("id") or "")
        if not passage_id:
            raise ValueError("Corpus records require id")
        if passage_id in corpus_index:
            raise ValueError(f"Duplicate corpus passage id: {passage_id}")
        corpus_index[passage_id] = deepcopy(record)
    trajectory_indexes = {
        source_id: _sample_index(records, source_id=source_id)
        for source_id, records in trajectory_sources.items()
    }
    fixed_indexes = {
        source_id: _sample_index(records, source_id=source_id)
        for source_id, records in fixed_evidence_sources.items()
    }

    bundles: dict[str, dict[str, Any]] = {}
    for review in review_events:
        review_event_id = str(review.get("review_event_id") or "")
        machine = review.get("machine_boundary_event") or {}
        sample_id = str(review.get("sample_id") or "")
        source_id = str(machine.get("source_id") or "")
        source_kind = str(machine.get("source_kind") or "")
        round_index = int(machine.get("round") or 0)
        if not review_event_id or not sample_id or not source_id or not round_index:
            raise ValueError("Review events require review_event_id, sample_id, source_id, and round")
        if source_kind == "trajectory":
            source_record = _require_sample_record(
                trajectory_indexes,
                source_id=source_id,
                sample_id=sample_id,
                round_index=round_index,
            )
            steps = [
                step
                for step in source_record.get("trajectory") or []
                if int(step.get("round") or 0) == round_index
            ]
            if len(steps) != 1:
                raise ValueError(
                    f"Could not resolve exact source/round for {source_id}/{sample_id}/r{round_index}"
                )
            source_round_record = deepcopy(steps[0])
        elif source_kind == "fixed_evidence":
            if round_index != 1:
                raise ValueError(
                    f"Could not resolve exact source/round for "
                    f"{source_id}/{sample_id}/r{round_index}"
                )
            source_record = _require_sample_record(
                fixed_indexes,
                source_id=source_id,
                sample_id=sample_id,
                round_index=round_index,
            )
            source_round_record = deepcopy(source_record)
        else:
            raise ValueError(f"Unsupported source kind for evidence reconstruction: {source_kind}")

        oracle = machine.get("oracle_evidence") or {}
        retrieved_ids = [str(value) for value in oracle.get("retrieved_ids_cumulative") or []]
        support_ids = [str(value) for value in oracle.get("supporting_passage_ids") or []]
        requested_ids = list(dict.fromkeys(retrieved_ids + support_ids))
        missing_ids = [passage_id for passage_id in requested_ids if passage_id not in corpus_index]
        if missing_ids:
            raise ValueError(
                f"Missing corpus passage text for {review_event_id}: {', '.join(missing_ids)}"
            )
        retrieved_passages = [_passage_record(corpus_index[value], support_ids) for value in retrieved_ids]
        support_passages = [_passage_record(corpus_index[value], support_ids) for value in support_ids]
        bundles[review_event_id] = {
            "review_event_id": review_event_id,
            "sample_id": sample_id,
            "source_id": source_id,
            "source_kind": source_kind,
            "round": round_index,
            "retrieved_passage_ids": retrieved_ids,
            "supporting_passage_ids": support_ids,
            "retrieved_passages": retrieved_passages,
            "gold_support_passages": support_passages,
            "source_round_record": source_round_record,
            "source_record_id": str(source_record.get("id") or source_record.get("sample_id") or ""),
            "evidence_reconstruction_complete": True,
            "evidence_reconstruction_provenance": {
                "exact_source_match": True,
                "exact_sample_match": True,
                "exact_round_match": True,
                "round_match_basis": (
                    "native_trajectory_round"
                    if source_kind == "trajectory"
                    else "fixed_evidence_single_record_r1"
                ),
                "passage_text_source": "musique_corpus",
            },
        }
    return bundles


def adjudicate_review_events(
    review_events: Iterable[dict[str, Any]],
    evidence_bundles: Mapping[str, dict[str, Any]],
    overrides: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    override_rows = [deepcopy(row) for row in overrides]
    adjudicated: list[dict[str, Any]] = []
    reviewed_at = datetime.now(timezone.utc).isoformat()
    for review in review_events:
        review_event_id = str(review.get("review_event_id") or "")
        bundle = evidence_bundles.get(review_event_id)
        if not bundle or not bundle.get("evidence_reconstruction_complete"):
            raise ValueError(f"Complete evidence bundle required for {review_event_id}")
        machine = review.get("machine_boundary_event") or {}
        labels = _default_adjudicated_labels(machine)
        matching_overrides = [row for row in override_rows if _override_matches(row, review)]
        applied_override_ids: list[str] = []
        override_notes: list[str] = []
        override_confidences: list[str] = []
        decision_override = ""
        status_override = ""
        for override in matching_overrides:
            override_id = str(override.get("override_id") or "")
            if not override_id:
                raise ValueError("Every adjudication override requires override_id")
            unknown_fields = set(override.get("set_labels") or {}) - set(ADJUDICATED_LABEL_FIELDS)
            if unknown_fields:
                raise ValueError(f"Unknown adjudicated label fields in {override_id}: {sorted(unknown_fields)}")
            labels.update(deepcopy(override.get("set_labels") or {}))
            applied_override_ids.append(override_id)
            if override.get("reason"):
                override_notes.append(str(override["reason"]))
            if override.get("confidence"):
                override_confidences.append(str(override["confidence"]))
            if override.get("decision"):
                decision_override = str(override["decision"])
            if override.get("status"):
                status_override = str(override["status"])

        machine_suggestions = review.get("assistant_suggestions") or {}
        differs_from_prefill = any(
            labels[field] != machine_suggestions.get(field) for field in ADJUDICATED_LABEL_FIELDS
        )
        if labels["evidence_state"] == "ambiguous":
            decision = "exclude_event"
            status = "assistant_excluded"
            confidence = "high"
        else:
            decision = "correct_labels" if differs_from_prefill else "accept_assistant_suggestion"
            status = "assistant_adjudicated"
            confidence = "medium" if labels["first_loss_boundary"] in {"C_form", "C_align", "V"} else "high"
        if decision_override:
            decision = decision_override
        if status_override:
            status = status_override
        if override_confidences:
            confidence = override_confidences[-1]
        unsafe_success = (
            str(machine.get("outcome_state") or "") in {"exact", "alias_exact", "relaxed"}
            and labels["evidence_state"] == "incomplete"
            and status != "assistant_excluded"
        )
        action_gap = labels["first_loss_boundary"] in {"C_form", "C_align", "V"}
        rationale = _adjudication_rationale(labels, machine, unsafe_success, action_gap)
        if override_notes:
            rationale = rationale + " Overrides: " + " ".join(override_notes)
        row = deepcopy(review)
        row.update(
            {
                "assistant_adjudication_protocol_version": ADJUDICATION_PROTOCOL_VERSION,
                "assistant_adjudicated_labels": labels,
                "assistant_adjudication_decision": decision,
                "assistant_adjudication_status": status,
                "assistant_adjudication_confidence": confidence,
                "assistant_adjudication_rationale": rationale,
                "assistant_action_set_gap": action_gap,
                "unsafe_success": unsafe_success,
                "answer_outcome": str(machine.get("outcome_state") or ""),
                "applied_override_ids": applied_override_ids,
                "evidence_bundle": deepcopy(bundle),
                "assistant_reviewer_provenance": {
                    "reviewer_type": "ai_assistant_proxy",
                    "reviewer_id": "codex_assistant",
                    "reviewed_at": reviewed_at,
                    "review_protocol_version": ADJUDICATION_PROTOCOL_VERSION,
                    "is_human_reviewer": False,
                },
                "eligible_for_training": False,
                "assistant_adjudication_provenance": {
                    "authoritative_human_gold": False,
                    "uses_human_review": False,
                    "exact_source_evidence_reconstructed": True,
                    "semantic_override_manifest_applied": bool(applied_override_ids),
                },
            }
        )
        validate_assistant_adjudication(row)
        adjudicated.append(row)
    return adjudicated


def validate_assistant_adjudication(row: dict[str, Any]) -> None:
    labels = row.get("assistant_adjudicated_labels") or {}
    if set(labels) != set(ADJUDICATED_LABEL_FIELDS) or any(labels[field] is None for field in labels):
        raise ValueError("Assistant-adjudicated labels must be complete")
    reviewer = row.get("assistant_reviewer_provenance") or {}
    if (
        reviewer.get("reviewer_type") != "ai_assistant_proxy"
        or reviewer.get("reviewer_id") != "codex_assistant"
        or reviewer.get("is_human_reviewer") is not False
    ):
        raise ValueError("Assistant adjudication requires explicit non-human reviewer provenance")
    provenance = row.get("assistant_adjudication_provenance") or {}
    if provenance.get("authoritative_human_gold") is not False or provenance.get(
        "uses_human_review"
    ) is not False:
        raise ValueError("Assistant adjudication must not claim human gold")
    if bool(row.get("eligible_for_training")):
        raise ValueError("Assistant-adjudicated events remain training-ineligible")
    human_labels = row.get("human_reviewed_labels") or {}
    if any(value is not None for value in human_labels.values()):
        raise ValueError("Assistant adjudication must not modify human-owned labels")
    if row.get("human_review_decision") is not None:
        raise ValueError("Assistant adjudication must not modify human-owned decision")
    if row.get("human_review_status") != "pending_human_confirmation":
        raise ValueError("Assistant adjudication must preserve human-owned pending status")
    reviewer_provenance = row.get("reviewer_provenance") or {}
    if any(reviewer_provenance.get(field) is not None for field in HUMAN_REVIEWER_PROVENANCE_FIELDS):
        raise ValueError("Assistant adjudication must not modify human-owned reviewer provenance")
    if row.get("human_review_notes") not in (None, ""):
        raise ValueError("Assistant adjudication must not modify human-owned notes")
    if not (row.get("evidence_bundle") or {}).get("evidence_reconstruction_complete"):
        raise ValueError("Assistant adjudication requires complete evidence reconstruction")
    if row.get("assistant_adjudication_status") not in {
        "assistant_adjudicated",
        "assistant_excluded",
        "assistant_deferred",
    }:
        raise ValueError("Invalid assistant adjudication status")


def summarize_assistant_adjudication(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(rows)
    changed = [
        row
        for row in records
        if row.get("assistant_adjudication_decision") == "correct_labels"
    ]
    excluded = [
        row
        for row in records
        if row.get("assistant_adjudication_status") == "assistant_excluded"
    ]
    excluded_question_ids = sorted({str(row.get("sample_id") or "") for row in excluded})
    corrected_question_ids = sorted({str(row.get("sample_id") or "") for row in changed})
    return {
        "adjudication_protocol_version": ADJUDICATION_PROTOCOL_VERSION,
        "event_count": len(records),
        "question_count": len({str(row.get("sample_id") or "") for row in records}),
        "event_tier_counts": dict(
            sorted(Counter(str(row.get("priority_tier") or "") for row in records).items())
        ),
        "assistant_adjudication_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("assistant_adjudication_status") or "") for row in records
                ).items()
            )
        ),
        "assistant_adjudication_decision_counts": dict(
            sorted(
                Counter(
                    str(row.get("assistant_adjudication_decision") or "") for row in records
                ).items()
            )
        ),
        "assistant_boundary_counts": dict(
            sorted(
                Counter(
                    str((row.get("assistant_adjudicated_labels") or {}).get("first_loss_boundary") or "")
                    for row in records
                ).items()
            )
        ),
        "assistant_adjudicated_event_count": sum(
            row.get("assistant_adjudication_status") == "assistant_adjudicated"
            for row in records
        ),
        "assistant_corrected_event_count": len(changed),
        "assistant_nonexcluded_label_revision_event_count": len(changed),
        "assistant_corrected_question_count": len(corrected_question_ids),
        "assistant_corrected_question_ids": corrected_question_ids,
        "assistant_excluded_event_count": len(excluded),
        "assistant_excluded_question_count": len(excluded_question_ids),
        "assistant_excluded_question_ids": excluded_question_ids,
        "assistant_wrong_target_event_count": sum(
            bool((row.get("assistant_adjudicated_labels") or {}).get("wrong_target"))
            for row in records
        ),
        "assistant_wrong_target_question_count": len(
            {
                str(row.get("sample_id") or "")
                for row in records
                if bool((row.get("assistant_adjudicated_labels") or {}).get("wrong_target"))
            }
        ),
        "assistant_conflict_state_counts": dict(
            sorted(
                Counter(
                    str((row.get("assistant_adjudicated_labels") or {}).get("conflict_state") or "")
                    for row in records
                ).items()
            )
        ),
        "assistant_candidate_failure_subtype_counts": dict(
            sorted(
                Counter(
                    str(
                        (row.get("assistant_adjudicated_labels") or {}).get(
                            "candidate_failure_subtype"
                        )
                        or ""
                    )
                    for row in records
                ).items()
            )
        ),
        "assistant_action_set_gap_event_count": sum(
            bool(row.get("assistant_action_set_gap")) for row in records
        ),
        "unsafe_success_event_count": sum(bool(row.get("unsafe_success")) for row in records),
        "override_applied_event_count": sum(bool(row.get("applied_override_ids")) for row in records),
        "human_confirmed_event_count": sum(
            row.get("human_review_status") == "human_confirmed" for row in records
        ),
        "training_eligible_event_count": sum(
            bool(row.get("eligible_for_training")) for row in records
        ),
        "remaining_human_confirmation_event_count": sum(
            row.get("human_review_status") == "pending_human_confirmation" for row in records
        ),
    }


def _sample_index(
    records: Iterable[dict[str, Any]],
    *,
    source_id: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        sample_id = str(record.get("id") or record.get("sample_id") or "")
        if not sample_id:
            raise ValueError(f"Source {source_id} contains a record without sample id")
        if sample_id in result:
            raise ValueError(f"Source {source_id} contains duplicate sample id {sample_id}")
        result[sample_id] = deepcopy(record)
    return result


def _require_sample_record(
    indexes: Mapping[str, Mapping[str, dict[str, Any]]],
    *,
    source_id: str,
    sample_id: str,
    round_index: int,
) -> dict[str, Any]:
    source = indexes.get(source_id)
    if source is None or sample_id not in source:
        raise ValueError(
            f"Could not resolve exact source/round for {source_id}/{sample_id}/r{round_index}"
        )
    return deepcopy(source[sample_id])


def _passage_record(record: dict[str, Any], support_ids: list[str]) -> dict[str, Any]:
    return {
        "id": str(record.get("id") or ""),
        "title": str(record.get("title") or ""),
        "text": str(record.get("text") or ""),
        "is_gold_support": str(record.get("id") or "") in set(support_ids),
        "metadata": deepcopy(record.get("metadata") or {}),
    }


def _default_adjudicated_labels(machine: dict[str, Any]) -> dict[str, Any]:
    evidence_state = str(machine.get("evidence_state") or "")
    candidate_state = str(machine.get("candidate_state") or "")
    if evidence_state == "ambiguous":
        boundary = "ambiguous"
    elif evidence_state != "complete":
        boundary = "E"
    elif candidate_state == "none":
        boundary = "C_form"
    elif candidate_state == "wrong_only":
        boundary = "C_align"
    else:
        verifier_accepts = str(machine.get("verifier_state") or "") == "correct_accept" or bool(
            (machine.get("verifier_disposition") or {}).get("accepts_correct_candidate")
        )
        if not verifier_accepts:
            boundary = "V"
        elif str(machine.get("observable_through") or "") == "V":
            boundary = "none"
        elif str(machine.get("policy_state") or "") != "correct_answer":
            boundary = "P"
        elif str(machine.get("outcome_state") or "") in {"alias_exact", "relaxed"}:
            boundary = "O"
        else:
            boundary = "none"
    if boundary == "C_form":
        failure_subtype = "not_formed"
    elif boundary == "C_align":
        failure_subtype = "other"
    elif boundary == "E" and candidate_state == "wrong_only":
        failure_subtype = "other"
    else:
        failure_subtype = "none"
    return {
        "first_loss_boundary": boundary,
        "evidence_state": evidence_state,
        "candidate_state": candidate_state,
        "candidate_failure_subtype": failure_subtype,
        "conflict_state": "none",
        "wrong_target": False,
        "recommended_action": _recommended_action(boundary, machine),
    }


def _recommended_action(boundary: str, machine: dict[str, Any]) -> str:
    if boundary == "E":
        budget = machine.get("budget_remaining")
        exhausted = budget is None
        try:
            exhausted = exhausted or float(budget) <= 0
        except (TypeError, ValueError):
            exhausted = True
        return "abstain" if bool(machine.get("is_terminal")) and exhausted else "repair_missing_hop"
    if boundary in {"C_form", "C_align", "V", "ambiguous"}:
        return "abstain"
    return "answer"


def _override_matches(override: dict[str, Any], review: dict[str, Any]) -> bool:
    match = override.get("match") or {}
    machine = review.get("machine_boundary_event") or {}
    values = {
        "review_event_id": str(review.get("review_event_id") or ""),
        "sample_id": str(review.get("sample_id") or ""),
        "source_id": str(machine.get("source_id") or ""),
        "source_kind": str(machine.get("source_kind") or ""),
        "round": int(machine.get("round") or 0),
        "machine_boundary": str(machine.get("first_loss_boundary") or ""),
    }
    return bool(match) and all(values.get(key) == value for key, value in match.items())


def _adjudication_rationale(
    labels: dict[str, Any],
    machine: dict[str, Any],
    unsafe_success: bool,
    action_gap: bool,
) -> str:
    boundary = labels["first_loss_boundary"]
    if boundary == "E":
        rationale = "Current cumulative evidence does not contain every required gold-support passage."
    elif boundary == "C_form":
        rationale = "Gold support is complete, but no final-slot candidate is formed."
    elif boundary == "C_align":
        rationale = "Gold support is complete, but the final-slot candidate set is wrong-only."
    elif boundary == "V":
        rationale = "A semantically correct final candidate exists, but the verifier does not accept it."
    elif boundary == "P":
        rationale = "A correct candidate is verifier-accepted, but policy does not answer correctly."
    elif boundary == "O":
        rationale = "The answer is semantically correct under alias/relaxed matching but not primary exact surface."
    elif boundary == "ambiguous":
        rationale = "Gold support is explicitly non-entailing or otherwise ambiguous; exclude from boundary gold."
    else:
        rationale = "No safety-stage loss is observed under the reconstructed event state."
    if unsafe_success:
        rationale += " Exact answer outcome is retained separately as unsafe_success; it does not override incomplete evidence."
    if action_gap:
        rationale += " The current controller vocabulary lacks a stage-specific repair, so abstain is the safe available action."
    if str(machine.get("first_loss_boundary") or "") != boundary:
        rationale += f" Machine boundary {machine.get('first_loss_boundary')} is corrected to {boundary}."
    return rationale
