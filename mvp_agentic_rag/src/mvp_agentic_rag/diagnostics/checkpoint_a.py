from __future__ import annotations

import csv
import io
import json
import random
from collections import Counter, defaultdict
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from typing import Any

from .action_normalization import normalize_allowed_actions, normalize_runtime_action
from .claim_risk_schema import ALLOWED_RISK_TYPES, validate_record


IMPORTANT_PATHS = [
    "final_action",
    "final_answer",
    "gold_answer",
    "trajectory[].action",
    "trajectory[].verifier_output.overall_sufficiency",
    "trajectory[].verifier_output.final_target_match",
    "trajectory[].verifier_output.claims[].status",
    "trajectory[].slot_binding_verifier_result.ordered_hop_binding.final_relation",
    "trajectory[].slot_binding_verifier_result.ordered_hop_binding.missing_critical_hops[]",
    "trajectory[].repair_query_quality_bucket",
    "trajectory[].repair_closed",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def check_source_runs(run_dirs: list[Path]) -> dict[str, Any]:
    reports = []
    id_sets: dict[str, set[str]] = {}
    for run_dir in run_dirs:
        trajectory_path = run_dir / "trajectories.jsonl"
        metrics_path = run_dir / "metrics.json"
        rows = read_jsonl(trajectory_path) if trajectory_path.exists() else []
        sample_ids = {str(row.get("id", "")) for row in rows if row.get("id")}
        final_actions = Counter(str(row.get("final_action", "")) for row in rows)
        hop_distribution = Counter(_hop_from_sample_id(str(row.get("id", ""))) for row in rows)
        id_sets[run_dir.name] = sample_ids
        reports.append(
            {
                "run": str(run_dir),
                "run_name": run_dir.name,
                "exists": run_dir.exists(),
                "has_trajectories": trajectory_path.exists(),
                "has_metrics": metrics_path.exists(),
                "row_count": len(rows),
                "sample_ids": sorted(sample_ids),
                "final_action_count": dict(final_actions),
                "hop_distribution": dict(hop_distribution),
                "errors": _source_run_errors(run_dir, trajectory_path, rows),
            }
        )

    overlaps = []
    for left, right in combinations(id_sets, 2):
        overlap = sorted(id_sets[left] & id_sets[right])
        overlaps.append({"left": left, "right": right, "overlap_count": len(overlap), "sample_ids": overlap})

    return {"runs": reports, "pairwise_overlap": overlaps}


def audit_trajectory_fields(run_dirs: list[Path], max_records_per_run: int = 5) -> dict[str, Any]:
    reports = []
    for run_dir in run_dirs:
        rows = read_jsonl(run_dir / "trajectories.jsonl")[:max_records_per_run]
        path_stats = {}
        for path in IMPORTANT_PATHS:
            count = sum(1 for row in rows if _path_present(row, path))
            path_stats[path] = {
                "present_count": count,
                "total_count": len(rows),
                "present_rate": count / len(rows) if rows else 0.0,
            }
        reports.append(
            {
                "run": str(run_dir),
                "run_name": run_dir.name,
                "sampled_records": len(rows),
                "top_level_keys": sorted({key for row in rows for key in row.keys()}),
                "path_stats": path_stats,
                "safe_extraction_fields": [
                    path for path, stats in path_stats.items() if stats["present_count"] > 0
                ],
            }
        )
    return {"runs": reports}


def load_corpus(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    return {str(row.get("id")): row for row in read_jsonl(path)}


def build_candidates(run_dirs: list[Path], corpus: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    corpus = corpus or {}
    candidates = []
    for run_dir in run_dirs:
        for row in read_jsonl(run_dir / "trajectories.jsonl"):
            steps = row.get("trajectory") or []
            selected_steps = _select_candidate_steps(steps)
            for step in selected_steps:
                record = _candidate_from_step(row, step, run_dir.name, corpus)
                if not record:
                    continue
                candidates.append(record)
    return candidates


def export_candidate_pool_quality(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    by_risk = Counter(candidate.get("risk_type", "unknown") for candidate in candidates)
    by_action = Counter(candidate.get("oracle_action", "unknown") for candidate in candidates)
    by_rule = Counter((candidate.get("mining_reason") or {}).get("rule", "unknown") for candidate in candidates)
    by_claim_source = Counter((candidate.get("metadata") or {}).get("claims_source", "unknown") for candidate in candidates)
    return {
        "total_candidates": len(candidates),
        "records_by_risk_type": dict(by_risk),
        "records_by_oracle_action": dict(by_action),
        "records_by_mining_reason_rule": dict(by_rule),
        "records_by_claims_source": dict(by_claim_source),
        "records_with_ordered_hop_signal": sum(1 for candidate in candidates if _has_ordered_hop_signal(candidate)),
        "records_with_label_provenance": sum(1 for candidate in candidates if candidate.get("label_provenance")),
        "validation_error_count": sum(1 for candidate in candidates if validate_record(candidate)),
    }


def sample_candidates(candidates: list[dict[str, Any]], target_total: int, seed: int = 13) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        groups[str(candidate.get("risk_type", "unknown"))].append(candidate)
    for rows in groups.values():
        rng.shuffle(rows)

    selected = []
    while len(selected) < min(target_total, len(candidates)):
        progressed = False
        for risk_type in sorted(groups):
            if len(selected) >= target_total:
                break
            rows = groups[risk_type]
            if not rows:
                continue
            selected.append(rows.pop(0))
            progressed = True
        if not progressed:
            break
    return selected


def export_annotation_sheet(
    records: list[dict[str, Any]],
    max_evidence_chars: int | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    markdown_parts = ["# Claim-Risk Pilot Annotation Sheet\n"]
    review_records = []
    for record in records:
        review_record = dict(record)
        review_record.setdefault("annotation_status", "pending_review")
        review_record.setdefault("notes", "")
        if compact:
            review_record = _compact_review_record(review_record, max_evidence_chars or 450)
        markdown_parts.append(_record_to_markdown(review_record, max_evidence_chars=max_evidence_chars))
        review_records.append(review_record)
    return {"markdown": "\n".join(markdown_parts), "review_records": review_records}


def quality_to_markdown(quality: dict[str, Any]) -> str:
    lines = ["# Claim-Risk Candidate Pool Quality", ""]
    lines.append(f"- total_candidates: {quality.get('total_candidates', 0)}")
    lines.append(f"- validation_error_count: {quality.get('validation_error_count', 0)}")
    for key in ["records_by_risk_type", "records_by_oracle_action", "records_by_mining_reason_rule"]:
        lines.append("")
        lines.append(f"## {key}")
        for label, count in sorted((quality.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")
    return "\n".join(lines) + "\n"


CSV_FIELDNAMES = [
    "id",
    "sample_id",
    "question",
    "gold_answer",
    "candidate_answer",
    "hop",
    "round",
    "risk_type",
    "oracle_action",
    "claim_support",
    "claims",
    "critical_missing_claims",
    "noncritical_missing_claims",
    "contradicted_claims",
    "wrong_target",
    "bridge_as_final",
    "final_answer_supported",
    "evidence_sufficiency",
    "oracle_repair_target",
    "evidence_preview",
    "source_run",
    "mining_reason",
    "label_provenance",
    "annotation_status",
    "notes",
]

REVIEW_STATUS_MAP = {
    "reviewed_ok": "human_verified",
    "human_verified": "human_verified",
    "ok": "human_verified",
    "drop": "excluded",
    "excluded": "excluded",
    "needs_fix": "adjudication_needed",
    "adjudication_needed": "adjudication_needed",
    "unclear": "adjudication_needed",
}

RISK_TYPE_REVIEW_MAP: dict[str, str] = {}


def review_records_to_csv(records: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({field: _csv_field(record, field) for field in CSV_FIELDNAMES})
    return buffer.getvalue()


def merge_review_csv_into_records(records: list[dict[str, Any]], csv_text: str) -> list[dict[str, Any]]:
    review_rows = {
        row.get("id", ""): row
        for row in csv.DictReader(io.StringIO(csv_text))
        if row.get("id")
    }
    merged = []
    for record in records:
        updated = deepcopy(record)
        review = review_rows.get(str(record.get("id", "")))
        if review:
            _apply_review_row(updated, review)
        merged.append(updated)
    return merged


def export_pilot_review_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    annotated_records = [
        record
        for record in records
        if record.get("annotation_status") in {"human_verified", "adjudication_needed", "excluded"}
    ]
    human_verified = [record for record in records if record.get("annotation_status") == "human_verified"]
    excluded = [record for record in records if record.get("annotation_status") == "excluded"]
    adjudication = [record for record in records if record.get("annotation_status") == "adjudication_needed"]
    validation_errors = {
        str(record.get("id", "")): validate_record(record)
        for record in human_verified
    }
    validation_errors = {
        record_id: errors
        for record_id, errors in validation_errors.items()
        if errors
    }
    annotated_count = len(annotated_records)
    valid_count = len(human_verified)
    schema_issue_count = sum(len(errors) for errors in validation_errors.values())
    pass_count = valid_count - len(validation_errors)
    validate_pass_rate = pass_count / valid_count if valid_count else 0.0
    adjudication_rate = len(adjudication) / annotated_count if annotated_count else 0.0
    gate_checks = {
        "annotated_count": {"value": annotated_count, "threshold": ">= 30", "passed": annotated_count >= 30},
        "adjudication_needed_rate": {
            "value": adjudication_rate,
            "threshold": "<= 0.25",
            "passed": adjudication_rate <= 0.25,
        },
        "validate_record_pass_rate": {
            "value": validate_pass_rate,
            "threshold": ">= 0.90",
            "passed": validate_pass_rate >= 0.90,
        },
        "schema_issue_count": {"value": schema_issue_count, "threshold": "== 0", "passed": schema_issue_count == 0},
    }
    go = all(check["passed"] for check in gate_checks.values())
    original_risk_types = Counter(
        (record.get("metadata") or {}).get("review_original_risk_type", "")
        for record in records
        if (record.get("metadata") or {}).get("review_original_risk_type")
    )
    return {
        "annotated_count": annotated_count,
        "valid_count": valid_count,
        "validate_record_pass_rate": validate_pass_rate,
        "adjudication_needed_count": len(adjudication),
        "adjudication_needed_rate": adjudication_rate,
        "excluded_count": len(excluded),
        "schema_issue_count": schema_issue_count,
        "schema_issue_records": validation_errors,
        "guideline_issue_count": len(adjudication),
        "risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in annotated_records)),
        "valid_risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in human_verified)),
        "hop_coverage": dict(Counter(str(record.get("hop", "unknown")) for record in annotated_records)),
        "oracle_action_distribution": dict(Counter(str(record.get("oracle_action", "unknown")) for record in annotated_records)),
        "valid_oracle_action_distribution": dict(
            Counter(str(record.get("oracle_action", "unknown")) for record in human_verified)
        ),
        "review_status_counts": dict(Counter(str(record.get("annotation_status", "unknown")) for record in annotated_records)),
        "reviewer_notes_summary": _reviewer_notes_summary(records),
        "recommended_schema_changes": _recommended_schema_changes(original_risk_types),
        "original_risk_type_mappings": dict(original_risk_types),
        "gate_checks": gate_checks,
        "go_or_no_go_for_full_batch": "go" if go else "no_go",
    }


def pilot_review_summary_to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Claim-Risk Pilot Review Summary",
        "",
        f"- annotated_count: {summary.get('annotated_count', 0)}",
        f"- valid_count: {summary.get('valid_count', 0)}",
        f"- validate_record_pass_rate: {summary.get('validate_record_pass_rate', 0.0):.4f}",
        f"- adjudication_needed_count: {summary.get('adjudication_needed_count', 0)}",
        f"- adjudication_needed_rate: {summary.get('adjudication_needed_rate', 0.0):.4f}",
        f"- excluded_count: {summary.get('excluded_count', 0)}",
        f"- schema_issue_count: {summary.get('schema_issue_count', 0)}",
        f"- guideline_issue_count: {summary.get('guideline_issue_count', 0)}",
        f"- go_or_no_go_for_full_batch: {summary.get('go_or_no_go_for_full_batch', 'no_go')}",
        "",
        "## Gate Checks",
        "",
        "| Gate | Value | Threshold | Passed |",
        "|---|---:|---|---|",
    ]
    for name, check in sorted((summary.get("gate_checks") or {}).items()):
        value = check.get("value", "")
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"| {name} | {value} | {check.get('threshold', '')} | {check.get('passed', False)} |")

    for title, key in [
        ("Risk Type Coverage", "risk_type_coverage"),
        ("Valid Risk Type Coverage", "valid_risk_type_coverage"),
        ("Oracle Action Distribution", "oracle_action_distribution"),
        ("Valid Oracle Action Distribution", "valid_oracle_action_distribution"),
        ("Hop Coverage", "hop_coverage"),
        ("Review Status Counts", "review_status_counts"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for label, count in sorted((summary.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")

    lines.extend(["", "## Reviewer Notes Summary", ""])
    for label, count in sorted((summary.get("reviewer_notes_summary") or {}).items()):
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Recommended Schema Changes", ""])
    recommendations = summary.get("recommended_schema_changes") or []
    if recommendations:
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")
    else:
        lines.append("- none")

    schema_records = summary.get("schema_issue_records") or {}
    if schema_records:
        lines.extend(["", "## Schema Issue Records", ""])
        for record_id, errors in sorted(schema_records.items()):
            lines.append(f"- `{record_id}`: {', '.join(errors)}")

    return "\n".join(lines) + "\n"


def compact_review_form_to_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Pilot Annotation Review Compact Form",
        "",
        f"Total records: {len(records)}",
        "",
        "Use this Markdown for reading and decision-making. Apply final edits back to `pilot_annotation_review_compact.csv` or `pilot_annotation_review_template_compact.jsonl`.",
        "",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(_compact_form_record_lines(index, record))
    return "\n".join(lines).rstrip() + "\n"


def sanity_to_markdown(report: dict[str, Any]) -> str:
    lines = ["# Claim-Risk Source Run Sanity", ""]
    for run in report.get("runs", []):
        lines.append(f"## {run['run_name']}")
        lines.append(f"- exists: {run['exists']}")
        lines.append(f"- has_trajectories: {run['has_trajectories']}")
        lines.append(f"- has_metrics: {run['has_metrics']}")
        lines.append(f"- row_count: {run['row_count']}")
        lines.append(f"- errors: {', '.join(run['errors']) if run['errors'] else 'none'}")
        lines.append("")
    return "\n".join(lines)


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = ["# Claim-Risk Trajectory Field Audit", ""]
    for run in audit.get("runs", []):
        lines.append(f"## {run['run_name']}")
        lines.append(f"- sampled_records: {run['sampled_records']}")
        for path, stats in sorted(run.get("path_stats", {}).items()):
            lines.append(f"- {path}: {stats['present_count']}/{stats['total_count']} ({stats['present_rate']:.2f})")
        lines.append("")
    return "\n".join(lines)


def _csv_field(record: dict[str, Any], field: str) -> str:
    if field == "claim_support":
        support = record.get("claim_support") or {}
        return "; ".join(f"{key}={value}" for key, value in sorted(support.items()))
    if field == "claims":
        return " || ".join(
            f"{claim.get('claim_id', '')}: {claim.get('text', '')}"
            for claim in record.get("claims", [])
        )
    if field == "evidence_preview":
        evidence_rows = record.get("evidence_preview") or record.get("evidence", [])
        return " || ".join(_csv_evidence_preview(item) for item in evidence_rows)
    if field in {
        "critical_missing_claims",
        "noncritical_missing_claims",
        "contradicted_claims",
    }:
        return "; ".join(str(value) for value in record.get(field, []))
    if field in {"oracle_repair_target", "mining_reason", "label_provenance"}:
        return json.dumps(record.get(field, {}), ensure_ascii=False, sort_keys=True)
    value = record.get(field, "")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _csv_evidence_preview(evidence: dict[str, Any]) -> str:
    text = evidence.get("text_preview", evidence.get("text", ""))
    suffix = " [truncated]" if evidence.get("truncated") else ""
    return f"{evidence.get('id', '')} | {evidence.get('title', '')} | {text}{suffix}"


def _apply_review_row(record: dict[str, Any], review: dict[str, str]) -> None:
    metadata = record.setdefault("metadata", {})
    original_status = (review.get("annotation_status") or "").strip()
    if original_status:
        metadata["review_original_status"] = original_status
    record["annotation_status"] = REVIEW_STATUS_MAP.get(original_status, "adjudication_needed")

    original_risk_type = (review.get("risk_type") or "").strip()
    if original_risk_type:
        metadata["review_original_risk_type"] = original_risk_type
        record["risk_type"] = RISK_TYPE_REVIEW_MAP.get(original_risk_type, original_risk_type)
        if record["risk_type"] not in ALLOWED_RISK_TYPES:
            record["annotation_status"] = "adjudication_needed"
        metadata["risk_type"] = record["risk_type"]

    for key in ["oracle_action", "evidence_sufficiency"]:
        if review.get(key):
            record[key] = review[key].strip()
    for key in ["wrong_target", "bridge_as_final", "final_answer_supported"]:
        if review.get(key):
            record[key] = _parse_bool(review[key])
    if "final_answer_supported" in record:
        record["should_abstain"] = record.get("oracle_action") == "abstain"

    if review.get("claim_support"):
        record["claim_support"] = _parse_claim_support(review["claim_support"])
    for key in ["critical_missing_claims", "noncritical_missing_claims", "contradicted_claims"]:
        if key in review:
            record[key] = _parse_semicolon_list(review.get(key, ""))
    if review.get("oracle_repair_target"):
        record["oracle_repair_target"] = _parse_json_object(review["oracle_repair_target"])
    if review.get("notes") is not None:
        record["notes"] = review.get("notes", "")

    provenance = record.setdefault("label_provenance", {})
    provenance["uses_human_review"] = True


def _parse_claim_support(text: str) -> dict[str, str]:
    support = {}
    for item in _parse_semicolon_list(text):
        if "=" not in item:
            continue
        claim_id, label = item.split("=", 1)
        support[claim_id.strip()] = label.strip()
    return support


def _parse_semicolon_list(text: str) -> list[str]:
    return [item.strip() for item in str(text or "").split(";") if item.strip()]


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _parse_bool(text: str) -> bool:
    return str(text).strip().lower() in {"1", "true", "yes", "y"}


def _reviewer_notes_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    notes = [str(record.get("notes", "")).lower() for record in records]
    return {
        "notes_nonempty": sum(1 for note in notes if note.strip()),
        "notes_drop_dataset_issue": sum(1 for note in notes if "drop:" in note and "dataset issue" in note),
        "notes_need_fix_signal": sum(1 for note in notes if "needs_fix" in note or "fix:" in note),
    }


def _recommended_schema_changes(original_risk_types: Counter[str]) -> list[str]:
    return []


def _compact_form_record_lines(index: int, record: dict[str, Any]) -> list[str]:
    sample_id = _display_value(record.get("sample_id", ""))
    risk_type = _display_value(record.get("risk_type", ""))
    oracle_action = _display_value(record.get("oracle_action", ""))
    lines = [
        f"## {index}. {sample_id} | {risk_type} | {oracle_action}",
        "",
        f"**Record ID:** `{_display_value(record.get('id', ''))}`",
        "",
        f"**Source Run:** `{_display_value(record.get('source_run', ''))}`",
        "",
        "**Question**",
        "",
        _display_value(record.get("question", "")),
        "",
        "**Answers**",
        "",
        f"- Gold: `{_display_value(record.get('gold_answer', ''))}`",
        f"- Candidate: `{_display_value(record.get('candidate_answer', ''))}`",
        f"- Hop/Round: `{_display_value(record.get('hop', ''))}` / `{_display_value(record.get('round', ''))}`",
        "",
        "**Claims**",
        "",
    ]
    claims = record.get("claims") or []
    if claims:
        for claim in claims:
            lines.append(f"- {_display_value(claim.get('claim_id', ''))}: {_display_value(claim.get('text', ''))}")
    else:
        lines.append("- -")

    lines.extend(["", "**Evidence Preview**", ""])
    evidence_rows = record.get("evidence_preview") or record.get("evidence") or []
    if evidence_rows:
        for evidence in evidence_rows:
            suffix = " [truncated]" if evidence.get("truncated") else ""
            lines.append(
                "- "
                f"{_display_value(evidence.get('id', ''))} | "
                f"{_display_value(evidence.get('title', ''))} | "
                f"{_display_value(evidence.get('text_preview', evidence.get('text', '')))}{suffix}"
            )
    else:
        lines.append("- -")

    label_fields = [
        "claim_support",
        "critical_missing_claims",
        "noncritical_missing_claims",
        "contradicted_claims",
        "wrong_target",
        "bridge_as_final",
        "final_answer_supported",
        "evidence_sufficiency",
        "oracle_action",
        "oracle_repair_target",
        "annotation_status",
        "notes",
    ]
    lines.extend(["", "**Current Preliminary Labels**", "", "| Field | Current value |", "|---|---|"])
    for field in label_fields:
        lines.append(f"| `{field}` | {_markdown_table_value(_compact_form_field(record, field))} |")

    lines.extend(
        [
            "",
            "**Provenance**",
            "",
            f"- mining_reason: `{json.dumps(record.get('mining_reason', {}), ensure_ascii=False, sort_keys=True)}`",
            f"- label_provenance: `{json.dumps(record.get('label_provenance', {}), ensure_ascii=False, sort_keys=True)}`",
            "",
            "**Human Review Notes**",
            "",
            "- Decision:",
            "- Reason:",
            "- Need full evidence lookup: yes/no",
            "",
            "---",
            "",
        ]
    )
    return lines


def _compact_form_field(record: dict[str, Any], field: str) -> str:
    if field == "claim_support":
        return _csv_field(record, field) or "-"
    if field in {
        "critical_missing_claims",
        "noncritical_missing_claims",
        "contradicted_claims",
    }:
        return _csv_field(record, field) or "-"
    if field == "oracle_repair_target":
        return json.dumps(record.get(field, {}), ensure_ascii=False, sort_keys=True) or "-"
    return _display_value(record.get(field, ""))


def _display_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    return text if text else "-"


def _markdown_table_value(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _candidate_from_step(
    row: dict[str, Any],
    step: dict[str, Any],
    run_name: str,
    corpus: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    verifier = step.get("verifier_output") or {}
    claims = _claims_from_verifier(verifier, row)
    claim_support = {claim["claim_id"]: claim["preliminary_support"] for claim in claims}
    runtime_action = str(step.get("action") or row.get("final_action") or "")
    diagnostic_action = _oracle_action(row, step, verifier)
    risk_type = _risk_type(row, step, verifier, diagnostic_action)
    record = {
        "id": f"{run_name}::{row.get('id')}::r{step.get('round', 0)}",
        "dataset": "musique",
        "source_run": run_name,
        "sample_id": str(row.get("id", "")),
        "question": str(row.get("question", "")),
        "gold_answer": str(row.get("gold_answer", "")),
        "candidate_answer": str(row.get("final_answer", "")),
        "hop": _hop_from_sample_id(str(row.get("id", ""))),
        "round": int(step.get("round", 0) or 0),
        "claims": [{key: value for key, value in claim.items() if key != "preliminary_support"} for claim in claims],
        "evidence": _evidence_from_step(step, corpus),
        "claim_support": claim_support,
        "evidence_sufficiency": _evidence_sufficiency(verifier),
        "critical_missing_claims": [
            claim["claim_id"] for claim in claims if claim_support[claim["claim_id"]] in {"unsupported", "unclear"} and claim["role"] == "critical"
        ],
        "noncritical_missing_claims": [],
        "contradicted_claims": [claim["claim_id"] for claim in claims if claim_support[claim["claim_id"]] == "contradicted"],
        "wrong_target": _wrong_target(verifier, step),
        "bridge_as_final": _bridge_as_final(row, step),
        "final_answer_supported": _final_answer_supported(verifier, step, str(row.get("final_answer", ""))),
        "should_abstain": diagnostic_action == "abstain",
        "oracle_action": diagnostic_action,
        "oracle_repair_target": _repair_target(step, verifier),
        "risk_type": risk_type,
        "state": {
            "round": int(step.get("round", 0) or 0),
            "max_rounds": len(row.get("trajectory") or []),
            "budget_remaining": int(step.get("budget_remaining", 0) or 0),
            "allowed_actions": normalize_allowed_actions(["answer", "continue_search", "refine_query", "ordered_hop_repair", "read_more_chunks", "abstain"]),
        },
        "metadata": {
            "risk_type": risk_type,
            "claims_source": "verifier_output",
            "source_runtime_action": runtime_action,
            "final_action": row.get("final_action", ""),
            "repair_closed": step.get("repair_closed", ""),
            "repair_query_quality_bucket": step.get("repair_query_quality_bucket", ""),
        },
        "mining_reason": _mining_reason(row, step, risk_type),
        "label_provenance": {
            "uses_gold_answer": False,
            "uses_gold_chain": False,
            "uses_model_output": True,
            "uses_human_review": False,
            "runtime_available": True,
        },
        "action_metadata": {
            "runtime_action": runtime_action,
            "diagnostic_action": normalize_runtime_action(runtime_action),
        },
        "annotation_status": "pending_review",
        "notes": "",
    }
    return record


def _claims_from_verifier(verifier: dict[str, Any], row: dict[str, Any]) -> list[dict[str, Any]]:
    raw_claims = verifier.get("claims") or []
    if not raw_claims:
        raw_claims = [{"claim": str(row.get("final_answer") or row.get("question")), "status": "unclear", "is_critical": True, "evidence_ids": []}]
    claims = []
    for idx, claim in enumerate(raw_claims, start=1):
        status = str(claim.get("status", "unclear"))
        if status not in {"supported", "unsupported", "contradicted", "unclear"}:
            status = "unclear"
        role = "critical" if claim.get("is_critical", False) else "supporting"
        claims.append(
            {
                "claim_id": f"c{idx}",
                "text": str(claim.get("claim", "")),
                "role": role,
                "source": "verifier_output",
                "evidence_ids": [str(value) for value in claim.get("evidence_ids", [])],
                "missing_evidence": str(claim.get("missing_evidence", "")),
                "preliminary_support": status,
            }
        )
    return claims


def _oracle_action(row: dict[str, Any], step: dict[str, Any], verifier: dict[str, Any]) -> str:
    if _final_answer_supported(verifier, step, str(row.get("final_answer", ""))):
        return "answer"
    if _has_contradiction(verifier):
        return "disambiguate_conflict"
    if _repair_target(step, verifier):
        return "repair_missing_hop"
    if step.get("budget_remaining", 0) <= 0:
        return "abstain"
    if float(step.get("evidence_gain", 0.0) or 0.0) <= 0 and step.get("repair_closed") in {"repair_unresolved_terminal", "repair_expired"}:
        return "abstain"
    if normalize_runtime_action(str(step.get("action", ""))) == "read_more":
        return "read_more"
    if verifier.get("overall_sufficiency") in {"insufficient", "unclear"}:
        return "refine_query"
    return normalize_runtime_action(str(row.get("final_action", "")))


def _risk_type(row: dict[str, Any], step: dict[str, Any], verifier: dict[str, Any], action: str) -> str:
    if _final_answer_supported(verifier, step, str(row.get("final_answer", ""))) and row.get("final_action") == "answer":
        return "supported_answer"
    if _bridge_as_final(row, step):
        return "bridge_as_final"
    if _wrong_target(verifier, step):
        return "wrong_target"
    if _has_contradiction(verifier):
        return "contradiction"
    if action == "repair_missing_hop":
        return "repairable_missing_hop"
    if float(step.get("evidence_gain", 0.0) or 0.0) <= 0:
        return "no_new_evidence"
    return "critical_gap" if _has_critical_gap(verifier) else "insufficient_evidence"


def _repair_target(step: dict[str, Any], verifier: dict[str, Any]) -> dict[str, Any]:
    ordered = _ordered_hop(step)
    missing = ordered.get("missing_critical_hops") or []
    bridge_values = ordered.get("bound_bridge_values") or []
    final_relation = ordered.get("final_relation") or ""
    suggested = step.get("repair_next_query") or verifier.get("suggested_query") or ""
    target = {
        "missing_hop": str(missing[0]) if missing else "",
        "anchor_entity": str(bridge_values[-1]) if bridge_values else "",
        "target_relation": str(final_relation),
        "suggested_query": str(suggested),
    }
    return {key: value for key, value in target.items() if value}


def _ordered_hop(step: dict[str, Any]) -> dict[str, Any]:
    direct = step.get("ordered_hop_binding")
    if isinstance(direct, dict):
        return direct
    nested = ((step.get("slot_binding_verifier_result") or {}).get("ordered_hop_binding") or {})
    return nested if isinstance(nested, dict) else {}


def _evidence_sufficiency(verifier: dict[str, Any]) -> str:
    value = str(verifier.get("overall_sufficiency", "unclear"))
    if value == "sufficient":
        return "sufficient"
    if _has_contradiction(verifier):
        return "conflicting"
    if value in {"insufficient", "unclear"}:
        return value
    return "unclear"


def _final_answer_supported(verifier: dict[str, Any], step: dict[str, Any], candidate_answer: str = "") -> bool:
    claims = verifier.get("claims") or []
    critical = [claim for claim in claims if claim.get("is_critical", False)] or claims
    return (
        bool(str(candidate_answer or "").strip())
        and verifier.get("overall_sufficiency") == "sufficient"
        and verifier.get("need_more_evidence") is False
        and verifier.get("final_target_match") is True
        and bool(critical)
        and all(claim.get("status") == "supported" for claim in critical)
    )


def _has_critical_gap(verifier: dict[str, Any]) -> bool:
    return any(
        claim.get("is_critical", False) and claim.get("status") in {"unsupported", "unclear"}
        for claim in verifier.get("claims", [])
    )


def _has_contradiction(verifier: dict[str, Any]) -> bool:
    return any(claim.get("status") == "contradicted" for claim in verifier.get("claims", []))


def _wrong_target(verifier: dict[str, Any], step: dict[str, Any]) -> bool:
    if verifier.get("final_target_match") is False:
        return True
    decision = ((step.get("slot_binding_verifier_result") or {}).get("decision_head") or {}).get("risk") or {}
    return float(decision.get("wrong_target_risk", 0.0) or 0.0) > 0


def _bridge_as_final(row: dict[str, Any], step: dict[str, Any]) -> bool:
    answer = " ".join(str(row.get("final_answer", "")).lower().split())
    if not answer:
        return False
    bridges = [" ".join(str(value).lower().split()) for value in _ordered_hop(step).get("bound_bridge_values", [])]
    return answer in bridges


def _mining_reason(row: dict[str, Any], step: dict[str, Any], risk_type: str) -> dict[str, Any]:
    rule = risk_type
    fields = ["final_action", "trajectory[].verifier_output"]
    if _ordered_hop(step):
        fields.append("ordered_hop_binding")
    if step.get("repair_query_quality_bucket"):
        fields.append("repair_query_quality_bucket")
    confidence = "strong" if risk_type == "supported_answer" else "medium"
    return {"rule": rule, "matched_fields": fields, "confidence": confidence}


def _select_candidate_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for step in steps:
        verifier = step.get("verifier_output") or {}
        if step.get("action") != "answer" or verifier.get("overall_sufficiency") != "sufficient" or step.get("repair_started"):
            selected.append(step)
    return selected or steps[-1:]


def _evidence_from_step(step: dict[str, Any], corpus: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    evidence = []
    for passage_id in step.get("retrieved_ids", [])[:5]:
        passage = corpus.get(str(passage_id), {})
        evidence.append(
            {
                "id": str(passage_id),
                "title": str(passage.get("title") or passage_id),
                "text": str(passage.get("text", "")),
            }
        )
    return evidence


def _has_ordered_hop_signal(candidate: dict[str, Any]) -> bool:
    fields = (candidate.get("mining_reason") or {}).get("matched_fields", [])
    return "ordered_hop_binding" in fields


def _source_run_errors(run_dir: Path, trajectory_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    errors = []
    if not run_dir.exists():
        errors.append("missing_run_dir")
    if not trajectory_path.exists():
        errors.append("missing_trajectories_jsonl")
    if trajectory_path.exists() and not rows:
        errors.append("empty_trajectories_jsonl")
    return errors


def _path_present(row: dict[str, Any], path: str) -> bool:
    return any(True for _ in _values_at_path(row, path))


def _values_at_path(value: Any, path: str):
    parts = path.split(".")
    yield from _walk_path(value, parts)


def _walk_path(value: Any, parts: list[str]):
    if not parts:
        yield value
        return
    part = parts[0]
    is_array = part.endswith("[]")
    key = part[:-2] if is_array else part
    if not isinstance(value, dict) or key not in value:
        return
    next_value = value[key]
    if is_array:
        if not isinstance(next_value, list):
            return
        for item in next_value:
            yield from _walk_path(item, parts[1:])
        return
    yield from _walk_path(next_value, parts[1:])


def _hop_from_sample_id(sample_id: str) -> int | str:
    prefix = str(sample_id).split("__", 1)[0]
    if prefix.endswith("hop"):
        try:
            return int(prefix[:-3])
        except ValueError:
            return prefix
    return "unknown"


def _compact_review_record(record: dict[str, Any], max_evidence_chars: int) -> dict[str, Any]:
    compact = dict(record)
    evidence = compact.pop("evidence", [])
    compact["evidence_preview"] = [_preview_evidence(item, max_evidence_chars) for item in evidence]
    compact["evidence_full_ref"] = {
        "source": "full_review_template_or_data/musique_corpus.jsonl",
        "passage_ids": [str(item.get("id", "")) for item in evidence],
    }
    return compact


def _preview_evidence(evidence: dict[str, Any], max_evidence_chars: int) -> dict[str, Any]:
    text = str(evidence.get("text", ""))
    preview = text[:max_evidence_chars]
    return {
        "id": str(evidence.get("id", "")),
        "title": str(evidence.get("title", "")),
        "text_preview": preview,
        "truncated": len(text) > len(preview),
    }


def _record_to_markdown(record: dict[str, Any], max_evidence_chars: int | None = None) -> str:
    lines = [
        f"## Record {record['id']}",
        "",
        f"- sample_id: {record.get('sample_id', '')}",
        f"- risk_type: {record.get('risk_type', '')}",
        f"- oracle_action: {record.get('oracle_action', '')}",
        f"- source_run: {record.get('source_run', '')}",
        "",
        f"Question: {record.get('question', '')}",
        "",
        f"Gold answer: {record.get('gold_answer', '')}",
        "",
        f"Candidate answer: {record.get('candidate_answer', '')}",
        "",
        "Claims:",
    ]
    for claim in record.get("claims", []):
        lines.append(f"- {claim.get('claim_id')}: [{record.get('claim_support', {}).get(claim.get('claim_id'), 'unclear')}] {claim.get('text', '')}")
    lines.extend(["", "Evidence:"])
    evidence_rows = record.get("evidence_preview") or record.get("evidence", [])
    for evidence in evidence_rows:
        text = evidence.get("text_preview", evidence.get("text", ""))
        if max_evidence_chars is not None:
            text = str(text)[:max_evidence_chars]
        suffix = " [truncated]" if evidence.get("truncated") else ""
        lines.append(f"- {evidence.get('id')}: {evidence.get('title', '')} {text}{suffix}".strip())
    lines.extend(["", f"Mining reason: `{json.dumps(record.get('mining_reason', {}), ensure_ascii=False)}`", ""])
    return "\n".join(lines)
