from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean


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
        abstention_supported = []
        no_new_evidence = []
        for item in items:
            steps = item.get("trajectory", [])
            has_unsupported = any(
                claim.get("status") in {"unsupported", "contradicted", "unclear"}
                for step in steps
                for claim in step.get("verifier_output", {}).get("claims", [])
            )
            unsupported.append(1 if has_unsupported else 0)
            if item.get("final_action") == "answer":
                answered_unsupported.append(1 if has_unsupported else 0)
                final_step = steps[-1] if steps else {}
                final_answered_unsupported.append(1 if _has_unsupported_claims(final_step) else 0)
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
            "abstention_precision": mean(abstention_supported) if abstention_supported else 0.0,
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
