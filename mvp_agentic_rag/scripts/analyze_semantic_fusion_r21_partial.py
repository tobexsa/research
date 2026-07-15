from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mvp_agentic_rag.answer_canonicalizer import relaxed_answer_match
from mvp_agentic_rag.evaluator import evaluate_records, exact_match


GAIN_IDS = {
    "2hop__136179_13529",
    "2hop__167577_31122",
    "3hop1__136129_87694_124169",
    "4hop1__161810_583746_457883_650651",
    "4hop1__236903_153080_33897_81096",
}
LOSS_IDS = {
    "2hop__142699_67465",
    "2hop__194469_83289",
    "2hop__23459_35124",
    "2hop__247353_55227",
    "3hop1__103881_443779_52195",
    "3hop1__140786_2053_5289",
    "3hop1__144439_443779_52195",
}


def _load(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _correct(row: dict) -> bool:
    prediction = str(row.get("final_answer") or "")
    gold = str(row.get("gold_answer") or "")
    return bool(prediction) and (
        exact_match(prediction, gold) or relaxed_answer_match(prediction, gold)
    )


def _binding(step: dict) -> dict:
    return dict(
        step.get("slot_binding_verifier_result")
        or step.get("slot_state_binding_verifier_result")
        or {}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--r12",
        default=(
            "runs/layer1_siliconflow_qwen3_14b_semantic_binding_"
            "stratified45_20260713_r12/trajectories.jsonl"
        ),
    )
    parser.add_argument(
        "--r20",
        default=(
            "runs/layer1_siliconflow_qwen3_14b_semantic_certificate_"
            "stratified45_20260714_r20/trajectories.jsonl"
        ),
    )
    parser.add_argument(
        "--r21",
        default=(
            "runs/layer1_siliconflow_qwen3_14b_semantic_fusion_"
            "gain_loss12_20260714_r21/trajectories.jsonl"
        ),
    )
    parser.add_argument("--corpus", default="data/musique_corpus.jsonl")
    parser.add_argument(
        "--json-output",
        default="analysis/semantic_fusion_r21_partial_failure_analysis_20260714.json",
    )
    parser.add_argument(
        "--md-output",
        default="analysis/semantic_fusion_r21_partial_failure_analysis_20260714.md",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    r12 = {row["id"]: row for row in _load(Path(args.r12))}
    r20 = {row["id"]: row for row in _load(Path(args.r20))}
    r21_rows = _load(Path(args.r21))
    r21 = {row["id"]: row for row in r21_rows}
    if len(r21) != len(r21_rows):
        raise ValueError("partial R21 contains duplicate IDs")

    completed_gain_ids = sorted(GAIN_IDS & set(r21))
    completed_loss_ids = sorted(LOSS_IDS & set(r21))
    retained_gains = [sample_id for sample_id in completed_gain_ids if _correct(r21[sample_id])]
    recovered_losses = [sample_id for sample_id in completed_loss_ids if _correct(r21[sample_id])]

    ordinal_id = "2hop__167577_31122"
    ordinal_events = [
        event
        for step in r21[ordinal_id]["trajectory"]
        for event in step.get("slot_state_transition_events", [])
        if event.get("event") == "competing_bound_object_conflict"
    ]
    ordinal_failure = {
        "sample_id": ordinal_id,
        "r20_answer": r20[ordinal_id].get("final_answer", ""),
        "r21_answer": r21[ordinal_id].get("final_answer", ""),
        "events": ordinal_events,
        "root_cause": (
            "surface-equivalent ordinal values ('18th century' and '18th') "
            "were treated as competing objects, creating a false hard conflict"
        ),
        "recommended_fix": (
            "compare hop objects with type-aware ordinal equivalence before "
            "emitting competing_bound_object_conflict"
        ),
    }

    date_id = "2hop__142699_67465"
    date_row = r21[date_id]
    date_step = date_row["trajectory"][-1]
    date_binding = _binding(date_step)
    binding_evidence_ids = set(date_binding.get("evidence_ids") or [])
    if not binding_evidence_ids:
        required_hops = (
            date_binding.get("ordered_hop_binding") or {}
        ).get("required_hops") or []
        final_hops = [hop for hop in required_hops if hop.get("is_final_hop") is True]
        if len(final_hops) == 1:
            binding_evidence_ids.update(
                final_hops[0].get("supporting_evidence_ids") or []
            )
    evidence = {
        row["id"]: row
        for row in _load(Path(args.corpus))
        if row.get("id") in binding_evidence_ids
    }
    full_dates = sorted(
        {
            match.group(0)
            for row in evidence.values()
            for match in re.finditer(
                r"\b(?:January|February|March|April|May|June|July|August|"
                r"September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
                str(row.get("text") or ""),
            )
        }
    )
    date_failure = {
        "sample_id": date_id,
        "r12_answer": r12[date_id].get("final_answer", ""),
        "r21_answer": date_row.get("final_answer", ""),
        "binding_value": date_binding.get("bound_value", ""),
        "binding_evidence_ids": sorted(binding_evidence_ids),
        "answer_type": (date_binding.get("question_slot_parser") or {}).get(
            "answer_type", ""
        ),
        "full_dates_in_retrieved_evidence": full_dates,
        "root_cause": (
            "the generic verifier bound a bare year even though the same local "
            "final-hop evidence contained one more specific full date"
        ),
        "recommended_fix": (
            "for a date target and a bare-year candidate, promote only a unique "
            "same-year full date from the binding evidence IDs; otherwise fail closed"
        ),
    }

    result = {
        "status": "partial_gate_failed",
        "completed": len(r21_rows),
        "total": 12,
        "partial_metrics": evaluate_records(r21_rows, run_name="r21_partial_8"),
        "completed_gain_count": len(completed_gain_ids),
        "retained_gain_count": len(retained_gains),
        "retained_gain_ids": retained_gains,
        "completed_loss_count": len(completed_loss_ids),
        "recovered_loss_count": len(recovered_losses),
        "recovered_loss_ids": recovered_losses,
        "hard_gate_failed": len(retained_gains) < len(completed_gain_ids),
        "failure_slices": {
            "ordinal_surface_conflict": ordinal_failure,
            "date_granularity_collapse": date_failure,
            "external_endpoint": {
                "status": "blocked",
                "error": "HTTP 403 Forbidden",
                "first_failure_after_completed": 8,
                "retry_added_rows": 0,
                "methodological_interpretation": "none",
            },
        },
        "decision": (
            "Do not launch phase 2. Repair ordinal equivalence and unique local "
            "date precision as explicit generic-compatibility invariants, validate "
            "offline, then retry the same fixed 12-case gate when the endpoint is available."
        ),
    }

    json_output = Path(args.json_output)
    md_output = Path(args.md_output)
    if not args.overwrite and (json_output.exists() or md_output.exists()):
        raise FileExistsError("refusing to overwrite existing analysis outputs")
    json_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    metrics = result["partial_metrics"]["methods"]["claim_risk"]
    md_output.write_text(
        "\n".join(
            [
                "# R21 Partial Failure Analysis",
                "",
                "## Verdict",
                "",
                "R21 is an incomplete 8/12 run and has already failed the fixed gate. "
                "It retains four of five completed gains and recovers two of three "
                "completed losses; phase 2 is not authorized.",
                "",
                "## Partial Metrics (Not Full-Gate Metrics)",
                "",
                f"- Accuracy: {metrics['overall_acc']:.4f}",
                f"- Answer F1: {metrics['answer_f1']:.4f}",
                f"- Coverage: {metrics['coverage']:.4f}",
                f"- Final unsupported: {metrics['final_answered_unsupported_rate']:.4f}",
                "",
                "## Failure 1: False Ordinal Conflict",
                "",
                "`18th century` and `18th` were treated as different bound objects. "
                "The reducer emitted `competing_bound_object_conflict` and the "
                "no-fallback lane safely abstained. This is a type-aware identity bug, "
                "not a reason to relax hard-conflict safety.",
                "",
                "## Failure 2: Date Granularity Collapse",
                "",
                f"The verifier emitted `2011`, while retrieved binding evidence contains "
                f"the unique full date `{', '.join(full_dates)}`. A generic date target "
                "must not lose available day-level precision.",
                "",
                "## External Failure",
                "",
                "SiliconFlow returned HTTP 403 after eight rows and again before the "
                "retry could add a row. This is recorded as an endpoint failure, not a "
                "method result.",
                "",
                "## Decision",
                "",
                result["decision"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
