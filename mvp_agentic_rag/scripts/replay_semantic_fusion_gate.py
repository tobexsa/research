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
from mvp_agentic_rag.slot_execution_state import (
    FinalCandidateState,
    HopExecutionState,
    SlotExecutionState,
)
from mvp_agentic_rag.state_controller import FusionLaneRouter


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


def _state_from_record(record: dict) -> SlotExecutionState:
    hops = tuple(
        HopExecutionState(
            hop_id=str(item.get("hop_id") or ""),
            semantic_key=str(item.get("semantic_key") or ""),
            hop_index=int(item.get("hop_index") or 0),
            subject=str(item.get("subject") or ""),
            relation=str(item.get("relation") or ""),
            object_value=str(item.get("object_value") or ""),
            status=str(item.get("status") or "unresolved"),
            is_final_hop=bool(item.get("is_final_hop", False)),
            is_critical=bool(item.get("is_critical", False)),
            dependency_hop_ids=tuple(item.get("dependency_hop_ids") or ()),
            evidence_ids=tuple(item.get("evidence_ids") or ()),
            missing_requirements=tuple(item.get("missing_requirements") or ()),
            confidence=float(item.get("confidence") or 0.0),
            source=str(item.get("source") or ""),
            last_updated_round=int(item.get("last_updated_round") or 0),
            subject_entity_id=str(item.get("subject_entity_id") or ""),
            subject_type=str(item.get("subject_type") or "entity"),
            relation_id=str(item.get("relation_id") or ""),
            expected_object_type=str(item.get("expected_object_type") or "entity"),
            object_entity_id=str(item.get("object_entity_id") or ""),
        )
        for item in record.get("hops", [])
    )
    candidates = tuple(
        FinalCandidateState(
            normalized_value=str(item.get("normalized_value") or ""),
            value=str(item.get("value") or ""),
            source_hop_id=str(item.get("source_hop_id") or ""),
            evidence_ids=tuple(item.get("evidence_ids") or ()),
            status=str(item.get("status") or "observed"),
            typed_reject_category=str(item.get("typed_reject_category") or ""),
            rejection_reason=str(item.get("rejection_reason") or ""),
            preserved=bool(item.get("preserved", False)),
            first_seen_round=int(item.get("first_seen_round") or 0),
            last_seen_round=int(item.get("last_seen_round") or 0),
        )
        for item in record.get("candidates", [])
    )
    return SlotExecutionState(
        sample_id=str(record.get("sample_id") or ""),
        topology_status=str(record.get("topology_status") or "topology_unavailable"),
        round_idx=int(record.get("round_idx") or 0),
        hops=hops,
        candidates=candidates,
        active_candidate_key=str(record.get("active_candidate_key") or ""),
        first_critical_missing_hop_id=str(
            record.get("first_critical_missing_hop_id") or ""
        ),
        completed_hop_ids=tuple(record.get("completed_hop_ids") or ()),
        conflict_hop_ids=tuple(record.get("conflict_hop_ids") or ()),
        no_progress_count=int(record.get("no_progress_count") or 0),
        last_repair_target_hop_id=str(
            record.get("last_repair_target_hop_id") or ""
        ),
        state_fingerprint=str(record.get("state_fingerprint") or ""),
        topology_diagnostic=dict(record.get("topology_diagnostic") or {}),
        topology_version=int(record.get("topology_version") or 0),
        topology_fingerprint=str(record.get("topology_fingerprint") or ""),
    )


