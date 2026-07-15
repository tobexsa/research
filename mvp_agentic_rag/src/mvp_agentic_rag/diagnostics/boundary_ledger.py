from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Iterable

from ..answer_canonicalizer import relaxed_answer_match
from ..evaluator import exact_match, normalize, token_f1


BOUNDARY_ORDER = {
    "ambiguous": -1,
    "E": 0,
    "C_form": 1,
    "C_align": 1,
    "V": 2,
    "P": 3,
    "O": 4,
    "none": 5,
}

_DIRECT_FINAL_CANDIDATE_KEYS = (
    "slot_ledger_candidate_answer",
    "preserved_final_candidate",
    "structured_final_candidate",
    "answer_extraction_repair_candidate",
    "wrong_target_replacement_candidate",
    "ordered_hop_chain_complete_final_object",
    "slot_binding_verifier_value",
)


def build_trajectory_ledger(
    source_id: str,
    trajectories: Iterable[dict[str, Any]],
    samples: Iterable[dict[str, Any]],
    *,
    ambiguity_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    sample_map = _sample_map(samples)
    ambiguity_overrides = ambiguity_overrides or {}
    ledger: list[dict[str, Any]] = []
    for trajectory_record in trajectories:
        sample_id = str(trajectory_record.get("id") or trajectory_record.get("sample_id") or "")
        sample = _resolved_sample(
            sample_id,
            trajectory_record,
            sample_map.get(sample_id),
            ambiguity_overrides.get(sample_id),
        )
        steps = list(trajectory_record.get("trajectory") or [])
        cumulative_retrieved: list[str] = []
        cumulative_retrieved_seen: set[str] = set()
        cumulative_candidates: list[dict[str, Any]] = []
        for index, step in enumerate(steps):
            for passage_id in step.get("retrieved_ids") or []:
                passage_id = str(passage_id or "").strip()
                if passage_id and passage_id not in cumulative_retrieved_seen:
                    cumulative_retrieved_seen.add(passage_id)
                    cumulative_retrieved.append(passage_id)
            is_terminal = index == len(steps) - 1
            current_candidates = extract_candidate_records(
                step,
                final_answer=str(trajectory_record.get("final_answer") or "") if is_terminal else "",
                include_final_answer=is_terminal and trajectory_record.get("final_action") == "answer",
            )
            cumulative_candidates = _merge_candidate_lists(cumulative_candidates, current_candidates)
            ledger.append(
                _build_boundary_record(
                    source_id=source_id,
                    source_kind="trajectory",
                    sample=sample,
                    step=step,
                    trajectory_record=trajectory_record,
                    round_index=int(step.get("round") or index + 1),
                    is_terminal=is_terminal,
                    cumulative_retrieved=cumulative_retrieved,
                    current_candidates=current_candidates,
                    cumulative_candidates=cumulative_candidates,
                    observable_through="P",
                    evidence_grade="observed_trajectory",
                )
            )
    return ledger


def build_fixed_evidence_ledger(
    source_id: str,
    gate_records: Iterable[dict[str, Any]],
    samples: Iterable[dict[str, Any]],
    *,
    ambiguity_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    sample_map = _sample_map(samples)
    ambiguity_overrides = ambiguity_overrides or {}
    ledger: list[dict[str, Any]] = []
    for gate_record in gate_records:
        sample_id = str(gate_record.get("id") or gate_record.get("sample_id") or "")
        trajectory_like = {
            "id": sample_id,
            "question": gate_record.get("question", ""),
            "gold_answer": gate_record.get("gold_answer", ""),
            "final_action": "",
            "final_answer": "",
        }
        sample = _resolved_sample(
            sample_id,
            trajectory_like,
            sample_map.get(sample_id),
            ambiguity_overrides.get(sample_id),
        )
        step = {
            "round": 1,
            "retrieved_ids": list(gate_record.get("evidence_ids") or []),
            "action": "",
            "budget_remaining": None,
            "slot_binding_verifier_result": dict(gate_record.get("binding_result") or {}),
            "verifier_output": {},
        }
        candidates = extract_candidate_records(step)
        for value in gate_record.get("candidate_values") or []:
            _add_candidate(
                candidates,
                value=value,
                source="fixed_gate.candidate_values",
                role="final_answer",
                relation="fills_final_slot",
                evidence_ids=gate_record.get("evidence_ids") or [],
                final_slot_signal=True,
            )
        candidates = _merge_candidate_lists([], candidates)
        record = _build_boundary_record(
            source_id=source_id,
            source_kind="fixed_evidence",
            sample=sample,
            step=step,
            trajectory_record=trajectory_like,
            round_index=1,
            is_terminal=True,
            cumulative_retrieved=list(gate_record.get("evidence_ids") or []),
            current_candidates=candidates,
            cumulative_candidates=candidates,
            observable_through="V",
            evidence_grade="observed_fixed_evidence",
        )
        record["fixed_evidence_probe"] = {
            "candidate_match_reported": bool(gate_record.get("candidate_match")),
            "parse_status": str(gate_record.get("parse_status") or "unknown"),
            "attempt_count": int(gate_record.get("attempt_count") or 0),
        }
        ledger.append(record)
    return ledger


def extract_candidate_records(
    step: dict[str, Any],
    *,
    final_answer: str = "",
    include_final_answer: bool = False,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in _DIRECT_FINAL_CANDIDATE_KEYS:
        _add_candidate(
            records,
            value=step.get(key),
            source=f"step.{key}",
            role="final_answer",
            relation="fills_final_slot",
            evidence_ids=step.get(f"{key}_evidence_ids") or [],
            final_slot_signal=True,
        )
    if include_final_answer:
        _add_candidate(
            records,
            value=final_answer,
            source="runtime.final_answer",
            role="final_answer",
            relation="fills_final_slot",
            evidence_ids=[],
            final_slot_signal=True,
        )
    for key, value in step.items():
        if not isinstance(value, dict) or not key.endswith("slot_binding_verifier_result"):
            continue
        source_prefix = "slot_binding" if key == "slot_binding_verifier_result" else key
        _extract_binding_candidates(records, value, source_prefix)
    return _merge_candidate_lists([], records)


def summarize_boundary_ledger(ledger: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(ledger)
    terminal_rows = [row for row in rows if row.get("is_terminal")]
    boundary_counts = Counter(str(row.get("first_loss_boundary") or "unknown") for row in rows)
    terminal_counts = Counter(str(row.get("first_loss_boundary") or "unknown") for row in terminal_rows)
    source_counts = Counter(str(row.get("source_id") or "unknown") for row in rows)
    evidence_counts = Counter(str(row.get("evidence_state") or "unknown") for row in rows)
    candidate_counts = Counter(str(row.get("candidate_state") or "unknown") for row in rows)
    verifier_counts = Counter(str(row.get("verifier_state") or "unknown") for row in rows)
    surface_near_match_count = sum(
        bool((row.get("candidate_state_details") or {}).get("surface_near_match_present"))
        for row in rows
    )
    terminal_surface_near_match_count = sum(
        bool((row.get("candidate_state_details") or {}).get("surface_near_match_present"))
        for row in terminal_rows
    )
    explicit_ambiguity_count = sum(
        str(row.get("first_loss_boundary") or "") == "ambiguous"
        and str(row.get("ambiguity_reason") or "") not in {"", "missing_supporting_passage_ids"}
        for row in rows
    )
    eligible_count = len(rows) - explicit_ambiguity_count
    labeled_count = sum(
        str(row.get("first_loss_boundary") or "unknown") not in {"ambiguous", "unknown"}
        for row in rows
    )
    non_ambiguous_count = sum(
        str(row.get("first_loss_boundary") or "unknown") != "ambiguous" for row in rows
    )
    observed_fixed = [row for row in rows if row.get("evidence_grade") == "observed_fixed_evidence"]
    fixed_correct = sum(bool(row.get("candidate_state_details", {}).get("correct_final_candidate_present")) for row in observed_fixed)
    return {
        "record_count": len(rows),
        "unique_question_count": len({str(row.get("sample_id") or "") for row in rows}),
        "terminal_record_count": len(terminal_rows),
        "source_counts": dict(sorted(source_counts.items())),
        "boundary_counts": dict(sorted(boundary_counts.items())),
        "terminal_boundary_counts": dict(sorted(terminal_counts.items())),
        "evidence_state_counts": dict(sorted(evidence_counts.items())),
        "candidate_state_counts": dict(sorted(candidate_counts.items())),
        "verifier_state_counts": dict(sorted(verifier_counts.items())),
        "surface_near_match_record_count": surface_near_match_count,
        "terminal_surface_near_match_record_count": terminal_surface_near_match_count,
        "explicit_ambiguity_count": explicit_ambiguity_count,
        "eligible_record_count": eligible_count,
        "label_coverage_count": labeled_count,
        "label_coverage_rate": labeled_count / eligible_count if eligible_count else 0.0,
        "non_ambiguous_record_count": non_ambiguous_count,
        "non_ambiguous_record_rate": non_ambiguous_count / len(rows) if rows else 0.0,
        "fixed_evidence_probe_count": len(observed_fixed),
        "fixed_evidence_correct_candidate_count": fixed_correct,
        "fixed_evidence_correct_candidate_rate": fixed_correct / len(observed_fixed) if observed_fixed else 0.0,
    }


def build_intervention_matrix(
    trajectory_ledger: Iterable[dict[str, Any]],
    fixed_evidence_ledger: Iterable[dict[str, Any]],
    *,
    target_count: int = 25,
) -> list[dict[str, Any]]:
    trajectory_rows = [
        row for row in trajectory_ledger if row.get("source_kind") == "trajectory"
    ]
    fixed_rows = {str(row.get("sample_id") or ""): row for row in fixed_evidence_ledger}
    anchors = _terminal_anchor_rows(trajectory_rows)
    selected = _select_intervention_anchors(anchors, set(fixed_rows), target_count)
    transitions = _observed_transition_map(trajectory_rows)
    matrix: list[dict[str, Any]] = []
    for anchor in selected:
        sample_id = str(anchor.get("sample_id") or "")
        fixed_row = fixed_rows.get(sample_id)
        matrix.append(
            {
                "intervention_id": f"ecvpo::{sample_id}",
                "sample_id": sample_id,
                "group_id": str(anchor.get("group_id") or sample_id),
                "question": str(anchor.get("question") or ""),
                "gold_answer": str(anchor.get("gold_answer") or ""),
                "baseline": _boundary_snapshot(anchor),
                "observed_fixed_evidence": _fixed_evidence_probe(anchor, fixed_row),
                "observed_trajectory_transition": transitions.get(
                    sample_id,
                    _empty_transition_probe(),
                ),
                "oracle_stage_restoration": _oracle_stage_restoration(anchor),
                "claim_scope": (
                    "Observed probes report stored executions; oracle restoration only tests the "
                    "factorized state contract and is not runtime recovery evidence."
                ),
            }
        )
    return matrix


def audit_grouped_splits(
    dev_records: Iterable[dict[str, Any]],
    test_records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    dev = list(dev_records)
    test = list(test_records)
    dev_ids = sorted({_record_sample_id(record) for record in dev if _record_sample_id(record)})
    test_ids = sorted({_record_sample_id(record) for record in test if _record_sample_id(record)})
    overlap = sorted(set(dev_ids) & set(test_ids))
    dev_parts = {part for sample_id in dev_ids for part in _decomposition_ids(sample_id)}
    test_parts = {part for sample_id in test_ids for part in _decomposition_ids(sample_id)}
    source_runs_dev = {str(record.get("source_run") or "") for record in dev if record.get("source_run")}
    source_runs_test = {str(record.get("source_run") or "") for record in test if record.get("source_run")}
    return {
        "dev_record_count": len(dev),
        "test_record_count": len(test),
        "dev_unique_question_count": len(dev_ids),
        "test_unique_question_count": len(test_ids),
        "overlapping_question_count": len(overlap),
        "overlapping_question_ids": overlap,
        "overlapping_decomposition_ids": sorted(dev_parts & test_parts),
        "overlapping_source_runs": sorted(source_runs_dev & source_runs_test),
        "question_group_split_is_clean": not overlap,
        "recommended_group_key": "sample_id with all rounds, source runs, and perturbations co-located",
    }


def _build_boundary_record(
    *,
    source_id: str,
    source_kind: str,
    sample: dict[str, Any],
    step: dict[str, Any],
    trajectory_record: dict[str, Any],
    round_index: int,
    is_terminal: bool,
    cumulative_retrieved: list[str],
    current_candidates: list[dict[str, Any]],
    cumulative_candidates: list[dict[str, Any]],
    observable_through: str,
    evidence_grade: str,
) -> dict[str, Any]:
    gold_values = _gold_values(sample)
    ambiguity_reason = _ambiguity_reason(sample.get("metadata") or {})
    supporting_ids = [str(value) for value in sample.get("supporting_passage_ids") or []]
    retrieved_set = set(cumulative_retrieved)
    support_seen = [value for value in supporting_ids if value in retrieved_set]
    if ambiguity_reason:
        evidence_state = "ambiguous"
    elif not supporting_ids:
        evidence_state = "ambiguous"
        ambiguity_reason = "missing_supporting_passage_ids"
    elif set(supporting_ids).issubset(retrieved_set):
        evidence_state = "complete"
    else:
        evidence_state = "incomplete"

    candidate_details = _candidate_state_details(current_candidates, gold_values)
    verifier = _verifier_state(step, candidate_details, gold_values)
    policy = _policy_state(
        step,
        trajectory_record,
        is_terminal=is_terminal,
        gold_values=gold_values,
        observable_through=observable_through,
    )
    row = {
        "ledger_id": f"{source_id}::{sample['id']}::r{round_index}",
        "source_id": source_id,
        "source_kind": source_kind,
        "evidence_grade": evidence_grade,
        "sample_id": str(sample["id"]),
        "group_id": str(sample["id"]),
        "question": str(sample.get("question") or ""),
        "gold_answer": str(sample.get("answer") or ""),
        "answer_aliases": list(sample.get("answer_aliases") or []),
        "round": round_index,
        "is_terminal": is_terminal,
        "observable_through": observable_through,
        "runtime_action": str(step.get("action") or ""),
        "budget_remaining": step.get("budget_remaining"),
        "evidence_state": evidence_state,
        "ambiguity_reason": ambiguity_reason,
        "oracle_evidence": {
            "supporting_passage_ids": supporting_ids,
            "retrieved_supporting_ids": support_seen,
            "retrieved_ids_cumulative": list(cumulative_retrieved),
            "coverage_count": len(support_seen),
            "required_count": len(supporting_ids),
            "coverage_rate": len(support_seen) / len(supporting_ids) if supporting_ids else 0.0,
            "uses_gold_support": True,
        },
        "candidate_state": candidate_details["candidate_state"],
        "candidate_state_details": candidate_details,
        "candidate_records": current_candidates,
        "cumulative_candidate_records": cumulative_candidates,
        "verifier_state": verifier["verifier_state"],
        "verifier_disposition": verifier,
        "policy_state": policy["policy_state"],
        "policy_disposition": policy,
        "outcome_state": policy["outcome_state"],
        "label_provenance": {
            "uses_gold_answer": True,
            "uses_gold_support": True,
            "uses_runtime_trajectory": source_kind == "trajectory",
            "uses_fixed_evidence_gate": source_kind == "fixed_evidence",
        },
    }
    row["first_loss_boundary"] = _first_loss_boundary(row)
    return row


def _candidate_state_details(
    candidate_records: list[dict[str, Any]],
    gold_values: list[str],
) -> dict[str, Any]:
    all_values = [record["value"] for record in candidate_records]
    final_records = [record for record in candidate_records if record.get("final_slot_signal")]
    final_values = [record["value"] for record in final_records]
    correct_records = [record for record in final_records if _matches_any(record["value"], gold_values)]
    wrong_records = [record for record in final_records if not _matches_any(record["value"], gold_values)]
    near_records = [
        record
        for record in wrong_records
        if max((token_f1(record["value"], gold) for gold in gold_values), default=0.0) >= 0.8
    ]
    if not final_records:
        state = "none"
    elif correct_records and wrong_records:
        state = "mixed"
    elif correct_records:
        state = "correct_present"
    else:
        state = "wrong_only"
    return {
        "candidate_state": state,
        "all_candidate_values": all_values,
        "final_candidate_values": final_values,
        "correct_final_candidate_values": [record["value"] for record in correct_records],
        "wrong_final_candidate_values": [record["value"] for record in wrong_records],
        "surface_near_match_values": [record["value"] for record in near_records],
        "correct_final_candidate_present": bool(correct_records),
        "wrong_final_candidate_present": bool(wrong_records),
        "surface_near_match_present": bool(near_records),
    }


def _verifier_state(
    step: dict[str, Any],
    candidate_details: dict[str, Any],
    gold_values: list[str],
) -> dict[str, Any]:
    verifier_output = step.get("verifier_output") or {}
    claims = list(verifier_output.get("claims") or [])
    critical_bad = any(
        bool(claim.get("is_critical"))
        and str(claim.get("status") or "").lower() in {"unsupported", "contradicted", "unclear"}
        for claim in claims
    )
    generic_accept = bool(
        verifier_output
        and verifier_output.get("overall_sufficiency") == "sufficient"
        and verifier_output.get("final_target_match") is not False
        and not critical_bad
    )
    binding_accept = False
    binding_accepts_correct = False
    binding_sources: list[str] = []
    for key, value in step.items():
        if not isinstance(value, dict) or not key.endswith("slot_binding_verifier_result"):
            continue
        action = str(
            (value.get("decision_head") or {}).get("action")
            or (value.get("decision") or {}).get("action")
            or ""
        )
        accepted = bool(value.get("supports_slot")) and action in {"", "answer", "support"}
        candidate_values = _binding_candidate_values(value)
        binding_accept = binding_accept or accepted
        if accepted and any(_matches_any(candidate, gold_values) for candidate in candidate_values):
            binding_accepts_correct = True
            binding_sources.append(key)
    correct_present = bool(candidate_details.get("correct_final_candidate_present"))
    accept_signal = generic_accept or binding_accept
    accepts_correct = correct_present and (binding_accepts_correct or generic_accept)
    if accepts_correct:
        state = "correct_accept"
    elif correct_present:
        state = "false_reject"
    elif accept_signal:
        state = "false_accept"
    elif verifier_output or any(key.endswith("slot_binding_verifier_result") for key in step):
        state = "reject_without_correct_candidate"
    else:
        state = "unknown"
    return {
        "verifier_state": state,
        "generic_accept_signal": generic_accept,
        "binding_accept_signal": binding_accept,
        "accept_signal": accept_signal,
        "accepts_correct_candidate": accepts_correct,
        "critical_bad_claim_present": critical_bad,
        "binding_accepts_correct_sources": sorted(binding_sources),
        "overall_sufficiency": str(verifier_output.get("overall_sufficiency") or "unknown"),
        "final_target_match": verifier_output.get("final_target_match"),
    }


def _policy_state(
    step: dict[str, Any],
    trajectory_record: dict[str, Any],
    *,
    is_terminal: bool,
    gold_values: list[str],
    observable_through: str,
) -> dict[str, Any]:
    if observable_through != "P":
        return {
            "policy_state": "not_observed",
            "policy_answered": None,
            "policy_answered_correctly": None,
            "runtime_final_action": "",
            "runtime_final_answer": "",
            "outcome_state": "not_observed",
        }
    runtime_action = str(step.get("action") or "")
    final_action = str(trajectory_record.get("final_action") or "") if is_terminal else ""
    policy_answered = runtime_action == "answer" or final_action == "answer"
    final_answer = str(trajectory_record.get("final_answer") or "") if is_terminal else ""
    match_kind = _match_kind(final_answer, gold_values) if policy_answered else "not_answered"
    answered_correctly = match_kind in {"exact", "alias_exact", "relaxed"}
    if policy_answered and answered_correctly:
        policy_state = "correct_answer"
    elif policy_answered:
        policy_state = "incorrect_answer"
    elif step.get("budget_remaining") == 0:
        policy_state = "budget_blocked"
    elif runtime_action == "abstain" or final_action == "abstain":
        policy_state = "abstained"
    else:
        policy_state = "deferred"
    return {
        "policy_state": policy_state,
        "policy_answered": policy_answered,
        "policy_answered_correctly": answered_correctly,
        "runtime_final_action": final_action,
        "runtime_final_answer": final_answer,
        "outcome_state": match_kind,
    }


def _first_loss_boundary(row: dict[str, Any]) -> str:
    if row.get("evidence_state") == "ambiguous":
        return "ambiguous"
    if row.get("outcome_state") == "exact":
        return "none"
    if row.get("outcome_state") in {"alias_exact", "relaxed"}:
        return "O"
    if row.get("evidence_state") != "complete":
        return "E"
    if row.get("candidate_state") == "none":
        return "C_form"
    if row.get("candidate_state") == "wrong_only":
        return "C_align"
    if not bool((row.get("verifier_disposition") or {}).get("accepts_correct_candidate")):
        return "V"
    if row.get("observable_through") == "V":
        return "none"
    if not bool((row.get("policy_disposition") or {}).get("policy_answered_correctly")):
        return "P"
    return "none"


def _extract_binding_candidates(
    records: list[dict[str, Any]],
    binding: dict[str, Any],
    source_prefix: str,
) -> None:
    role_label = binding.get("candidate_role_labeler") or {}
    ordered = binding.get("ordered_hop_binding") or {}
    bound_role = str(role_label.get("candidate_role") or role_label.get("role") or "")
    bound_relation = str(role_label.get("relation_to_question") or "")
    bound_final = bool(
        binding.get("supports_slot")
        or ordered.get("candidate_is_final_relation_object")
        or _role_is_final(bound_role, bound_relation)
    )
    _add_candidate(
        records,
        value=binding.get("bound_value"),
        source=f"{source_prefix}.bound_value",
        role=bound_role,
        relation=bound_relation,
        evidence_ids=binding.get("evidence_ids") or [],
        final_slot_signal=bound_final,
    )
    _add_candidate(
        records,
        value=role_label.get("candidate"),
        source=f"{source_prefix}.candidate_role_labeler",
        role=bound_role,
        relation=bound_relation,
        evidence_ids=binding.get("evidence_ids") or [],
        final_slot_signal=_role_is_final(bound_role, bound_relation),
    )
    for candidate_role in binding.get("candidate_roles") or []:
        if not isinstance(candidate_role, dict):
            continue
        role = str(candidate_role.get("candidate_role") or candidate_role.get("role") or "")
        relation = str(candidate_role.get("relation_to_question") or "")
        _add_candidate(
            records,
            value=candidate_role.get("candidate"),
            source=f"{source_prefix}.candidate_roles",
            role=role,
            relation=relation,
            evidence_ids=candidate_role.get("evidence_ids") or binding.get("evidence_ids") or [],
            final_slot_signal=_role_is_final(role, relation),
        )
    _add_candidate(
        records,
        value=ordered.get("final_relation_object"),
        source=f"{source_prefix}.ordered_hop_binding",
        role="final_answer" if ordered.get("candidate_is_final_relation_object") else "",
        relation="fills_final_slot" if ordered.get("candidate_is_final_relation_object") else "",
        evidence_ids=ordered.get("evidence_ids") or binding.get("evidence_ids") or [],
        final_slot_signal=bool(ordered.get("candidate_is_final_relation_object")),
    )
    entailment = binding.get("slot_entailment") or binding.get("slot_bound_entailment") or {}
    entailed = bool(entailment.get("entails_answer") or entailment.get("entailed"))
    _add_candidate(
        records,
        value=entailment.get("candidate"),
        source=f"{source_prefix}.slot_entailment",
        role="final_answer" if entailed else "",
        relation="fills_final_slot" if entailed else "",
        evidence_ids=entailment.get("evidence_ids") or [],
        final_slot_signal=entailed,
    )


def _add_candidate(
    records: list[dict[str, Any]],
    *,
    value: Any,
    source: str,
    role: str,
    relation: str,
    evidence_ids: Iterable[Any],
    final_slot_signal: bool,
) -> None:
    candidate = " ".join(str(value or "").split())
    normalized = " ".join(normalize(candidate))
    if not normalized or normalized in {"unknown", "unknown answer", "n a", "none"}:
        return
    records.append(
        {
            "value": candidate,
            "normalized": normalized,
            "sources": [source],
            "roles": [role] if role else [],
            "relations": [relation] if relation else [],
            "evidence_ids": sorted({str(item) for item in evidence_ids if str(item or "").strip()}),
            "final_slot_signal": bool(final_slot_signal),
        }
    )


def _merge_candidate_lists(
    existing: Iterable[dict[str, Any]],
    incoming: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in list(existing) + list(incoming):
        key = str(record.get("normalized") or " ".join(normalize(str(record.get("value") or ""))))
        if not key:
            continue
        target = merged.setdefault(
            key,
            {
                "value": str(record.get("value") or ""),
                "normalized": key,
                "sources": [],
                "roles": [],
                "relations": [],
                "evidence_ids": [],
                "final_slot_signal": False,
            },
        )
        for field in ("sources", "roles", "relations", "evidence_ids"):
            target[field] = sorted(set(target[field]) | {str(value) for value in record.get(field) or [] if str(value)})
        target["final_slot_signal"] = bool(target["final_slot_signal"] or record.get("final_slot_signal"))
    return list(merged.values())


def _binding_candidate_values(binding: dict[str, Any]) -> list[str]:
    records: list[dict[str, Any]] = []
    _extract_binding_candidates(records, binding, "binding")
    return [record["value"] for record in _merge_candidate_lists([], records)]


def _sample_map(samples: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for sample in samples:
        sample_id = str(sample.get("id") or sample.get("sample_id") or "")
        if sample_id:
            result[sample_id] = deepcopy(sample)
    return result


def _resolved_sample(
    sample_id: str,
    trajectory_record: dict[str, Any],
    sample: dict[str, Any] | None,
    ambiguity_override: dict[str, Any] | None,
) -> dict[str, Any]:
    resolved = deepcopy(sample or {})
    resolved["id"] = sample_id
    resolved.setdefault("question", trajectory_record.get("question", ""))
    resolved.setdefault("answer", trajectory_record.get("gold_answer", ""))
    resolved.setdefault("answer_aliases", [])
    resolved.setdefault("supporting_passage_ids", trajectory_record.get("supporting_passage_ids", []))
    metadata = dict(resolved.get("metadata") or trajectory_record.get("sample_metadata") or {})
    if ambiguity_override:
        metadata["evaluation_issue"] = dict(ambiguity_override)
    resolved["metadata"] = metadata
    return resolved


def _gold_values(sample: dict[str, Any]) -> list[str]:
    values = [str(sample.get("answer") or "")]
    values.extend(str(value or "") for value in sample.get("answer_aliases") or [])
    return [value for value in values if value.strip()]


def _matches_any(candidate: str, gold_values: Iterable[str]) -> bool:
    return _match_kind(candidate, list(gold_values)) != "none"


def _match_kind(candidate: str, gold_values: list[str]) -> str:
    candidate = str(candidate or "").strip()
    if not candidate:
        return "none"
    if gold_values and exact_match(candidate, gold_values[0]):
        return "exact"
    if any(exact_match(candidate, gold) for gold in gold_values[1:]):
        return "alias_exact"
    if any(relaxed_answer_match(candidate, gold) for gold in gold_values):
        return "relaxed"
    return "none"


def _role_is_final(role: str, relation: str) -> bool:
    role = str(role or "").strip().lower()
    relation = str(relation or "").strip().lower()
    return role == "final_answer" and relation in {"", "fills_final_slot"}


def _ambiguity_reason(metadata: dict[str, Any]) -> str:
    issue = metadata.get("evaluation_issue") or {}
    if not isinstance(issue, dict):
        return ""
    if issue.get("exclude_from_acceptance") is True or issue.get("category") == "dataset_evidence_ambiguity":
        return str(issue.get("subcategory") or issue.get("category") or "dataset_evidence_ambiguity")
    return ""


def _terminal_anchor_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    source_sizes = Counter(str(row.get("source_id") or "") for row in rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("sample_id") or "")].append(row)
    anchors = {}
    for sample_id, candidates in grouped.items():
        anchors[sample_id] = max(
            candidates,
            key=lambda row: (
                int(bool(row.get("is_terminal"))),
                source_sizes[str(row.get("source_id") or "")],
                int(row.get("round") or 0),
                str(row.get("source_id") or ""),
            ),
        )
    return anchors


def _select_intervention_anchors(
    anchors: dict[str, dict[str, Any]],
    fixed_ids: set[str],
    target_count: int,
) -> list[dict[str, Any]]:
    if target_count <= 0:
        return []
    selected_ids = [sample_id for sample_id in sorted(fixed_ids) if sample_id in anchors]
    selected_set = set(selected_ids)
    buckets: dict[str, list[str]] = defaultdict(list)
    for sample_id, row in anchors.items():
        boundary = str(row.get("first_loss_boundary") or "unknown")
        if boundary not in {"ambiguous", "none", "unknown"} and sample_id not in selected_set:
            buckets[boundary].append(sample_id)
    for values in buckets.values():
        values.sort()
    boundary_order = ("E", "C_form", "C_align", "V", "P", "O")
    while len(selected_ids) < target_count and any(buckets.get(boundary) for boundary in boundary_order):
        for boundary in boundary_order:
            if len(selected_ids) >= target_count:
                break
            if buckets.get(boundary):
                sample_id = buckets[boundary].pop(0)
                if sample_id not in selected_set:
                    selected_ids.append(sample_id)
                    selected_set.add(sample_id)
    if len(selected_ids) < target_count:
        for sample_id in sorted(anchors):
            if sample_id in selected_set:
                continue
            selected_ids.append(sample_id)
            selected_set.add(sample_id)
            if len(selected_ids) >= target_count:
                break
    if len(selected_ids) < target_count:
        raise ValueError(
            f"Requested {target_count} unique intervention questions but only {len(selected_ids)} are available"
        )
    return [anchors[sample_id] for sample_id in selected_ids[:target_count]]


def _observed_transition_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_source_sample: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source_sample[(str(row.get("source_id") or ""), str(row.get("sample_id") or ""))].append(row)
    candidates_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (_, sample_id), grouped_rows in by_source_sample.items():
        ordered = sorted(grouped_rows, key=lambda row: int(row.get("round") or 0))
        for before, after in zip(ordered, ordered[1:]):
            before_ids = set((before.get("oracle_evidence") or {}).get("retrieved_ids_cumulative") or [])
            after_ids = set((after.get("oracle_evidence") or {}).get("retrieved_ids_cumulative") or [])
            before_boundary = str(before.get("first_loss_boundary") or "unknown")
            after_boundary = str(after.get("first_loss_boundary") or "unknown")
            candidates_by_sample[sample_id].append(
                {
                    "available": True,
                    "evidence_grade": "observed_trajectory_transition",
                    "source_id": before.get("source_id"),
                    "from_round": before.get("round"),
                    "to_round": after.get("round"),
                    "intervening_action": before.get("runtime_action"),
                    "before_boundary": before_boundary,
                    "after_boundary": after_boundary,
                    "boundary_advanced": _boundary_rank(after_boundary) > _boundary_rank(before_boundary),
                    "new_retrieved_ids": sorted(after_ids - before_ids),
                    "correct_candidate_before": bool(
                        (before.get("candidate_state_details") or {}).get("correct_final_candidate_present")
                    ),
                    "correct_candidate_after": bool(
                        (after.get("candidate_state_details") or {}).get("correct_final_candidate_present")
                    ),
                    "limitation": "Natural trajectory transitions may change multiple runtime variables and are not isolated interventions.",
                }
            )
    result = {}
    for sample_id, candidates in candidates_by_sample.items():
        result[sample_id] = max(
            candidates,
            key=lambda item: (
                int(item["boundary_advanced"]),
                _boundary_rank(item["after_boundary"]) - _boundary_rank(item["before_boundary"]),
                int(item["to_round"] or 0),
            ),
        )
    return result


def _fixed_evidence_probe(
    baseline: dict[str, Any],
    fixed_row: dict[str, Any] | None,
) -> dict[str, Any]:
    if fixed_row is None:
        return {
            "available": False,
            "evidence_grade": "observed_fixed_evidence",
            "before_boundary": baseline.get("first_loss_boundary"),
            "after_boundary": "not_observed",
            "correct_candidate_present_before": bool(
                (baseline.get("candidate_state_details") or {}).get("correct_final_candidate_present")
            ),
            "correct_candidate_present_after": None,
            "correct_candidate_newly_recovered": None,
            "boundary_advanced": None,
            "limitation": "No completed fixed-evidence gate record exists for this question.",
        }
    before = str(baseline.get("first_loss_boundary") or "unknown")
    after = str(fixed_row.get("first_loss_boundary") or "unknown")
    correct_before = bool(
        (baseline.get("candidate_state_details") or {}).get("correct_final_candidate_present")
    )
    correct_after = bool(
        (fixed_row.get("candidate_state_details") or {}).get("correct_final_candidate_present")
    )
    return {
        "available": True,
        "evidence_grade": "observed_fixed_evidence",
        "source_id": fixed_row.get("source_id"),
        "before_boundary": before,
        "after_boundary": after,
        "correct_candidate_present_before": correct_before,
        "correct_candidate_present_after": correct_after,
        "correct_candidate_newly_recovered": correct_after and not correct_before,
        "boundary_advanced": _boundary_rank(after) > _boundary_rank(before),
        "observable_through": fixed_row.get("observable_through"),
        "parse_status": (fixed_row.get("fixed_evidence_probe") or {}).get("parse_status"),
        "limitation": "The fixed-evidence gate observes E-to-C/V behavior but does not execute the final policy.",
    }


def _empty_transition_probe() -> dict[str, Any]:
    return {
        "available": False,
        "evidence_grade": "observed_trajectory_transition",
        "before_boundary": "not_observed",
        "after_boundary": "not_observed",
        "boundary_advanced": None,
        "limitation": "No later round exists for an observed transition probe.",
    }


def _oracle_stage_restoration(anchor: dict[str, Any]) -> dict[str, Any]:
    before = str(anchor.get("first_loss_boundary") or "unknown")
    restored = deepcopy(anchor)
    _restore_stage(restored, before)
    after = _first_loss_boundary(restored)
    cumulative = deepcopy(anchor)
    sequence = []
    start_index = _restoration_start_index(before)
    for stage in ("E", "C", "V", "P", "O")[start_index:]:
        _restore_stage(cumulative, stage)
        current = _first_loss_boundary(cumulative)
        sequence.append({"stage": stage, "after_boundary": current})
        if current == "none":
            break
    return {
        "available": before not in {"ambiguous", "unknown", "none"},
        "evidence_grade": "oracle_stage_restoration",
        "target_boundary": before,
        "after_single_boundary_restoration": after,
        "clears_target_boundary": after != before,
        "reaches_safe_answer_after_single_restoration": after == "none",
        "cumulative_restoration_sequence": sequence,
        "minimum_prefix_length": len(sequence),
        "limitation": (
            "This deterministic oracle probe mutates the factorized state only. It does not rerun retrieval, "
            "candidate generation, verification, or policy execution."
        ),
    }


def _restore_stage(row: dict[str, Any], stage: str) -> None:
    if stage == "E":
        row["evidence_state"] = "complete"
        row["ambiguity_reason"] = ""
    elif stage in {"C", "C_form", "C_align"}:
        row["candidate_state"] = "correct_present"
        details = dict(row.get("candidate_state_details") or {})
        details["candidate_state"] = "correct_present"
        details["correct_final_candidate_present"] = True
        details["correct_final_candidate_values"] = [str(row.get("gold_answer") or "")]
        details["final_candidate_values"] = [str(row.get("gold_answer") or "")]
        row["candidate_state_details"] = details
    elif stage == "V":
        row["verifier_state"] = "correct_accept"
        disposition = dict(row.get("verifier_disposition") or {})
        disposition["verifier_state"] = "correct_accept"
        disposition["accepts_correct_candidate"] = True
        disposition["accept_signal"] = True
        row["verifier_disposition"] = disposition
    elif stage == "P":
        row["policy_state"] = "correct_answer"
        disposition = dict(row.get("policy_disposition") or {})
        disposition["policy_state"] = "correct_answer"
        disposition["policy_answered"] = True
        disposition["policy_answered_correctly"] = True
        disposition["outcome_state"] = "exact"
        row["policy_disposition"] = disposition
        row["outcome_state"] = "exact"
        row["observable_through"] = "P"
    elif stage == "O":
        row["outcome_state"] = "exact"
        disposition = dict(row.get("policy_disposition") or {})
        disposition["outcome_state"] = "exact"
        disposition["policy_answered"] = True
        disposition["policy_answered_correctly"] = True
        row["policy_disposition"] = disposition


def _restoration_start_index(boundary: str) -> int:
    if boundary == "E":
        return 0
    if boundary in {"C_form", "C_align"}:
        return 1
    if boundary == "V":
        return 2
    if boundary == "P":
        return 3
    if boundary == "O":
        return 4
    return 0


def _boundary_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id"),
        "round": row.get("round"),
        "first_loss_boundary": row.get("first_loss_boundary"),
        "evidence_state": row.get("evidence_state"),
        "candidate_state": row.get("candidate_state"),
        "verifier_state": row.get("verifier_state"),
        "policy_state": row.get("policy_state"),
        "outcome_state": row.get("outcome_state"),
    }


def _boundary_rank(boundary: str) -> int:
    return BOUNDARY_ORDER.get(str(boundary or "unknown"), -2)


def _record_sample_id(record: dict[str, Any]) -> str:
    direct = str(record.get("sample_id") or "")
    if direct:
        return direct
    record_id = str(record.get("id") or "")
    if "::" in record_id:
        parts = record_id.split("::")
        if len(parts) >= 2:
            return parts[-2] if parts[-1].startswith("r") else parts[-1]
    return record_id


def _decomposition_ids(sample_id: str) -> list[str]:
    if "__" not in sample_id:
        return []
    return [part for part in sample_id.split("__", 1)[1].split("_") if part]
