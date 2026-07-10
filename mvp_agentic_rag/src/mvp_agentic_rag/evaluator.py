from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

from .answer_canonicalizer import relaxed_answer_match


def normalize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_f1(prediction: str, gold: str) -> float:
    pred = normalize(prediction)
    target = normalize(gold)
    if not pred and not target:
        return 1.0
    if not pred or not target:
        return 0.0
    overlap = len(set(pred) & set(target))
    if overlap == 0:
        return 0.0
    precision = overlap / len(set(pred))
    recall = overlap / len(set(target))
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, gold: str) -> bool:
    return normalize(prediction) == normalize(gold)


def evaluate_records(records: list[dict], run_name: str = "run") -> dict:
    by_method: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_method[record["method"]].append(record)
    methods = {}
    for method, items in sorted(by_method.items()):
        f1s = [token_f1(item.get("final_answer", ""), item.get("gold_answer", "")) for item in items]
        exacts = [1 if exact_match(item.get("final_answer", ""), item.get("gold_answer", "")) else 0 for item in items]
        answered_f1s = [
            token_f1(item.get("final_answer", ""), item.get("gold_answer", ""))
            for item in items
            if item.get("final_action") == "answer"
        ]
        answered_exacts = [
            1 if exact_match(item.get("final_answer", ""), item.get("gold_answer", "")) else 0
            for item in items
            if item.get("final_action") == "answer"
        ]
        retrieval_calls = [item.get("cost", {}).get("retrieval_calls", 0) for item in items]
        abstentions = [1 if item.get("final_action") == "abstain" else 0 for item in items]
        coverage = [1 if item.get("final_action") == "answer" else 0 for item in items]
        unsupported = []
        answered_unsupported = []
        final_answered_unsupported = []
        final_answered_unsupported_excluding_structured_slot_verified = []
        structured_slot_verified_final_answers = []
        final_answered_unsupported_structured_slot_verified = []
        abstention_supported = []
        no_new_evidence = []
        normalized_answer_matches = []
        alias_or_surface_form_mismatches = []
        for item in items:
            steps = item.get("trajectory", [])
            if item.get("final_action") == "answer":
                strict_match = exact_match(item.get("final_answer", ""), item.get("gold_answer", ""))
                relaxed_match = relaxed_answer_match(item.get("final_answer", ""), item.get("gold_answer", ""))
                normalized_answer_matches.append(1 if (strict_match or relaxed_match) else 0)
                alias_or_surface_form_mismatches.append(1 if (not strict_match and relaxed_match) else 0)
            has_unsupported = any(
                claim.get("status") in {"unsupported", "contradicted", "unclear"}
                for step in steps
                for claim in step.get("verifier_output", {}).get("claims", [])
            )
            unsupported.append(1 if has_unsupported else 0)
            if item.get("final_action") == "answer":
                answered_unsupported.append(1 if has_unsupported else 0)
                final_step = steps[-1] if steps else {}
                has_final_unsupported = _has_unsupported_claims(final_step)
                structured_slot_verified = _structured_slot_verified_final_answer(final_step)
                final_answered_unsupported.append(1 if has_final_unsupported else 0)
                final_answered_unsupported_excluding_structured_slot_verified.append(
                    1 if has_final_unsupported and not structured_slot_verified else 0
                )
                structured_slot_verified_final_answers.append(1 if structured_slot_verified else 0)
                final_answered_unsupported_structured_slot_verified.append(
                    1 if has_final_unsupported and structured_slot_verified else 0
                )
            if item.get("final_action") == "abstain":
                final_verifier = steps[-1].get("verifier_output", {}) if steps else {}
                abstention_supported.append(1 if final_verifier.get("overall_sufficiency") != "sufficient" else 0)
            no_new_evidence.append(1 if any(step.get("evidence_gain", 0) <= 0 for step in steps[1:]) else 0)
        avg_retrieval_calls = mean(retrieval_calls) if retrieval_calls else 0.0
        answer_f1 = mean(f1s) if f1s else 0.0
        overall_acc = mean(exacts) if exacts else 0.0
        methods[method] = {
            "count": len(items),
            "overall_acc": overall_acc,
            "overall_em": overall_acc,
            "answer_f1": answer_f1,
            "avg_retrieval_calls": avg_retrieval_calls,
            "unsupported_claim_rate": mean(unsupported) if unsupported else 0.0,
            "abstention_rate": mean(abstentions) if abstentions else 0.0,
            "no_new_evidence_call_rate": mean(no_new_evidence) if no_new_evidence else 0.0,
            "coverage": mean(coverage) if coverage else 0.0,
            "selective_acc": mean(answered_exacts) if answered_exacts else 0.0,
            "selective_answer_f1": mean(answered_f1s) if answered_f1s else 0.0,
            "cost_normalized_acc": overall_acc / avg_retrieval_calls if avg_retrieval_calls else 0.0,
            "cost_normalized_f1": answer_f1 / avg_retrieval_calls if avg_retrieval_calls else 0.0,
            "wasted_retrieval_rate": mean(no_new_evidence) if no_new_evidence else 0.0,
            "answered_unsupported_rate": mean(answered_unsupported) if answered_unsupported else 0.0,
            "final_answered_unsupported_rate": mean(final_answered_unsupported)
            if final_answered_unsupported
            else 0.0,
            "final_answered_unsupported_excluding_structured_slot_verified_rate": mean(
                final_answered_unsupported_excluding_structured_slot_verified
            )
            if final_answered_unsupported_excluding_structured_slot_verified
            else 0.0,
            "structured_slot_verified_final_answer_count": sum(structured_slot_verified_final_answers),
            "final_answered_unsupported_structured_slot_verified_count": sum(
                final_answered_unsupported_structured_slot_verified
            ),
            "normalized_answer_match_count": sum(normalized_answer_matches),
            "normalized_answer_match_rate": mean(normalized_answer_matches) if normalized_answer_matches else 0.0,
            "alias_or_surface_form_mismatch_count": sum(alias_or_surface_form_mismatches),
            "alias_or_surface_form_mismatch_rate": mean(alias_or_surface_form_mismatches)
            if alias_or_surface_form_mismatches
            else 0.0,
            "abstention_precision": mean(abstention_supported) if abstention_supported else 0.0,
            "evaluation_slices": _evaluation_slices(items),
            "hop_metrics": _hop_metrics(items),
        }
    return {"run_name": run_name, "methods": methods}


