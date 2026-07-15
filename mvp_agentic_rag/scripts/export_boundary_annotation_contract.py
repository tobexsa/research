from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.data_loader import read_jsonl, write_jsonl
from mvp_agentic_rag.diagnostics.boundary_annotation import (
    ACTION_VALUES,
    BOUNDARY_VALUES,
    CANDIDATE_FAILURE_VALUES,
    CANDIDATE_VALUES,
    CONFLICT_VALUES,
    CONTRACT_VERSION,
    DEFAULT_SPLIT_RATIOS,
    EVIDENCE_VALUES,
    REQUIRED_REVIEWED_FIELDS,
    assign_component_splits,
    build_annotation_packets,
    build_question_components,
    build_question_profiles,
    select_priority_batch,
    summarize_annotation_contract,
    validate_annotation_packet,
)


OUTPUT_NAMES = {
    "contract_json": "boundary_annotation_contract.json",
    "contract_markdown": "boundary_annotation_contract.md",
    "components": "component_manifest.jsonl",
    "split_manifest": "provisional_split_manifest.json",
    "packets": "grouped_annotation_packets.jsonl",
    "priority_batch": "priority_annotation_batch.jsonl",
    "priority_batch_markdown": "priority_annotation_batch.md",
    "summary_json": "expansion_summary.json",
    "summary_markdown": "expansion_summary.md",
    "campaign_manifest": "campaign_manifest.json",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export question-grouped, provenance-safe boundary annotation packets from an "
            "existing E/C/V/P/O ledger."
        )
    )
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--interventions", required=True)
    parser.add_argument("--human-verified", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--priority-count", type=int, default=24)
    args = parser.parse_args(argv)

    inputs = {
        "ledger": Path(args.ledger),
        "interventions": Path(args.interventions),
        "human_verified_claim_risk": Path(args.human_verified),
    }
    _require_files(inputs)
    if args.priority_count <= 0:
        raise ValueError("--priority-count must be positive")

    ledger = list(read_jsonl(inputs["ledger"]))
    interventions = list(read_jsonl(inputs["interventions"]))
    human_verified = list(read_jsonl(inputs["human_verified_claim_risk"]))
    if not ledger:
        raise ValueError("The boundary ledger is empty")

    profiles = build_question_profiles(ledger, interventions, human_verified)
    components = build_question_components(profiles)
    component_map = {
        sample_id: str(component["component_group_id"])
        for component in components
        for sample_id in component["sample_ids"]
    }
    split_map = assign_component_splits(components, profiles)
    packets = build_annotation_packets(profiles, component_map, split_map)
    priority_batch = select_priority_batch(packets, target_count=args.priority_count)

    component_manifest = _component_manifest(components, profiles, split_map)
    summary = summarize_annotation_contract(
        packets,
        priority_batch,
        component_manifest,
        split_map,
    )
    summary.update(
        _source_and_expansion_summary(
            ledger,
            interventions,
            human_verified,
            packets,
            priority_batch,
        )
    )
    _validate_export(
        profiles=profiles,
        packets=packets,
        batch=priority_batch,
        components=component_manifest,
        split_map=split_map,
        summary=summary,
    )

    contract = _contract_document()
    split_manifest = _split_manifest(component_manifest, split_map, summary)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {key: output_dir / filename for key, filename in OUTPUT_NAMES.items()}

    _write_json(output_paths["contract_json"], contract)
    output_paths["contract_markdown"].write_text(
        _contract_markdown(contract), encoding="utf-8"
    )
    write_jsonl(output_paths["components"], component_manifest)
    _write_json(output_paths["split_manifest"], split_manifest)
    write_jsonl(output_paths["packets"], packets)
    write_jsonl(output_paths["priority_batch"], priority_batch)
    output_paths["priority_batch_markdown"].write_text(
        _priority_batch_markdown(priority_batch), encoding="utf-8"
    )
    _write_json(output_paths["summary_json"], summary)
    output_paths["summary_markdown"].write_text(
        _summary_markdown(summary, priority_batch), encoding="utf-8"
    )

    manifest = {
        "campaign_id": "boundary_annotation_contract_v1_20260710",
        "parent_campaign_id": "ecvpo_boundary_audit_v0_20260710",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_version": CONTRACT_VERSION,
        "inputs": {
            name: {
                "path": str(path.resolve()),
                "sha256": _sha256(path),
                "record_count": {
                    "ledger": len(ledger),
                    "interventions": len(interventions),
                    "human_verified_claim_risk": len(human_verified),
                }[name],
            }
            for name, path in inputs.items()
        },
        "constraints": {
            "training_executed": False,
            "full_300_executed": False,
            "controller_behavior_changed": False,
            "network_or_model_calls_executed": False,
            "machine_boundary_labels_promoted_to_human_gold": False,
        },
        "output_counts": {
            "packet_count": len(packets),
            "priority_batch_count": len(priority_batch),
            "component_count": len(component_manifest),
            "boundary_event_count": summary["boundary_event_count"],
            "training_eligible_packet_count": summary["training_eligible_packet_count"],
        },
        "validation": {
            "all_p0_in_priority_batch": summary["all_p0_in_priority_batch"],
            "split_is_leakage_safe": summary["split_is_leakage_safe"],
            "all_boundary_annotations_pending": (
                summary["pending_review_packet_count"] == summary["packet_count"]
            ),
        },
        "outputs": {name: str(path.resolve()) for name, path in output_paths.items()},
    }
    _write_json(output_paths["campaign_manifest"], manifest)
    _validate_written_outputs(output_paths, summary)

    print(f"packets={len(packets)}")
    print(f"components={len(component_manifest)}")
    print(f"priority_batch={len(priority_batch)}")
    print(f"p0_questions={summary['p0_question_count']}")
    print(f"split_is_leakage_safe={str(summary['split_is_leakage_safe']).lower()}")
    print(f"training_eligible_packets={summary['training_eligible_packet_count']}")
    print(f"output_dir={output_dir.resolve()}")
    return 0


def _require_files(paths: dict[str, Path]) -> None:
    missing = [f"{name}={path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing annotation campaign inputs: " + ", ".join(missing))


def _component_manifest(
    components: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    split_map: dict[str, str],
) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for component in components:
        component_id = str(component["component_group_id"])
        sample_ids = list(component["sample_ids"])
        tier_counts = Counter(profiles[sample_id]["priority_tier"] for sample_id in sample_ids)
        reason_counts = Counter(
            reason
            for sample_id in sample_ids
            for reason in profiles[sample_id]["priority_reasons"]
        )
        manifest.append(
            {
                **component,
                "proposed_split": split_map[component_id],
                "split_status": "provisional_not_publication_ready",
                "priority_tier_counts": dict(sorted(tier_counts.items())),
                "priority_reason_question_counts": dict(sorted(reason_counts.items())),
            }
        )
    return sorted(manifest, key=lambda item: item["component_group_id"])


def _source_and_expansion_summary(
    ledger: list[dict[str, Any]],
    interventions: list[dict[str, Any]],
    human_verified: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    priority_batch: list[dict[str, Any]],
) -> dict[str, Any]:
    ledger_ids = {str(row.get("sample_id") or "") for row in ledger}
    intervention_ids = {str(row.get("sample_id") or "") for row in interventions}
    human_ids = {str(row.get("sample_id") or "") for row in human_verified}
    batch_ids = {str(packet.get("sample_id") or "") for packet in priority_batch}
    reason_pool: dict[str, set[str]] = defaultdict(set)
    reason_batch: dict[str, set[str]] = defaultdict(set)
    for packet in packets:
        sample_id = str(packet.get("sample_id") or "")
        for reason in packet.get("priority_reasons") or []:
            reason_pool[str(reason)].add(sample_id)
            if sample_id in batch_ids:
                reason_batch[str(reason)].add(sample_id)
    all_reasons = sorted(set(reason_pool) | set(reason_batch))
    return {
        "input_record_counts": {
            "ledger": len(ledger),
            "interventions": len(interventions),
            "human_verified_claim_risk": len(human_verified),
        },
        "input_unique_question_counts": {
            "ledger": len(ledger_ids - {""}),
            "interventions": len(intervention_ids - {""}),
            "human_verified_claim_risk": len(human_ids - {""}),
        },
        "join_coverage": {
            "ledger_questions_with_intervention": len(ledger_ids & intervention_ids),
            "ledger_questions_with_human_verified_claim_risk": len(ledger_ids & human_ids),
            "human_verified_questions_outside_ledger": len(human_ids - ledger_ids - {""}),
            "intervention_questions_outside_ledger": len(intervention_ids - ledger_ids - {""}),
        },
        "expansion_focus": {
            reason: {
                "available_question_count": len(reason_pool[reason]),
                "selected_question_count": len(reason_batch[reason]),
                "remaining_unselected_question_count": len(reason_pool[reason] - batch_ids),
            }
            for reason in all_reasons
        },
        "new_human_verified_boundary_label_count": 0,
        "data_gap_statement": (
            "The batch expands review coverage, not boundary gold. Conflict and wrong-target "
            "signals copied from human-verified claim-risk records remain contextual until the "
            "per-event boundary review is completed."
        ),
    }


def _validate_export(
    *,
    profiles: dict[str, dict[str, Any]],
    packets: list[dict[str, Any]],
    batch: list[dict[str, Any]],
    components: list[dict[str, Any]],
    split_map: dict[str, str],
    summary: dict[str, Any],
) -> None:
    for packet in packets:
        validate_annotation_packet(packet)
    profile_ids = set(profiles)
    packet_ids = [str(packet.get("sample_id") or "") for packet in packets]
    component_ids = [
        str(sample_id)
        for component in components
        for sample_id in component.get("sample_ids") or []
    ]
    batch_ids = [str(packet.get("sample_id") or "") for packet in batch]
    if set(packet_ids) != profile_ids or len(packet_ids) != len(set(packet_ids)):
        raise ValueError("Every ledger question must appear in exactly one annotation packet")
    if set(component_ids) != profile_ids or len(component_ids) != len(set(component_ids)):
        raise ValueError("Every ledger question must appear in exactly one component")
    if len(batch_ids) != len(set(batch_ids)):
        raise ValueError("Priority batch contains duplicate question groups")
    if set(split_map) != {str(component["component_group_id"]) for component in components}:
        raise ValueError("Every component must have exactly one provisional split")
    if not summary.get("all_p0_in_priority_batch"):
        raise ValueError("Priority batch dropped one or more P0 packets")
    if not summary.get("split_is_leakage_safe"):
        raise ValueError("Question/component/decomposition split leakage detected")
    if int(summary.get("training_eligible_packet_count") or 0) != 0:
        raise ValueError("Generated boundary packets must remain training-ineligible")
    if int(summary.get("pending_review_packet_count") or 0) != len(packets):
        raise ValueError("Generated boundary packets must remain pending_review")


def _contract_document() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "scope": (
            "Question-grouped boundary review for stored multi-hop RAG rounds, source runs, "
            "fixed-evidence probes, and human-verified claim-risk context."
        ),
        "grouping_contract": {
            "question_group_key": "sample_id",
            "question_invariant": (
                "All rounds, source runs, fixed-evidence probes, and joined risk events for one "
                "sample_id stay in one packet and one split."
            ),
            "strict_component_rule": (
                "Questions transitively sharing any MuSiQue decomposition ID stay in one "
                "component and one split."
            ),
        },
        "boundary_contract": {
            "ordering": ["E", ["C_form", "C_align"], "V", "P", "O"],
            "definitions": {
                "E": "Required answer-entailing gold support is not fully retrieved.",
                "C_form": "Evidence is complete but no final-slot candidate is formed.",
                "C_align": "Final-slot candidates exist but none matches gold or aliases.",
                "V": "A correct final candidate exists but no verifier acceptance applies to it.",
                "P": "A correct candidate is accepted but policy does not emit a correct answer.",
                "O": "Emitted answer is relaxed/alias-correct but not exact primary-answer surface.",
                "none": "No loss is observed through the available boundary.",
                "ambiguous": "Dataset evidence or required gold-support metadata is ambiguous.",
            },
        },
        "annotation_contract": {
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
        },
        "priority_contract": {
            "P0": [
                "human_verified_wrong_target",
                "human_verified_conflict",
                "observed_e_to_c_transition",
            ],
            "P1": [
                "terminal_c_form_or_c_align",
                "wrong_only_or_false_accept_candidate",
            ],
            "P2": ["high_coverage_e_missing_or_wrong_candidate"],
            "P3": ["contextual_boundary_state"],
            "batch_invariant": "Every P0 packet must be included; fail if capacity is too small.",
        },
        "provenance_contract": {
            "machine_boundary_prefill_status": "pending_review",
            "machine_boundary_prefill_is_human_gold": False,
            "source_human_review_scope": "copied claim-risk fields only",
            "source_human_review_does_not_transfer_to_boundary_labels": True,
            "generated_training_eligible": False,
        },
        "split_contract": {
            "ratios": DEFAULT_SPLIT_RATIOS,
            "assignment_unit": "transitive_decomposition_component",
            "status": "provisional_not_publication_ready",
            "publication_rule": "Freeze only after boundary review and final dataset audit.",
        },
    }


