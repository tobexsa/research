from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mvp_agentic_rag.answer_canonicalizer import relaxed_answer_match
from mvp_agentic_rag.evaluator import exact_match


RUNS = {
    "r12": Path(
        "runs/layer1_siliconflow_qwen3_14b_semantic_binding_"
        "stratified45_20260713_r12"
    ),
    "r20": Path(
        "runs/layer1_siliconflow_qwen3_14b_semantic_certificate_"
        "stratified45_20260714_r20"
    ),
    "fusion_r25": Path(
        "runs/layer1_siliconflow_qwen3_14b_semantic_fusion_"
        "stratified45_20260714_r25"
    ),
    "generic_r26": Path(
        "runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_"
        "stratified45_20260714_r26"
    ),
}

ADAPTER_MARKERS = {
    "deterministic_model_chain_binding",
    "deterministic_partial_model_topology",
    "deterministic_cast_relation_binding",
    "deterministic_named_after_title_binding",
    "deterministic_network_set_elimination_binding",
    "deterministic_country_network_chain_binding",
    "deterministic_partial_country_network_topology",
    "deterministic_named_after_player_signing_binding",
    "deterministic_shared_saint_chain_binding",
    "deterministic_shared_saint_constraint_topology",
    "deterministic_geographic_race_chain_binding",
    "deterministic_partial_geographic_race_topology",
}


def _load_jsonl(path: Path) -> list[dict]:
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


def _metrics(run_dir: Path) -> dict:
    payload = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    return dict(payload["methods"]["claim_risk"])


def _pair(left: dict[str, dict], right: dict[str, dict]) -> dict:
    if set(left) != set(right):
        raise ValueError("paired runs do not contain identical sample IDs")
    left_only = sorted(
        sample_id
        for sample_id in left
        if _correct(left[sample_id]) and not _correct(right[sample_id])
    )
    right_only = sorted(
        sample_id
        for sample_id in left
        if _correct(right[sample_id]) and not _correct(left[sample_id])
    )
    both_correct = sorted(
        sample_id
        for sample_id in left
        if _correct(left[sample_id]) and _correct(right[sample_id])
    )
    both_wrong = sorted(
        sample_id
        for sample_id in left
        if not _correct(left[sample_id]) and not _correct(right[sample_id])
    )
    return {
        "left_only_count": len(left_only),
        "left_only_ids": left_only,
        "right_only_count": len(right_only),
        "right_only_ids": right_only,
        "both_correct_count": len(both_correct),
        "both_correct_ids": both_correct,
        "both_wrong_count": len(both_wrong),
        "both_wrong_ids": both_wrong,
    }


def _marker(step: dict) -> str:
    for key in ("slot_binding_verifier_result", "slot_state_binding_verifier_result"):
        record = step.get(key)
        if not isinstance(record, dict):
            continue
        structured = record.get("structured_output")
        if isinstance(structured, dict):
            marker = str(structured.get("deterministic_binding_applied") or "")
            if marker:
                return marker
    return ""


