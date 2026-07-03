from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze v1.3.2 repair-query failure modes.")
    parser.add_argument("--v1-3-1-run", type=Path, required=True)
    parser.add_argument("--v1-3-2-run", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--docs-dir", type=Path, required=True)
    args = parser.parse_args()

    old_records = load_records(args.v1_3_1_run / "trajectories.jsonl")
    new_records = load_records(args.v1_3_2_run / "trajectories.jsonl")
    summary = {
        "v1_3_2": analyze_v1_3_2(new_records),
        "delta": compare_runs(old_records, new_records),
        "four_hop_bottleneck": analyze_four_hop_bottleneck(new_records),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    (args.docs_dir / "v1_3_2_answered_unsupported_audit.md").write_text(
        answered_unsupported_markdown(summary["v1_3_2"]["answered_unsupported"]),
        encoding="utf-8",
    )
    (args.docs_dir / "v1_3_1_vs_v1_3_2_delta.md").write_text(
        delta_markdown(summary["delta"]),
        encoding="utf-8",
    )
    (args.docs_dir / "v1_3_2_4hop_bottleneck.md").write_text(
        four_hop_markdown(summary["four_hop_bottleneck"]),
        encoding="utf-8",
    )
    print(json.dumps(summary["v1_3_2"]["headline"], indent=2, ensure_ascii=False))


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def analyze_v1_3_2(records: list[dict[str, Any]]) -> dict[str, Any]:
    answered_unsupported_cases = []
    risk_counts = Counter()
    for record in records:
        if record.get("final_action") != "answer":
            continue
        unsupported_claims = _unsupported_claims(record)
        if not unsupported_claims:
            continue
        risk_class = _answered_unsupported_risk_class(record, unsupported_claims)
        risk_counts[risk_class] += 1
        answered_unsupported_cases.append(
            {
                "id": record.get("id"),
                "hop": hop_label(record),
                "question": record.get("question"),
                "final_answer": record.get("final_answer"),
                "gold_answer": record.get("gold_answer"),
                "exact_match": exact_match(record.get("final_answer", ""), record.get("gold_answer", "")),
                "risk_class": risk_class,
                "unsupported_claim_count": len(unsupported_claims),
                "unsupported_claims": unsupported_claims,
                "final_target_evidence_ids": _last_value(record, "slot_ledger_final_target_evidence_ids", []),
                "repair_closed": _last_value(record, "repair_closed", ""),
                "repair_query_action": _last_value(record, "repair_query_action", ""),
                "repair_query_quality_bucket": _last_value(record, "repair_query_quality_bucket", ""),
            }
        )
    return {
        "headline": {
            "records": len(records),
            "answered_unsupported_count": len(answered_unsupported_cases),
            "answered_unsupported_risk_counts": dict(risk_counts),
        },
        "answered_unsupported": {
            "count": len(answered_unsupported_cases),
            "risk_counts": dict(risk_counts),
            "cases": answered_unsupported_cases,
        },
    }


def compare_runs(old_records: list[dict[str, Any]], new_records: list[dict[str, Any]]) -> dict[str, Any]:
    old_by_id = {record.get("id"): record for record in old_records}
    transition_counts = Counter()
    cases = []
    for new in new_records:
        sample_id = new.get("id")
        old = old_by_id.get(sample_id)
        if old is None:
            continue
        transition = _transition(old, new)
        transition_counts[transition] += 1
        cases.append(
            {
                "id": sample_id,
                "hop": hop_label(new),
                "transition": transition,
                "old_action": old.get("final_action"),
                "new_action": new.get("final_action"),
                "old_answer": old.get("final_answer"),
                "new_answer": new.get("final_answer"),
                "gold_answer": new.get("gold_answer"),
                "old_exact": _record_exact(old),
                "new_exact": _record_exact(new),
                "old_repair_closed": _last_value(old, "repair_closed", ""),
                "new_repair_closed": _last_value(new, "repair_closed", ""),
                "new_repair_query_rewritten": bool(_last_value(new, "repair_query_rewritten", False)),
                "new_repair_query_quality_bucket": _last_value(new, "repair_query_quality_bucket", ""),
            }
        )
    return {
        "count": len(cases),
        "transition_counts": dict(transition_counts),
        "cases": cases,
    }


def analyze_four_hop_bottleneck(records: list[dict[str, Any]]) -> dict[str, Any]:
    cases = []
    verified_prefix_count = 0
    for record in records:
        if hop_label(record) != "4hop":
            continue
        case = _four_hop_case(record)
        if case["has_verified_chain_progress"]:
            verified_prefix_count += 1
        cases.append(case)
    return {
        "count": len(cases),
        "answered": sum(1 for record in records if hop_label(record) == "4hop" and record.get("final_action") == "answer"),
        "verified_prefix_count": verified_prefix_count,
        "cases": cases,
    }


def answered_unsupported_markdown(summary: dict[str, Any]) -> str:
    lines = ["# v1.3.2 Answered Unsupported Audit", ""]
    lines.append(f"- cases: {summary['count']}")
    for key, value in summary["risk_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "| id | hop | exact | risk | unsupported | repair_closed |", "| --- | --- | --- | --- | ---: | --- |"])
    for case in summary["cases"]:
        lines.append(
            f"| {case['id']} | {case['hop']} | {case['exact_match']} | {case['risk_class']} | "
            f"{case['unsupported_claim_count']} | {case['repair_closed']} |"
        )
    return "\n".join(lines) + "\n"


def delta_markdown(summary: dict[str, Any]) -> str:
    lines = ["# v1.3.1 vs v1.3.2 Delta", ""]
    for key, value in summary["transition_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "| id | hop | transition | old | new | new_rewrite |", "| --- | --- | --- | --- | --- | --- |"])
    for case in summary["cases"]:
        lines.append(
            f"| {case['id']} | {case['hop']} | {case['transition']} | {case['old_action']} | "
            f"{case['new_action']} | {case['new_repair_query_rewritten']} |"
        )
    return "\n".join(lines) + "\n"


def four_hop_markdown(summary: dict[str, Any]) -> str:
    lines = ["# v1.3.2 4-hop Bottleneck", ""]
    lines.append(f"- cases: {summary['count']}")
    lines.append(f"- answered: {summary['answered']}")
    lines.append(f"- verified_prefix_count: {summary['verified_prefix_count']}")
    lines.extend(["", "| id | action | verified_prefix | next_missing_relation | repair_closed |", "| --- | --- | --- | --- | --- |"])
    for case in summary["cases"]:
        lines.append(
            f"| {case['id']} | {case['final_action']} | {case['has_verified_chain_progress']} | "
            f"{case['next_missing_relation']} | {case['repair_closed']} |"
        )
    return "\n".join(lines) + "\n"


def _four_hop_case(record: dict[str, Any]) -> dict[str, Any]:
    step = _last_step_with_binding(record) or (record.get("trajectory") or [{}])[-1]
    binding = step.get("slot_binding_verifier_result") or {}
    ordered = binding.get("ordered_hop_binding") or {}
    required_hops = [hop for hop in ordered.get("required_hops", []) if isinstance(hop, dict)]
    verified_prefix_hops = [
        int(hop.get("hop_index", 0) or 0)
        for hop in required_hops
        if hop.get("status") == "bound" and hop.get("supporting_evidence_ids")
    ]
    missing = [
        hop for hop in required_hops if hop.get("status") in {"missing", "ambiguous"} and not hop.get("is_final_hop", False)
    ]
    missing_relation = ""
    if missing:
        missing_relation = str(missing[0].get("relation", "") or "")
    elif ordered.get("missing_critical_hops"):
        missing_relation = str(ordered.get("missing_critical_hops", [""])[0] or "")
    return {
        "id": record.get("id"),
        "question": record.get("question"),
        "final_action": record.get("final_action"),
        "final_answer": record.get("final_answer"),
        "gold_answer": record.get("gold_answer"),
        "verified_prefix_hops": verified_prefix_hops,
        "has_verified_chain_progress": bool(verified_prefix_hops),
        "next_missing_relation": missing_relation,
        "bound_bridge_values": list(ordered.get("bound_bridge_values", [])),
        "missing_critical_hops": list(ordered.get("missing_critical_hops", [])),
        "repair_next_query": step.get("repair_next_query", ""),
        "repair_closed": step.get("repair_closed", ""),
        "repair_retrieved_new_evidence": bool(step.get("repair_retrieved_new_evidence", False)),
    }


def _transition(old: dict[str, Any], new: dict[str, Any]) -> str:
    old_answered = old.get("final_action") == "answer"
    new_answered = new.get("final_action") == "answer"
    old_exact = _record_exact(old)
    new_exact = _record_exact(new)
    if not old_answered and new_answered and new_exact:
        return "abstain_to_correct"
    if not old_answered and new_answered and not new_exact:
        return "abstain_to_wrong"
    if old_answered and old_exact and not new_answered:
        return "correct_to_abstain"
    if old_answered and not old_exact and not new_answered:
        return "wrong_to_abstain"
    if old_answered and old_exact and new_answered and not new_exact:
        return "correct_to_wrong"
    if old_answered and not old_exact and new_answered and new_exact:
        return "wrong_to_correct"
    if not old_answered and not new_answered:
        return "unchanged_abstain"
    if old_answered and new_answered and old_exact == new_exact:
        return "unchanged_answer"
    return "other"


def _unsupported_claims(record: dict[str, Any]) -> list[dict[str, Any]]:
    claims = []
    for step in record.get("trajectory", []):
        verifier = step.get("verifier_output") or {}
        for claim in verifier.get("claims", []):
            if claim.get("status") in {"unsupported", "contradicted", "unclear"}:
                claims.append(
                    {
                        "claim": claim.get("claim", ""),
                        "status": claim.get("status", ""),
                        "evidence_ids": list(claim.get("evidence_ids", [])),
                        "is_critical": bool(claim.get("is_critical", False)),
                        "answer_slot": verifier.get("answer_slot", ""),
                        "final_target_match": verifier.get("final_target_match"),
                    }
                )
    return claims


def _answered_unsupported_risk_class(record: dict[str, Any], claims: list[dict[str, Any]]) -> str:
    final_evidence = _last_value(record, "slot_ledger_final_target_evidence_ids", [])
    if not _record_exact(record):
        return "final_answer_risk"
    if not final_evidence:
        return "final_answer_risk"
    for claim in claims:
        if claim.get("final_target_match") is True or str(claim.get("answer_slot", "")).lower() == "final requested target":
            if claim.get("is_critical") and not claim.get("evidence_ids"):
                return "final_answer_risk"
    return "intermediate_or_verifier_noise"


def _last_value(record: dict[str, Any], key: str, default: Any) -> Any:
    for step in reversed(record.get("trajectory", [])):
        if key in step:
            return step[key]
    return default


def _last_step_with_binding(record: dict[str, Any]) -> dict[str, Any] | None:
    for step in reversed(record.get("trajectory", [])):
        binding = step.get("slot_binding_verifier_result")
        if isinstance(binding, dict) and binding.get("ordered_hop_binding"):
            return step
    return None


def hop_label(record: dict[str, Any]) -> str:
    sample_id = str(record.get("id", ""))
    if "__" not in sample_id:
        return str(record.get("hop") or "unknown")
    prefix = sample_id.split("__", 1)[0]
    return re.sub(r"\d+$", "", prefix) if prefix.startswith(("3hop", "4hop")) else prefix


def _record_exact(record: dict[str, Any]) -> bool:
    return exact_match(record.get("final_answer", ""), record.get("gold_answer", ""))


def exact_match(prediction: str, gold: str) -> bool:
    return _normalize_answer(prediction) == _normalize_answer(gold)


def _normalize_answer(text: str) -> str:
    return " ".join(str(text or "").lower().split())


if __name__ == "__main__":
    main()
