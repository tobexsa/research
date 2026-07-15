from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace

from .semantic_hop_resolver import (
    canonical_hop_id,
    canonical_entity_id,
    canonical_relation_id,
    is_generic_entity,
    normalize_missing_requirement,
    normalize_text,
    resolve_hop_update,
    resolve_missing_requirement,
    typed_hop_identity,
)


HOP_STATUSES = {
    "unresolved",
    "candidate_present",
    "support_incomplete",
    "verified",
    "rejected",
    "ambiguous",
    "conflicted",
}

CANDIDATE_STATUSES = {
    "observed",
    "support_incomplete",
    "verified",
    "rejected",
    "contradicted",
}

CANONICAL_RUNTIME_CATEGORIES = {
    "bridge_as_final",
    "wrong_target",
    "insufficient_bridge_evidence",
    "answer_extraction_failure",
    "verifier_parse_failure",
    "empty_binding",
    "unknown_binding_reject",
}

_CANDIDATE_PRIORITY = {
    "verified": 0,
    "support_incomplete": 1,
    "observed": 2,
}

_NON_AUTHORITATIVE_CANDIDATE_CATEGORIES = {
    "answer_extraction_failure",
    "verifier_parse_failure",
    "empty_binding",
}

_TRUSTED_TOPOLOGY_REVISION_REASONS = {
    "deterministic_model_chain_binding",
    "deterministic_cast_relation_binding",
    "deterministic_named_after_title_binding",
    "deterministic_network_set_elimination_binding",
    "deterministic_country_network_chain_binding",
    "deterministic_named_after_player_signing_binding",
    "deterministic_shared_saint_chain_binding",
    "deterministic_geographic_race_chain_binding",
}


@dataclass(frozen=True)
class HopExecutionState:
    hop_id: str
    semantic_key: str
    hop_index: int
    subject: str
    relation: str
    object_value: str
    status: str
    is_final_hop: bool
    is_critical: bool
    dependency_hop_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    confidence: float
    source: str
    last_updated_round: int
    subject_entity_id: str = ""
    subject_type: str = "entity"
    relation_id: str = ""
    expected_object_type: str = "entity"
    object_entity_id: str = ""

    def to_record(self) -> dict:
        return {
            "hop_id": self.hop_id,
            "semantic_key": self.semantic_key,
            "hop_index": self.hop_index,
            "subject": self.subject,
            "relation": self.relation,
            "object_value": self.object_value,
            "status": self.status,
            "is_final_hop": self.is_final_hop,
            "is_critical": self.is_critical,
            "dependency_hop_ids": list(self.dependency_hop_ids),
            "evidence_ids": list(self.evidence_ids),
            "missing_requirements": list(self.missing_requirements),
            "confidence": self.confidence,
            "source": self.source,
            "last_updated_round": self.last_updated_round,
            "subject_entity_id": self.subject_entity_id,
            "subject_type": self.subject_type,
            "relation_id": self.relation_id,
            "expected_object_type": self.expected_object_type,
            "object_entity_id": self.object_entity_id,
        }


@dataclass(frozen=True)
class FinalCandidateState:
    normalized_value: str
    value: str
    source_hop_id: str
    evidence_ids: tuple[str, ...]
    status: str
    typed_reject_category: str
    rejection_reason: str
    preserved: bool
    first_seen_round: int
    last_seen_round: int

    def to_record(self) -> dict:
        return {
            "normalized_value": self.normalized_value,
            "value": self.value,
            "source_hop_id": self.source_hop_id,
            "evidence_ids": list(self.evidence_ids),
            "status": self.status,
            "typed_reject_category": self.typed_reject_category,
            "rejection_reason": self.rejection_reason,
            "preserved": self.preserved,
            "first_seen_round": self.first_seen_round,
            "last_seen_round": self.last_seen_round,
        }