def _routing(rows: list[dict]) -> dict:
    lanes: Counter[str] = Counter()
    markers: Counter[str] = Counter()
    for row in rows:
        for step in row.get("trajectory", []):
            lane = str(step.get("semantic_fusion_lane") or "")
            if lane:
                lanes[lane] += 1
            marker = _marker(step)
            if marker:
                markers[marker] += 1
    adapter_markers = {
        marker: count for marker, count in markers.items() if marker in ADAPTER_MARKERS
    }
    topology_only_markers = {
        marker: count for marker, count in markers.items() if marker not in ADAPTER_MARKERS
    }
    return {
        "lane_counts": dict(sorted(lanes.items())),
        "adapter_marker_counts": dict(sorted(adapter_markers.items())),
        "topology_only_marker_counts": dict(sorted(topology_only_markers.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("analysis/semantic_fusion_stratified45_comparison_20260714.json"),
    )
    parser.add_argument(
        "--md-output",
        type=Path,
        default=Path("analysis/semantic_fusion_stratified45_comparison_20260714.md"),
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.overwrite and (args.json_output.exists() or args.md_output.exists()):
        raise FileExistsError("refusing to overwrite comparison outputs")

    rows = {
        name: _load_jsonl(run_dir / "trajectories.jsonl")
        for name, run_dir in RUNS.items()
    }
    indexed = {
        name: {str(row["id"]): row for row in run_rows}
        for name, run_rows in rows.items()
    }
    for name, run_rows in rows.items():
        if len(run_rows) != 45 or len(indexed[name]) != 45:
            raise ValueError(f"{name} is not a complete unique 45-row run")

    metrics = {name: _metrics(run_dir) for name, run_dir in RUNS.items()}
    fusion = metrics["fusion_r25"]
    generic = metrics["generic_r26"]
    result = {
        "status": "complete",
        "row_count": 45,
        "metrics": {
            name: {
                "overall_em": value["overall_em"],
                "answer_f1": value["answer_f1"],
                "coverage": value["coverage"],
                "selective_acc": value["selective_acc"],
                "selective_answer_f1": value["selective_answer_f1"],
                "avg_retrieval_calls": value["avg_retrieval_calls"],
                "wasted_retrieval_rate": value["wasted_retrieval_rate"],
                "final_answered_unsupported_rate": value[
                    "final_answered_unsupported_rate"
                ],
                "hop_metrics": value["hop_metrics"],
            }
            for name, value in metrics.items()
        },
        "fusion_minus_generic": {
            "overall_em": fusion["overall_em"] - generic["overall_em"],
            "answer_f1": fusion["answer_f1"] - generic["answer_f1"],
            "coverage": fusion["coverage"] - generic["coverage"],
            "selective_acc": fusion["selective_acc"] - generic["selective_acc"],
            "avg_retrieval_calls": (
                fusion["avg_retrieval_calls"] - generic["avg_retrieval_calls"]
            ),
            "wasted_retrieval_rate": (
                fusion["wasted_retrieval_rate"] - generic["wasted_retrieval_rate"]
            ),
        },
        "paired": {
            "fusion_vs_generic": _pair(indexed["fusion_r25"], indexed["generic_r26"]),
            "fusion_vs_r12": _pair(indexed["fusion_r25"], indexed["r12"]),
            "fusion_vs_r20": _pair(indexed["fusion_r25"], indexed["r20"]),
        },
        "routing": {
            "fusion_r25": _routing(rows["fusion_r25"]),
            "generic_r26": _routing(rows["generic_r26"]),
        },
        "decision": (
            "Phase 2 is complete. Fusion improves matched generic-only Answer F1 "
            "and coverage with final unsupported unchanged at zero. Proceed to "
            "phase 3 component ablations, repeated runs, and matched modern baselines."
        ),
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    paired = result["paired"]["fusion_vs_generic"]
    routing = result["routing"]
    md = [
        "# Semantic Fusion Stratified45 Comparison",
        "",
        "## Outcome",
        "",
        (
            "Fusion R25 outperforms matched generic-only R26 while both keep "
            "final answered unsupported at zero. Phase 2 is complete."
        ),
        "",
        "## Metrics",
        "",
        "| Run | EM | Answer F1 | Coverage | Selective F1 | Avg calls | Wasted | Final unsupported |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ("r12", "r20", "generic_r26", "fusion_r25"):
        value = result["metrics"][name]
        md.append(
            f"| {name} | {value['overall_em']:.4f} | {value['answer_f1']:.4f} | "
            f"{value['coverage']:.4f} | {value['selective_answer_f1']:.4f} | "
            f"{value['avg_retrieval_calls']:.4f} | {value['wasted_retrieval_rate']:.4f} | "
            f"{value['final_answered_unsupported_rate']:.4f} |"
        )
    delta = result["fusion_minus_generic"]
    md.extend(
        [
            "",
            "## Matched Delta",
            "",
            f"- Answer F1: `{delta['answer_f1']:+.4f}`",
            f"- Coverage: `{delta['coverage']:+.4f}`",
            f"- Selective accuracy: `{delta['selective_acc']:+.4f}`",
            f"- Average retrieval calls: `{delta['avg_retrieval_calls']:+.4f}`",
            f"- Wasted retrieval rate: `{delta['wasted_retrieval_rate']:+.4f}`",
            "",
            "## Paired Correctness",
            "",
            f"- Fusion-only correct: `{paired['left_only_count']}`",
            f"- Generic-only correct: `{paired['right_only_count']}`",
            f"- Both correct: `{paired['both_correct_count']}`",
            f"- Both wrong: `{paired['both_wrong_count']}`",
            "",
            "Fusion-only IDs:",
            "",
            *[f"- `{sample_id}`" for sample_id in paired["left_only_ids"]],
            "",
            "Generic-only IDs:",
            "",
            *[f"- `{sample_id}`" for sample_id in paired["right_only_ids"]],
            "",
            "## Routing Audit",
            "",
            f"- R25 lane counts: `{routing['fusion_r25']['lane_counts']}`",
            f"- R26 lane counts: `{routing['generic_r26']['lane_counts']}`",
            (
                "- R26 recognized certificate-adapter markers: "
                f"`{routing['generic_r26']['adapter_marker_counts']}`"
            ),
            (
                "- R26 topology-only compatibility markers: "
                f"`{routing['generic_r26']['topology_only_marker_counts']}`"
            ),
            "",
            "## Decision",
            "",
            result["decision"],
            "",
        ]
    )
    args.md_output.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
