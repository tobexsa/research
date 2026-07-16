from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from mvp_agentic_rag.slot_execution_state import (
    SlotExecutionState,
    SlotStateUpdate,
    reduce_slot_execution_state,
)


_CANDIDATE_TRANSITIONS = {"candidate_observed", "candidate_state_updated"}
_UNSUPPORTED_FINAL_STATUSES = {"unsupported", "contradicted", "unclear"}


def _binding_record(step: dict) -> dict:
    for key in ("slot_state_binding_verifier_result", "slot_binding_verifier_result"):
        value = step.get(key)
        if isinstance(value, dict) and value:
            return value
    return {}


def _critical_ancestor_closure_complete(state: SlotExecutionState) -> bool:
    critical_hops = [hop for hop in state.hops if hop.is_critical]
    if not critical_hops:
        return False
    by_id = {hop.hop_id: hop for hop in state.hops}

    def verified_with_ancestors(hop_id: str, visiting: frozenset[str]) -> bool:
        if hop_id in visiting:
            return False
        hop = by_id.get(hop_id)
        if hop is None or hop.status != "verified":
            return False
        next_visiting = visiting | {hop_id}
        return all(
            verified_with_ancestors(dependency_id, next_visiting)
            for dependency_id in hop.dependency_hop_ids
        )

    return all(
        verified_with_ancestors(hop.hop_id, frozenset())
        for hop in critical_hops
    )


def _terminal_invariant_violations(
    row: dict,
    state: SlotExecutionState,
    local_evidence_ids: set[str],
) -> tuple[str, ...]:
    if row.get("final_action") != "answer":
        return ()
    trajectory = row.get("trajectory")
    if not isinstance(trajectory, list) or not trajectory:
        return ("answered_without_terminal_step",)
    step = trajectory[-1] if isinstance(trajectory[-1], dict) else {}
    reasons: set[str] = set()
    strict_certificate = step.get("semantic_fusion_lane") == "strict_certificate"
    original_actions = {
        str(step.get("controller_policy_v1_original_action") or ""),
        str(step.get("answer_safety_guard_original_action") or ""),
    }
    if "abstain" in original_actions and not strict_certificate:
        reasons.add("terminal_answer_overrides_abstain")

    verifier = step.get("verifier_output")
    if not isinstance(verifier, dict):
        reasons.add("terminal_answer_without_verifier")
    else:
        if verifier.get("need_more_evidence") is True:
            reasons.add("terminal_answer_needs_more_evidence")
        claims = verifier.get("claims")
        if isinstance(claims, list):
            critical_claims = [
                claim
                for claim in claims
                if isinstance(claim, dict) and claim.get("is_critical") is True
            ]
            if any(
                str(claim.get("status") or "") in _UNSUPPORTED_FINAL_STATUSES
                for claim in critical_claims
            ):
                reasons.add("terminal_answer_has_unsupported_claim")
            claim_ids = {
                str(evidence_id)
                for claim in critical_claims
                for evidence_id in claim.get("evidence_ids", [])
                if str(evidence_id)
            }
            if critical_claims and not claim_ids:
                reasons.add("terminal_answer_without_claim_evidence")
            elif claim_ids and not _evidence_ids_match_local(
                claim_ids,
                local_evidence_ids,
            ):
                reasons.add("terminal_answer_with_nonlocal_claim_evidence")

    binding = _binding_record(step)
    binding_complete = False
    if binding:
        ordered = binding.get("ordered_hop_binding")
        ordered = ordered if isinstance(ordered, dict) else {}
        set_level = binding.get("set_level_sufficiency")
        set_level = set_level if isinstance(set_level, dict) else {}
        binding_evidence_ids = {
            str(value) for value in binding.get("evidence_ids", []) if str(value)
        }
        binding_complete = bool(
            binding.get("supports_slot") is True
            and binding_evidence_ids
            and _evidence_ids_match_local(binding_evidence_ids, local_evidence_ids)
            and ordered.get("chain_complete") is True
            and not ordered.get("missing_critical_hops")
            and set_level.get("final_slot_covered") is True
            and set_level.get("all_required_hops_covered") is True
            and set_level.get("evidence_set_sufficient") is True
            and set_level.get("conflict_on_final_slot") is not True
            and set_level.get("conflict_on_bridge") is not True
        )
        if binding.get("supports_slot") is not True:
            reasons.add("terminal_answer_without_slot_support")
        if ordered.get("chain_complete") is not True:
            reasons.add("terminal_answer_with_incomplete_chain")
        if set_level.get("final_slot_covered") is not True:
            reasons.add("terminal_answer_with_uncovered_final_slot")
    else:
        reasons.add("terminal_answer_without_binding")

    if not _critical_ancestor_closure_complete(state) and not binding_complete:
        reasons.add("terminal_answer_without_ancestor_closure")
    return tuple(sorted(reasons))


