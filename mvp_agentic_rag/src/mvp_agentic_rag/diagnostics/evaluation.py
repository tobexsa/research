from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any


ALLOWED_SUPPORT = {"supported", "unsupported", "contradicted", "unclear"}
ALLOWED_SUFFICIENCY = {"sufficient", "insufficient", "conflicting", "unclear"}
POLICY_ACTIONS = [
    "answer",
    "refine_query",
    "repair_missing_hop",
    "disambiguate_conflict",
    "read_more",
    "abstain",
]
RISK_TYPES = [
    "supported_answer",
    "critical_gap",
    "wrong_target",
    "bridge_as_final",
    "contradiction",
    "repairable_missing_hop",
    "answer_extraction_failure",
]


def safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def binary_metrics(gold: Sequence[bool], predicted: Sequence[bool]) -> dict[str, float | int]:
    tp = sum(1 for g, p in zip(gold, predicted) if g and p)
    fp = sum(1 for g, p in zip(gold, predicted) if not g and p)
    fn = sum(1 for g, p in zip(gold, predicted) if g and not p)
    tn = sum(1 for g, p in zip(gold, predicted) if not g and not p)
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    return {
        "support": sum(1 for value in gold if value),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "accuracy": safe_divide(tp + tn, tp + tn + fp + fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def multiclass_metrics(gold: Sequence[str], predicted: Sequence[str], labels: Sequence[str]) -> dict[str, Any]:
    label_list = list(dict.fromkeys(str(label) for label in labels))
    total = min(len(gold), len(predicted))
    correct = sum(1 for g, p in zip(gold, predicted) if g == p)
    per_label = {}
    for label in label_list:
        per_label[label] = binary_metrics(
            [value == label for value in gold],
            [value == label for value in predicted],
        )
    confusion: dict[str, dict[str, int]] = {}
    for gold_label, predicted_label in zip(gold, predicted):
        confusion.setdefault(str(gold_label), {})
        confusion[str(gold_label)][str(predicted_label)] = confusion[str(gold_label)].get(str(predicted_label), 0) + 1
    return {
        "accuracy": safe_divide(correct, total),
        "macro_precision": _mean([float(values["precision"]) for values in per_label.values()]),
        "macro_recall": _mean([float(values["recall"]) for values in per_label.values()]),
        "macro_f1": _mean([float(values["f1"]) for values in per_label.values()]),
        "balanced_accuracy": _mean([float(values["recall"]) for values in per_label.values()]),
        "per_label": per_label,
        "confusion": confusion,
    }


def evaluate_predictions(gold_records: list[dict], prediction_records: list[dict]) -> dict[str, Any]:
    gold_id_counts = Counter(str(record.get("id", "")) for record in gold_records)
    prediction_id_counts = Counter(str(record.get("id", "")) for record in prediction_records)
    unique_gold_ids = {record_id for record_id, count in gold_id_counts.items() if record_id and count == 1}
    unique_prediction_ids = {record_id for record_id, count in prediction_id_counts.items() if record_id and count == 1}
    duplicate_gold_ids = sorted(record_id for record_id, count in gold_id_counts.items() if record_id and count > 1)
    duplicate_prediction_ids = sorted(record_id for record_id, count in prediction_id_counts.items() if record_id and count > 1)

    gold_by_id = {str(record.get("id", "")): record for record in gold_records if gold_id_counts[str(record.get("id", ""))] == 1}
    predictions_by_id = {
        str(record.get("id", "")): record
        for record in prediction_records
        if prediction_id_counts[str(record.get("id", ""))] == 1
    }
    missing_prediction_ids = sorted(unique_gold_ids - unique_prediction_ids)
    extra_prediction_ids = sorted(unique_prediction_ids - unique_gold_ids)
    schema_issues = _prediction_schema_issues(prediction_records)

    pairs = [
        (gold_by_id[record_id], predictions_by_id[record_id])
        for record_id in sorted(unique_gold_ids & unique_prediction_ids)
        if not schema_issues.get(record_id)
    ]

    gold_actions = [str(gold.get("oracle_action", "")) for gold, _ in pairs]
    predicted_actions = [str(prediction.get("predicted_oracle_action", "")) for _, prediction in pairs]
    action_labels = sorted(set(POLICY_ACTIONS) | set(gold_actions) | set(predicted_actions))
    action_metrics = multiclass_metrics(gold_actions, predicted_actions, action_labels)

    diagnostic_metrics = _diagnostic_metrics(pairs, gold_records)
    policy_metrics = _policy_metrics(pairs, action_metrics)
    all_records_metrics = {
        "status": "available",
        "evaluated_count": len(pairs),
        "claim_support_accuracy": diagnostic_metrics["claim_support_accuracy"],
        "oracle_action_accuracy": policy_metrics["oracle_action_accuracy"],
    }
    clean_claims_metrics = _clean_claim_metrics(pairs)
    scarce_bucket_notes = _scarce_bucket_notes(gold_records)
    integrity = {
        "gold_count": len(gold_records),
        "prediction_count": len(prediction_records),
        "matched_prediction_count": len(pairs),
        "missing_prediction_count": len(missing_prediction_ids),
        "missing_prediction_ids": missing_prediction_ids,
        "extra_prediction_count": len(extra_prediction_ids),
        "extra_prediction_ids": extra_prediction_ids,
        "duplicate_gold_count": len(duplicate_gold_ids),
        "duplicate_gold_ids": duplicate_gold_ids,
        "duplicate_prediction_count": len(duplicate_prediction_ids),
        "duplicate_prediction_ids": duplicate_prediction_ids,
        "prediction_schema_issue_count": sum(1 for issues in schema_issues.values() if issues),
        "prediction_schema_issue_records": schema_issues,
    }
    no_go = any(
        integrity[key] > 0
        for key in [
            "missing_prediction_count",
            "extra_prediction_count",
            "duplicate_gold_count",
            "duplicate_prediction_count",
            "prediction_schema_issue_count",
        ]
    )
    return {
        "input_counts": {
            "gold_count": len(gold_records),
            "prediction_count": len(prediction_records),
            "evaluated_count": len(pairs),
        },
        "prediction_integrity": integrity,
        "all_records_metrics": all_records_metrics,
        "clean_claims_metrics": clean_claims_metrics,
        "diagnostic_metrics": diagnostic_metrics,
        "policy_metrics": policy_metrics,
        "by_risk_type": _group_metrics(pairs, "risk_type"),
        "by_oracle_action": _group_metrics(pairs, "oracle_action"),
        "by_source_run": _group_metrics(pairs, "source_run"),
        "scarce_bucket_notes": scarce_bucket_notes,
        "go_or_no_go_for_checkpoint_c_evaluation": "no_go" if no_go else "go",
    }


def render_metrics_markdown(metrics: dict) -> str:
    integrity = metrics.get("prediction_integrity", {})
    diagnostic = metrics.get("diagnostic_metrics", {})
    policy = metrics.get("policy_metrics", {})
    lines = [
        "# Claim-Risk Diagnostic Metrics",
        "",
        "## Input Counts",
        f"- gold_count: {metrics.get('input_counts', {}).get('gold_count', 0)}",
        f"- prediction_count: {metrics.get('input_counts', {}).get('prediction_count', 0)}",
        f"- evaluated_count: {metrics.get('input_counts', {}).get('evaluated_count', 0)}",
        "",
        "## Prediction Integrity",
    ]
    for key in [
        "missing_prediction_count",
        "extra_prediction_count",
        "duplicate_gold_count",
        "duplicate_prediction_count",
        "prediction_schema_issue_count",
    ]:
        lines.append(f"- {key}: {integrity.get(key, 0)}")
    lines.extend(
        [
            "",
            "## Diagnostic Metrics",
            f"- claim_support_accuracy: {diagnostic.get('claim_support_accuracy', 0.0):.4f}",
            f"- evidence_sufficiency_accuracy: {diagnostic.get('evidence_sufficiency_accuracy', 0.0):.4f}",
            "",
            "## Policy Metrics",
            f"- oracle_action_accuracy: {policy.get('oracle_action_accuracy', 0.0):.4f}",
            f"- oracle_action_macro_f1: {policy.get('oracle_action_macro_f1', 0.0):.4f}",
            f"- missed_repair_opportunity_rate: {policy.get('missed_repair_opportunity_rate', 0.0):.4f}",
            f"- over_abstain_rate: {policy.get('over_abstain_rate', 0.0):.4f}",
            f"- unsafe_answer_rate: {policy.get('unsafe_answer_rate', 0.0):.4f}",
            (
                "- unsafe_answer_rate_excluding_terminal_carry_forward: "
                f"{policy.get('unsafe_answer_rate_excluding_terminal_carry_forward', 0.0):.4f}"
            ),
            (
                "- terminal_carry_forward_unsafe_count: "
                f"{policy.get('terminal_carry_forward_unsafe_count', 0)}"
            ),
            (
                "- intermediate_repair_step_error_count: "
                f"{policy.get('intermediate_repair_step_error_count', 0)}"
            ),
            (
                "- final_outcome_correct_after_repair_count: "
                f"{policy.get('final_outcome_correct_after_repair_count', 0)}"
            ),
            (
                "- answer_false_negative_but_final_correct_count: "
                f"{policy.get('answer_false_negative_but_final_correct_count', 0)}"
            ),
            "",
            f"- go_or_no_go_for_checkpoint_c_evaluation: {metrics.get('go_or_no_go_for_checkpoint_c_evaluation', 'no_go')}",
            "",
        ]
    )
    return "\n".join(lines)


def _prediction_schema_issues(prediction_records: list[dict]) -> dict[str, list[str]]:
    issues_by_id: dict[str, list[str]] = {}
    required = {
        "id",
        "predicted_claim_support",
        "predicted_evidence_sufficiency",
        "predicted_wrong_target",
        "predicted_bridge_as_final",
        "predicted_oracle_action",
        "predicted_repair_target",
        "prediction_source",
        "source_run",
    }
    for index, prediction in enumerate(prediction_records):
        record_id = str(prediction.get("id") or f"<missing-id:{index}>")
        issues = []
        for key in sorted(required):
            if key not in prediction:
                issues.append(f"missing:{key}")
        claim_support = prediction.get("predicted_claim_support")
        if not isinstance(claim_support, dict):
            issues.append("invalid:predicted_claim_support")
        else:
            for claim_id, support in claim_support.items():
                if support not in ALLOWED_SUPPORT:
                    issues.append(f"invalid:predicted_claim_support.{claim_id}")
        if prediction.get("predicted_evidence_sufficiency") not in ALLOWED_SUFFICIENCY:
            issues.append("invalid:predicted_evidence_sufficiency")
        if not isinstance(prediction.get("predicted_wrong_target"), bool):
            issues.append("invalid:predicted_wrong_target")
        if not isinstance(prediction.get("predicted_bridge_as_final"), bool):
            issues.append("invalid:predicted_bridge_as_final")
        if prediction.get("predicted_oracle_action") not in POLICY_ACTIONS:
            issues.append("invalid:predicted_oracle_action")
        if not isinstance(prediction.get("predicted_repair_target"), dict):
            issues.append("invalid:predicted_repair_target")
        if issues:
            issues_by_id[record_id] = issues
    return issues_by_id


def _diagnostic_metrics(pairs: list[tuple[dict, dict]], all_gold_records: list[dict]) -> dict[str, Any]:
    claim_total = 0
    claim_correct = 0
    for gold, prediction in pairs:
        predicted_claim_support = prediction.get("predicted_claim_support") or {}
        for claim_id, gold_support in (gold.get("claim_support") or {}).items():
            claim_total += 1
            if predicted_claim_support.get(claim_id, "unclear") == gold_support:
                claim_correct += 1

    gold_sufficiency = [str(gold.get("evidence_sufficiency", "unclear")) for gold, _ in pairs]
    predicted_sufficiency = [
        str(prediction.get("predicted_evidence_sufficiency", "unclear")) for _, prediction in pairs
    ]
    sufficiency_labels = sorted(set(ALLOWED_SUFFICIENCY) | set(gold_sufficiency) | set(predicted_sufficiency))
    sufficiency_metrics = multiclass_metrics(gold_sufficiency, predicted_sufficiency, sufficiency_labels)

    risk_labels = sorted(set(RISK_TYPES) | {str(record.get("risk_type")) for record in all_gold_records if record.get("risk_type")})
    risk_type_metrics = {}
    for risk_type in risk_labels:
        risk_type_metrics[risk_type] = binary_metrics(
            [gold.get("risk_type") == risk_type for gold, _ in pairs],
            [_prediction_has_risk(prediction, risk_type) for _, prediction in pairs],
        )
    wrong_target = binary_metrics(
        [bool(gold.get("wrong_target")) for gold, _ in pairs],
        [bool(prediction.get("predicted_wrong_target")) for _, prediction in pairs],
    )
    bridge_as_final = binary_metrics(
        [bool(gold.get("bridge_as_final")) for gold, _ in pairs],
        [bool(prediction.get("predicted_bridge_as_final")) for _, prediction in pairs],
    )
    return {
        "claim_support_accuracy": safe_divide(claim_correct, claim_total),
        "claim_support_correct": claim_correct,
        "claim_support_total": claim_total,
        "evidence_sufficiency_accuracy": sufficiency_metrics["accuracy"],
        "evidence_sufficiency_macro_f1": sufficiency_metrics["macro_f1"],
        "evidence_sufficiency_metrics": sufficiency_metrics,
        "risk_type_metrics": risk_type_metrics,
        "wrong_target_accuracy": wrong_target["accuracy"],
        "wrong_target_metrics": wrong_target,
        "bridge_as_final_accuracy": bridge_as_final["accuracy"],
        "bridge_as_final_metrics": bridge_as_final,
    }


def _policy_metrics(pairs: list[tuple[dict, dict]], action_metrics: dict[str, Any]) -> dict[str, Any]:
    gold_actions = [str(gold.get("oracle_action", "")) for gold, _ in pairs]
    predicted_actions = [str(prediction.get("predicted_oracle_action", "")) for _, prediction in pairs]
    repair_pairs = [(gold, prediction) for gold, prediction in pairs if gold.get("oracle_action") == "repair_missing_hop"]
    exact_repair_matches = [
        _repair_target_exact(gold.get("oracle_repair_target") or {}, prediction.get("predicted_repair_target") or {})
        for gold, prediction in repair_pairs
    ]
    partial_repair_matches = {}
    for field in ["missing_hop", "anchor_entity", "target_relation", "suggested_query"]:
        field_matches = [
            _norm_text((gold.get("oracle_repair_target") or {}).get(field))
            == _norm_text((prediction.get("predicted_repair_target") or {}).get(field))
            for gold, prediction in repair_pairs
            if _norm_text((gold.get("oracle_repair_target") or {}).get(field))
        ]
        partial_repair_matches[field] = safe_divide(sum(1 for value in field_matches if value), len(field_matches))

    missed_repair = sum(
        1
        for gold_action, predicted_action in zip(gold_actions, predicted_actions)
        if gold_action == "repair_missing_hop" and predicted_action in {"abstain", "refine_query"}
    )
    repair_gold_count = sum(1 for action in gold_actions if action == "repair_missing_hop")
    over_abstain_denominator = sum(
        1 for action in gold_actions if action in {"answer", "repair_missing_hop", "read_more", "refine_query"}
    )
    over_abstain = sum(
        1
        for gold_action, predicted_action in zip(gold_actions, predicted_actions)
        if gold_action in {"answer", "repair_missing_hop", "read_more", "refine_query"} and predicted_action == "abstain"
    )
    predicted_answer_count = sum(1 for action in predicted_actions if action == "answer")
    unsafe_answers = sum(
        1
        for gold_action, predicted_action in zip(gold_actions, predicted_actions)
        if gold_action != "answer" and predicted_action == "answer"
    )
    non_terminal_answer_count = sum(
        1
        for (_, prediction), predicted_action in zip(pairs, predicted_actions)
        if predicted_action == "answer" and not bool(prediction.get("terminal_carry_forward"))
    )
    non_terminal_unsafe_answers = sum(
        1
        for (gold, prediction), predicted_action in zip(pairs, predicted_actions)
        if (
            gold.get("oracle_action") != "answer"
            and predicted_action == "answer"
            and not bool(prediction.get("terminal_carry_forward"))
        )
    )
    terminal_carry_forward_unsafe_count = sum(
        1
        for (gold, prediction), predicted_action in zip(pairs, predicted_actions)
        if (
            gold.get("oracle_action") != "answer"
            and predicted_action == "answer"
            and bool(prediction.get("terminal_carry_forward"))
        )
    )
    intermediate_repair_step_error_count = sum(
        1
        for _, prediction in pairs
        if prediction.get("intermediate_repair_step_error") is True
    )
    final_outcome_correct_after_repair_count = sum(
        1
        for _, prediction in pairs
        if prediction.get("final_outcome_correct_after_repair") is True
    )
    answer_false_negative_but_final_correct_count = sum(
        1
        for gold, prediction in pairs
        if gold.get("oracle_action") == "answer"
        and prediction.get("predicted_oracle_action") != "answer"
        and prediction.get("runtime_final_answer_matches_gold") is True
    )
    abstention_metrics = binary_metrics(
        [action == "abstain" for action in gold_actions],
        [action == "abstain" for action in predicted_actions],
    )
    return {
        "oracle_action_accuracy": action_metrics["accuracy"],
        "oracle_action_macro_f1": action_metrics["macro_f1"],
        "balanced_action_accuracy": action_metrics["balanced_accuracy"],
        "per_action": action_metrics["per_label"],
        "action_confusion": action_metrics["confusion"],
        "abstention_precision": abstention_metrics["precision"],
        "abstention_recall": abstention_metrics["recall"],
        "repair_target_exact_match": safe_divide(sum(1 for value in exact_repair_matches if value), len(exact_repair_matches)),
        "repair_target_partial_match": partial_repair_matches,
        "missed_repair_opportunity_rate": safe_divide(missed_repair, repair_gold_count),
        "over_abstain_rate": safe_divide(over_abstain, over_abstain_denominator),
        "unsafe_answer_rate": safe_divide(unsafe_answers, predicted_answer_count),
        "unsafe_answer_rate_excluding_terminal_carry_forward": safe_divide(
            non_terminal_unsafe_answers,
            non_terminal_answer_count,
        ),
        "terminal_carry_forward_unsafe_count": terminal_carry_forward_unsafe_count,
        "intermediate_repair_step_error_count": intermediate_repair_step_error_count,
        "final_outcome_correct_after_repair_count": final_outcome_correct_after_repair_count,
        "answer_false_negative_but_final_correct_count": answer_false_negative_but_final_correct_count,
    }


def _clean_claim_metrics(pairs: list[tuple[dict, dict]]) -> dict[str, Any]:
    clean_pairs = [
        (gold, prediction)
        for gold, prediction in pairs
        if (gold.get("metadata") or {}).get("claims_source") != "verifier_output"
        and not bool((gold.get("label_provenance") or {}).get("uses_model_output"))
    ]
    if not clean_pairs:
        return {"status": "not_available", "count": 0}
    claim_total = 0
    claim_correct = 0
    for gold, prediction in clean_pairs:
        for claim_id, support in (gold.get("claim_support") or {}).items():
            claim_total += 1
            if (prediction.get("predicted_claim_support") or {}).get(claim_id, "unclear") == support:
                claim_correct += 1
    return {
        "status": "available",
        "count": len(clean_pairs),
        "claim_support_accuracy": safe_divide(claim_correct, claim_total),
    }


def _scarce_bucket_notes(gold_records: list[dict]) -> list[dict[str, Any]]:
    counts = Counter(str(record.get("risk_type", "")) for record in gold_records if record.get("risk_type"))
    labels = sorted(set(RISK_TYPES) | set(counts))
    return [
        {
            "risk_type": label,
            "support": counts.get(label, 0),
            "note": "support_below_5_do_not_use_alone_for_training_decision",
        }
        for label in labels
        if counts.get(label, 0) < 5
    ]


def _group_metrics(pairs: list[tuple[dict, dict]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for gold, prediction in pairs:
        grouped[str(gold.get(field) or (gold.get("metadata") or {}).get(field) or "unknown")].append((gold, prediction))
    metrics = {}
    for value, value_pairs in sorted(grouped.items()):
        correct = sum(
            1 for gold, prediction in value_pairs if gold.get("oracle_action") == prediction.get("predicted_oracle_action")
        )
        metrics[value] = {
            "count": len(value_pairs),
            "oracle_action_accuracy": safe_divide(correct, len(value_pairs)),
        }
    return metrics


def _prediction_has_risk(prediction: dict, risk_type: str) -> bool:
    action = prediction.get("predicted_oracle_action")
    sufficiency = prediction.get("predicted_evidence_sufficiency")
    claim_support = prediction.get("predicted_claim_support") or {}
    if risk_type == "supported_answer":
        return (
            action == "answer"
            and sufficiency == "sufficient"
            and not prediction.get("predicted_wrong_target")
            and not prediction.get("predicted_bridge_as_final")
            and all(value == "supported" for value in claim_support.values())
        )
    if risk_type == "critical_gap":
        return sufficiency == "insufficient" and action in {"refine_query", "read_more", "abstain"}
    if risk_type == "wrong_target":
        return bool(prediction.get("predicted_wrong_target"))
    if risk_type == "bridge_as_final":
        return bool(prediction.get("predicted_bridge_as_final"))
    if risk_type == "contradiction":
        return sufficiency == "conflicting" or action == "disambiguate_conflict" or "contradicted" in set(claim_support.values())
    if risk_type == "repairable_missing_hop":
        return action == "repair_missing_hop"
    if risk_type == "answer_extraction_failure":
        repair_target = prediction.get("predicted_repair_target") or {}
        return any(_norm_text(value) == "answer extraction failure" for value in repair_target.values())
    return False


def _repair_target_exact(gold_target: dict, predicted_target: dict) -> bool:
    fields = ["missing_hop", "anchor_entity", "target_relation", "suggested_query"]
    return all(_norm_text(gold_target.get(field)) == _norm_text(predicted_target.get(field)) for field in fields)


def _norm_text(value: object) -> str:
    return " ".join(str(value or "").lower().split())


def _mean(values: Sequence[float]) -> float:
    return safe_divide(sum(values), len(values))
