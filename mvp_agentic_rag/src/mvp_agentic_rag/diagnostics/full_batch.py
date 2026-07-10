from __future__ import annotations

import random
from collections import Counter
from collections import defaultdict
from typing import Any

from .claim_risk_schema import validate_record


CORE_RISK_TYPES = {
    "supported_answer",
    "critical_gap",
    "wrong_target",
    "repairable_missing_hop",
    "answer_extraction_failure",
}


def export_full_batch_preflight(
    records: list[dict[str, Any]],
    *,
    candidate_pool_quality: dict[str, Any] | None = None,
    min_total: int = 120,
    max_total: int = 200,
) -> dict[str, Any]:
    risk_counts = Counter(str(record.get("risk_type", "unknown")) for record in records)
    action_counts = Counter(str(record.get("oracle_action", "unknown")) for record in records)
    hop_counts = Counter(str(record.get("hop", "unknown")) for record in records)
    duplicate_ids = _duplicate_ids(records)
    validation_errors = {
        str(record.get("id", "")): errors
        for record in records
        if (errors := validate_record(record))
    }
    total = len(records)
    schema_issue_count = sum(len(errors) for errors in validation_errors.values())
    pass_count = total - len(validation_errors)
    validate_pass_rate = pass_count / total if total else 0.0
    available_risk_counts = _available_risk_counts(candidate_pool_quality)
    has_candidate_pool_quality = bool(available_risk_counts)
    available_core_risk_types = sorted(
        risk_type for risk_type in CORE_RISK_TYPES if available_risk_counts.get(risk_type, 0) > 0
    )
    missing_available_risk_types = sorted(
        risk_type for risk_type in available_core_risk_types if risk_counts.get(risk_type, 0) == 0
    )
    represented_available_count = len(available_core_risk_types) - len(missing_available_risk_types)
    min_represented_available = min(5, len(available_core_risk_types))
    coverage_warnings = []
    if not has_candidate_pool_quality:
        coverage_warnings.append("candidate_pool_quality missing; risk availability checks are not authoritative")
    coverage_warnings.extend(
        f"{risk_type} unavailable in candidate_pool_quality"
        for risk_type in sorted(CORE_RISK_TYPES)
        if available_risk_counts and available_risk_counts.get(risk_type, 0) == 0
    )
    has_4hop_or_repairable = (
        any(record.get("hop") == 4 for record in records) or risk_counts.get("repairable_missing_hop", 0) > 0
    )

    gate_checks = {
        "total_count_min": {"value": total, "threshold": f">= {min_total}", "passed": total >= min_total},
        "total_count_max": {"value": total, "threshold": f"<= {max_total}", "passed": total <= max_total},
        "validate_record_pass_rate": {
            "value": validate_pass_rate,
            "threshold": ">= 0.90",
            "passed": validate_pass_rate >= 0.90,
        },
        "schema_issue_count": {"value": schema_issue_count, "threshold": "== 0", "passed": schema_issue_count == 0},
        "candidate_pool_quality_available": {
            "value": has_candidate_pool_quality,
            "threshold": "true",
            "passed": has_candidate_pool_quality,
        },
        "represented_available_risk_type_count": {
            "value": represented_available_count,
            "threshold": f">= {min_represented_available}",
            "passed": represented_available_count >= min_represented_available,
        },
        "has_supported_answer_if_available": _available_bucket_check("supported_answer", risk_counts, available_risk_counts),
        "has_wrong_target_if_available": _available_bucket_check("wrong_target", risk_counts, available_risk_counts),
        "has_repairable_missing_hop_if_available": _available_bucket_check(
            "repairable_missing_hop", risk_counts, available_risk_counts
        ),
        "has_answer_extraction_failure_if_available": _available_bucket_check(
            "answer_extraction_failure", risk_counts, available_risk_counts
        ),
        "has_4hop_or_repairable_record": {
            "value": has_4hop_or_repairable,
            "threshold": "true",
            "passed": has_4hop_or_repairable,
        },
        "action_coverage_count": {"value": len(action_counts), "threshold": ">= 3", "passed": len(action_counts) >= 3},
        "duplicate_id_count": {"value": len(duplicate_ids), "threshold": "== 0", "passed": len(duplicate_ids) == 0},
    }
    return {
        "total_count": total,
        "validate_record_pass_rate": validate_pass_rate,
        "schema_issue_count": schema_issue_count,
        "schema_issue_records": validation_errors,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "available_risk_type_count": len(available_core_risk_types),
        "represented_available_risk_type_count": represented_available_count,
        "missing_available_risk_types": missing_available_risk_types,
        "coverage_warnings": coverage_warnings,
        "risk_type_coverage": dict(risk_counts),
        "available_risk_type_coverage": dict(available_risk_counts),
        "oracle_action_distribution": dict(action_counts),
        "hop_coverage": dict(hop_counts),
        "gate_checks": gate_checks,
        "go_or_no_go_for_review": "go" if all(check["passed"] for check in gate_checks.values()) else "no_go",
    }