def _with_current_provenance(step: dict) -> dict:
    record = dict(step.get("slot_execution_state_after") or {})
    diagnostic = dict(record.get("topology_diagnostic") or {})
    binding = dict(
        step.get("slot_binding_verifier_result")
        or step.get("slot_state_binding_verifier_result")
        or {}
    )
    structured = dict(binding.get("structured_output") or {})
    deterministic = str(structured.get("deterministic_binding_applied") or "")
    if deterministic:
        diagnostic["deterministic_binding_applied"] = deterministic
    binding_diagnostic = dict(binding.get("topology_diagnostic") or {})
    if binding_diagnostic.get("evidence_certificate_binding") is True:
        diagnostic["evidence_certificate_binding"] = True
    record["topology_diagnostic"] = diagnostic
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the fixed 12-case gate with the runtime fusion router."
    )
    parser.add_argument(
        "--gate", default="data/musique_semantic_fusion_gain_loss12_20260714.jsonl"
    )
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
        "--json-output",
        default="analysis/semantic_fusion_gain_loss12_replay_20260714.json",
    )
    parser.add_argument(
        "--md-output",
        default="analysis/semantic_fusion_gain_loss12_replay_20260714.md",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    gate_rows = _load_jsonl(Path(args.gate))
    gate_ids = [str(row.get("id") or "") for row in gate_rows]
    expected = GAIN_IDS | LOSS_IDS
    if len(gate_ids) != 12 or len(set(gate_ids)) != 12 or set(gate_ids) != expected:
        raise ValueError("fixed gate membership or uniqueness changed")

    r12 = {row["id"]: row for row in _load_jsonl(Path(args.r12))}
    r20 = {row["id"]: row for row in _load_jsonl(Path(args.r20))}
    router = FusionLaneRouter()
    records = []
    lane_counts = Counter()
    for sample_id in gate_ids:
        lane_records = []
        for step in r20[sample_id]["trajectory"]:
            state = _state_from_record(_with_current_provenance(step))
            decision = router.classify(state)
            lane_counts[decision.lane] += 1
            lane_records.append(
                {
                    "round": int(step.get("round") or 0),
                    "action": str(step.get("action") or ""),
                    **decision.to_record(),
                }
            )
        records.append(
            {
                "sample_id": sample_id,
                "group": "gain" if sample_id in GAIN_IDS else "loss",
                "hop": int(r20[sample_id].get("hop") or 0),
                "gold_answer": r20[sample_id].get("gold_answer", ""),
                "r12_answer": r12[sample_id].get("final_answer", ""),
                "r12_correct": _correct(r12[sample_id]),
                "r20_answer": r20[sample_id].get("final_answer", ""),
                "r20_correct": _correct(r20[sample_id]),
                "lane_trace": lane_records,
            }
        )

    summary = {
        "gate_count": len(records),
        "gain_count": sum(item["group"] == "gain" for item in records),
        "loss_count": sum(item["group"] == "loss" for item in records),
        "lane_step_counts": dict(sorted(lane_counts.items())),
        "router_input_contract": "SlotExecutionState only; no sample/gold fields",
        "records": records,
        "interpretation": (
            "This replay audits separability and safety signals only. It does not "
            "claim a fused answer because the live fusion changes which verifier "
            "protocol is called before later state exists."
        ),
    }

    json_output = Path(args.json_output)
    md_output = Path(args.md_output)
    if not args.overwrite and (json_output.exists() or md_output.exists()):
        raise FileExistsError("refusing to overwrite existing replay outputs")
    json_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Semantic Fusion Gain/Loss-12 Replay Audit",
        "",
        "This is a structural replay of stored R20 states, not a fused outcome run.",
        "",
        "| Group | Sample | Hop | R12 | R20 | R20 lane trace |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in records:
        trace = " -> ".join(step["lane"] for step in item["lane_trace"])
        lines.append(
            f"| {item['group']} | `{item['sample_id']}` | {item['hop']} | "
            f"{item['r12_answer'] or 'abstain'} | {item['r20_answer'] or 'abstain'} | {trace} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The router consumes only canonical runtime state.",
            "- Stored R20 replay can validate certificate/no-fallback separation,",
            "  but cannot simulate the R12-compatible verifier outputs that the live",
            "  Fusion run will produce before strict-certificate escalation.",
            "- The real 12-case gate remains the decisive phase-1 result.",
            "",
        ]
    )
    md_output.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
