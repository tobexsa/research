from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
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
from mvp_agentic_rag.diagnostics.boundary_adjudication import (
    ADJUDICATION_PROTOCOL_VERSION,
    adjudicate_review_events,
    build_evidence_bundles,
    summarize_assistant_adjudication,
    validate_assistant_adjudication,
)


OUTPUT_NAMES = {
    "evidence": "evidence_bundles.jsonl",
    "events": "assistant_adjudicated_events.jsonl",
    "questions": "assistant_adjudicated_questions.jsonl",
    "combined_csv": "assistant_adjudication_sheet.csv",
    "p0_csv": "p0_assistant_adjudication.csv",
    "p1_csv": "p1_assistant_adjudication.csv",
    "p2_csv": "p2_assistant_adjudication.csv",
    "summary_json": "assistant_adjudication_summary.json",
    "summary_markdown": "assistant_adjudication_summary.md",
    "manifest": "campaign_manifest.json",
}


CSV_FIELDS = [
    "review_event_order",
    "question_review_order",
    "priority_tier",
    "sample_id",
    "question",
    "gold_answer",
    "source_id",
    "round",
    "is_terminal",
    "coverage_rate",
    "retrieved_passage_ids",
    "supporting_passage_ids",
    "machine_first_loss_boundary",
    "machine_candidate_state",
    "machine_correct_candidate_values",
    "machine_wrong_candidate_values",
    "machine_verifier_state",
    "machine_policy_state",
    "machine_outcome_state",
    "assistant_first_loss_boundary",
    "assistant_evidence_state",
    "assistant_candidate_state",
    "assistant_candidate_failure_subtype",
    "assistant_conflict_state",
    "assistant_wrong_target",
    "assistant_recommended_action",
    "assistant_adjudication_decision",
    "assistant_adjudication_status",
    "assistant_adjudication_confidence",
    "assistant_action_set_gap",
    "unsafe_success",
    "applied_override_ids",
    "assistant_adjudication_rationale",
    "assistant_reviewer_id",
    "assistant_reviewer_type",
    "is_human_reviewer",
    "human_review_status",
    "eligible_for_training",
]
HUMAN_OWNED_TOP_LEVEL_FIELDS = (
    "human_review_decision",
    "human_review_status",
    "human_review_notes",
)
HUMAN_OWNED_NESTED_FIELDS = {
    "human_reviewed_labels": (
        "first_loss_boundary",
        "evidence_state",
        "candidate_state",
        "candidate_failure_subtype",
        "conflict_state",
        "wrong_target",
        "recommended_action",
    ),
    "reviewer_provenance": (
        "reviewer_id",
        "reviewed_at",
        "review_protocol_version",
    ),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export evidence-backed assistant proxy adjudication for boundary review events."
    )
    parser.add_argument("--review-events", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--trajectory-source", action="append", default=[])
    parser.add_argument("--fixed-source", action="append", default=[])
    parser.add_argument("--overrides", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-p0", type=int)
    parser.add_argument("--expected-p1", type=int)
    parser.add_argument("--expected-p2", type=int)
    args = parser.parse_args(argv)

    review_path = Path(args.review_events)
    corpus_path = Path(args.corpus)
    overrides_path = Path(args.overrides)
    for name, path in (
        ("review events", review_path),
        ("corpus", corpus_path),
        ("overrides", overrides_path),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {name}: {path}")
    trajectory_paths = _parse_source_paths(args.trajectory_source, "trajectory")
    fixed_paths = _parse_source_paths(args.fixed_source, "fixed evidence")
    review_events = list(read_jsonl(review_path))
    corpus_records = list(read_jsonl(corpus_path))
    trajectory_sources = {
        source_id: list(read_jsonl(path)) for source_id, path in trajectory_paths.items()
    }
    fixed_sources = {
        source_id: list(read_jsonl(path)) for source_id, path in fixed_paths.items()
    }
    override_manifest = json.loads(overrides_path.read_text(encoding="utf-8"))
    overrides = list(override_manifest.get("overrides") or [])
    if str(override_manifest.get("manifest_version") or "") != "assistant_override_manifest_v1":
        raise ValueError("Unsupported assistant override manifest version")

    evidence_map = build_evidence_bundles(
        review_events,
        corpus_records,
        trajectory_sources=trajectory_sources,
        fixed_evidence_sources=fixed_sources,
    )
    adjudicated = adjudicate_review_events(review_events, evidence_map, overrides)
    questions = _question_summaries(adjudicated)
    summary = summarize_assistant_adjudication(adjudicated)
    summary.update(_human_owned_field_changes(review_events, adjudicated))
    summary["question_tier_counts"] = dict(
        sorted(Counter(row["priority_tier"] for row in questions).items())
    )
    summary["override_manifest"] = {
        "path": str(overrides_path.resolve()),
        "sha256": _sha256(overrides_path),
        "override_count": len(overrides),
    }
    expected_counts = {
        "P0": args.expected_p0,
        "P1": args.expected_p1,
        "P2": args.expected_p2,
    }
    _validate_expected_counts(summary, expected_counts)
    _validate_adjudication(adjudicated, questions, evidence_map, summary)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / value for key, value in OUTPUT_NAMES.items()}
    ordered_evidence = [evidence_map[row["review_event_id"]] for row in adjudicated]
    write_jsonl(paths["evidence"], ordered_evidence)
    write_jsonl(paths["events"], adjudicated)
    write_jsonl(paths["questions"], questions)
    csv_rows = [_csv_row(row) for row in adjudicated]
    _write_csv(paths["combined_csv"], csv_rows)
    _write_csv(paths["p0_csv"], [row for row in csv_rows if row["priority_tier"] == "P0"])
    _write_csv(paths["p1_csv"], [row for row in csv_rows if row["priority_tier"] == "P1"])
    _write_csv(paths["p2_csv"], [row for row in csv_rows if row["priority_tier"] == "P2"])
    _write_json(paths["summary_json"], summary)
    paths["summary_markdown"].write_text(
        _summary_markdown(summary, questions), encoding="utf-8"
    )

    source_inputs = {
        **{f"trajectory::{key}": value for key, value in trajectory_paths.items()},
        **{f"fixed::{key}": value for key, value in fixed_paths.items()},
    }
    manifest = {
        "campaign_id": "boundary_assistant_adjudication_v1_20260710",
        "parent_campaign_id": "boundary_annotation_review_v1_20260710",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "adjudication_protocol_version": ADJUDICATION_PROTOCOL_VERSION,
        "inputs": {
            "review_events": _input_record(review_path, len(review_events)),
            "corpus": _input_record(corpus_path, len(corpus_records)),
            "overrides": _input_record(overrides_path, len(overrides)),
            "sources": {
                key: _input_record(path, len(trajectory_sources.get(key.split("::", 1)[-1], fixed_sources.get(key.split("::", 1)[-1], []))))
                for key, path in source_inputs.items()
            },
        },
        "constraints": {
            "network_or_model_calls_executed": False,
            "training_executed": False,
            "controller_behavior_changed": False,
            "human_verified_labels_created": False,
            "assistant_proxy_provenance_required": True,
        },
        "output_counts": {
            "question_count": summary["question_count"],
            "event_count": summary["event_count"],
            "question_tier_counts": summary["question_tier_counts"],
            "event_tier_counts": summary["event_tier_counts"],
            "human_confirmed_event_count": summary["human_confirmed_event_count"],
            "human_owned_field_change_event_count": summary[
                "human_owned_field_change_event_count"
            ],
            "human_owned_field_change_value_count": summary[
                "human_owned_field_change_value_count"
            ],
            "training_eligible_event_count": summary["training_eligible_event_count"],
        },
        "outputs": {name: str(path.resolve()) for name, path in paths.items()},
    }
    _write_json(paths["manifest"], manifest)
    _validate_written_outputs(paths, summary)

    print(f"questions={summary['question_count']}")
    print(f"events={summary['event_count']}")
    print(
        "tiers="
        + ",".join(
            f"{tier}:{summary['question_tier_counts'].get(tier, 0)}"
            for tier in ("P0", "P1", "P2")
        )
    )
    print(f"corrected_events={summary['assistant_corrected_event_count']}")
    print(f"excluded_events={summary['assistant_excluded_event_count']}")
    print(f"unsafe_success_events={summary['unsafe_success_event_count']}")
    print(
        "human_owned_field_changes="
        f"{summary['human_owned_field_change_event_count']}/"
        f"{summary['human_owned_field_change_value_count']}"
    )
    print(f"human_confirmed_events={summary['human_confirmed_event_count']}")
    print(f"training_eligible_events={summary['training_eligible_event_count']}")
    print(f"output_dir={output_dir.resolve()}")
    return 0


def _parse_source_paths(values: list[str], label: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} source must use SOURCE_ID=PATH")
        source_id, raw_path = value.split("=", 1)
        source_id = source_id.strip()
        path = Path(raw_path.strip())
        if not source_id or not path.is_file():
            raise FileNotFoundError(f"Invalid {label} source mapping: {value}")
        if source_id in result:
            raise ValueError(f"Duplicate {label} source id: {source_id}")
        result[source_id] = path
    return result


def _question_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("sample_id") or "")].append(row)
    result = []
    for sample_id, events in sorted(
        groups.items(), key=lambda item: min(int(row.get("question_review_order") or 0) for row in item[1])
    ):
        first = min(events, key=lambda row: int(row.get("review_event_order") or 0))
        result.append(
            {
                "question_review_order": int(first.get("question_review_order") or 0),
                "priority_tier": str(first.get("priority_tier") or ""),
                "sample_id": sample_id,
                "question": str(first.get("question") or ""),
                "gold_answer": str(first.get("gold_answer") or ""),
                "event_count": len(events),
                "assistant_boundary_counts": dict(
                    sorted(
                        Counter(
                            row["assistant_adjudicated_labels"]["first_loss_boundary"]
                            for row in events
                        ).items()
                    )
                ),
                "assistant_decision_counts": dict(
                    sorted(
                        Counter(row["assistant_adjudication_decision"] for row in events).items()
                    )
                ),
                "assistant_status_counts": dict(
                    sorted(
                        Counter(row["assistant_adjudication_status"] for row in events).items()
                    )
                ),
                "override_ids": sorted(
                    {
                        override_id
                        for row in events
                        for override_id in row.get("applied_override_ids") or []
                    }
                ),
                "unsafe_success_event_count": sum(bool(row.get("unsafe_success")) for row in events),
                "action_set_gap_event_count": sum(
                    bool(row.get("assistant_action_set_gap")) for row in events
                ),
                "human_review_status": "pending_human_confirmation",
                "eligible_for_training": False,
            }
        )
    return result