def _hop_metrics(items: list[dict]) -> dict[str, dict[str, float | int]]:
    by_hop: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_hop[_hop_label(item)].append(item)
    metrics = {}
    for hop, hop_items in sorted(by_hop.items()):
        answered = [item for item in hop_items if item.get("final_action") == "answer"]
        f1s = [token_f1(item.get("final_answer", ""), item.get("gold_answer", "")) for item in hop_items]
        answered_f1s = [token_f1(item.get("final_answer", ""), item.get("gold_answer", "")) for item in answered]
        exacts = [1 if exact_match(item.get("final_answer", ""), item.get("gold_answer", "")) else 0 for item in hop_items]
        answered_exacts = [
            1 if exact_match(item.get("final_answer", ""), item.get("gold_answer", "")) else 0
            for item in answered
        ]
        metrics[hop] = {
            "count": len(hop_items),
            "answered": len(answered),
            "overall_acc": mean(exacts) if exacts else 0.0,
            "overall_em": mean(exacts) if exacts else 0.0,
            "answer_f1": mean(f1s) if f1s else 0.0,
            "coverage": len(answered) / len(hop_items) if hop_items else 0.0,
            "selective_acc": mean(answered_exacts) if answered_exacts else 0.0,
            "selective_answer_f1": mean(answered_f1s) if answered_f1s else 0.0,
        }
    return metrics


def _hop_label(record: dict) -> str:
    sample_id = str(record.get("id", ""))
    if "__" not in sample_id:
        return str(record.get("hop") or "unknown")
    prefix = sample_id.split("__", 1)[0]
    if prefix.startswith(("3hop", "4hop")):
        return re.sub(r"\d+$", "", prefix)
    return prefix


def _has_unsupported_claims(step: dict) -> bool:
    return any(
        claim.get("status") in {"unsupported", "contradicted", "unclear"}
        for claim in step.get("verifier_output", {}).get("claims", [])
    )


def _structured_slot_verified_final_answer(step: dict) -> bool:
    if _direct_slot_ledger_verified_final_answer(step):
        return True
    if not step.get("pre_final_slot_gate_accept"):
        return False
    binding_record = step.get("slot_binding_verifier_result") or {}
    if not binding_record.get("supports_slot"):
        return False
    if not str(binding_record.get("bound_value") or "").strip():
        return False
    if not binding_record.get("evidence_ids"):
        return False
    decision_head = binding_record.get("decision_head") or {}
    if decision_head.get("action") != "answer":
        return False
    typed_decision = step.get("typed_target_slot_binder_result") or {}
    if typed_decision and typed_decision.get("accepted") is not True:
        return False
    return bool(step.get("slot_ledger_final_target_evidence_ids"))


def _direct_slot_ledger_verified_final_answer(step: dict) -> bool:
    if not step.get("slot_ledger_answer_from_final_target"):
        return False
    if not step.get("slot_ledger_final_target_evidence_ids"):
        return False
    return bool(step.get("slot_ledger_century_evidence_utilization_acceptance"))