def full_batch_preflight_to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Claim-Risk Full Batch Preflight",
        "",
        f"- total_count: {summary.get('total_count', 0)}",
        f"- validate_record_pass_rate: {summary.get('validate_record_pass_rate', 0.0):.4f}",
        f"- schema_issue_count: {summary.get('schema_issue_count', 0)}",
        f"- duplicate_id_count: {summary.get('duplicate_id_count', 0)}",
        f"- available_risk_type_count: {summary.get('available_risk_type_count', 0)}",
        f"- represented_available_risk_type_count: {summary.get('represented_available_risk_type_count', 0)}",
        f"- go_or_no_go_for_review: {summary.get('go_or_no_go_for_review', 'no_go')}",
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
        ("Available Risk Type Coverage", "available_risk_type_coverage"),
        ("Oracle Action Distribution", "oracle_action_distribution"),
        ("Hop Coverage", "hop_coverage"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for label, count in sorted((summary.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")

    schema_records = summary.get("schema_issue_records") or {}
    if schema_records:
        lines.extend(["", "## Schema Issue Records", ""])
        for record_id, errors in sorted(schema_records.items()):
            lines.append(f"- `{record_id}`: {', '.join(errors)}")

    warnings = summary.get("coverage_warnings") or []
    if warnings:
        lines.extend(["", "## Coverage Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def export_full_review_summary(
    records: list[dict[str, Any]],
    *,
    min_annotated: int = 120,
    min_human_verified: int = 100,
    max_adjudication_rate: float = 0.25,
    max_excluded_rate: float = 0.35,
    min_valid_risk_types: int = 5,
) -> dict[str, Any]:
    annotated = [r for r in records if r.get("annotation_status") in {"human_verified", "excluded", "adjudication_needed"}]
    human_verified = [r for r in records if r.get("annotation_status") == "human_verified"]
    excluded = [r for r in records if r.get("annotation_status") == "excluded"]
    adjudication = [r for r in records if r.get("annotation_status") == "adjudication_needed"]
    validation_errors = {
        str(record.get("id", "")): errors
        for record in human_verified
        if (errors := validate_record(record))
    }
    annotated_count = len(annotated)
    human_verified_count = len(human_verified)
    schema_issue_count = sum(len(errors) for errors in validation_errors.values())
    pass_count = human_verified_count - len(validation_errors)
    validate_pass_rate = pass_count / human_verified_count if human_verified_count else 0.0
    adjudication_rate = len(adjudication) / annotated_count if annotated_count else 0.0
    excluded_rate = len(excluded) / annotated_count if annotated_count else 0.0
    valid_risk_counts = Counter(str(record.get("risk_type", "unknown")) for record in human_verified)
    human_review_provenance_issue_records = sorted(
        str(record.get("id", ""))
        for record in human_verified
        if record.get("label_provenance", {}).get("uses_human_review") is not True
    )

    gate_checks = {
        "annotated_count": {
            "value": annotated_count,
            "threshold": f">= {min_annotated}",
            "passed": annotated_count >= min_annotated,
        },
        "human_verified_count": {
            "value": human_verified_count,
            "threshold": f">= {min_human_verified}",
            "passed": human_verified_count >= min_human_verified,
        },
        "validate_record_pass_rate": {
            "value": validate_pass_rate,
            "threshold": ">= 0.90",
            "passed": validate_pass_rate >= 0.90,
        },
        "schema_issue_count": {"value": schema_issue_count, "threshold": "== 0", "passed": schema_issue_count == 0},
        "human_review_provenance_issue_count": {
            "value": len(human_review_provenance_issue_records),
            "threshold": "== 0",
            "passed": len(human_review_provenance_issue_records) == 0,
        },
        "adjudication_needed_rate": {
            "value": adjudication_rate,
            "threshold": f"<= {max_adjudication_rate}",
            "passed": adjudication_rate <= max_adjudication_rate,
        },
        "excluded_rate": {
            "value": excluded_rate,
            "threshold": f"<= {max_excluded_rate}",
            "passed": excluded_rate <= max_excluded_rate,
        },
        "represented_valid_risk_type_count": {
            "value": len(valid_risk_counts),
            "threshold": f">= {min_valid_risk_types}",
            "passed": len(valid_risk_counts) >= min_valid_risk_types,
        },
    }
    return {
        "annotated_count": annotated_count,
        "human_verified_count": human_verified_count,
        "validate_record_pass_rate": validate_pass_rate,
        "adjudication_needed_count": len(adjudication),
        "adjudication_needed_rate": adjudication_rate,
        "excluded_count": len(excluded),
        "excluded_rate": excluded_rate,
        "schema_issue_count": schema_issue_count,
        "schema_issue_records": validation_errors,
        "human_review_provenance_issue_count": len(human_review_provenance_issue_records),
        "human_review_provenance_issue_records": human_review_provenance_issue_records,
        "risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in annotated)),
        "valid_risk_type_coverage": dict(valid_risk_counts),
        "oracle_action_distribution": dict(Counter(str(record.get("oracle_action", "unknown")) for record in annotated)),
        "valid_oracle_action_distribution": dict(
            Counter(str(record.get("oracle_action", "unknown")) for record in human_verified)
        ),
        "review_status_counts": dict(Counter(str(record.get("annotation_status", "unknown")) for record in annotated)),
        "gate_checks": gate_checks,
        "go_or_no_go_for_checkpoint_c": "go" if all(check["passed"] for check in gate_checks.values()) else "no_go",
    }


def full_review_summary_to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Claim-Risk Full Review Summary",
        "",
        f"- annotated_count: {summary.get('annotated_count', 0)}",
        f"- human_verified_count: {summary.get('human_verified_count', 0)}",
        f"- validate_record_pass_rate: {summary.get('validate_record_pass_rate', 0.0):.4f}",
        f"- adjudication_needed_count: {summary.get('adjudication_needed_count', 0)}",
        f"- adjudication_needed_rate: {summary.get('adjudication_needed_rate', 0.0):.4f}",
        f"- excluded_count: {summary.get('excluded_count', 0)}",
        f"- excluded_rate: {summary.get('excluded_rate', 0.0):.4f}",
        f"- schema_issue_count: {summary.get('schema_issue_count', 0)}",
        f"- human_review_provenance_issue_count: {summary.get('human_review_provenance_issue_count', 0)}",
        f"- go_or_no_go_for_checkpoint_c: {summary.get('go_or_no_go_for_checkpoint_c', 'no_go')}",
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
        ("Review Status Counts", "review_status_counts"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for label, count in sorted((summary.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")

    for title, key in [
        ("Schema Issue Records", "schema_issue_records"),
        ("Human Review Provenance Issue Records", "human_review_provenance_issue_records"),
    ]:
        values = summary.get(key) or {}
        if values:
            lines.extend(["", f"## {title}", ""])
            if isinstance(values, dict):
                for record_id, errors in sorted(values.items()):
                    lines.append(f"- `{record_id}`: {', '.join(errors)}")
            else:
                for record_id in values:
                    lines.append(f"- `{record_id}`")

    return "\n".join(lines) + "\n"


def filter_human_verified_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("annotation_status") == "human_verified"]


def split_human_verified_records(
    records: list[dict[str, Any]],
    *,
    dev_ratio: float = 0.3,
    seed: int = 13,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(str(record.get("risk_type", "unknown")), str(record.get("hop", "unknown")))].append(record)

    rng = random.Random(seed)
    dev: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda r: str(r.get("id", "")))
        rng.shuffle(group)
        dev_count = int(round(len(group) * dev_ratio))
        if len(group) > 1:
            dev_count = min(max(dev_count, 1), len(group) - 1)
        else:
            dev_count = 0
        dev.extend(group[:dev_count])
        test.extend(group[dev_count:])

    return {
        "dev": sorted(dev, key=lambda r: str(r.get("id", ""))),
        "test": sorted(test, key=lambda r: str(r.get("id", ""))),
    }


def validate_human_verified_dataset(
    records: list[dict[str, Any]],
    *,
    dev_records: list[dict[str, Any]] | None = None,
    test_records: list[dict[str, Any]] | None = None,
    expected_risk_types: set[str] | None = None,
    scarce_risk_types: set[str] | None = None,
) -> dict[str, Any]:
    expected_risk_types = expected_risk_types or set()
    scarce_risk_types = scarce_risk_types or set()
    duplicate_ids = _duplicate_ids(records)
    schema_issue_records = {
        str(record.get("id", "")): errors
        for record in records
        if (errors := validate_record(record))
    }
    status_issue_records = sorted(
        str(record.get("id", ""))
        for record in records
        if record.get("annotation_status") != "human_verified"
    )
    human_review_issue_records = sorted(
        str(record.get("id", ""))
        for record in records
        if record.get("label_provenance", {}).get("uses_human_review") is not True
    )

    dev_ids = {str(record.get("id", "")) for record in dev_records or []}
    test_ids = {str(record.get("id", "")) for record in test_records or []}
    overlap_ids = sorted(dev_ids & test_ids)
    test_status_issue_records = sorted(
        str(record.get("id", ""))
        for record in test_records or []
        if record.get("annotation_status") != "human_verified"
    )

    all_risk_types = expected_risk_types or {str(record.get("risk_type", "unknown")) for record in records}
    test_risk_types = {str(record.get("risk_type", "unknown")) for record in test_records or []}
    missing_test_risk_types: list[str] = []
    if test_records is not None:
        missing_test_risk_types = sorted(
            risk_type
            for risk_type in all_risk_types - test_risk_types
            if risk_type not in scarce_risk_types
        )

    valid = not any(
        [
            duplicate_ids,
            schema_issue_records,
            status_issue_records,
            human_review_issue_records,
            overlap_ids,
            test_status_issue_records,
            missing_test_risk_types,
        ]
    )
    return {
        "valid": valid,
        "record_count": len(records),
        "duplicate_ids": duplicate_ids,
        "schema_issue_count": sum(len(errors) for errors in schema_issue_records.values()),
        "schema_issue_records": schema_issue_records,
        "status_issue_records": status_issue_records,
        "human_review_issue_records": human_review_issue_records,
        "dev_count": len(dev_records or []),
        "test_count": len(test_records or []),
        "dev_test_overlap_ids": overlap_ids,
        "test_status_issue_records": test_status_issue_records,
        "missing_test_risk_types": missing_test_risk_types,
        "expected_risk_types": sorted(expected_risk_types),
        "scarce_risk_types": sorted(scarce_risk_types),
        "risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in records)),
        "test_risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in test_records or [])),
    }


def _available_risk_counts(candidate_pool_quality: dict[str, Any] | None) -> Counter[str]:
    raw = (candidate_pool_quality or {}).get("records_by_risk_type") or {}
    return Counter({str(key): int(value) for key, value in raw.items()})


def _available_bucket_check(
    risk_type: str,
    risk_counts: Counter[str],
    available_risk_counts: Counter[str],
) -> dict[str, Any]:
    available = available_risk_counts.get(risk_type, 0)
    selected = risk_counts.get(risk_type, 0)
    if not available_risk_counts or available == 0:
        return {"value": selected, "threshold": "not available", "passed": True}
    return {"value": selected, "threshold": "> 0 when available", "passed": selected > 0}


def _duplicate_ids(records: list[dict[str, Any]]) -> list[str]:
    counts = Counter(str(record.get("id", "")) for record in records)
    return sorted(record_id for record_id, count in counts.items() if record_id and count > 1)