def _validate_expected_counts(summary: dict[str, Any], expected: dict[str, int | None]) -> None:
    for tier, value in expected.items():
        if value is not None and int(summary["question_tier_counts"].get(tier, 0)) != value:
            raise ValueError(
                f"Expected {value} {tier} questions, found {summary['question_tier_counts'].get(tier, 0)}"
            )


def _validate_adjudication(
    events: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    evidence_map: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    for event in events:
        validate_assistant_adjudication(event)
    event_ids = [str(row.get("review_event_id") or "") for row in events]
    if len(event_ids) != len(set(event_ids)) or set(event_ids) != set(evidence_map):
        raise ValueError("Evidence/adjudication event conservation failed")
    if sum(int(row.get("event_count") or 0) for row in questions) != len(events):
        raise ValueError("Question/event conservation failed")
    if summary["human_confirmed_event_count"] != 0 or summary["training_eligible_event_count"] != 0:
        raise ValueError("Assistant adjudication must not create human or training-ready records")
    if (
        summary["human_owned_field_change_event_count"] != 0
        or summary["human_owned_field_change_value_count"] != 0
    ):
        raise ValueError("Assistant adjudication must not modify human-owned fields")


def _csv_row(row: dict[str, Any]) -> dict[str, Any]:
    machine = row.get("machine_boundary_event") or {}
    details = machine.get("candidate_state_details") or {}
    oracle = machine.get("oracle_evidence") or {}
    labels = row.get("assistant_adjudicated_labels") or {}
    reviewer = row.get("assistant_reviewer_provenance") or {}
    bundle = row.get("evidence_bundle") or {}
    return {
        "review_event_order": row.get("review_event_order"),
        "question_review_order": row.get("question_review_order"),
        "priority_tier": row.get("priority_tier"),
        "sample_id": row.get("sample_id"),
        "question": row.get("question"),
        "gold_answer": row.get("gold_answer"),
        "source_id": machine.get("source_id"),
        "round": machine.get("round"),
        "is_terminal": machine.get("is_terminal"),
        "coverage_rate": oracle.get("coverage_rate"),
        "retrieved_passage_ids": _join(bundle.get("retrieved_passage_ids") or []),
        "supporting_passage_ids": _join(bundle.get("supporting_passage_ids") or []),
        "machine_first_loss_boundary": machine.get("first_loss_boundary"),
        "machine_candidate_state": machine.get("candidate_state"),
        "machine_correct_candidate_values": _join(details.get("correct_final_candidate_values") or []),
        "machine_wrong_candidate_values": _join(details.get("wrong_final_candidate_values") or []),
        "machine_verifier_state": machine.get("verifier_state"),
        "machine_policy_state": machine.get("policy_state"),
        "machine_outcome_state": machine.get("outcome_state"),
        "assistant_first_loss_boundary": labels.get("first_loss_boundary"),
        "assistant_evidence_state": labels.get("evidence_state"),
        "assistant_candidate_state": labels.get("candidate_state"),
        "assistant_candidate_failure_subtype": labels.get("candidate_failure_subtype"),
        "assistant_conflict_state": labels.get("conflict_state"),
        "assistant_wrong_target": labels.get("wrong_target"),
        "assistant_recommended_action": labels.get("recommended_action"),
        "assistant_adjudication_decision": row.get("assistant_adjudication_decision"),
        "assistant_adjudication_status": row.get("assistant_adjudication_status"),
        "assistant_adjudication_confidence": row.get("assistant_adjudication_confidence"),
        "assistant_action_set_gap": row.get("assistant_action_set_gap"),
        "unsafe_success": row.get("unsafe_success"),
        "applied_override_ids": _join(row.get("applied_override_ids") or []),
        "assistant_adjudication_rationale": row.get("assistant_adjudication_rationale"),
        "assistant_reviewer_id": reviewer.get("reviewer_id"),
        "assistant_reviewer_type": reviewer.get("reviewer_type"),
        "is_human_reviewer": reviewer.get("is_human_reviewer"),
        "human_review_status": row.get("human_review_status"),
        "eligible_for_training": row.get("eligible_for_training"),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _summary_markdown(summary: dict[str, Any], questions: list[dict[str, Any]]) -> str:
    lines = [
        "# Assistant Boundary Adjudication Summary",
        "",
        "This is an evidence-backed AI proxy review, not human gold. All events remain pending human confirmation and training-ineligible.",
        "",
        "Fixed-evidence rows are observable only through V; `none` on those rows means no loss observed through V, not a completed policy/O success.",
        "",
        "## Counts",
        "",
        f"- Questions: {summary['question_count']}",
        f"- Events: {summary['event_count']}",
        f"- Assistant-adjudicated events: {summary['assistant_adjudicated_event_count']}",
        f"- Assistant-excluded events: {summary['assistant_excluded_event_count']}",
        f"- Assistant-excluded questions: {summary['assistant_excluded_question_count']}",
        f"- Non-excluded label revisions from precheck: {summary['assistant_nonexcluded_label_revision_event_count']}",
        f"- Events with audited semantic overrides: {summary['override_applied_event_count']}",
        f"- Wrong-target events: {summary['assistant_wrong_target_event_count']}",
        f"- Unsafe-success events: {summary['unsafe_success_event_count']}",
        f"- Action-set-gap events: {summary['assistant_action_set_gap_event_count']}",
        f"- Human-owned-field changed events: {summary['human_owned_field_change_event_count']}",
        f"- Human-owned-field changed values: {summary['human_owned_field_change_value_count']}",
        f"- Human-confirmed events: {summary['human_confirmed_event_count']}",
        f"- Training-eligible events: {summary['training_eligible_event_count']}",
        "",
        "## Boundary Distribution",
        "",
        "| Boundary | Events |",
        "| --- | ---: |",
    ]
    for boundary, count in summary["assistant_boundary_counts"].items():
        lines.append(f"| `{boundary}` | {count} |")
    lines.extend(
        [
            "",
            "## Conflict-State Distribution",
            "",
            "| Conflict state | Events |",
            "| --- | ---: |",
        ]
    )
    for state, count in summary["assistant_conflict_state_counts"].items():
        lines.append(f"| `{state}` | {count} |")
    lines.extend(
        [
            "",
            "## Question Review",
            "",
            "| Order | Tier | Sample | Events | Corrected/excluded | Unsafe success | Action gaps | Overrides |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for question in questions:
        changed = int(question["assistant_decision_counts"].get("correct_labels", 0)) + int(
            question["assistant_decision_counts"].get("exclude_event", 0)
        )
        lines.append(
            f"| {question['question_review_order']} | `{question['priority_tier']}` | "
            f"`{_md(question['sample_id'])}` | {question['event_count']} | {changed} | "
            f"{question['unsafe_success_event_count']} | {question['action_set_gap_event_count']} | "
            f"{', '.join(f'`{_md(value)}`' for value in question['override_ids'])} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Gate",
            "",
            "The proxy review is complete only as assistant adjudication. A human must confirm or correct the labels before any importer may promote annotation status; split freeze remains a separate gate.",
            "",
        ]
    )
    return "\n".join(lines)


def _human_owned_field_changes(
    original_events: list[dict[str, Any]], adjudicated_events: list[dict[str, Any]]
) -> dict[str, int]:
    originals_by_id: dict[str, dict[str, Any]] = {}
    for row in original_events:
        review_event_id = str(row.get("review_event_id") or "")
        if not review_event_id:
            raise ValueError("Review event missing review_event_id")
        if review_event_id in originals_by_id:
            raise ValueError(f"Duplicate review_event_id in review events: {review_event_id}")
        originals_by_id[review_event_id] = row

    changed_event_count = 0
    changed_value_count = 0
    for row in adjudicated_events:
        review_event_id = str(row.get("review_event_id") or "")
        original = originals_by_id.get(review_event_id)
        if original is None:
            raise ValueError(f"Missing original review event for {review_event_id}")
        changed_paths = []
        for field in HUMAN_OWNED_TOP_LEVEL_FIELDS:
            if original.get(field) != row.get(field):
                changed_paths.append(field)
        for root, fields in HUMAN_OWNED_NESTED_FIELDS.items():
            original_values = original.get(root) or {}
            adjudicated_values = row.get(root) or {}
            for field in fields:
                if original_values.get(field) != adjudicated_values.get(field):
                    changed_paths.append(f"{root}.{field}")
        if changed_paths:
            changed_event_count += 1
            changed_value_count += len(changed_paths)
    return {
        "human_owned_field_change_event_count": changed_event_count,
        "human_owned_field_change_value_count": changed_value_count,
    }


def _validate_written_outputs(paths: dict[str, Path], summary: dict[str, Any]) -> None:
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError(f"Missing adjudication outputs: {missing}")
    evidence = [json.loads(line) for line in paths["evidence"].read_text(encoding="utf-8").splitlines()]
    events = [json.loads(line) for line in paths["events"].read_text(encoding="utf-8").splitlines()]
    questions = [json.loads(line) for line in paths["questions"].read_text(encoding="utf-8").splitlines()]
    with paths["combined_csv"].open(newline="", encoding="utf-8-sig") as handle:
        csv_rows = list(csv.DictReader(handle))
    json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    json.loads(paths["manifest"].read_text(encoding="utf-8"))
    expected_events = int(summary["event_count"])
    expected_questions = int(summary["question_count"])
    if len(evidence) != expected_events or len(events) != expected_events or len(csv_rows) != expected_events:
        raise ValueError("Written event/evidence/CSV counts disagree")
    if len(questions) != expected_questions:
        raise ValueError("Written question count disagrees")


def _input_record(path: Path, count: int) -> dict[str, Any]:
    return {"path": str(path.resolve()), "sha256": _sha256(path), "record_count": count}


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


def _join(values: Iterable[Any]) -> str:
    return "; ".join(str(value) for value in values if value is not None and str(value) != "")


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