def _split_manifest(
    components: list[dict[str, Any]],
    split_map: dict[str, str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "status": "provisional_not_publication_ready",
        "ratios": DEFAULT_SPLIT_RATIOS,
        "assignment_unit": "transitive_decomposition_component",
        "component_assignments": dict(sorted(split_map.items())),
        "components": components,
        "validation": {
            "question_cross_split_count": summary["question_cross_split_count"],
            "component_cross_split_count": summary["component_cross_split_count"],
            "decomposition_id_cross_split_count": summary[
                "decomposition_id_cross_split_count"
            ],
            "split_is_leakage_safe": summary["split_is_leakage_safe"],
        },
    }


def _contract_markdown(contract: dict[str, Any]) -> str:
    definitions = contract["boundary_contract"]["definitions"]
    lines = [
        "# Boundary Annotation Data Contract v1",
        "",
        "## Scope",
        "",
        contract["scope"],
        "",
        "## Immutable Grouping",
        "",
        f"- Question key: `{contract['grouping_contract']['question_group_key']}`.",
        f"- {contract['grouping_contract']['question_invariant']}",
        f"- {contract['grouping_contract']['strict_component_rule']}",
        "",
        "## Boundary Labels",
        "",
        "| Label | Definition |",
        "| --- | --- |",
    ]
    lines.extend(f"| `{label}` | {_md(definition)} |" for label, definition in definitions.items())
    lines.extend(
        [
            "",
            "## Review Fields",
            "",
            "Each ledger event receives an independent review slot with these required fields:",
            "",
            *[f"- `{field}`" for field in REQUIRED_REVIEWED_FIELDS],
            "",
            "The allowed control actions are "
            + ", ".join(f"`{value}`" for value in ACTION_VALUES)
            + ".",
            "",
            "## Priority",
            "",
            "| Tier | Question-level trigger |",
            "| --- | --- |",
        ]
    )
    for tier, reasons in contract["priority_contract"].items():
        if tier.startswith("P"):
            lines.append(f"| `{tier}` | {', '.join(f'`{reason}`' for reason in reasons)} |")
    lines.extend(
        [
            "",
            "Every P0 packet must enter the first batch. The exporter fails when the requested "
            "capacity is smaller than the P0 pool.",
            "",
            "## Provenance And Training",
            "",
            "- Ledger-derived boundary values are machine prefill, not human gold.",
            "- Human verification on joined claim-risk records applies only to those copied source fields.",
            "- New boundary annotations start as `pending_review` and `eligible_for_training=false`.",
            "- Training eligibility requires completed event-level boundary review and a later split freeze.",
            "",
            "## Split Status",
            "",
            "The 60/20/20 split is provisional. Assignment happens at the transitive decomposition "
            "component level and is not publication-ready until review and final audit are complete.",
            "",
        ]
    )
    return "\n".join(lines)


def _priority_batch_markdown(batch: list[dict[str, Any]]) -> str:
    lines = [
        "# Priority Boundary Annotation Batch",
        "",
        "All entries remain `pending_review` and are ineligible for training.",
        "",
        "| Order | Tier | Sample | Split | Rounds | Verified risk context | Priority reasons |",
        "| ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for index, packet in enumerate(batch, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{packet['priority_tier']}`",
                    f"`{_md(packet['sample_id'])}`",
                    f"`{packet['proposed_split']}`",
                    str(len(packet.get("boundary_events") or [])),
                    str(len(packet.get("human_verified_risk_events") or [])),
                    ", ".join(f"`{_md(reason)}`" for reason in packet.get("priority_reasons") or []),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _summary_markdown(summary: dict[str, Any], batch: list[dict[str, Any]]) -> str:
    lines = [
        "# Boundary Annotation Expansion Summary",
        "",
        "## Validation",
        "",
        f"- Question packets: {summary['packet_count']}",
        f"- Boundary events: {summary['boundary_event_count']}",
        f"- Connected components: {summary['component_count']}",
        f"- Priority batch: {summary['priority_batch_count']}",
        f"- P0 questions: {summary['p0_question_count']}",
        f"- All P0 selected: `{str(summary['all_p0_in_priority_batch']).lower()}`",
        f"- Leakage-safe provisional split: `{str(summary['split_is_leakage_safe']).lower()}`",
        f"- `pending_review` packets: {summary['pending_review_packet_count']}",
        f"- Training-eligible packets: {summary['training_eligible_packet_count']}",
        "",
        "## Priority Coverage",
        "",
        "| Reason | Available questions | Selected | Remaining |",
        "| --- | ---: | ---: | ---: |",
    ]
    for reason, values in summary["expansion_focus"].items():
        lines.append(
            f"| `{_md(reason)}` | {values['available_question_count']} | "
            f"{values['selected_question_count']} | {values['remaining_unselected_question_count']} |"
        )
    lines.extend(
        [
            "",
            "## Provisional Split",
            "",
        "| Split | Questions | Components | P0 | P1 | P2 | P3 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for split in DEFAULT_SPLIT_RATIOS:
        tiers = summary["split_priority_tier_counts"].get(split, {})
        lines.append(
            f"| `{split}` | {summary['split_question_counts'].get(split, 0)} | "
            f"{summary['split_component_counts'].get(split, 0)} | "
            f"{tiers.get('P0', 0)} | {tiers.get('P1', 0)} | "
            f"{tiers.get('P2', 0)} | {tiers.get('P3', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Gap",
            "",
            summary["data_gap_statement"],
            "",
            "The next operation is human boundary review of the exported batch, beginning with "
            "P0 conflict/wrong-target and observed E-to-C packets. No model training is authorized "
            "by this export.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_written_outputs(paths: dict[str, Path], expected_summary: dict[str, Any]) -> None:
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError(f"Exporter did not write required outputs: {missing}")
    json_keys = ("contract_json", "split_manifest", "summary_json", "campaign_manifest")
    for key in json_keys:
        json.loads(paths[key].read_text(encoding="utf-8"))
    jsonl_keys = ("components", "packets", "priority_batch")
    parsed = {
        key: [json.loads(line) for line in paths[key].read_text(encoding="utf-8").splitlines()]
        for key in jsonl_keys
    }
    if len(parsed["packets"]) != int(expected_summary["packet_count"]):
        raise ValueError("Written packet count does not match validated summary")
    if len(parsed["components"]) != int(expected_summary["component_count"]):
        raise ValueError("Written component count does not match validated summary")
    if len(parsed["priority_batch"]) != int(expected_summary["priority_batch_count"]):
        raise ValueError("Written priority batch count does not match validated summary")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
