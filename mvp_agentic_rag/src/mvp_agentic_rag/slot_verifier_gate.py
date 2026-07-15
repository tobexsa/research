from __future__ import annotations

import json
from pathlib import Path

from .answer_canonicalizer import relaxed_answer_match
from .evaluator import exact_match, normalize
from .schemas import Passage, Sample
from .slot_binding_verifier import LLMSlotBindingVerifier, SlotBindingResult
from .slot_ledger import SlotLedger, build_slot_plan, evidence_ids_are_local
from .target_slot_binder import TargetSlotBindingDecision, validate_slot_binding_result


def acceptance_eligible_samples(samples: list[Sample]) -> list[Sample]:
    return [sample for sample in samples if not _excluded_from_acceptance(sample)]


def evaluate_slot_verifier_sample(
    sample: Sample,
    evidence: list[Passage],
    verifier: LLMSlotBindingVerifier,
) -> dict:
    slot_ledger = SlotLedger(build_slot_plan(sample))
    result = verifier.bind_final_slot(sample, evidence, slot_ledger)
    typed_decision = validate_slot_binding_result(
        sample,
        evidence,
        slot_ledger,
        result,
        structured_acceptance=True,
        ordered_hop_gate=True,
    )
    candidates = slot_binding_candidate_values(result)
    structured = dict(result.structured_output or {})
    return {
        "id": sample.sample_id,
        "question": sample.question,
        "gold_answer": sample.gold_answer,
        "evidence_ids": [passage.passage_id for passage in evidence],
        "candidate_values": candidates,
        "candidate_match": any(_answers_match(candidate, sample.gold_answer) for candidate in candidates),
        "parse_status": str(structured.get("parse_status") or "unknown"),
        "attempt_count": int(structured.get("attempt_count") or 0),
        "typed_binder_accepted": typed_decision.accepted,
        "typed_binder_reason": typed_decision.reason,
        "component_acceptance": slot_binding_component_accepted(
            sample,
            evidence,
            slot_ledger,
            result,
            typed_decision,
        ),
        "structured_output": structured,
        "binding_result": result.to_record(),
    }


def slot_binding_component_accepted(
    sample: Sample,
    evidence: list[Passage],
    slot_ledger: SlotLedger,
    result: SlotBindingResult,
    typed_decision: TargetSlotBindingDecision,
) -> bool:
    structured_acceptance = typed_decision.reason == "structured_final_slot_acceptance"
    retrieved_ids = {passage.passage_id for passage in evidence}
    return bool(
        (result.supports_slot or structured_acceptance)
        and result.slot_name == slot_ledger.plan.final_slot
        and result.bound_value.strip()
        and result.evidence_ids
        and (result.slot_relation_match or structured_acceptance)
        and (result.answer_type_match or structured_acceptance)
        and typed_decision.accepted
        and set(result.evidence_ids).issubset(retrieved_ids)
        and evidence_ids_are_local(result.evidence_ids, sample.sample_id)
    )


def slot_binding_candidate_values(result: SlotBindingResult) -> list[str]:
    values = [str(result.bound_value or "")]
    ordered = result.ordered_hop_binding
    if ordered.candidate_is_final_relation_object:
        values.append(str(ordered.final_relation_object or ""))
    for role in result.candidate_roles:
        if role.role == "final_answer" and role.relation_to_question in {"", "fills_final_slot"}:
            values.append(str(role.candidate or ""))
    if result.slot_entailment.entails_answer:
        values.append(str(result.slot_entailment.candidate or ""))
    return _deduplicate_candidates(values)


