from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def token_f1(prediction: str, gold: str) -> float:
    pred_tokens = _tokens(prediction)
    gold_tokens = _tokens(gold)
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    overlap = Counter(pred_tokens) & Counter(gold_tokens)
    common = sum(overlap.values())
    if common == 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def _tokens(text: str) -> list[str]:
    import re

    return re.findall(r"[a-z0-9]+", text.lower())


def load_records(path: Path, method: str) -> dict[str, dict[str, Any]]:
    records = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("method") == method:
                record["computed_f1"] = token_f1(record.get("final_answer", ""), record.get("gold_answer", ""))
                records[str(record["id"])] = record
    return records


def repair_count(record: dict[str, Any]) -> int:
    return sum(1 for step in record.get("trajectory", []) if step.get("answer_repair"))


def last_step(record: dict[str, Any]) -> dict[str, Any]:
    trajectory = record.get("trajectory") or []
    return trajectory[-1] if trajectory else {}


def classify(original: dict[str, Any], qwen: dict[str, Any]) -> str:
    original_f1 = original["computed_f1"]
    qwen_f1 = qwen["computed_f1"]
    original_action = original.get("final_action")
    qwen_action = qwen.get("final_action")
    original_repair = repair_count(original)
    qwen_repair = repair_count(qwen)
    qwen_last = last_step(qwen)
    original_last = last_step(original)
    qwen_suff = (qwen_last.get("verifier_output") or {}).get("overall_sufficiency", "")
    original_suff = (original_last.get("verifier_output") or {}).get("overall_sufficiency", "")

    if original_f1 > qwen_f1 and original_repair > qwen_repair:
        return "answer_repair_not_triggered_or_not_needed_by_qwen"
    if original_action == "answer" and qwen_action == "abstain":
        if qwen_suff == "sufficient":
            return "qwen_abstained_despite_sufficient_verifier"
        return "qwen_verifier_stricter_or_answer_not_supported"
    if original_action == "abstain" and qwen_action == "answer":
        return "qwen_verifier_or_answer_more_permissive"
    if original_action == "answer" and qwen_action == "answer" and original_f1 > qwen_f1:
        if qwen_suff == "sufficient" and original_suff == "sufficient":
            return "answer_generation_lower_quality"
        return "verifier_state_changed"
    if qwen_f1 > original_f1:
        if qwen_repair > original_repair:
            return "qwen_answer_repair_helped"
        if original_action == "abstain" and qwen_action == "answer":
            return "qwen_answered_where_original_abstained"
        return "qwen_answer_generation_improved"
    return "tie_or_small_difference"


def summarize_record(label: str, record: dict[str, Any]) -> dict[str, Any]:
    step = last_step(record)
    verifier = step.get("verifier_output") or {}
    return {
        f"{label}_action": record.get("final_action", ""),
        f"{label}_answer": record.get("final_answer", ""),
        f"{label}_f1": record.get("computed_f1", 0.0),
        f"{label}_calls": record.get("cost", {}).get("retrieval_calls", ""),
        f"{label}_repair_count": repair_count(record),
        f"{label}_last_suff": verifier.get("overall_sufficiency", ""),
        f"{label}_last_need_more": verifier.get("need_more_evidence", ""),
        f"{label}_last_statuses": "|".join(
            str(claim.get("status", "")) for claim in verifier.get("claims", [])
        ),
        f"{label}_last_evidence_ids": "|".join(
            evidence_id
            for claim in verifier.get("claims", [])
            for evidence_id in claim.get("evidence_ids", [])
        ),
        f"{label}_last_query": step.get("query", ""),
        f"{label}_last_action": step.get("action", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--qwen", required=True)
    parser.add_argument("--method", default="claim_risk")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args()

    original = load_records(Path(args.original), args.method)
    qwen = load_records(Path(args.qwen), args.method)
    shared_ids = sorted(set(original) & set(qwen))
    rows = []
    for sample_id in shared_ids:
        original_record = original[sample_id]
        qwen_record = qwen[sample_id]
        delta = qwen_record["computed_f1"] - original_record["computed_f1"]
        row = {
            "id": sample_id,
            "question": qwen_record.get("question", ""),
            "gold": qwen_record.get("gold_answer", ""),
            "delta_qwen_minus_original": delta,
            "diagnosis": classify(original_record, qwen_record),
        }
        row.update(summarize_record("original", original_record))
        row.update(summarize_record("qwen", qwen_record))
        rows.append(row)

    rows.sort(key=lambda item: item["delta_qwen_minus_original"])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "case_deltas.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    diagnosis_counts = Counter(row["diagnosis"] for row in rows)
    regressions = [row for row in rows if row["delta_qwen_minus_original"] < -1e-9]
    improvements = [row for row in rows if row["delta_qwen_minus_original"] > 1e-9]
    report_path = output_dir / "diagnosis_summary.md"
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Qwen3 Regression Diagnosis\n\n")
        handle.write(f"- method: `{args.method}`\n")
        handle.write(f"- shared cases: {len(shared_ids)}\n")
        handle.write(f"- regressions: {len(regressions)}\n")
        handle.write(f"- improvements: {len(improvements)}\n")
        handle.write(f"- ties: {len(rows) - len(regressions) - len(improvements)}\n\n")
        handle.write("## Diagnosis Counts\n\n")
        for name, count in diagnosis_counts.most_common():
            handle.write(f"- {name}: {count}\n")
        handle.write("\n## Largest Regressions\n\n")
        for row in rows[: args.top_k]:
            _write_case(handle, row)
        handle.write("\n## Largest Improvements\n\n")
        for row in sorted(rows, key=lambda item: item["delta_qwen_minus_original"], reverse=True)[: args.top_k]:
            _write_case(handle, row)

    print(report_path)
    print(csv_path)
    return 0


def _write_case(handle, row: dict[str, Any]) -> None:
    handle.write(f"### {row['id']} delta={row['delta_qwen_minus_original']:.4f}\n\n")
    handle.write(f"- diagnosis: `{row['diagnosis']}`\n")
    handle.write(f"- question: {row['question']}\n")
    handle.write(f"- gold: {row['gold']}\n")
    handle.write(
        f"- original: action={row['original_action']} f1={row['original_f1']:.4f} "
        f"repair={row['original_repair_count']} suff={row['original_last_suff']} "
        f"answer={row['original_answer']}\n"
    )
    handle.write(
        f"- qwen: action={row['qwen_action']} f1={row['qwen_f1']:.4f} "
        f"repair={row['qwen_repair_count']} suff={row['qwen_last_suff']} "
        f"answer={row['qwen_answer']}\n\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
