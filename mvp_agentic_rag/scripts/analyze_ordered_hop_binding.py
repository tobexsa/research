from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


V1_2_FIELDS = [
    "question_slot_parser",
    "candidate_role_labeler",
    "ordered_hop_binding",
    "slot_bound_entailment",
    "set_level_sufficiency",
    "decision_head",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze ordered-hop binding diagnostics from trajectories.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir
    records = _load_records(run_dir / "trajectories.jsonl")
    summary = analyze(records)
    output = args.output or run_dir / "ordered_hop_binding_summary.json"
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (output.with_suffix(".md")).write_text(_to_markdown(summary), encoding="utf-8")
    print(json.dumps(summary["headline"], indent=2, ensure_ascii=False))


def analyze(records: list[dict[str, Any]]) -> dict[str, Any]:
    field_presence = Counter()
    action_counts = Counter()
    candidate_role_counts = Counter()
    role_error_counts = Counter()
    abstain_reason_counts = Counter()
    hop_counts = defaultdict(Counter)
    branch_counts = Counter()
    wrong_target_accepted = []
    candidate_extraction_failures = []
    ordered_repair_cases = []

    total_steps = 0
    answer_by_hop = Counter()
    total_by_hop = Counter()
    for record in records:
        hop = _hop_label(record)
        total_by_hop[hop] += 1
        if record.get("final_action") == "answer":
            answer_by_hop[hop] += 1
        for step in record.get("trajectory", []):
            total_steps += 1
            binding = step.get("slot_binding_verifier_result") or {}
            for field in V1_2_FIELDS:
                if field in binding:
                    field_presence[field] += 1
            role = binding.get("candidate_role_labeler") or {}
            ordered = binding.get("ordered_hop_binding") or {}
            decision = binding.get("decision_head") or {}
            action = decision.get("action") or step.get("action")
            action_counts[str(action)] += 1
            candidate_role_counts[str(role.get("candidate_role", "missing"))] += 1
            role_error_counts[str(role.get("role_error_type", "missing"))] += 1
            abstain_reason_counts[str(decision.get("abstain_reason", "missing"))] += 1
            if step.get("config_seen_by_verifier"):
                branch_counts["config_seen_by_verifier"] += 1
            if step.get("ordered_hop_binding_enabled"):
                branch_counts["ordered_hop_binding_enabled"] += 1
            if step.get("structured_acceptance_branch_taken"):
                branch_counts["structured_acceptance_branch_taken"] += 1
            if step.get("legacy_acceptance_branch_taken"):
                branch_counts["legacy_acceptance_branch_taken"] += 1
            if step.get("candidate_extraction_failure"):
                candidate_extraction_failures.append(_case_row(record, step, role, ordered, decision))
            if action == "ordered_hop_repair":
                ordered_repair_cases.append(_case_row(record, step, role, ordered, decision))
            if (
                record.get("final_action") == "answer"
                and role.get("candidate_role") not in {"", None, "final_answer", "missing"}
            ):
                wrong_target_accepted.append(_case_row(record, step, role, ordered, decision))
            hop_counts[hop]["steps"] += 1
            hop_counts[hop][f"action:{action}"] += 1
            hop_counts[hop][f"role:{role.get('candidate_role', 'missing')}"] += 1

    field_coverage = {
        field: (field_presence[field] / total_steps if total_steps else 0.0)
        for field in V1_2_FIELDS
    }
    hop_coverage = {
        hop: (answer_by_hop[hop] / total_by_hop[hop] if total_by_hop[hop] else 0.0)
        for hop in sorted(total_by_hop)
    }
    return {
        "headline": {
            "records": len(records),
            "steps": total_steps,
            "v1_2_field_coverage_min": min(field_coverage.values()) if field_coverage else 0.0,
            "wrong_target_accepted_count": len(wrong_target_accepted),
            "candidate_extraction_failure_count": len(candidate_extraction_failures),
            "ordered_hop_repair_count": len(ordered_repair_cases),
            "hop_coverage": hop_coverage,
        },
        "field_coverage": field_coverage,
        "action_counts": dict(action_counts),
        "candidate_role_counts": dict(candidate_role_counts),
        "role_error_counts": dict(role_error_counts),
        "abstain_reason_counts": dict(abstain_reason_counts),
        "branch_counts": dict(branch_counts),
        "hop_counts": {hop: dict(counts) for hop, counts in sorted(hop_counts.items())},
        "wrong_target_accepted_cases": wrong_target_accepted,
        "candidate_extraction_failure_cases": candidate_extraction_failures,
        "ordered_hop_repair_cases": ordered_repair_cases,
    }


def _load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _hop_label(record: dict[str, Any]) -> str:
    sample_id = str(record.get("id", ""))
    if "__" in sample_id:
        prefix = sample_id.split("__", 1)[0]
        return re.sub(r"\d+$", "", prefix) if prefix.startswith(("3hop", "4hop")) else prefix
    return "unknown"


def _case_row(record: dict[str, Any], step: dict[str, Any], role: dict[str, Any], ordered: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": record.get("id"),
        "question": record.get("question"),
        "pred": record.get("final_answer"),
        "gold": record.get("gold_answer"),
        "final_action": record.get("final_action"),
        "candidate": role.get("candidate"),
        "candidate_role": role.get("candidate_role"),
        "role_error_type": role.get("role_error_type"),
        "filled_hop_index": ordered.get("filled_hop_index"),
        "final_hop_index": ordered.get("final_hop_index"),
        "chain_complete": ordered.get("chain_complete"),
        "candidate_is_final_relation_object": ordered.get("candidate_is_final_relation_object"),
        "decision_action": decision.get("action"),
        "abstain_reason": decision.get("abstain_reason"),
        "retrieved_ids": step.get("retrieved_ids", []),
    }


def _to_markdown(summary: dict[str, Any]) -> str:
    lines = ["# Ordered-Hop Binding Summary", ""]
    for key, value in summary["headline"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Field Coverage", ""])
    for key, value in summary["field_coverage"].items():
        lines.append(f"- {key}: {value:.4f}")
    lines.extend(["", "## Counts", ""])
    for section in ["action_counts", "candidate_role_counts", "role_error_counts", "abstain_reason_counts", "branch_counts"]:
        lines.append(f"### {section}")
        for key, value in summary[section].items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
