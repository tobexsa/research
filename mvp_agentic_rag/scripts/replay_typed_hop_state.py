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


def _binding_record(step: dict) -> dict:
    for key in ("slot_state_binding_verifier_result", "slot_binding_verifier_result"):
        value = step.get(key)
        if isinstance(value, dict) and value:
            return value
    return {}


def replay(path: Path) -> dict:
    event_counts: Counter[str] = Counter()
    phase_event_counts: Counter[str] = Counter()
    sample_records: list[dict] = []
    same_round_topology_rejects = 0
    unsafe_failure_candidate_transitions = 0
    structured_legacy_requirement_items = 0
    structured_requirement_objects_after_replay = 0

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