def _evidence_ids_match_local(
    evidence_ids: set[str],
    local_evidence_ids: set[str],
) -> bool:
    if not evidence_ids:
        return False
    for evidence_id in evidence_ids:
        if evidence_id in local_evidence_ids:
            continue
        if "::" not in evidence_id and any(
            local_id.endswith(f"::{evidence_id}")
            for local_id in local_evidence_ids
        ):
            continue
        return False
    return True


def replay(path: Path) -> dict:
    event_counts: Counter[str] = Counter()
    phase_event_counts: Counter[str] = Counter()
    sample_records: list[dict] = []
    same_round_topology_rejects = 0
    unsafe_failure_candidate_transitions = 0
    structured_legacy_requirement_items = 0
    structured_requirement_objects_after_replay = 0
    terminal_invariant_counts: Counter[str] = Counter()
    terminal_invariant_samples: dict[str, list[str]] = {}

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        sample_id = str(row.get("id") or "")
        state = SlotExecutionState.empty(sample_id)
        local_evidence_ids: set[str] = set()
        sample_events: list[dict] = []
        for step in row.get("trajectory", []):
            if not isinstance(step, dict):
                continue
            local_evidence_ids.update(str(value) for value in step.get("retrieved_ids", []) if str(value))
            binding = _binding_record(step)
            ordered = binding.get("ordered_hop_binding") if isinstance(binding.get("ordered_hop_binding"), dict) else {}
            legacy_hints = ordered.get("missing_critical_hops", [])
            if isinstance(legacy_hints, list):
                structured_legacy_requirement_items += sum(isinstance(value, dict) for value in legacy_hints)
            structured = ordered.get("missing_requirements", [])
            if isinstance(structured, list):
                structured_requirement_objects_after_replay += sum(isinstance(value, dict) for value in structured)

            update = SlotStateUpdate(
                sample_id=sample_id,
                round_idx=int(step.get("round", 0) or 0),
                slot_binding_record=binding,
                runtime_metadata=dict(step),
                legacy_slot_ledger_record=(
                    dict(step.get("slot_ledger")) if isinstance(step.get("slot_ledger"), dict) else {}
                ),
                verifier_record=(
                    dict(step.get("verifier_output"))
                    if isinstance(step.get("verifier_output"), dict)
                    else {}
                ),
                local_evidence_ids=tuple(sorted(local_evidence_ids)),
            )
            for phase in ("planning", "terminal"):
                previous_round = state.round_idx
                reduction = reduce_slot_execution_state(state, update)
                state = reduction.state
                primary_reason = str((state.topology_diagnostic or {}).get("primary_reason") or "")
                for event in reduction.transition_events:
                    event_name = str(event.get("event") or "")
                    event_counts[event_name] += 1
                    phase_event_counts[f"{phase}:{event_name}"] += 1
                    sample_events.append({"phase": phase, **event})
                    if (
                        event_name == "topology_update_rejected"
                        and update.round_idx == previous_round
                    ):
                        same_round_topology_rejects += 1
                    if (
                        primary_reason in {"required_hops_malformed", "verifier_parse_failure"}
                        and event_name in _CANDIDATE_TRANSITIONS
                    ):
                        unsafe_failure_candidate_transitions += 1

        terminal_violations = _terminal_invariant_violations(
            row,
            state,
            local_evidence_ids,
        )
        if terminal_violations:
            terminal_invariant_samples[sample_id] = list(terminal_violations)
            terminal_invariant_counts.update(terminal_violations)

        sample_records.append(
            {
                "id": sample_id,
                "final_answer": row.get("final_answer"),
                "final_action": row.get("final_action"),
                "topology_version": state.topology_version,
                "topology_fingerprint": state.topology_fingerprint,
                "hop_count": len(state.hops),
                "verified_hop_count": sum(hop.status == "verified" for hop in state.hops),
                "candidate_values": [candidate.value for candidate in state.candidates],
                "candidate_statuses": [candidate.status for candidate in state.candidates],
                "terminal_invariant_violations": list(terminal_violations),
                "events": sample_events,
            }
        )

    revision_samples = [
        sample["id"]
        for sample in sample_records
        if any(event.get("event") == "topology_revision_applied" for event in sample["events"])
    ]
    return {
        "source": str(path),
        "row_count": len(rows),
        "event_counts": dict(sorted(event_counts.items())),
        "phase_event_counts": dict(sorted(phase_event_counts.items())),
        "same_round_topology_update_rejected": same_round_topology_rejects,
        "unsafe_failure_candidate_transitions": unsafe_failure_candidate_transitions,
        "structured_legacy_requirement_items": structured_legacy_requirement_items,
        "structured_requirement_objects_after_replay": structured_requirement_objects_after_replay,
        "terminal_invariant_violation_count": sum(terminal_invariant_counts.values()),
        "terminal_invariant_counts": dict(sorted(terminal_invariant_counts.items())),
        "terminal_invariant_samples": dict(sorted(terminal_invariant_samples.items())),
        "topology_revision_applied_samples": revision_samples,
        "samples": sample_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trajectory_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = replay(args.trajectory_path)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
