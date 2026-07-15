from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Iterable


REVIEW_CONTRACT_VERSION = "boundary_human_review_queue_v1"
TIER_ORDER = {"P0": 0, "P1": 1, "P2": 2}
HUMAN_REVIEW_FIELDS = (
    "first_loss_boundary",
    "evidence_state",
    "candidate_state",
    "candidate_failure_subtype",
    "conflict_state",
    "wrong_target",
    "recommended_action",
)


def build_review_events(packets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_packets = _ordered_packets(packets)
    review_events: list[dict[str, Any]] = []
    global_order = 0
    for question_order, packet in enumerate(ordered_packets, start=1):
        sample_id = str(packet.get("sample_id") or "")
        risk_context = _source_risk_context(packet.get("human_verified_risk_events") or [])
        for event_order, event in enumerate(packet.get("boundary_events") or [], start=1):
            global_order += 1
            suggestions = _assistant_suggestions(event, risk_context)
            flags = _attention_flags(event, risk_context, suggestions)
            high_count = sum(flag["severity"] == "high" for flag in flags)
            review = {
                "review_contract_version": REVIEW_CONTRACT_VERSION,
                "review_event_id": f"human_review::{event.get('ledger_id', '')}",
                "review_event_order": global_order,
                "question_review_order": question_order,
                "event_order_within_question": event_order,
                "priority_tier": str(packet.get("priority_tier") or ""),
                "priority_score": int(packet.get("priority_score") or 0),
                "priority_reasons": list(packet.get("priority_reasons") or []),
                "sample_id": sample_id,
                "question": str(packet.get("question") or ""),
                "gold_answer": str(packet.get("gold_answer") or ""),
                "component_group_id": str(packet.get("component_group_id") or ""),
                "proposed_split": str(packet.get("proposed_split") or ""),
                "ledger_id": str(event.get("ledger_id") or ""),
                "machine_boundary_event": deepcopy(event),
                "source_risk_context": risk_context,
                "assistant_suggestions": suggestions,
                "assistant_precheck_status": (
                    "needs_human_adjudication" if flags else "ready_for_confirmation"
                ),
                "assistant_suggestion_confidence": (
                    "low" if high_count else ("medium" if flags else "high")
                ),
                "attention_flags": flags,
                "human_reviewed_labels": {field: None for field in HUMAN_REVIEW_FIELDS},
                "human_review_decision": None,
                "human_review_status": "pending_human_confirmation",
                "reviewer_provenance": {
                    "reviewer_id": None,
                    "reviewed_at": None,
                    "review_protocol_version": None,
                },
                "human_review_notes": "",
                "eligible_for_training": False,
                "provenance": {
                    "assistant_suggestions": {
                        "authoritative": False,
                        "uses_human_review": False,
                        "may_be_copied_to_human_fields_automatically": False,
                    },
                    "source_risk_context": {
                        "contains_human_verified_source_fields": bool(
                            risk_context["human_verified_source_record_count"]
                        ),
                        "scope": "claim_risk_context_only_not_boundary_gold",
                    },
                },
            }
            validate_review_event(review)
            review_events.append(review)
    return review_events


def build_question_review_queue(
    packets: Iterable[dict[str, Any]],
    review_events: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered_packets = _ordered_packets(packets)
    events_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in review_events:
        events_by_sample[str(event.get("sample_id") or "")].append(event)
    queue: list[dict[str, Any]] = []
    for question_order, packet in enumerate(ordered_packets, start=1):
        sample_id = str(packet.get("sample_id") or "")
        events = sorted(
            events_by_sample.get(sample_id, []),
            key=lambda event: int(event.get("event_order_within_question") or 0),
        )
        flags = [flag for event in events for flag in event.get("attention_flags") or []]
        terminal_boundaries = sorted(
            {
                str((event.get("machine_boundary_event") or {}).get("first_loss_boundary") or "")
                for event in events
                if (event.get("machine_boundary_event") or {}).get("is_terminal")
            }
        )
        question_flags = _question_attention_flags(events, terminal_boundaries)
        all_flag_codes = [flag["code"] for flag in flags + question_flags]
        queue.append(
            {
                "review_contract_version": REVIEW_CONTRACT_VERSION,
                "question_review_order": question_order,
                "priority_tier": str(packet.get("priority_tier") or ""),
                "priority_score": int(packet.get("priority_score") or 0),
                "priority_reasons": list(packet.get("priority_reasons") or []),
                "sample_id": sample_id,
                "question": str(packet.get("question") or ""),
                "gold_answer": str(packet.get("gold_answer") or ""),
                "component_group_id": str(packet.get("component_group_id") or ""),
                "proposed_split": str(packet.get("proposed_split") or ""),
                "event_count": len(events),
                "review_event_ids": [str(event.get("review_event_id") or "") for event in events],
                "machine_boundary_counts": dict(
                    sorted(
                        Counter(
                            str(
                                (event.get("machine_boundary_event") or {}).get(
                                    "first_loss_boundary"
                                )
                                or "unknown"
                            )
                            for event in events
                        ).items()
                    )
                ),
                "terminal_machine_boundaries": terminal_boundaries,
                "source_risk_context": deepcopy(
                    events[0]["source_risk_context"] if events else _source_risk_context([])
                ),
                "assistant_precheck": {
                    "needs_human_adjudication_event_count": sum(
                        event.get("assistant_precheck_status") == "needs_human_adjudication"
                        for event in events
                    ),
                    "attention_flag_counts": dict(sorted(Counter(all_flag_codes).items())),
                    "question_attention_flags": question_flags,
                    "scope": "non_authoritative_assistance_only",
                },
                "human_review_status": "not_started",
                "human_confirmed_event_count": 0,
                "reviewer_provenance": {
                    "reviewer_id": None,
                    "reviewed_at": None,
                    "review_protocol_version": None,
                },
                "human_question_notes": "",
                "eligible_for_training": False,
            }
        )
    return queue


def summarize_review_queue(
    review_events: Iterable[dict[str, Any]],
    question_queue: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    events = list(review_events)
    questions = list(question_queue)
    tiers = [str(question.get("priority_tier") or "") for question in questions]
    flag_event_counts = Counter()
    flag_question_ids: dict[str, set[str]] = defaultdict(set)
    severity_counts = Counter()
    for event in events:
        for flag in event.get("attention_flags") or []:
            code = str(flag.get("code") or "")
            flag_event_counts[code] += 1
            flag_question_ids[code].add(str(event.get("sample_id") or ""))
            severity_counts[str(flag.get("severity") or "unknown")] += 1
    for question in questions:
        for flag in (question.get("assistant_precheck") or {}).get(
            "question_attention_flags"
        ) or []:
            code = str(flag.get("code") or "")
            flag_question_ids[code].add(str(question.get("sample_id") or ""))
    return {
        "review_contract_version": REVIEW_CONTRACT_VERSION,
        "question_count": len(questions),
        "event_count": len(events),
        "question_tier_counts": dict(sorted(Counter(tiers).items())),
        "event_tier_counts": dict(
            sorted(Counter(str(event.get("priority_tier") or "") for event in events).items())
        ),
        "review_order_is_p0_then_p1_then_p2": tiers
        == sorted(tiers, key=lambda tier: TIER_ORDER.get(tier, 99)),
        "assistant_precheck_status_counts": dict(
            sorted(
                Counter(
                    str(event.get("assistant_precheck_status") or "") for event in events
                ).items()
            )
        ),
        "assistant_attention_flag_event_counts": dict(sorted(flag_event_counts.items())),
        "assistant_attention_flag_question_counts": {
            code: len(sample_ids) for code, sample_ids in sorted(flag_question_ids.items())
        },
        "assistant_attention_flag_question_ids": {
            code: sorted(sample_ids) for code, sample_ids in sorted(flag_question_ids.items())
        },
        "assistant_attention_severity_counts": dict(sorted(severity_counts.items())),
        "assistant_unresolved_action_suggestion_count": sum(
            (event.get("assistant_suggestions") or {}).get("recommended_action") is None
            for event in events
        ),
        "human_confirmed_event_count": sum(
            event.get("human_review_status") == "human_confirmed" for event in events
        ),
        "human_completed_question_count": sum(
            question.get("human_review_status") == "completed" for question in questions
        ),
        "training_eligible_event_count": sum(
            bool(event.get("eligible_for_training")) for event in events
        ),
        "training_eligible_question_count": sum(
            bool(question.get("eligible_for_training")) for question in questions
        ),
        "source_conflict_context_question_count": sum(
            bool((question.get("source_risk_context") or {}).get("has_conflict_context"))
            for question in questions
        ),
        "source_wrong_target_context_question_count": sum(
            bool((question.get("source_risk_context") or {}).get("has_wrong_target_context"))
            for question in questions
        ),
        "handoff_status": "awaiting_human_confirmation",
    }


def validate_review_event(
    event: dict[str, Any],
    *,
    require_blank_human_fields: bool = True,
) -> None:
    required = {
        "review_event_id",
        "review_event_order",
        "priority_tier",
        "sample_id",
        "ledger_id",
        "machine_boundary_event",
        "assistant_suggestions",
        "human_reviewed_labels",
        "human_review_status",
        "reviewer_provenance",
        "eligible_for_training",
        "provenance",
    }
    missing = sorted(required - set(event))
    if missing:
        raise ValueError(f"Review event missing required fields: {missing}")
    if str(event.get("priority_tier") or "") not in TIER_ORDER:
        raise ValueError("Review queue accepts only P0, P1, and P2 packets")
    sample_id = str(event.get("sample_id") or "")
    machine_event = event.get("machine_boundary_event") or {}
    if not sample_id or str(machine_event.get("sample_id") or "") != sample_id:
        raise ValueError("Review event and machine boundary event must share sample_id")
    if str(machine_event.get("ledger_id") or "") != str(event.get("ledger_id") or ""):
        raise ValueError("Review event must preserve its ledger_id")
    assistant_provenance = (event.get("provenance") or {}).get(
        "assistant_suggestions"
    ) or {}
    if assistant_provenance.get("authoritative") is not False or assistant_provenance.get(
        "uses_human_review"
    ) is not False:
        raise ValueError("Assistant suggestions must remain non-authoritative machine assistance")
    if bool(event.get("eligible_for_training")):
        raise ValueError("Unconfirmed review events must not be training-eligible")
    if require_blank_human_fields:
        reviewed = event.get("human_reviewed_labels") or {}
        if set(reviewed) != set(HUMAN_REVIEW_FIELDS) or any(
            value is not None for value in reviewed.values()
        ):
            raise ValueError("Exported human-reviewed labels must remain blank")
        reviewer = event.get("reviewer_provenance") or {}
        if any(value is not None for value in reviewer.values()):
            raise ValueError("Exported reviewer provenance must remain blank")
        if event.get("human_review_status") != "pending_human_confirmation":
            raise ValueError("Exported review events must await human confirmation")


def _ordered_packets(packets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [deepcopy(packet) for packet in packets]
    sample_ids = [str(packet.get("sample_id") or "") for packet in rows]
    if "" in sample_ids or len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Review packets require unique, non-empty sample_id values")
    unsupported = sorted(
        {
            str(packet.get("priority_tier") or "")
            for packet in rows
            if str(packet.get("priority_tier") or "") not in TIER_ORDER
        }
    )
    if unsupported:
        raise ValueError(f"Review queue contains unsupported tiers: {unsupported}")
    return sorted(
        rows,
        key=lambda packet: (
            TIER_ORDER[str(packet.get("priority_tier") or "")],
            -int(packet.get("priority_score") or 0),
            str(packet.get("sample_id") or ""),
        ),
    )


def _source_risk_context(human_events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(human_events)
    conflict_rows = [row for row in rows if _is_conflict_context(row)]
    wrong_target_rows = [row for row in rows if _is_wrong_target_context(row)]
    bridge_rows = [row for row in rows if bool(row.get("bridge_as_final"))]
    human_verified_count = sum(
        str(row.get("source_annotation_status") or row.get("annotation_status") or "")
        == "human_verified"
        for row in rows
    )
    return {
        "source_record_count": len(rows),
        "human_verified_source_record_count": human_verified_count,
        "risk_type_counts": dict(
            sorted(Counter(str(row.get("risk_type") or "unknown") for row in rows).items())
        ),
        "oracle_action_counts": dict(
            sorted(Counter(str(row.get("oracle_action") or "unknown") for row in rows).items())
        ),
        "conflict_context_record_count": len(conflict_rows),
        "wrong_target_context_record_count": len(wrong_target_rows),
        "bridge_as_final_context_record_count": len(bridge_rows),
        "has_conflict_context": bool(conflict_rows),
        "has_wrong_target_context": bool(wrong_target_rows),
        "has_bridge_as_final_context": bool(bridge_rows),
        "transfer_policy": "context_only_requires_event_level_human_confirmation",
    }


def _is_conflict_context(row: dict[str, Any]) -> bool:
    risk_type = str(row.get("risk_type") or "").lower()
    return (
        bool(row.get("contradicted_claims"))
        or str(row.get("oracle_action") or "") == "disambiguate_conflict"
        or "contradiction" in risk_type
        or "conflict" in risk_type
    )


def _is_wrong_target_context(row: dict[str, Any]) -> bool:
    return bool(row.get("wrong_target")) or "wrong_target" in str(
        row.get("risk_type") or ""
    ).lower()


def _assistant_suggestions(
    event: dict[str, Any],
    risk_context: dict[str, Any],
) -> dict[str, Any]:
    boundary = str(event.get("first_loss_boundary") or "")
    candidate_state = str(event.get("candidate_state") or "")
    if boundary == "C_form":
        candidate_failure = "not_formed"
    elif boundary == "C_align":
        if risk_context.get("has_wrong_target_context"):
            candidate_failure = "wrong_target"
        elif risk_context.get("has_bridge_as_final_context"):
            candidate_failure = "bridge_as_final"
        else:
            candidate_failure = "other"
    elif boundary == "E" and candidate_state == "wrong_only":
        candidate_failure = "other"
    else:
        candidate_failure = "none"
    return {
        "first_loss_boundary": boundary,
        "evidence_state": str(event.get("evidence_state") or ""),
        "candidate_state": candidate_state,
        "candidate_failure_subtype": candidate_failure,
        "conflict_state": "unclear" if risk_context.get("has_conflict_context") else "none",
        "wrong_target": bool(risk_context.get("has_wrong_target_context")),
        "recommended_action": _suggested_action(event, risk_context),
        "scope": "non_authoritative_machine_assistance_pending_human_confirmation",
    }


def _suggested_action(
    event: dict[str, Any],
    risk_context: dict[str, Any],
) -> str | None:
    boundary = str(event.get("first_loss_boundary") or "")
    if boundary == "E":
        if bool(event.get("is_terminal")) and _budget_exhausted(event.get("budget_remaining")):
            return "abstain"
        return "repair_missing_hop"
    if boundary == "C_align" and (
        risk_context.get("has_conflict_context") or risk_context.get("has_wrong_target_context")
    ):
        return "disambiguate_conflict"
    if boundary in {"P", "O", "none"}:
        return "answer"
    if boundary == "ambiguous":
        return "abstain"
    return None


def _budget_exhausted(value: Any) -> bool:
    if value is None:
        return True
    try:
        return float(value) <= 0
    except (TypeError, ValueError):
        return True


def _attention_flags(
    event: dict[str, Any],
    risk_context: dict[str, Any],
    suggestions: dict[str, Any],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    boundary = str(event.get("first_loss_boundary") or "")
    evidence_state = str(event.get("evidence_state") or "")
    candidate_state = str(event.get("candidate_state") or "")
    outcome = str(event.get("outcome_state") or "")
    verifier = str(event.get("verifier_state") or "")
    details = event.get("candidate_state_details") or {}
    if evidence_state != "complete" and outcome in {"exact", "alias_exact", "relaxed"}:
        _add_flag(
            flags,
            "outcome_override_masks_incomplete_evidence",
            "high",
            "The emitted answer is correct by surface evaluation while oracle support remains incomplete; decide whether the boundary task labels answer loss or evidence safety.",
        )
    if evidence_state == "ambiguous" or boundary == "ambiguous":
        _add_flag(
            flags,
            "dataset_evidence_ambiguity",
            "high",
            "Dataset evidence or support metadata is explicitly ambiguous and may require exclusion.",
        )
    if evidence_state != "complete" and candidate_state == "correct_present":
        _add_flag(
            flags,
            "correct_candidate_under_incomplete_evidence",
            "medium",
            "A gold-matching candidate exists before oracle support is complete; downstream acceptance must remain masked or separately audited.",
        )
    if candidate_state == "wrong_only" and "false_accept" in verifier:
        _add_flag(
            flags,
            "false_accept_wrong_candidate",
            "high",
            "The verifier accepts a wrong-only final candidate set.",
        )
    if bool(details.get("surface_near_match_present")):
        _add_flag(
            flags,
            "surface_near_match_requires_alias_check",
            "medium",
            "A wrong-only candidate is close to gold and requires alias/canonicalization review.",
        )
    if boundary == "C_form":
        _add_flag(
            flags,
            "controller_action_gap_for_c_form",
            "medium",
            "Evidence is complete but the current action vocabulary has no candidate-regeneration or answer-extraction action.",
        )
    if boundary == "C_align" and suggestions.get("recommended_action") is None:
        _add_flag(
            flags,
            "controller_action_gap_for_c_align",
            "medium",
            "A wrong-only candidate is present without event-level conflict proof; disambiguation cannot be assigned automatically.",
        )
    if boundary == "V":
        _add_flag(
            flags,
            "controller_action_gap_for_v",
            "medium",
            "A correct candidate is verifier-rejected, but the current action vocabulary has no verifier-reconsideration action.",
        )
    if risk_context.get("has_conflict_context"):
        _add_flag(
            flags,
            "source_conflict_context_requires_event_level_confirmation",
            "medium",
            "Human-verified conflict exists in source claim-risk records, but may come from another run or round.",
        )
    if risk_context.get("has_wrong_target_context"):
        _add_flag(
            flags,
            "source_wrong_target_context_requires_event_level_confirmation",
            "high",
            "Human-verified wrong-target context exists, but must be re-confirmed for this ledger event.",
        )
    return flags


def _question_attention_flags(
    events: list[dict[str, Any]],
    terminal_boundaries: list[str],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if len(terminal_boundaries) > 1:
        _add_flag(
            flags,
            "cross_source_terminal_boundary_disagreement",
            "medium",
            "Stored source runs or probes terminate at different boundaries; review each event independently.",
        )
    source_ids = {
        str((event.get("machine_boundary_event") or {}).get("source_id") or "")
        for event in events
    }
    if len(source_ids) > 1:
        _add_flag(
            flags,
            "multiple_source_conditions_in_question_packet",
            "info",
            "The packet intentionally groups multiple source conditions under one immutable question key.",
        )
    return flags


def _add_flag(
    flags: list[dict[str, str]],
    code: str,
    severity: str,
    detail: str,
) -> None:
    if any(flag.get("code") == code for flag in flags):
        return
    flags.append({"code": code, "severity": severity, "detail": detail})