@dataclass(frozen=True)
class SlotExecutionState:
    sample_id: str
    topology_status: str
    round_idx: int
    hops: tuple[HopExecutionState, ...]
    candidates: tuple[FinalCandidateState, ...]
    active_candidate_key: str
    first_critical_missing_hop_id: str
    completed_hop_ids: tuple[str, ...]
    conflict_hop_ids: tuple[str, ...]
    no_progress_count: int
    last_repair_target_hop_id: str
    state_fingerprint: str
    topology_diagnostic: dict = field(default_factory=dict)
    topology_version: int = 0
    topology_fingerprint: str = ""

    @classmethod
    def empty(cls, sample_id: str) -> "SlotExecutionState":
        state = cls(
            sample_id=str(sample_id),
            topology_status="topology_unavailable",
            round_idx=0,
            hops=(),
            candidates=(),
            active_candidate_key="",
            first_critical_missing_hop_id="",
            completed_hop_ids=(),
            conflict_hop_ids=(),
            no_progress_count=0,
            last_repair_target_hop_id="",
            state_fingerprint="",
            topology_diagnostic={},
            topology_version=0,
            topology_fingerprint="",
        )
        return replace(state, state_fingerprint=state.semantic_fingerprint())

    def semantic_fingerprint(self) -> str:
        payload = {
            "sample_id": self.sample_id,
            "topology_status": self.topology_status,
            "hops": [
                {
                    "hop_id": hop.hop_id,
                    "semantic_key": hop.semantic_key,
                    "subject_entity_id": hop.subject_entity_id,
                    "relation_id": hop.relation_id,
                    "expected_object_type": hop.expected_object_type,
                    "object_value": _normalize(hop.object_value),
                    "object_entity_id": hop.object_entity_id,
                    "status": hop.status,
                    "evidence_ids": list(_sorted_unique(hop.evidence_ids)),
                    "missing_requirements": list(_normalized_unique(hop.missing_requirements)),
                }
                for hop in _ordered_hops(self.hops)
            ],
            "candidates": [
                {
                    "normalized_value": candidate.normalized_value,
                    "source_hop_id": candidate.source_hop_id,
                    "evidence_ids": list(_sorted_unique(candidate.evidence_ids)),
                    "status": candidate.status,
                    "typed_reject_category": candidate.typed_reject_category,
                    "rejection_reason": candidate.rejection_reason,
                    "preserved": candidate.preserved,
                }
                for candidate in _ordered_candidates(self.candidates)
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_record(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "topology_status": self.topology_status,
            "round_idx": self.round_idx,
            "hops": [hop.to_record() for hop in _ordered_hops(self.hops)],
            "candidates": [candidate.to_record() for candidate in _ordered_candidates(self.candidates)],
            "active_candidate_key": self.active_candidate_key,
            "first_critical_missing_hop_id": self.first_critical_missing_hop_id,
            "completed_hop_ids": list(self.completed_hop_ids),
            "conflict_hop_ids": list(self.conflict_hop_ids),
            "no_progress_count": self.no_progress_count,
            "last_repair_target_hop_id": self.last_repair_target_hop_id,
            "state_fingerprint": self.state_fingerprint,
            "topology_diagnostic": dict(self.topology_diagnostic or {}),
            "topology_version": self.topology_version,
            "topology_fingerprint": self.topology_fingerprint,
        }


@dataclass(frozen=True)
class SlotStateUpdate:
    sample_id: str
    round_idx: int
    slot_binding_record: dict
    runtime_metadata: dict
    legacy_slot_ledger_record: dict
    verifier_record: dict
    local_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class SlotStateReduction:
    state: SlotExecutionState
    transition_events: tuple[dict, ...]
    progress: bool
    progress_reasons: tuple[str, ...]
    regression_blocked: bool


def extract_canonical_runtime_category(binding_record: dict, runtime_metadata: dict) -> str:
    decision = _dict(binding_record.get("decision_head"))
    structured = _dict(binding_record.get("structured_output"))
    if structured.get("parse_status") in {"failed", "error"}:
        return "verifier_parse_failure"
    if (
        runtime_metadata.get("slot_binding_verifier_invoked") is True
        and not structured
        and not binding_record
    ):
        return "verifier_parse_failure"
    for value in (
        binding_record.get("typed_reject_category"),
        decision.get("typed_reject_category"),
        decision.get("abstain_reason"),
    ):
        normalized = _normalize(value).replace(" ", "_")
        if normalized in CANONICAL_RUNTIME_CATEGORIES:
            return normalized
    if (
        runtime_metadata.get("final_candidate_preserved") is True
        and runtime_metadata.get("bridge_evidence_incomplete") is True
    ):
        return "insufficient_bridge_evidence"
    return ""


def hypothetical_state_action(state: SlotExecutionState) -> tuple[str, str]:
    if state.conflict_hop_ids:
        return "disambiguate_conflict", ""
    if state.first_critical_missing_hop_id:
        return "repair_missing_hop", state.first_critical_missing_hop_id
    active = next(
        (candidate for candidate in state.candidates if candidate.normalized_value == state.active_candidate_key),
        None,
    )
    if (
        active is not None
        and active.status == "verified"
        and state.hops
        and all(hop.status == "verified" for hop in state.hops if hop.is_critical)
    ):
        return "await_final_gates", ""
    return "no_state_action", ""


def reduce_slot_execution_state(
    previous: SlotExecutionState,
    update: SlotStateUpdate,
) -> SlotStateReduction:
    if previous.sample_id != str(update.sample_id):
        raise ValueError("slot execution state sample_id mismatch")
    if update.round_idx < previous.round_idx:
        return SlotStateReduction(
            state=previous,
            transition_events=(
                {
                    "event": "stale_update_ignored",
                    "incoming_round_idx": update.round_idx,
                    "current_round_idx": previous.round_idx,
                },
            ),
            progress=False,
            progress_reasons=(),
            regression_blocked=False,
        )

    binding_record = _dict(update.slot_binding_record)
    topology_diagnostic = _topology_diagnostic(binding_record, update.runtime_metadata)
    if topology_diagnostic.get("primary_reason") == "required_hops_malformed":
        event_name = "topology_invalid" if not previous.hops else "incoming_topology_invalid"
        return _finish_reduction(
            previous,
            update.round_idx,
            topology_status=previous.topology_status,
            hops=previous.hops,
            candidates=previous.candidates,
            events=[
                {
                    "event": event_name,
                    "reason": str(
                        topology_diagnostic.get("required_hops_error")
                        or "required_hops_malformed"
                    ),
                    "round_idx": update.round_idx,
                }
            ],
            regression_blocked=False,
            topology_diagnostic=topology_diagnostic,
        )
    category = extract_canonical_runtime_category(binding_record, update.runtime_metadata)
    if category == "verifier_parse_failure":
        events: list[dict] = []
        if not _normalize(_candidate_identity(binding_record, update.runtime_metadata)):
            events.append(
                {
                    "event": "unscoped_typed_reject_observed",
                    "typed_reject_category": category,
                    "round_idx": update.round_idx,
                }
            )
        return _finish_reduction(
            previous,
            update.round_idx,
            topology_status=previous.topology_status,
            hops=previous.hops,
            candidates=previous.candidates,
            events=events,
            regression_blocked=False,
            topology_diagnostic=topology_diagnostic,
        )

    local_evidence_ids = {str(value) for value in update.local_evidence_ids if str(value)}
    ordered = _dict(binding_record.get("ordered_hop_binding"))
    events: list[dict] = []
    regression_blocked = False
    hops = list(previous.hops)
    candidate_base = previous.candidates
    topology_status = previous.topology_status
    topology_version_override: int | None = None
    topology_fingerprint_override: str | None = None

    raw_required = ordered.get("required_hops", [])
    topology_error = ""
    if not isinstance(raw_required, list):
        topology_error = "required_hops_must_be_list"
        incoming_required: list[dict] = []
    elif any(not isinstance(item, dict) for item in raw_required):
        topology_error = "required_hop_must_be_object"
        incoming_required = []
    else:
        incoming_required = list(raw_required)
    if topology_error:
        event_name = "topology_invalid" if not previous.hops else "incoming_topology_invalid"
        events.append(
            {
                "event": event_name,
                "reason": topology_error,
                "round_idx": update.round_idx,
            }
        )
        return _finish_reduction(
            previous,
            update.round_idx,
            topology_status=previous.topology_status,
            hops=previous.hops,
            candidates=previous.candidates,
            events=events,
            regression_blocked=False,
            topology_diagnostic=topology_diagnostic,
        )

    canonical_incoming: list[dict] = []
    if incoming_required:
        canonical_incoming, topology_error = _canonicalize_required_hops(incoming_required)
        if topology_error:
            event_name = "topology_invalid" if not previous.hops else "incoming_topology_invalid"
            events.append(
                {
                    "event": event_name,
                    "reason": topology_error,
                    "round_idx": update.round_idx,
                }
            )
            return _finish_reduction(
                previous,
                update.round_idx,
                topology_status=previous.topology_status,
                hops=previous.hops,
                candidates=previous.candidates,
                events=events,
                regression_blocked=False,
                topology_diagnostic=topology_diagnostic,
            )

        topology_revision_applied = False
        if previous.hops and update.round_idx > previous.round_idx:
            revision_reason = _trusted_topology_revision_reason(binding_record)
            revision_hops = _initialize_hops(
                canonical_incoming,
                local_evidence_ids,
                update.round_idx,
                source="trusted_deterministic_topology_revision",
            )
            revision_hops, revision_bridge_events = _propagate_bridge_identities(
                revision_hops,
                update.round_idx,
            )
            revision_changes_topology = bool(
                _topology_fingerprint(tuple(revision_hops))
                != previous.topology_fingerprint
            )
            if revision_reason and revision_changes_topology:
                revision_error = _trusted_topology_revision_error(
                    binding_record,
                    canonical_incoming,
                    local_evidence_ids,
                    revision_reason,
                )
                if revision_error:
                    return _finish_reduction(
                        previous,
                        update.round_idx,
                        topology_status=previous.topology_status,
                        hops=previous.hops,
                        candidates=previous.candidates,
                        events=[
                            {
                                "event": "topology_revision_rejected",
                                "reason": revision_error,
                                "deterministic_binding_reason": revision_reason,
                                "round_idx": update.round_idx,
                            }
                        ],
                        regression_blocked=False,
                        topology_diagnostic=topology_diagnostic,
                    )
                hops = revision_hops
                candidate_base = ()
                topology_version_override = max(previous.topology_version, 1) + 1
                topology_fingerprint_override = _topology_fingerprint(tuple(hops))
                topology_revision_applied = True
                events.extend(revision_bridge_events)
                events.append(
                    {
                        "event": "topology_revision_applied",
                        "reason": revision_reason,
                        "from_topology_version": previous.topology_version,
                        "to_topology_version": topology_version_override,
                        "old_topology_fingerprint": previous.topology_fingerprint,
                        "new_topology_fingerprint": topology_fingerprint_override,
                        "round_idx": update.round_idx,
                    }
                )

        if previous.hops and update.round_idx > previous.round_idx and not topology_revision_applied:
            incoming_version = int(ordered.get("topology_version") or 0)
            incoming_fingerprint = str(ordered.get("topology_fingerprint") or "")
            version_mismatch = bool(
                incoming_version
                and previous.topology_version
                and incoming_version != previous.topology_version
            )
            fingerprint_mismatch = bool(
                incoming_fingerprint
                and previous.topology_fingerprint
                and incoming_fingerprint != previous.topology_fingerprint
            )
            if version_mismatch or fingerprint_mismatch:
                return _finish_reduction(
                    previous,
                    update.round_idx,
                    topology_status=previous.topology_status,
                    hops=previous.hops,
                    candidates=previous.candidates,
                    events=[
                        {
                            "event": "topology_update_rejected",
                            "reason": (
                                "topology_version_mismatch"
                                if version_mismatch
                                else "topology_fingerprint_mismatch"
                            ),
                            "incoming_topology_version": incoming_version,
                            "incoming_topology_fingerprint": incoming_fingerprint,
                            "round_idx": update.round_idx,
                        }
                    ],
                    regression_blocked=False,
                    topology_diagnostic=topology_diagnostic,
                )

        if not previous.hops:
            hops = _initialize_hops(canonical_incoming, local_evidence_ids, update.round_idx)
            topology_status = "ready"
            events.append({"event": "topology_initialized", "round_idx": update.round_idx})
        elif not topology_revision_applied:
            prior_records = [_hop_resolver_record(hop, previous.hops) for hop in _ordered_hops(previous.hops)]
            merged_by_id = {hop.hop_id: hop for hop in _ordered_hops(previous.hops)}
            resolved_ids: set[str] = set()
            for incoming in canonical_incoming:
                resolution = resolve_hop_update(
                    prior_records,
                    incoming,
                    canonical_is_final_hop=bool(incoming["_canonical_final"]),
                )
                if resolution.status != "resolved":
                    event_name = {
                        "ambiguous": "hop_update_ambiguous",
                        "rejected": "hop_update_rejected",
                    }.get(resolution.status, "hop_update_unmapped")
                    events.append(
                        {
                            "event": event_name,
                            "reason": resolution.reason,
                            "candidate_hop_ids": list(resolution.candidate_hop_ids),
                            "incoming_semantic_key": _semantic_key(
                                incoming,
                                bool(incoming["_canonical_final"]),
                            ),
                            "round_idx": update.round_idx,
                        }
                    )
                    # Preserve the historical diagnostic for genuinely
                    # incompatible legacy records while valid paraphrases use
                    # the typed update path above.
                    events.append(
                        {
                            "event": "hop_schema_drift_ignored",
                            "hop_id": resolution.hop_id,
                            "incoming_semantic_key": _semantic_key(
                                incoming,
                                bool(incoming["_canonical_final"]),
                            ),
                            "round_idx": update.round_idx,
                        }
                    )
                    continue
                if resolution.hop_id in resolved_ids:
                    events.append(
                        {
                            "event": "hop_update_rejected",
                            "hop_id": resolution.hop_id,
                            "reason": "duplicate_hop_update",
                            "round_idx": update.round_idx,
                        }
                    )
                    continue
                prior = merged_by_id[resolution.hop_id]
                merged, blocked, hop_events = _merge_hop(
                    prior,
                    incoming,
                    local_evidence_ids,
                    update.round_idx,
                    binding_record,
                )
                merged_by_id[resolution.hop_id] = merged
                resolved_ids.add(resolution.hop_id)
                regression_blocked = regression_blocked or blocked
                events.extend(hop_events)
                if merged != prior:
                    events.append(
                        {
                            "event": "hop_update_resolved",
                            "hop_id": resolution.hop_id,
                            "reason": resolution.reason,
                            "round_idx": update.round_idx,
                        }
                    )
            hops = list(_ordered_hops(tuple(merged_by_id.values())))

    hops, bridge_events = _propagate_bridge_identities(hops, update.round_idx)
    events.extend(bridge_events)

    if not incoming_required and not topology_error and not previous.hops:
        bootstrap, bootstrap_reason = _bootstrap_required_hops(ordered)
        if bootstrap:
            canonical_incoming, bootstrap_error = _canonicalize_required_hops(bootstrap)
            if not bootstrap_error:
                hops = _initialize_hops(
                    canonical_incoming,
                    local_evidence_ids,
                    update.round_idx,
                    source="diagnostic_bootstrap",
                )
                topology_status = "ready"
                topology_diagnostic = {
                    **topology_diagnostic,
                    "primary_reason": "required_hops_missing",
                    "secondary_reasons": _unique_texts(
                        [*(topology_diagnostic.get("secondary_reasons") or []), "topology_bootstrap_applied"]
                    ),
                    "bootstrap_applied": True,
                    "bootstrap_reason": bootstrap_reason,
                    "bootstrap_hop_count": len(canonical_incoming),
                }
                events.append(
                    {
                        "event": "topology_bootstrap_applied",
                        "reason": bootstrap_reason,
                        "round_idx": update.round_idx,
                    }
                )

    structured_requirements = ordered.get("missing_requirements", [])
    legacy_hints = ordered.get("missing_critical_hops", [])
    requirements = (
        list(structured_requirements)
        if isinstance(structured_requirements, list) and structured_requirements
        else list(legacy_hints) if isinstance(legacy_hints, list) else []
    )
    mapped_hops, hint_events, hint_blocked = _apply_missing_hints(
        hops,
        requirements,
        update.round_idx,
    )
    hops = mapped_hops
    events.extend(hint_events)
    regression_blocked = regression_blocked or hint_blocked
    binding_mismatch_events = [
        event
        for event in hint_events
        if str(event.get("reason") or "").startswith("hop_binding_")
    ]
    if binding_mismatch_events:
        topology_diagnostic = {
            **topology_diagnostic,
            "secondary_reasons": _unique_texts(
                [
                    *(topology_diagnostic.get("secondary_reasons") or []),
                    *(str(event.get("reason") or "") for event in binding_mismatch_events),
                ]
            ),
            "binding_mismatch_details": [
                {
                    "reason": str(event.get("reason") or ""),
                    "hint": str(event.get("hint") or ""),
                    "candidate_hop_ids": list(event.get("candidate_hop_ids") or []),
                    "mismatch": dict(event.get("binding_mismatch") or {}),
                }
                for event in binding_mismatch_events
            ],
        }

    hops, conflict_events = _apply_scoped_hop_conflicts(
        hops,
        binding_record,
        update.verifier_record,
        local_evidence_ids,
        update.round_idx,
    )
    events.extend(conflict_events)

    candidates, candidate_events = _reduce_candidates(
        candidate_base,
        hops,
        binding_record,
        update.runtime_metadata,
        update.legacy_slot_ledger_record,
        local_evidence_ids,
        update.round_idx,
    )
    events.extend(candidate_events)

    return _finish_reduction(
        previous,
        update.round_idx,
        topology_status=topology_status,
        hops=tuple(hops),
        candidates=tuple(candidates),
        events=events,
        regression_blocked=regression_blocked,
        topology_diagnostic=topology_diagnostic,
        topology_version=topology_version_override,
        topology_fingerprint=topology_fingerprint_override,
    )


def _finish_reduction(
    previous: SlotExecutionState,
    round_idx: int,
    *,
    topology_status: str,
    hops: tuple[HopExecutionState, ...] | list[HopExecutionState],
    candidates: tuple[FinalCandidateState, ...] | list[FinalCandidateState],
    events: list[dict],
    regression_blocked: bool,
    topology_diagnostic: dict | None = None,
    topology_version: int | None = None,
    topology_fingerprint: str | None = None,
) -> SlotStateReduction:
    ordered_hops = _ordered_hops(tuple(hops))
    ordered_candidates = _ordered_candidates(tuple(candidates))
    completed = tuple(hop.hop_id for hop in ordered_hops if hop.status == "verified")
    conflicts = tuple(hop.hop_id for hop in ordered_hops if hop.status == "conflicted")
    active_key = _active_candidate_key(ordered_candidates)
    first_missing = _first_critical_missing_hop(ordered_hops, conflicts)

    provisional = SlotExecutionState(
        sample_id=previous.sample_id,
        topology_status=topology_status,
        round_idx=max(previous.round_idx, round_idx),
        hops=ordered_hops,
        candidates=ordered_candidates,
        active_candidate_key=active_key,
        first_critical_missing_hop_id=first_missing,
        completed_hop_ids=completed,
        conflict_hop_ids=conflicts,
        no_progress_count=previous.no_progress_count,
        last_repair_target_hop_id=previous.last_repair_target_hop_id,
        state_fingerprint="",
        topology_diagnostic=dict(topology_diagnostic or {}),
        topology_version=(
            topology_version
            if topology_version is not None
            else (previous.topology_version or (1 if ordered_hops else 0))
        ),
        topology_fingerprint=(
            topology_fingerprint
            if topology_fingerprint is not None
            else (
                previous.topology_fingerprint
                or (_topology_fingerprint(ordered_hops) if ordered_hops else "")
            )
        ),
    )
    fingerprint = provisional.semantic_fingerprint()
    progress = fingerprint != previous.state_fingerprint
    if round_idx > previous.round_idx:
        no_progress_count = 0 if progress else previous.no_progress_count + 1
    else:
        no_progress_count = previous.no_progress_count
    state = replace(
        provisional,
        no_progress_count=no_progress_count,
        state_fingerprint=fingerprint,
    )
    progress_reasons = tuple(
        dict.fromkeys(
            str(event.get("event"))
            for event in events
            if str(event.get("event"))
            not in {
                "stale_update_ignored",
                "unmapped_missing_critical_hint",
                "unscoped_conflict_observed",
                "unscoped_typed_reject_observed",
            }
        )
    )
    return SlotStateReduction(
        state=state,
        transition_events=tuple(events),
        progress=progress,
        progress_reasons=progress_reasons if progress else (),
        regression_blocked=regression_blocked,
    )


def _canonicalize_required_hops(required_hops: list[dict]) -> tuple[list[dict], str]:
    prepared: list[dict] = []
    try:
        for item in required_hops:
            hop_index = int(item.get("hop_index", 0))
            prepared.append({**item, "hop_index": hop_index})
    except (TypeError, ValueError):
        return [], "invalid_hop_index"
    prepared.sort(key=lambda item: int(item["hop_index"]))
    indexes = [int(item["hop_index"]) for item in prepared]
    if indexes != list(range(1, len(prepared) + 1)):
        return [], "hop_indexes_must_be_contiguous_1_to_n"
    explicit_final = [item for item in prepared if item.get("is_final_hop") is True]
    if len(explicit_final) > 1:
        return [], "multiple_final_hops"
    highest_index = indexes[-1]
    if explicit_final and int(explicit_final[0]["hop_index"]) != highest_index:
        return [], "final_hop_must_have_highest_index"
    return [
        {**item, "_canonical_final": int(item["hop_index"]) == highest_index}
        for item in prepared
    ], ""


def _trusted_topology_revision_reason(binding_record: dict) -> str:
    reason = _clean(binding_record.get("reason"))
    marker = _clean(
        _dict(binding_record.get("structured_output")).get(
            "deterministic_binding_applied"
        )
    )
    if reason in _TRUSTED_TOPOLOGY_REVISION_REASONS and marker == reason:
        return reason
    if marker in _TRUSTED_TOPOLOGY_REVISION_REASONS:
        # Preserve the attempted reason so a marker/reason mismatch is
        # rejected explicitly rather than falling through to ordinary drift.
        return marker
    return ""


def _trusted_topology_revision_error(
    binding_record: dict,
    canonical_hops: list[dict],
    local_evidence_ids: set[str],
    revision_reason: str,
) -> str:
    """Return an error unless a deterministic replacement is evidence-closed."""

    structured = _dict(binding_record.get("structured_output"))
    if _clean(binding_record.get("reason")) != revision_reason:
        return "deterministic_reason_marker_mismatch"
    if _clean(structured.get("deterministic_binding_applied")) != revision_reason:
        return "deterministic_binding_marker_missing"
    if _normalize(structured.get("parse_status")) not in {
        "parsed",
        "repaired",
        "schema_repaired",
    }:
        return "deterministic_binding_parse_status_not_safe"
    diagnostic = _dict(binding_record.get("topology_diagnostic"))
    if diagnostic and diagnostic.get("primary_reason") != "required_hops_present":
        return "deterministic_topology_diagnostic_not_safe"
    if binding_record.get("supports_slot") is not True:
        return "deterministic_binding_does_not_support_slot"
    if binding_record.get("slot_relation_match") is not True:
        return "deterministic_slot_relation_mismatch"
    if binding_record.get("answer_type_match") is not True:
        return "deterministic_answer_type_mismatch"

    ordered = _dict(binding_record.get("ordered_hop_binding"))
    if ordered.get("chain_complete") is not True:
        return "deterministic_chain_incomplete"
    if ordered.get("candidate_is_final_relation_object") is not True:
        return "deterministic_candidate_not_final_relation_object"
    if ordered.get("missing_critical_hops"):
        return "deterministic_chain_reports_missing_hops"
    if ordered.get("missing_requirements"):
        return "deterministic_chain_reports_missing_requirements"

    set_level = _dict(binding_record.get("set_level_sufficiency"))
    if set_level.get("final_slot_covered") is not True:
        return "deterministic_final_slot_not_covered"
    if set_level.get("all_required_hops_covered") is not True:
        return "deterministic_required_hops_not_covered"
    if set_level.get("conflict_on_final_slot") is not False:
        return "deterministic_final_slot_conflict_not_clean"
    # Older deterministic certificates omitted this false-valued field from
    # serialization even though the allowlisted binder constructed it as
    # false. An explicit true remains fatal; current records serialize false.
    if set_level.get("conflict_on_bridge") is True:
        return "deterministic_bridge_conflict_not_clean"

    candidate = _clean(binding_record.get("bound_value"))
    if not candidate or _is_sentinel_candidate(candidate):
        return "deterministic_candidate_missing_or_sentinel"
    final_hops = [hop for hop in canonical_hops if hop.get("_canonical_final")]
    if len(final_hops) != 1:
        return "deterministic_final_hop_not_unique"
    final_object = _clean(final_hops[0].get("object"))
    if _normalize(final_object) != _normalize(candidate):
        return "deterministic_final_object_candidate_mismatch"
    ordered_final_object = _clean(ordered.get("final_relation_object"))
    if ordered_final_object and _normalize(ordered_final_object) != _normalize(candidate):
        return "deterministic_ordered_final_object_candidate_mismatch"

    union_evidence_ids: set[str] = set()
    for hop in canonical_hops:
        if not _clean(hop.get("subject")):
            return "deterministic_hop_subject_missing"
        if not _clean(hop.get("relation")):
            return "deterministic_hop_relation_missing"
        if _normalize(hop.get("status")) != "bound":
            return "deterministic_hop_not_bound"
        object_value = _clean(hop.get("object"))
        if not object_value or _is_sentinel_candidate(object_value):
            return "deterministic_hop_object_missing_or_sentinel"
        raw_evidence_ids = hop.get("supporting_evidence_ids")
        if not isinstance(raw_evidence_ids, list):
            return "deterministic_hop_evidence_malformed"
        hop_evidence_ids = {
            str(value) for value in raw_evidence_ids if str(value)
        }
        if not hop_evidence_ids:
            return "deterministic_hop_evidence_missing"
        if not hop_evidence_ids.issubset(local_evidence_ids):
            return "deterministic_hop_evidence_not_local"
        union_evidence_ids.update(hop_evidence_ids)

    binding_evidence_ids = {
        str(value)
        for value in binding_record.get("evidence_ids", [])
        if str(value)
    }
    if not binding_evidence_ids or not binding_evidence_ids.issubset(local_evidence_ids):
        return "deterministic_binding_evidence_not_local"
    if not union_evidence_ids.issubset(binding_evidence_ids):
        return "deterministic_hop_evidence_not_in_binding_certificate"

    entailment = _dict(binding_record.get("slot_bound_entailment"))
    if (
        entailment.get("entails_answer", entailment.get("entailed")) is not True
        or entailment.get("contradicted") is True
    ):
        return "deterministic_entailment_not_clean"
    entailment_candidate = _clean(entailment.get("candidate"))
    if entailment_candidate and _normalize(entailment_candidate) != _normalize(candidate):
        return "deterministic_entailment_candidate_mismatch"
    return ""


def _topology_diagnostic(binding_record: dict, runtime_metadata: dict) -> dict:
    """Return a mutually ordered diagnosis for the current verifier result."""
    structured = _dict(binding_record.get("structured_output"))
    if structured.get("parse_status") in {"failed", "error"}:
        return {
            "primary_reason": "verifier_parse_failure",
            "secondary_reasons": [],
            "parse_status": structured.get("parse_status"),
        }
    if runtime_metadata.get("slot_binding_verifier_invoked") is True and not binding_record:
        return {
            "primary_reason": "verifier_parse_failure",
            "secondary_reasons": [],
            "verifier_invoked": True,
            "parse_status": "missing_result",
        }
    if runtime_metadata.get("slot_binding_verifier_invoked") is False and not binding_record:
        return {
            "primary_reason": "required_hops_missing",
            "secondary_reasons": ["verifier_not_invoked"],
            "verifier_invoked": False,
        }

    ordered = _dict(binding_record.get("ordered_hop_binding"))
    diagnostic = _dict(binding_record.get("topology_diagnostic"))
    if diagnostic:
        result = dict(diagnostic)
    else:
        raw_required = ordered.get("required_hops")
        if raw_required in (None, []):
            result = {
                "primary_reason": "required_hops_missing",
                "secondary_reasons": [],
                "required_hops_error": "required_hops_missing_or_empty",
            }
        elif not isinstance(raw_required, list) or any(not isinstance(item, dict) for item in raw_required):
            result = {
                "primary_reason": "required_hops_malformed",
                "secondary_reasons": [],
                "required_hops_error": (
                    "required_hops_must_be_list"
                    if not isinstance(raw_required, list)
                    else "required_hop_must_be_object"
                ),
            }
        else:
            _, canonical_error = _canonicalize_required_hops(raw_required)
            if canonical_error:
                result = {
                    "primary_reason": "required_hops_malformed",
                    "secondary_reasons": [],
                    "required_hops_error": canonical_error,
                }
            else:
                result = {
                    "primary_reason": "required_hops_present",
                    "secondary_reasons": [],
                    "required_hops_count": len(raw_required),
                }

    secondary = list(result.get("secondary_reasons") or [])
    hints = ordered.get("missing_critical_hops")
    if isinstance(hints, list) and any(_usable_diagnostic_text(value) for value in hints):
        if result.get("primary_reason") == "required_hops_missing" or not ordered.get("required_hops"):
            secondary.append("missing_hints_unmapped")

    role = _dict(binding_record.get("candidate_role_labeler"))
    role_value = _normalize(role.get("candidate_role") or role.get("role"))
    relation = _normalize(role.get("relation_to_question"))
    role_error = _normalize(role.get("role_error_type"))
    if role_value in {"unknown", "ambiguous"} or relation in {"", "ambiguous"} or "ambiguous" in role_error:
        secondary.append("ambiguous_target_mapping")

    raw_candidate = _candidate_identity(binding_record, runtime_metadata)
    if _is_sentinel_candidate(raw_candidate):
        secondary.append("sentinel_candidate_ignored")

    if result.get("primary_reason") == "required_hops_present":
        bound = [
            hop for hop in (ordered.get("required_hops") or [])
            if isinstance(hop, dict) and _normalize(hop.get("status")) == "bound"
        ]
        if not bound and (
            _normalize((binding_record.get("reason") or ""))
            or _normalize((_dict(binding_record.get("decision_head")).get("action") or ""))
        ):
            secondary.append("hop_binding_failure")
    elif not binding_record.get("supports_slot") and binding_record:
        reason = _normalize(binding_record.get("reason"))
        if "binding" in reason or "reject" in reason:
            secondary.append("hop_binding_failure")

    result["secondary_reasons"] = _unique_texts(secondary)
    result["verifier_invoked"] = runtime_metadata.get("slot_binding_verifier_invoked", True)
    deterministic_binding = _clean(structured.get("deterministic_binding_applied"))
    if deterministic_binding:
        result["deterministic_binding_applied"] = deterministic_binding
    return result


def _bootstrap_required_hops(ordered: dict) -> tuple[list[dict], str]:
    """Build an explicitly low-confidence topology from verifier hop hints.

    This never invents objects or evidence. It only turns relation/missing-hop
    strings already emitted by the verifier into unresolved hops so the state
    controller can name the first missing relation and issue a targeted query.
    """
    relations: list[str] = []
    missing_hints = ordered.get("missing_critical_hops", []) or []
    # A final relation by itself can describe an already-complete candidate;
    # only bootstrap when the verifier explicitly reports an unresolved hop.
    if not isinstance(missing_hints, list) or not missing_hints:
        return [], "no_missing_hop_signal"
    for value in missing_hints:
        text = _clean(value)
        if _usable_diagnostic_text(text) and _normalize(text) not in {_normalize(x) for x in relations}:
            relations.append(text)
    final_relation = _clean(ordered.get("final_relation"))
    if _usable_diagnostic_text(final_relation) and _normalize(final_relation) not in {
        _normalize(x) for x in relations
    }:
        relations.append(final_relation)
    if not relations:
        return [], "no_relation_or_missing_hop_signal"
    result = []
    for index, relation in enumerate(relations, start=1):
        result.append(
            {
                "hop_index": index,
                "subject": "",
                "relation": relation,
                "object": "",
                "status": "missing",
                "is_final_hop": index == len(relations),
                "supporting_evidence_ids": [],
                "confidence": 0.0,
            }
        )
    return result, "verifier_relation_and_missing_hop_hints"


def _usable_diagnostic_text(value: object) -> bool:
    text = _clean(value)
    if not text or len(text) > 160:
        return False
    if text.startswith("{") or text.startswith("["):
        return False
    return _normalize(text) not in {"unknown", "none", "null", "n/a", "na"}


def _unique_texts(values: object) -> list[str]:
    result: list[str] = []
    for value in values if isinstance(values, (list, tuple, set)) else []:
        text = _clean(value)
        if text and text not in result:
            result.append(text)
    return result


def _initialize_hops(
    incoming: list[dict],
    local_evidence_ids: set[str],
    round_idx: int,
    source: str = "ordered_hop_binding",
) -> list[HopExecutionState]:
    result: list[HopExecutionState] = []
    for position, item in enumerate(incoming):
        hop_index = int(item["hop_index"])
        hop_id = f"required_hop_{hop_index}"
        dependencies = (result[position - 1].hop_id,) if position else ()
        dependency_object_id = result[position - 1].object_entity_id if position else ""
        identity = typed_hop_identity(
            item,
            canonical_is_final_hop=bool(item["_canonical_final"]),
            default_hop_id=hop_id,
            dependency_hop_ids=dependencies,
            dependency_object_entity_id=dependency_object_id,
        )
        status, evidence_ids = _incoming_hop_status(item, local_evidence_ids)
        object_value = _clean(item.get("object"))
        result.append(
            HopExecutionState(
                hop_id=hop_id,
                semantic_key=_typed_semantic_key(hop_index, identity),
                hop_index=hop_index,
                subject=_clean(item.get("subject")),
                relation=_clean(item.get("relation")),
                object_value=object_value,
                status=status,
                is_final_hop=bool(item["_canonical_final"]),
                is_critical=True,
                dependency_hop_ids=dependencies,
                evidence_ids=evidence_ids,
                missing_requirements=(),
                confidence=_float(item.get("confidence")),
                source=source,
                last_updated_round=round_idx,
                subject_entity_id=identity["subject_entity_id"],
                subject_type=identity["subject_type"],
                relation_id=identity["relation_id"],
                expected_object_type=identity["expected_object_type"],
                object_entity_id=canonical_entity_id(object_value, identity["expected_object_type"]),
            )
        )
    return result


def _merge_hop(
    prior: HopExecutionState,
    incoming: dict,
    local_evidence_ids: set[str],
    round_idx: int,
    binding_record: dict,
) -> tuple[HopExecutionState, bool, list[dict]]:
    proposed_status, incoming_evidence = _incoming_hop_status(incoming, local_evidence_ids)
    incoming_object = _clean(incoming.get("object"))
    evidence_ids = _sorted_unique((*prior.evidence_ids, *incoming_evidence))
    events: list[dict] = []
    if (
        prior.object_value
        and incoming_object
        and prior.status == "verified"
        and not _hop_object_values_equivalent(
            prior.object_value,
            incoming_object,
            expected_object_type=prior.expected_object_type,
        )
        and proposed_status == "verified"
    ):
        events.append(
            {
                "event": "competing_bound_object_conflict",
                "hop_id": prior.hop_id,
                "existing_object": prior.object_value,
                "incoming_object": incoming_object,
                "round_idx": round_idx,
            }
        )
        return replace(
            prior,
            status="conflicted",
            evidence_ids=evidence_ids,
            last_updated_round=round_idx,
        ), False, events

    clean_conflicts = _binding_conflicts_are_explicitly_clean(binding_record)
    new_evidence = set(incoming_evidence) - set(prior.evidence_ids)
    allowed = _hop_transition_allowed(
        prior.status,
        proposed_status,
        explicit_conflict=False,
        clean_resolution=bool(new_evidence and clean_conflicts),
    )
    if not allowed:
        events.append(
            {
                "event": "state_regression_blocked",
                "hop_id": prior.hop_id,
                "from": prior.status,
                "to": proposed_status,
                "round_idx": round_idx,
            }
        )
        return prior, True, events

    merged = replace(
        prior,
        object_value=incoming_object or prior.object_value,
        object_entity_id=(
            canonical_entity_id(incoming_object, prior.expected_object_type)
            if incoming_object
            else prior.object_entity_id
        ),
        status=proposed_status,
        evidence_ids=evidence_ids,
        confidence=max(prior.confidence, _float(incoming.get("confidence"))),
        last_updated_round=round_idx if (
            proposed_status != prior.status
            or evidence_ids != prior.evidence_ids
            or (incoming_object and incoming_object != prior.object_value)
        ) else prior.last_updated_round,
    )
    if merged != prior:
        events.append(
            {
                "event": "hop_state_updated",
                "hop_id": prior.hop_id,
                "from": prior.status,
                "to": merged.status,
                "round_idx": round_idx,
            }
        )
    return merged, False, events


def _hop_object_values_equivalent(
    left: object,
    right: object,
    *,
    expected_object_type: str = "",
) -> bool:
    """Return conservative type-aware equivalence for state merge identity."""

    normalized_left = _normalize(left).strip(" .:;!?\"'")
    normalized_right = _normalize(right).strip(" .:;!?\"'")
    if normalized_left == normalized_right:
        return True
    ordinal_pattern = re.compile(r"^(\d{1,3}(?:st|nd|rd|th))(?:\s+century)?$")
    left_ordinal = ordinal_pattern.fullmatch(normalized_left)
    right_ordinal = ordinal_pattern.fullmatch(normalized_right)
    if left_ordinal and right_ordinal:
        return left_ordinal.group(1) == right_ordinal.group(1)
    return False


def _incoming_hop_status(item: dict, local_evidence_ids: set[str]) -> tuple[str, tuple[str, ...]]:
    incoming_evidence = tuple(
        value
        for value in _sorted_unique(item.get("supporting_evidence_ids", []))
        if value in local_evidence_ids
    )
    status = _normalize(item.get("status"))
    object_value = _clean(item.get("object"))
    if status == "bound" and incoming_evidence:
        return "verified", incoming_evidence
    if status == "bound" and object_value:
        return "candidate_present", incoming_evidence
    if status == "missing" and object_value:
        return "support_incomplete", incoming_evidence
    return "unresolved", incoming_evidence


def _hop_transition_allowed(
    old: str,
    new: str,
    *,
    explicit_conflict: bool,
    clean_resolution: bool,
) -> bool:
    if old == new:
        return True
    allowed = {
        "unresolved": {"candidate_present", "support_incomplete", "verified", "rejected", "ambiguous", "conflicted"},
        "candidate_present": {"support_incomplete", "verified", "rejected", "ambiguous", "conflicted"},
        "support_incomplete": {"verified", "rejected", "ambiguous", "conflicted"},
        "rejected": {"candidate_present", "support_incomplete", "verified", "ambiguous", "conflicted"},
        "ambiguous": {"candidate_present", "support_incomplete", "verified", "rejected", "conflicted"},
        "conflicted": {"verified", "rejected"},
        "verified": {"conflicted"},
    }
    if new not in allowed.get(old, set()):
        return False
    if old == "verified" and new == "conflicted":
        return explicit_conflict
    if old in {"ambiguous", "conflicted"} and new in {"candidate_present", "support_incomplete", "verified", "rejected"}:
        return clean_resolution
    return True


def _apply_missing_hints(
    hops: list[HopExecutionState],
    hints: object,
    round_idx: int,
) -> tuple[list[HopExecutionState], list[dict], bool]:
    result = list(hops)
    events: list[dict] = []
    regression_blocked = False
    if not isinstance(hints, list):
        return result, events, regression_blocked
    for raw_hint in hints:
        requirement = normalize_missing_requirement(raw_hint)
        if not requirement.get("raw_hint") and not requirement.get("target_hop_id"):
            continue
        resolution = resolve_missing_requirement(
            [_hop_resolver_record(hop, tuple(result)) for hop in result],
            raw_hint,
        )
        if resolution.status != "resolved":
            event_name = {
                "ambiguous": "ambiguous_missing_critical_hint",
                "rejected": "missing_requirement_rejected",
            }.get(resolution.status, "unmapped_missing_critical_hint")
            events.append(
                {
                    "event": event_name,
                    "hint": requirement.get("raw_hint") or _clean(raw_hint),
                    "reason": resolution.reason,
                    "candidate_hop_ids": list(resolution.candidate_hop_ids),
                    "binding_mismatch": dict(
                        (resolution.metadata or {}).get("binding_mismatch") or {}
                    ),
                    "round_idx": round_idx,
                }
            )
            if resolution.reason == "target_hop_not_repairable":
                regression_blocked = True
                events.append(
                    {
                        "event": "state_regression_blocked",
                        "hop_id": resolution.hop_id,
                        "from": "verified",
                        "to": "unresolved",
                        "round_idx": round_idx,
                    }
                )
            continue
        idx = next(index for index, hop in enumerate(result) if hop.hop_id == resolution.hop_id)
        prior = result[idx]
        proposed_status = "support_incomplete" if prior.object_value else "unresolved"
        if prior.status == "verified" and proposed_status != "verified":
            events.append(
                {
                    "event": "state_regression_blocked",
                    "hop_id": prior.hop_id,
                    "from": prior.status,
                    "to": proposed_status,
                    "round_idx": round_idx,
                }
            )
            regression_blocked = True
            continue
        requirement_key = (
            requirement.get("target_hop_id")
            or requirement.get("canonical_relation")
            or requirement.get("raw_hint")
        )
        requirements = _normalized_unique((*prior.missing_requirements, requirement_key))
        result[idx] = replace(
            prior,
            status=proposed_status if prior.status != "conflicted" else prior.status,
            missing_requirements=requirements,
            last_updated_round=round_idx if requirements != prior.missing_requirements else prior.last_updated_round,
        )
        events.append(
            {
                "event": "missing_requirement_resolved",
                "hop_id": prior.hop_id,
                "reason": resolution.reason,
                "requirement": requirement,
                "round_idx": round_idx,
            }
        )
    return result, events, regression_blocked


def _apply_scoped_hop_conflicts(
    hops: list[HopExecutionState],
    binding_record: dict,
    verifier_record: dict,
    local_evidence_ids: set[str],
    round_idx: int,
) -> tuple[list[HopExecutionState], list[dict]]:
    result = list(hops)
    events: list[dict] = []
    conflict_evidence: set[str] = set()
    direct_conflict_hop_ids: set[str] = set()
    for claim in verifier_record.get("claims", []) if isinstance(verifier_record, dict) else []:
        if isinstance(claim, dict) and _normalize(claim.get("status")) == "contradicted":
            claim_evidence = {
                value
                for value in _sorted_unique(claim.get("evidence_ids", []))
                if value in local_evidence_ids
            }
            if _is_branch_constraint_mismatch_claim(claim):
                candidate_hop_ids = [
                    hop.hop_id for hop in result if claim_evidence.intersection(hop.evidence_ids)
                ]
                events.append(
                    {
                        "event": "branch_constraint_mismatch_observed",
                        "reason": "shared_value_constraint_mismatch_not_fact_contradiction",
                        "candidate_hop_ids": candidate_hop_ids,
                        "evidence_ids": sorted(claim_evidence),
                        "round_idx": round_idx,
                    }
                )
                continue
            claim_text = _claim_scope_text(claim)
            candidate_hops = [
                hop for hop in result if claim_evidence.intersection(hop.evidence_ids)
            ]
            if claim_text:
                scoped_hops = [
                    hop
                    for hop in candidate_hops
                    if _claim_semantically_scopes_hop(claim_text, hop)
                ]
                if scoped_hops:
                    direct_conflict_hop_ids.update(hop.hop_id for hop in scoped_hops)
                elif claim_evidence:
                    events.append(
                        {
                            "event": "conflict_scope_mismatch_ignored",
                            "candidate_hop_ids": [hop.hop_id for hop in candidate_hops],
                            "evidence_ids": sorted(claim_evidence),
                            "claim": _clean(claim.get("claim")),
                            "round_idx": round_idx,
                        }
                    )
            else:
                # Legacy verifier records without claim text retain their
                # evidence-only fallback. Text-bearing claims must identify
                # the hop fact they are allowed to invalidate.
                conflict_evidence.update(claim_evidence)
    entailment = _dict(binding_record.get("slot_bound_entailment"))
    if entailment.get("contradicted") is True:
        entailment_evidence = {
            value
            for value in _sorted_unique(entailment.get("evidence_ids", []))
            if value in local_evidence_ids
        }
        # Only the proposition being tested is allowed to scope a
        # candidate-level contradiction onto a canonical hop.  Explanatory
        # reason/failure_reason text often mentions neighbouring bridge
        # entities (for example both Indonesia and East Timor) and is not a
        # fact assertion that may invalidate those bridge hops.
        entailment_text = _normalize(entailment.get("hypothesis"))
        candidate_hops = [
            hop for hop in result if entailment_evidence.intersection(hop.evidence_ids)
        ]
        scoped_hops = [
            hop
            for hop in candidate_hops
            if entailment_text and _claim_semantically_scopes_hop(entailment_text, hop)
        ]
        if scoped_hops:
            direct_conflict_hop_ids.update(hop.hop_id for hop in scoped_hops)
        elif entailment_text:
            events.append(
                {
                    "event": "candidate_contradiction_not_hop_conflict",
                    "candidate_hop_ids": [hop.hop_id for hop in candidate_hops],
                    "evidence_ids": sorted(entailment_evidence),
                    "hypothesis": _clean(entailment.get("hypothesis")),
                    "reason": _clean(entailment.get("reason")),
                    "failure_reason": _clean(entailment.get("failure_reason")),
                    "round_idx": round_idx,
                }
            )
        else:
            # Legacy records without semantic text retain evidence-only scope.
            conflict_evidence.update(entailment_evidence)

    scoped = False
    for idx, prior in enumerate(result):
        if (
            prior.hop_id in direct_conflict_hop_ids
            or conflict_evidence.intersection(prior.evidence_ids)
        ):
            result[idx] = replace(prior, status="conflicted", last_updated_round=round_idx)
            events.append(
                {
                    "event": "hop_conflict_observed",
                    "hop_id": prior.hop_id,
                    "round_idx": round_idx,
                }
            )
            scoped = True

    set_level = _dict(binding_record.get("set_level_sufficiency"))
    candidate_value = _candidate_identity(binding_record, {})
    binding_evidence = {
        value
        for value in _sorted_unique(binding_record.get("evidence_ids", []))
        if value in local_evidence_ids
    }
    if set_level.get("conflict_on_final_slot") is True and candidate_value and binding_evidence:
        final_indexes = [idx for idx, hop in enumerate(result) if hop.is_final_hop]
        if final_indexes:
            idx = final_indexes[0]
            prior = result[idx]
            result[idx] = replace(
                prior,
                status="conflicted",
                evidence_ids=_sorted_unique((*prior.evidence_ids, *binding_evidence)),
                last_updated_round=round_idx,
            )
            events.append(
                {
                    "event": "final_hop_conflict_observed",
                    "hop_id": prior.hop_id,
                    "round_idx": round_idx,
                }
            )
            scoped = True

    optional_bridge_conflict = _optional_set_level_bool(binding_record, "conflict_on_bridge")
    if optional_bridge_conflict is True and conflict_evidence:
        scoped = scoped or any(
            conflict_evidence.intersection(hop.evidence_ids) for hop in result if not hop.is_final_hop
        )

    overall_conflicting = _normalize(verifier_record.get("overall_sufficiency")) == "conflicting" if isinstance(verifier_record, dict) else False
    if (overall_conflicting or optional_bridge_conflict is True) and not scoped:
        events.append({"event": "unscoped_conflict_observed", "round_idx": round_idx})
    return result, events


def _claim_scope_text(claim: dict) -> str:
    return _normalize(
        " ".join(
            str(claim.get(key) or "")
            for key in ("claim", "reason")
        )
    )


def _claim_semantically_scopes_hop(
    claim_text: str,
    hop: HopExecutionState,
) -> bool:
    """Require a contradicted claim to identify the fact it can invalidate."""

    text = _normalize(claim_text)
    subject = _normalize(hop.subject)
    object_value = _normalize(hop.object_value)
    relation = _normalize(hop.relation_id or hop.relation).replace("-", "_")
    subject_match = bool(subject and subject in text and not is_generic_entity(subject))
    object_match = bool(object_value and object_value in text)
    relation_cues = {
        "located_on_shores_of": ("shore", "shores", "located on"),
        "located_in": ("located in", "lies in", "country", "state"),
        "dedicated_to": ("dedicated to", "dedication"),
        "same_as": ("same as", "same saint", "identical"),
        "death_year": ("died", "death", "year"),
        "created_by": ("created by", "creator", "network"),
        "winner": ("won", "winner", "victory"),
        "performer": ("performer", "performed by", "album by"),
        "largest_city_by_population": ("largest city", "most populated city"),
        "state_of_origin": ("born in", "from", "origin state"),
        "host_country": ("host country", "embassy", "mission"),
        "named_after": ("named after",),
        "signed_by": ("signed by", "signed"),
    }
    relation_match = any(cue in text for cue in relation_cues.get(relation, ()))
    return bool(subject_match and (relation_match or object_match))


def _is_branch_constraint_mismatch_claim(claim: dict) -> bool:
    text = _normalize(
        " ".join(
            str(claim.get(key) or "")
            for key in ("claim", "missing_evidence", "reason")
        )
    )
    if not text:
        return False
    return bool(
        "same saint" in text
        and any(marker in text for marker in ("no evidence", "not saint", "different saint"))
        and any(marker in text for marker in ("basilica", "cathedral", "church"))
    )


def _reduce_candidates(
    previous: tuple[FinalCandidateState, ...],
    hops: list[HopExecutionState],
    binding_record: dict,
    runtime_metadata: dict,
    legacy_slot_ledger_record: dict,
    local_evidence_ids: set[str],
    round_idx: int,
) -> tuple[tuple[FinalCandidateState, ...], list[dict]]:
    category = extract_canonical_runtime_category(binding_record, runtime_metadata)
    raw_primary_value = _candidate_identity(binding_record, runtime_metadata)
    primary_value = "" if _is_sentinel_candidate(raw_primary_value) else raw_primary_value
    events: list[dict] = []
    if raw_primary_value and not primary_value:
        events.append(
            {
                "event": "sentinel_candidate_ignored",
                "candidate": _clean(raw_primary_value),
                "round_idx": round_idx,
            }
        )
    if category and not _normalize(primary_value):
        events.append(
            {
                "event": "unscoped_typed_reject_observed",
                "typed_reject_category": category,
                "round_idx": round_idx,
            }
        )
    if category in _NON_AUTHORITATIVE_CANDIDATE_CATEGORIES:
        return _ordered_candidates(previous), events

    observations: dict[str, dict] = {}

    binding_evidence = tuple(
        value
        for value in _sorted_unique(binding_record.get("evidence_ids", []))
        if value in local_evidence_ids
    )
    for value in (
        binding_record.get("bound_value"),
        _dict(binding_record.get("candidate_role_labeler")).get("candidate"),
    ):
        clean_value = _clean(value)
        key = _normalize(clean_value)
        if not key or _is_sentinel_candidate(clean_value):
            continue
        existing_ids = observations.get(key, {}).get("evidence_ids", ())
        observations[key] = {
            "value": clean_value,
            "evidence_ids": _sorted_unique((*existing_ids, *binding_evidence)),
        }

    preserved_value = _clean(runtime_metadata.get("preserved_final_candidate"))
    if preserved_value and not _is_sentinel_candidate(preserved_value):
        key = _normalize(preserved_value)
        observations.setdefault(key, {"value": preserved_value, "evidence_ids": ()})

    legacy_value = _clean(runtime_metadata.get("slot_ledger_candidate_answer"))
    if legacy_value and not _is_sentinel_candidate(legacy_value):
        legacy_ids = runtime_metadata.get("slot_ledger_final_target_evidence_ids")
        if not isinstance(legacy_ids, list):
            slots = _dict(legacy_slot_ledger_record.get("slots"))
            legacy_ids = _dict(slots.get("final_target")).get("evidence_ids", [])
        key = _normalize(legacy_value)
        existing_ids = observations.get(key, {}).get("evidence_ids", ())
        observations[key] = {
            "value": legacy_value,
            "evidence_ids": _sorted_unique(
                (*existing_ids, *(value for value in legacy_ids if str(value) in local_evidence_ids))
            ),
        }

    candidates = {candidate.normalized_value: candidate for candidate in previous}
    primary_key = _normalize(primary_value)
    contradicted_key, contradicted_ids = _contradicted_candidate(binding_record, local_evidence_ids)

    for key, observation in observations.items():
        evidence_ids = _sorted_unique(observation["evidence_ids"])
        proposed_status = _candidate_status(
            key,
            primary_key,
            category,
            binding_record,
            runtime_metadata,
            evidence_ids,
            local_evidence_ids,
            contradicted_key,
        )
        preserved = bool(
            key == _normalize(runtime_metadata.get("preserved_final_candidate"))
            or runtime_metadata.get("final_candidate_preserved") is True and key == primary_key
            or category == "insufficient_bridge_evidence" and key == primary_key
        ) and proposed_status not in {"rejected", "contradicted"}
        source_hop_id = _candidate_source_hop(key, hops, binding_record)
        prior = candidates.get(key)
        if prior is None:
            candidates[key] = FinalCandidateState(
                normalized_value=key,
                value=observation["value"],
                source_hop_id=source_hop_id,
                evidence_ids=evidence_ids,
                status=proposed_status,
                typed_reject_category=category if key == primary_key else "",
                rejection_reason=_rejection_reason(binding_record) if key == primary_key else "",
                preserved=preserved,
                first_seen_round=round_idx,
                last_seen_round=round_idx,
            )
            events.append({"event": "candidate_observed", "candidate": observation["value"], "round_idx": round_idx})
            continue

        merged_evidence = _sorted_unique((*prior.evidence_ids, *evidence_ids))
        new_local_evidence = bool(set(evidence_ids) - set(prior.evidence_ids))
        explicit_binding_key = _normalize(_explicit_binding_candidate(binding_record))
        strict_same_evidence_correction = bool(
            prior.status == "rejected"
            and proposed_status == "verified"
        )
        clean_binding = bool(
            key == explicit_binding_key
            and not category
            and key != contradicted_key
            and (new_local_evidence or strict_same_evidence_correction)
        )
        next_status = _merge_candidate_status(prior.status, proposed_status, clean_binding)
        stale_rejection_cleared = bool(
            prior.status == "rejected"
            and next_status == "verified"
            and strict_same_evidence_correction
        )
        next_preserved = (prior.preserved or preserved) and next_status not in {"rejected", "contradicted"}
        updated = replace(
            prior,
            value=observation["value"] or prior.value,
            source_hop_id=source_hop_id or prior.source_hop_id,
            evidence_ids=merged_evidence,
            status=next_status,
            typed_reject_category=(
                ""
                if stale_rejection_cleared
                else category if key == primary_key and category else prior.typed_reject_category
            ),
            rejection_reason=(
                ""
                if stale_rejection_cleared
                else _rejection_reason(binding_record) if key == primary_key and category else prior.rejection_reason
            ),
            preserved=next_preserved,
            last_seen_round=round_idx,
        )
        candidates[key] = updated
        semantic_update = replace(updated, last_seen_round=prior.last_seen_round)
        if semantic_update != prior:
            events.append(
                {
                    "event": "candidate_state_updated",
                    "candidate": updated.value,
                    "from": prior.status,
                    "to": next_status,
                    **(
                        {"reason": "strict_binding_clears_stale_rejection"}
                        if stale_rejection_cleared
                        else {}
                    ),
                    "round_idx": round_idx,
                }
            )

    if contradicted_key and contradicted_key in candidates:
        prior = candidates[contradicted_key]
        merged_evidence = _sorted_unique((*prior.evidence_ids, *contradicted_ids))
        semantic_change = bool(
            prior.status != "contradicted"
            or prior.evidence_ids != merged_evidence
            or prior.preserved
        )
        if semantic_change:
            contradicted = replace(
                prior,
                status="contradicted",
                evidence_ids=merged_evidence,
                preserved=False,
                last_seen_round=round_idx,
            )
            candidates[contradicted_key] = contradicted
            events.append(
                {
                    "event": "candidate_state_updated",
                    "candidate": contradicted.value,
                    "from": prior.status,
                    "to": contradicted.status,
                    "round_idx": round_idx,
                }
            )
    return _ordered_candidates(tuple(candidates.values())), events


def _candidate_status(
    key: str,
    primary_key: str,
    category: str,
    binding_record: dict,
    runtime_metadata: dict,
    evidence_ids: tuple[str, ...],
    local_evidence_ids: set[str],
    contradicted_key: str,
) -> str:
    if key == contradicted_key:
        return "contradicted"
    if key == primary_key and category in {
        "bridge_as_final",
        "wrong_target",
        "unknown_binding_reject",
    }:
        return "rejected"
    if key == primary_key and category == "insufficient_bridge_evidence":
        return "support_incomplete"
    if key == primary_key and _candidate_is_explicitly_verified(
        binding_record,
        evidence_ids,
        local_evidence_ids,
    ):
        return "verified"
    if key == primary_key and _candidate_has_complete_but_unconfirmed_support(
        binding_record,
        evidence_ids,
        local_evidence_ids,
    ):
        return "support_incomplete"
    if (
        key == _normalize(runtime_metadata.get("preserved_final_candidate"))
        or runtime_metadata.get("final_candidate_preserved") is True and key == primary_key
    ):
        return "support_incomplete"
    return "observed"


def _candidate_is_explicitly_verified(
    binding_record: dict,
    evidence_ids: tuple[str, ...],
    local_evidence_ids: set[str],
) -> bool:
    ordered = _dict(binding_record.get("ordered_hop_binding"))
    set_level = _dict(binding_record.get("set_level_sufficiency"))
    conflict_on_bridge = _optional_set_level_bool(binding_record, "conflict_on_bridge")
    return bool(
        binding_record.get("supports_slot") is True
        and _clean(binding_record.get("bound_value"))
        and evidence_ids
        and set(evidence_ids).issubset(local_evidence_ids)
        and ordered.get("chain_complete") is True
        and set_level.get("all_required_hops_covered") is True
        and set_level.get("conflict_on_final_slot") is False
        and conflict_on_bridge is False
    )


def _candidate_has_complete_but_unconfirmed_support(
    binding_record: dict,
    evidence_ids: tuple[str, ...],
    local_evidence_ids: set[str],
) -> bool:
    ordered = _dict(binding_record.get("ordered_hop_binding"))
    set_level = _dict(binding_record.get("set_level_sufficiency"))
    return bool(
        binding_record.get("supports_slot") is True
        and _clean(binding_record.get("bound_value"))
        and evidence_ids
        and set(evidence_ids).issubset(local_evidence_ids)
        and ordered.get("chain_complete") is True
        and set_level.get("all_required_hops_covered") is True
        and set_level.get("conflict_on_final_slot") is False
        and _optional_set_level_bool(binding_record, "conflict_on_bridge") is None
    )


def _merge_candidate_status(old: str, new: str, clean_binding: bool) -> str:
    if old == new:
        return old
    if old == "verified":
        return "contradicted" if new == "contradicted" else old
    if old in {"rejected", "contradicted"}:
        if not clean_binding:
            return old
        if old == "contradicted" and new != "verified":
            return old
        return new
    if new in {"rejected", "contradicted"}:
        return new
    priority = {"observed": 0, "support_incomplete": 1, "verified": 2}
    return new if priority.get(new, -1) >= priority.get(old, -1) else old


def _candidate_identity(binding_record: dict, runtime_metadata: dict) -> str:
    for value in (
        binding_record.get("bound_value"),
        _dict(binding_record.get("candidate_role_labeler")).get("candidate"),
        runtime_metadata.get("preserved_final_candidate"),
        runtime_metadata.get("slot_ledger_candidate_answer"),
    ):
        if _clean(value):
            return _clean(value)
    return ""


def _is_sentinel_candidate(value: object) -> bool:
    normalized = _normalize(value).strip(" .:;!?\"'")
    return normalized in {
        "",
        "unknown",
        "unk",
        "unknown answer",
        "n/a",
        "na",
        "none",
        "null",
        "not available",
        "insufficient evidence",
        "cannot determine",
        "cannot be determined",
        "not enough information",
    }


def _explicit_binding_candidate(binding_record: dict) -> str:
    for value in (
        binding_record.get("bound_value"),
        _dict(binding_record.get("candidate_role_labeler")).get("candidate"),
    ):
        if _clean(value):
            return _clean(value)
    return ""


def _candidate_source_hop(
    candidate_key: str,
    hops: list[HopExecutionState],
    binding_record: dict,
) -> str:
    object_matches = [hop.hop_id for hop in hops if _normalize(hop.object_value) == candidate_key]
    if len(object_matches) == 1:
        return object_matches[0]
    ordered = _dict(binding_record.get("ordered_hop_binding"))
    try:
        filled_index = int(ordered.get("filled_hop_index", 0) or 0)
    except (TypeError, ValueError):
        filled_index = 0
    filled = next((hop.hop_id for hop in hops if hop.hop_index == filled_index), "")
    if filled:
        return filled
    if ordered.get("candidate_is_final_relation_object") is True:
        return next((hop.hop_id for hop in hops if hop.is_final_hop), "")
    return ""


def _contradicted_candidate(
    binding_record: dict,
    local_evidence_ids: set[str],
) -> tuple[str, tuple[str, ...]]:
    entailment = _dict(binding_record.get("slot_bound_entailment"))
    if entailment.get("contradicted") is not True:
        return "", ()
    evidence_ids = tuple(
        value
        for value in _sorted_unique(entailment.get("evidence_ids", []))
        if value in local_evidence_ids
    )
    if not evidence_ids:
        return "", ()
    return _normalize(entailment.get("candidate") or binding_record.get("bound_value")), evidence_ids


def _rejection_reason(binding_record: dict) -> str:
    decision = _dict(binding_record.get("decision_head"))
    return _clean(
        binding_record.get("typed_reject_reason")
        or decision.get("typed_target_slot_binder_reject_reason")
        or decision.get("abstain_reason")
    )


def _optional_set_level_bool(binding_record: dict, key: str) -> bool | None:
    set_level = _dict(binding_record.get("set_level_sufficiency"))
    if isinstance(set_level.get(key), bool):
        return bool(set_level[key])
    structured = _dict(binding_record.get("structured_output"))
    structured_set_level = _dict(structured.get("set_level_sufficiency"))
    if isinstance(structured_set_level.get(key), bool):
        return bool(structured_set_level[key])
    return None


def _binding_conflicts_are_explicitly_clean(binding_record: dict) -> bool:
    set_level = _dict(binding_record.get("set_level_sufficiency"))
    entailment = _dict(binding_record.get("slot_bound_entailment"))
    return bool(
        set_level.get("conflict_on_final_slot") is False
        and _optional_set_level_bool(binding_record, "conflict_on_bridge") is False
        and entailment.get("contradicted") is not True
    )


def _active_candidate_key(candidates: tuple[FinalCandidateState, ...]) -> str:
    viable = [candidate for candidate in candidates if candidate.status in _CANDIDATE_PRIORITY]
    if not viable:
        return ""
    viable.sort(
        key=lambda candidate: (
            _CANDIDATE_PRIORITY[candidate.status],
            -len(candidate.evidence_ids),
            candidate.first_seen_round,
            candidate.normalized_value,
        )
    )
    return viable[0].normalized_value


def _first_critical_missing_hop(
    hops: tuple[HopExecutionState, ...],
    conflict_hop_ids: tuple[str, ...],
) -> str:
    if conflict_hop_ids:
        return ""
    by_id = {hop.hop_id: hop for hop in hops}
    for hop in _ordered_hops(hops):
        if not hop.is_critical or hop.status in {"verified", "ambiguous", "conflicted"}:
            continue
        if all(by_id[dependency].status == "verified" for dependency in hop.dependency_hop_ids):
            return hop.hop_id
        return ""
    return ""


def _semantic_key(record: dict, canonical_is_final_hop: bool) -> str:
    hop_index = int(record.get("hop_index", 0))
    identity = typed_hop_identity(
        record,
        canonical_is_final_hop=canonical_is_final_hop,
        default_hop_id=f"required_hop_{hop_index}",
    )
    return _typed_semantic_key(hop_index, identity)


def _typed_semantic_key(hop_index: int, identity: dict) -> str:
    return "|".join(
        (
            str(hop_index),
            str(identity.get("subject_entity_id") or ""),
            str(identity.get("relation_id") or ""),
            str(identity.get("expected_object_type") or "entity"),
            "final" if identity.get("is_final_hop") else "bridge",
        )
    )


def _hop_resolver_record(hop: HopExecutionState, all_hops: tuple[HopExecutionState, ...]) -> dict:
    by_id = {item.hop_id: item for item in all_hops}
    dependency_object_ids = tuple(
        by_id[dependency_id].object_entity_id
        for dependency_id in hop.dependency_hop_ids
        if dependency_id in by_id and by_id[dependency_id].object_entity_id
    )
    return {
        **hop.to_record(),
        "dependency_object_entity_ids": dependency_object_ids,
    }


def _propagate_bridge_identities(
    hops: list[HopExecutionState],
    round_idx: int,
) -> tuple[list[HopExecutionState], list[dict]]:
    result = list(_ordered_hops(tuple(hops)))
    by_id = {hop.hop_id: hop for hop in result}
    events: list[dict] = []
    for index, hop in enumerate(result):
        if not hop.dependency_hop_ids:
            continue
        dependency = by_id.get(hop.dependency_hop_ids[-1])
        if dependency is None or not dependency.object_entity_id:
            continue
        subject_is_generic = is_generic_entity(hop.subject) or not hop.subject_entity_id
        if not subject_is_generic or hop.subject_entity_id == dependency.object_entity_id:
            continue
        identity = {
            "subject_entity_id": dependency.object_entity_id,
            "relation_id": hop.relation_id or canonical_relation_id(hop.relation),
            "expected_object_type": hop.expected_object_type,
            "is_final_hop": hop.is_final_hop,
        }
        updated = replace(
            hop,
            subject_entity_id=dependency.object_entity_id,
            semantic_key=_typed_semantic_key(hop.hop_index, identity),
            last_updated_round=round_idx,
        )
        result[index] = updated
        by_id[hop.hop_id] = updated
        events.append(
            {
                "event": "bridge_identity_propagated",
                "from_hop_id": dependency.hop_id,
                "to_hop_id": hop.hop_id,
                "entity_id": dependency.object_entity_id,
                "round_idx": round_idx,
            }
        )
    return result, events


def _topology_fingerprint(hops: tuple[HopExecutionState, ...]) -> str:
    payload = [
        {
            "hop_id": hop.hop_id,
            "hop_index": hop.hop_index,
            "subject_entity_id": hop.subject_entity_id,
            "relation_id": hop.relation_id,
            "expected_object_type": hop.expected_object_type,
            "dependency_hop_ids": list(hop.dependency_hop_ids),
            "is_final_hop": hop.is_final_hop,
        }
        for hop in _ordered_hops(hops)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ordered_hops(hops: tuple[HopExecutionState, ...]) -> tuple[HopExecutionState, ...]:
    return tuple(sorted(hops, key=lambda hop: (hop.hop_index, hop.hop_id)))


def _ordered_candidates(
    candidates: tuple[FinalCandidateState, ...],
) -> tuple[FinalCandidateState, ...]:
    return tuple(sorted(candidates, key=lambda candidate: candidate.normalized_value))


def _sorted_unique(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        return ()
    return tuple(sorted({str(value) for value in values if str(value)}))


def _normalized_unique(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        return ()
    return tuple(sorted({_normalize(value) for value in values if _normalize(value)}))


def _normalize(value: object) -> str:
    return " ".join(str(value or "").lower().split())


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