def _evaluation_slices(items: list[dict]) -> dict[str, dict]:
    all_support_retrieved_ids: list[str] = []
    all_support_no_candidate_ids: list[str] = []
    correct_candidate_present_ids: list[str] = []
    correct_candidate_rejected_ids: list[str] = []
    non_entailing_gold_ids: list[str] = []

    for item in items:
        sample_id = str(item.get("id") or "")
        candidates = _runtime_final_candidate_values(item)
        supporting_ids = {
            str(value)
            for value in item.get("supporting_passage_ids", [])
            if str(value or "").strip()
        }
        retrieved_ids = {
            str(value)
            for step in item.get("trajectory", [])
            for value in step.get("retrieved_ids", [])
            if str(value or "").strip()
        }
        if supporting_ids and supporting_ids.issubset(retrieved_ids):
            all_support_retrieved_ids.append(sample_id)
            if not candidates:
                all_support_no_candidate_ids.append(sample_id)

        gold_support_not_entailing = _gold_support_not_textually_entailing(item)
        if gold_support_not_entailing:
            non_entailing_gold_ids.append(sample_id)
        elif any(_answers_match(candidate, item.get("gold_answer", "")) for candidate in candidates):
            correct_candidate_present_ids.append(sample_id)
            final_answer_accepted = item.get("final_action") == "answer" and _answers_match(
                item.get("final_answer", ""),
                item.get("gold_answer", ""),
            )
            if not final_answer_accepted:
                correct_candidate_rejected_ids.append(sample_id)

    return {
        "all_support_retrieved_no_candidate": _slice_record(
            all_support_no_candidate_ids,
            len(all_support_retrieved_ids),
        ),
        "correct_candidate_rejected": _slice_record(
            correct_candidate_rejected_ids,
            len(correct_candidate_present_ids),
        ),
        "gold_support_not_textually_entailing": _slice_record(
            non_entailing_gold_ids,
            len(items),
        ),
    }


def _slice_record(sample_ids: list[str], eligible_count: int) -> dict:
    count = len(sample_ids)
    return {
        "count": count,
        "eligible_count": eligible_count,
        "rate": count / eligible_count if eligible_count else 0.0,
        "sample_ids": sample_ids,
    }


def _runtime_final_candidate_values(item: dict) -> list[str]:
    candidates: list[str] = []
    if item.get("final_action") == "answer":
        candidates.append(str(item.get("final_answer") or ""))
    direct_keys = (
        "slot_ledger_candidate_answer",
        "preserved_final_candidate",
        "structured_final_candidate",
        "answer_extraction_repair_candidate",
        "wrong_target_replacement_candidate",
        "ordered_hop_chain_complete_final_object",
        "slot_binding_verifier_value",
    )
    for step in item.get("trajectory", []):
        candidates.extend(str(step.get(key) or "") for key in direct_keys)
        binding = step.get("slot_binding_verifier_result") or {}
        if not isinstance(binding, dict):
            continue
        candidates.append(str(binding.get("bound_value") or ""))
        ordered = binding.get("ordered_hop_binding") or {}
        if isinstance(ordered, dict) and ordered.get("candidate_is_final_relation_object") is True:
            candidates.append(str(ordered.get("final_relation_object") or ""))
        role = binding.get("candidate_role_labeler") or {}
        if isinstance(role, dict) and _role_is_final_candidate(role):
            candidates.append(str(role.get("candidate") or ""))
        for candidate_role in binding.get("candidate_roles") or []:
            if isinstance(candidate_role, dict) and _role_is_final_candidate(candidate_role):
                candidates.append(str(candidate_role.get("candidate") or ""))
    seen = set()
    result = []
    for candidate in candidates:
        value = " ".join(str(candidate or "").split())
        normalized = " ".join(normalize(value))
        if not normalized or normalized in {"unknown", "unknown answer", "n a", "none"} or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return result


def _role_is_final_candidate(role: dict) -> bool:
    candidate_role = str(role.get("candidate_role") or role.get("role") or "").strip().lower()
    relation = str(role.get("relation_to_question") or "").strip().lower()
    return candidate_role == "final_answer" and relation in {"", "fills_final_slot"}


def _gold_support_not_textually_entailing(item: dict) -> bool:
    metadata = item.get("sample_metadata") or item.get("metadata") or {}
    if not isinstance(metadata, dict):
        return False
    issue = metadata.get("evaluation_issue") or {}
    return bool(
        isinstance(issue, dict)
        and issue.get("category") == "dataset_evidence_ambiguity"
        and issue.get("subcategory") == "gold_support_not_textually_entailing"
    )


def _answers_match(prediction: str, gold: str) -> bool:
    return exact_match(str(prediction or ""), str(gold or "")) or relaxed_answer_match(
        str(prediction or ""),
        str(gold or ""),
    )


def load_trajectory_records(path: str | Path) -> list[dict]:
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_metrics(run_dir: str | Path, run_name: str) -> dict:
    run_dir = Path(run_dir)
    metrics = evaluate_records(load_trajectory_records(run_dir / "trajectories.jsonl"), run_name)
    (run_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Metrics: {run_name}", ""]
    for method, values in metrics["methods"].items():
        lines.append(f"## {method}")
        for key, value in values.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    (run_dir / "metrics.md").write_text("\n".join(lines), encoding="utf-8")
    return metrics