def summarize_slot_verifier_gate(
    records: list[dict],
    *,
    required_correct_count: int = 5,
    min_parse_success_rate: float = 0.9,
) -> dict:
    eligible_count = len(records)
    parsed_count = sum(record.get("parse_status") in {"parsed", "repaired"} for record in records)
    correct_count = sum(bool(record.get("candidate_match")) for record in records)
    typed_accepted_count = sum(bool(record.get("typed_binder_accepted")) for record in records)
    component_acceptance_count = sum(bool(record.get("component_acceptance")) for record in records)
    parse_success_rate = parsed_count / eligible_count if eligible_count else 0.0
    failure_reasons = []
    if eligible_count != required_correct_count:
        failure_reasons.append("eligible_count_mismatch")
    if correct_count < required_correct_count:
        failure_reasons.append("correct_candidate_count_below_required")
    if parse_success_rate < min_parse_success_rate:
        failure_reasons.append("parse_success_rate_below_threshold")
    if typed_accepted_count < required_correct_count:
        failure_reasons.append("typed_binder_accepted_count_below_required")
    if component_acceptance_count < required_correct_count:
        failure_reasons.append("component_acceptance_count_below_required")
    return {
        "eligible_count": eligible_count,
        "parsed_count": parsed_count,
        "parse_success_rate": parse_success_rate,
        "correct_candidate_count": correct_count,
        "correct_candidate_rate": correct_count / eligible_count if eligible_count else 0.0,
        "typed_binder_accepted_count": typed_accepted_count,
        "typed_binder_accepted_rate": typed_accepted_count / eligible_count if eligible_count else 0.0,
        "component_acceptance_count": component_acceptance_count,
        "component_acceptance_rate": (
            component_acceptance_count / eligible_count if eligible_count else 0.0
        ),
        "required_correct_count": required_correct_count,
        "min_parse_success_rate": min_parse_success_rate,
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
        "records": list(records),
    }


def write_slot_verifier_gate_report(output_dir: str | Path, summary: dict) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "slot_verifier_gate_summary.json"
    markdown_path = output_dir / "slot_verifier_gate_summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    verdict = "GO" if summary.get("passed") else "NO-GO"
    lines = [
        "# Slot Verifier Fixed-Evidence Gate",
        "",
        f"- Verdict: **{verdict}**",
        f"- Correct candidates: {summary.get('correct_candidate_count', 0)}/{summary.get('required_correct_count', 5)}",
        f"- Typed binder accepted: {summary.get('typed_binder_accepted_count', 0)}/{summary.get('required_correct_count', 5)}",
        f"- Component acceptance: {summary.get('component_acceptance_count', 0)}/{summary.get('required_correct_count', 5)}",
        f"- Parse success: {summary.get('parsed_count', 0)}/{summary.get('eligible_count', 0)} "
        f"({float(summary.get('parse_success_rate', 0.0)):.4f})",
        f"- Required parse success rate: {float(summary.get('min_parse_success_rate', 0.9)):.4f}",
        "",
        "| id | gold | candidates | match | typed | component | parse | attempts |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for record in summary.get("records", []):
        candidates = ", ".join(str(value) for value in record.get("candidate_values", [])) or "none"
        lines.append(
            f"| {record.get('id', '')} | {record.get('gold_answer', '')} | {candidates} | "
            f"{bool(record.get('candidate_match'))} | {bool(record.get('typed_binder_accepted'))} | "
            f"{bool(record.get('component_acceptance'))} | {record.get('parse_status', '')} | "
            f"{int(record.get('attempt_count') or 0)} |"
        )
    if summary.get("failure_reasons"):
        lines.extend(["", "Failure reasons: " + ", ".join(summary["failure_reasons"])])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _excluded_from_acceptance(sample: Sample) -> bool:
    issue = sample.metadata.get("evaluation_issue") or {}
    return bool(isinstance(issue, dict) and issue.get("exclude_from_acceptance") is True)


def _answers_match(candidate: str, gold: str) -> bool:
    return exact_match(candidate, gold) or relaxed_answer_match(candidate, gold)


def _deduplicate_candidates(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        candidate = " ".join(str(value or "").split())
        key = tuple(normalize(candidate))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result
