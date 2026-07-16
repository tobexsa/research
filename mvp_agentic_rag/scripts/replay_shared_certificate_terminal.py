from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput
from mvp_agentic_rag.slot_binding_verifier import (
    OrderedHopBindingResult,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    SlotBoundEntailmentResult,
)
from mvp_agentic_rag.slot_execution_state import SlotExecutionState
from scripts.replay_semantic_fusion_gate import (
    _state_from_record,
    _with_current_provenance,
)
from scripts.replay_typed_hop_state import (
    _binding_record,
    _terminal_invariant_violations,
)


@dataclass(frozen=True)
class FrozenTerminalInput:
    state: SlotExecutionState
    state_record: dict[str, Any]
    verifier_output: VerifierOutput | None
    verifier_record: dict[str, Any]
    binding_result: SlotBindingResult | None
    binding_record: dict[str, Any]
    local_evidence_ids: frozenset[str]
    proposal_action: str
    budget_remaining: int
    repair_metadata: dict[str, Any]
    preterminal_metadata: dict[str, Any]
    terminal_step: dict[str, Any]
    input_digest_sha256: str


class _EmptyRetriever:
    def search(self, query: str, top_k: int) -> list:
        return []


def _agent(*, strict_enabled: bool) -> ClaimRiskAgent:
    return ClaimRiskAgent(
        _EmptyRetriever(),
        config={
            "claim_evidence_slot_ledger": True,
            "claim_evidence_ordered_hop_binding_gate": True,
            "claim_evidence_slot_binding_verifier": True,
            "slot_binding_verifier_backend": "fake_llm",
            "slot_binding_verifier_fake_response": "{}",
            "claim_evidence_typed_target_slot_binder": True,
            "repair_planner_v1": True,
            "claim_risk_answer_safety_guard": True,
            "claim_evidence_monotonic_slot_state_v1": True,
            "claim_evidence_typed_hop_update_protocol_v1": True,
            "claim_evidence_state_controller_v1": True,
            "claim_evidence_state_controller_enforce_v1": True,
            "claim_evidence_strict_certificate_generic_compatibility_v1": True,
            "claim_evidence_fusion_strict_certificate_enabled": strict_enabled,
        },
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _verifier_output_from_record(record: dict[str, Any]) -> VerifierOutput | None:
    if not record:
        return None
    claims = [
        ClaimAssessment(
            claim=str(item.get("claim") or ""),
            status=str(item.get("status") or "unclear"),
            evidence_ids=[str(value) for value in item.get("evidence_ids", [])],
            missing_evidence=str(item.get("missing_evidence") or ""),
            is_critical=bool(item.get("is_critical", False)),
        )
        for item in record.get("claims", [])
        if isinstance(item, dict)
    ]
    return VerifierOutput(
        claims=claims,
        overall_sufficiency=str(record.get("overall_sufficiency") or "unclear"),
        need_more_evidence=bool(record.get("need_more_evidence", False)),
        suggested_query=str(record.get("suggested_query") or ""),
        risk_score=float(record.get("risk_score") or 0.0),
        expected_gain=float(record.get("expected_gain") or 0.0),
        final_target_match=(
            bool(record["final_target_match"])
            if "final_target_match" in record
            else None
        ),
        answer_slot=str(record.get("answer_slot") or ""),
    )


def _binding_result_from_record(record: dict[str, Any]) -> SlotBindingResult | None:
    if not record:
        return None
    ordered_record = record.get("ordered_hop_binding")
    ordered_record = ordered_record if isinstance(ordered_record, dict) else {}
    set_record = record.get("set_level_sufficiency")
    set_record = set_record if isinstance(set_record, dict) else {}
    entailment_record = record.get("slot_entailment")
    entailment_record = (
        entailment_record if isinstance(entailment_record, dict) else {}
    )
    return SlotBindingResult(
        slot_name=str(record.get("slot_name") or "final_target"),
        supports_slot=bool(record.get("supports_slot", False)),
        bound_value=str(record.get("bound_value") or ""),
        evidence_ids=[str(value) for value in record.get("evidence_ids", [])],
        slot_relation_match=bool(record.get("slot_relation_match", False)),
        answer_type_match=bool(record.get("answer_type_match", False)),
        reason=str(record.get("reason") or ""),
        ordered_hop_binding=OrderedHopBindingResult(
            filled_hop_index=int(ordered_record.get("filled_hop_index") or 0),
            final_hop_index=int(ordered_record.get("final_hop_index") or 0),
            final_relation=str(ordered_record.get("final_relation") or ""),
            final_relation_object=str(
                ordered_record.get("final_relation_object") or ""
            ),
            candidate_is_final_relation_object=bool(
                ordered_record.get("candidate_is_final_relation_object", False)
            ),
            missing_critical_hops=[
                str(value)
                for value in ordered_record.get("missing_critical_hops", [])
            ],
            bound_bridge_values=[
                str(value) for value in ordered_record.get("bound_bridge_values", [])
            ],
            chain_complete=bool(ordered_record.get("chain_complete", False)),
            topology_version=int(ordered_record.get("topology_version") or 0),
            topology_fingerprint=str(
                ordered_record.get("topology_fingerprint") or ""
            ),
            missing_requirements=[
                dict(value)
                for value in ordered_record.get("missing_requirements", [])
                if isinstance(value, dict)
            ],
        ),
        slot_entailment=SlotBoundEntailmentResult(
            question=str(entailment_record.get("question") or ""),
            final_slot=str(entailment_record.get("final_slot") or "final_target"),
            candidate=str(entailment_record.get("candidate") or ""),
            evidence_ids=[
                str(value) for value in entailment_record.get("evidence_ids", [])
            ],
            entails_answer=bool(
                entailment_record.get(
                    "entails_answer",
                    entailment_record.get("entailed", False),
                )
            ),
            contradicted=bool(entailment_record.get("contradicted", False)),
            entailment_confidence=float(
                entailment_record.get("entailment_confidence") or 0.0
            ),
            hypothesis=str(entailment_record.get("hypothesis") or ""),
            reason=str(entailment_record.get("reason") or ""),
            failure_reason=str(entailment_record.get("failure_reason") or "unknown"),
        ),
        set_level_sufficiency=SetLevelSufficiencyResult(
            final_slot_covered=bool(set_record.get("final_slot_covered", False)),
            all_required_hops_covered=bool(
                set_record.get("all_required_hops_covered", False)
            ),
            missing_critical_hops=[
                str(value) for value in set_record.get("missing_critical_hops", [])
            ],
            noncritical_gaps=[
                str(value) for value in set_record.get("noncritical_gaps", [])
            ],
            missing_noncritical_hops=[
                str(value)
                for value in set_record.get("missing_noncritical_hops", [])
            ],
            conflict_on_final_slot=bool(
                set_record.get("conflict_on_final_slot", False)
            ),
            conflict_on_bridge=bool(set_record.get("conflict_on_bridge", False)),
            evidence_set_sufficient=bool(
                set_record.get("evidence_set_sufficient", False)
            ),
            sufficiency_confidence=float(
                set_record.get("sufficiency_confidence") or 0.0
            ),
            uncertainty=float(set_record.get("uncertainty", 1.0)),
        ),
        repair_target=(
            dict(record.get("repair_target"))
            if isinstance(record.get("repair_target"), dict)
            else {}
        ),
        structured_output=(
            dict(record.get("structured_output"))
            if isinstance(record.get("structured_output"), dict)
            else {}
        ),
        topology_diagnostic=(
            dict(record.get("topology_diagnostic"))
            if isinstance(record.get("topology_diagnostic"), dict)
            else {}
        ),
    )


def _sha256_json(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _extract_terminal_input(row: dict[str, Any]) -> FrozenTerminalInput:
    trajectory = row.get("trajectory")
    if not isinstance(trajectory, list) or not trajectory:
        raise ValueError("row has no terminal trajectory step")
    if not isinstance(trajectory[-1], dict):
        raise ValueError("terminal trajectory step is not an object")
    step = dict(trajectory[-1])
    state_record = _with_current_provenance(step)
    state = _state_from_record(state_record)
    verifier_record = (
        dict(step.get("verifier_output"))
        if isinstance(step.get("verifier_output"), dict)
        else {}
    )
    binding_record = dict(_binding_record(step))
    local_evidence_ids = frozenset(
        str(value)
        for item in trajectory
        if isinstance(item, dict)
        for value in item.get("retrieved_ids", [])
        if str(value)
    )
    proposal_action = str(
        step.get("state_controller_terminal_original_action")
        or step.get("action")
        or row.get("final_action")
        or "abstain"
    )
    repair_metadata = {
        key: step[key]
        for key in (
            "repair_next_query",
            "repair_target_valid",
            "repair_target_invalid_reasons",
        )
        if key in step
    }
    preterminal_metadata = {
        key: step[key]
        for key in (
            "controller_policy_v1_original_action",
            "controller_policy_v1_blocked_reason",
            "answer_safety_guard_original_action",
            "answer_safety_guard_reason",
        )
        if key in step
    }
    digest_record = {
        "state": state_record,
        "verifier_output": verifier_record,
        "binding_result": binding_record,
        "local_evidence_ids": sorted(local_evidence_ids),
        "proposal_action": proposal_action,
        "budget_remaining": int(step.get("budget_remaining") or 0),
        "repair_metadata": repair_metadata,
        "preterminal_metadata": preterminal_metadata,
    }
    return FrozenTerminalInput(
        state=state,
        state_record=state_record,
        verifier_output=_verifier_output_from_record(verifier_record),
        verifier_record=verifier_record,
        binding_result=_binding_result_from_record(binding_record),
        binding_record=binding_record,
        local_evidence_ids=local_evidence_ids,
        proposal_action=proposal_action,
        budget_remaining=int(step.get("budget_remaining") or 0),
        repair_metadata=repair_metadata,
        preterminal_metadata=preterminal_metadata,
        terminal_step=step,
        input_digest_sha256=_sha256_json(digest_record),
    )


def _replay_once(
    frozen: FrozenTerminalInput,
    *,
    strict_enabled: bool,
) -> dict[str, Any]:
    agent = _agent(strict_enabled=strict_enabled)
    action, metadata = agent._apply_state_controller_terminal(
        frozen.proposal_action,
        state=frozen.state,
        repair_metadata=dict(frozen.repair_metadata),
        budget_remaining=frozen.budget_remaining,
        preterminal_metadata=dict(frozen.preterminal_metadata),
        verifier_output=frozen.verifier_output,
        binding_result=frozen.binding_result,
        local_evidence_ids=set(frozen.local_evidence_ids),
    )
    audit_step = {
        **frozen.terminal_step,
        **metadata,
        "action": action,
    }
    violations = _terminal_invariant_violations(
        {"final_action": action, "trajectory": [audit_step]},
        frozen.state,
        set(frozen.local_evidence_ids),
    )
    return {
        "strict_enabled": strict_enabled,
        "lane": str(metadata.get("semantic_fusion_lane") or ""),
        "lane_reason": str(metadata.get("semantic_fusion_reason") or ""),
        "strict_certificate_reason": str(
            metadata.get("semantic_fusion_strict_certificate_reason") or ""
        ),
        "proposal_action": frozen.proposal_action,
        "action": action,
        "terminal_guard": bool(
            metadata.get("state_controller_terminal_guard", False)
        ),
        "terminal_downgrade": bool(
            metadata.get("state_controller_terminal_downgrade", False)
        ),
        "block_reasons": list(
            metadata.get("state_controller_terminal_block_reasons") or []
        ),
        "terminal_reason": str(
            metadata.get("state_controller_terminal_reason") or ""
        ),
        "terminal_invariant_violations": list(violations),
    }


def replay_row(row: dict[str, Any], *, repeat_count: int = 2) -> dict[str, Any]:
    if repeat_count < 2:
        raise ValueError("repeat_count must be at least 2")
    frozen = _extract_terminal_input(row)
    repeated = [
        {
            "strict_on": _replay_once(frozen, strict_enabled=True),
            "strict_off": _replay_once(frozen, strict_enabled=False),
        }
        for _ in range(repeat_count)
    ]
    deterministic = all(value == repeated[0] for value in repeated[1:])
    strict_on = repeated[0]["strict_on"]
    strict_off = repeated[0]["strict_off"]
    return {
        "sample_id": str(row.get("id") or ""),
        "input_digest_sha256": frozen.input_digest_sha256,
        "repeat_count": repeat_count,
        "deterministic_replay": deterministic,
        "strict_eligible": strict_on["lane"] == "strict_certificate",
        "action_changed": strict_on["action"] != strict_off["action"],
        "strict_on": strict_on,
        "strict_off": strict_off,
    }


def replay_file(path: Path, *, repeat_count: int = 2) -> dict[str, Any]:
    rows = _load_jsonl(path)
    sample_ids = [str(row.get("id") or "") for row in rows]
    if not rows:
        raise ValueError("trajectory file is empty")
    if any(not sample_id for sample_id in sample_ids):
        raise ValueError("trajectory row is missing an id")
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("trajectory sample ids are not unique")
    records = [replay_row(row, repeat_count=repeat_count) for row in rows]
    lane_counts_on = Counter(record["strict_on"]["lane"] for record in records)
    lane_counts_off = Counter(record["strict_off"]["lane"] for record in records)
    strict_on_violations = sum(
        len(record["strict_on"]["terminal_invariant_violations"])
        for record in records
    )
    strict_off_violations = sum(
        len(record["strict_off"]["terminal_invariant_violations"])
        for record in records
    )
    deterministic = all(record["deterministic_replay"] for record in records)
    return {
        "status": "complete" if deterministic else "rejected_nondeterministic",
        "source": str(path),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "row_count": len(records),
        "unique_sample_count": len(set(sample_ids)),
        "repeat_count": repeat_count,
        "deterministic_replay": deterministic,
        "strict_eligible_count": sum(
            bool(record["strict_eligible"]) for record in records
        ),
        "action_change_count": sum(
            bool(record["action_changed"]) for record in records
        ),
        "action_change_samples": [
            record["sample_id"] for record in records if record["action_changed"]
        ],
        "strict_on_lane_counts": dict(sorted(lane_counts_on.items())),
        "strict_off_lane_counts": dict(sorted(lane_counts_off.items())),
        "strict_on_terminal_invariant_violation_count": strict_on_violations,
        "strict_off_terminal_invariant_violation_count": strict_off_violations,
        "gate_pass": bool(
            deterministic
            and strict_on_violations == 0
            and strict_off_violations == 0
        ),
        "routing_input_contract": (
            "Frozen runtime state, verifier, binding, proposal, budget, repair "
            "metadata, and retrieved evidence IDs only; no gold fields"
        ),
        "records": records,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Shared-Certificate Terminal Replay",
        "",
        f"- Source: `{result['source']}`",
        f"- Rows / unique: `{result['row_count']} / {result['unique_sample_count']}`",
        f"- Repeat count: `{result['repeat_count']}`",
        f"- Deterministic replay: `{str(result['deterministic_replay']).lower()}`",
        f"- Strict eligible: `{result['strict_eligible_count']}`",
        f"- Strict-on/off action changes: `{result['action_change_count']}`",
        (
            "- Strict-on terminal invariant violations: "
            f"`{result['strict_on_terminal_invariant_violation_count']}`"
        ),
        (
            "- Strict-off terminal invariant violations: "
            f"`{result['strict_off_terminal_invariant_violation_count']}`"
        ),
        f"- Gate pass: `{str(result['gate_pass']).lower()}`",
        "",
        "| Sample | Eligible | Strict-on lane/action | Strict-off lane/action | Changed | Input digest |",
        "|---|---:|---|---|---:|---|",
    ]
    for record in result["records"]:
        lines.append(
            f"| `{record['sample_id']}` | "
            f"{str(record['strict_eligible']).lower()} | "
            f"{record['strict_on']['lane']} / {record['strict_on']['action']} | "
            f"{record['strict_off']['lane']} / {record['strict_off']['action']} | "
            f"{str(record['action_changed']).lower()} | "
            f"`{record['input_digest_sha256'][:12]}...` |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            f"{result['routing_input_contract']}.",
            "",
            "The replay reports sample IDs for audit only. It does not read gold",
            "answers, decompositions, or gold support to select a lane or action.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Replay byte-identical frozen terminal certificates with strict "
            "acceptance enabled and disabled."
        )
    )
    parser.add_argument("trajectory_path", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    parser.add_argument("--repeat-count", type=int, default=2)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.overwrite and (args.json_output.exists() or args.md_output.exists()):
        raise FileExistsError("refusing to overwrite existing replay outputs")
    result = replay_file(args.trajectory_path, repeat_count=args.repeat_count)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.md_output.write_text(_render_markdown(result), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
