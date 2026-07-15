from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.data_loader import read_jsonl, write_jsonl
from mvp_agentic_rag.diagnostics.boundary_review import (
    HUMAN_REVIEW_FIELDS,
    REVIEW_CONTRACT_VERSION,
    build_question_review_queue,
    build_review_events,
    summarize_review_queue,
    validate_review_event,
)


OUTPUT_NAMES = {
    "protocol": "review_protocol.md",
    "events": "assistant_precheck_events.jsonl",
    "questions": "question_review_queue.jsonl",
    "combined_csv": "human_review_sheet.csv",
    "p0_csv": "p0_human_review_sheet.csv",
    "p1_csv": "p1_human_review_sheet.csv",
    "p2_csv": "p2_human_review_sheet.csv",
    "summary_json": "precheck_summary.json",
    "summary_markdown": "precheck_summary.md",
    "manifest": "campaign_manifest.json",
}


CSV_FIELDS = [
    "review_event_order",
    "question_review_order",
    "event_order_within_question",
    "priority_tier",
    "priority_score",
    "sample_id",
    "question",
    "gold_answer",
    "proposed_split",
    "ledger_id",
    "source_id",
    "source_kind",
    "evidence_grade",
    "round",
    "is_terminal",
    "runtime_action",
    "budget_remaining",
    "coverage_rate",
    "coverage_count",
    "required_count",
    "machine_first_loss_boundary",
    "machine_evidence_state",
    "machine_candidate_state",
    "machine_verifier_state",
    "machine_policy_state",
    "machine_outcome_state",
    "machine_correct_candidate_values",
    "machine_wrong_candidate_values",
    "source_conflict_context",
    "source_wrong_target_context",
    "source_risk_type_counts",
    "assistant_first_loss_boundary",
    "assistant_evidence_state",
    "assistant_candidate_state",
    "assistant_candidate_failure_subtype",
    "assistant_conflict_state",
    "assistant_wrong_target",
    "assistant_recommended_action",
    "assistant_precheck_status",
    "assistant_suggestion_confidence",
    "attention_flag_codes",
    "attention_flag_details",
    "human_first_loss_boundary",
    "human_evidence_state",
    "human_candidate_state",
    "human_candidate_failure_subtype",
    "human_conflict_state",
    "human_wrong_target",
    "human_recommended_action",
    "human_review_decision",
    "human_review_status",
    "reviewer_id",
    "reviewed_at",
    "review_protocol_version",
    "human_review_notes",
    "eligible_for_training",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export a P0/P1/P2 human boundary-review queue with non-authoritative assistant "
            "suggestions and blank human fields."
        )
    )
    parser.add_argument("--priority-batch", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-p0", type=int)
    parser.add_argument("--expected-p1", type=int)
    parser.add_argument("--expected-p2", type=int)
    args = parser.parse_args(argv)

    input_path = Path(args.priority_batch)
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing priority batch: {input_path}")
    packets = list(read_jsonl(input_path))
    review_events = build_review_events(packets)
    question_queue = build_question_review_queue(packets, review_events)
    summary = summarize_review_queue(review_events, question_queue)
    expected_counts = {
        "P0": args.expected_p0,
        "P1": args.expected_p1,
        "P2": args.expected_p2,
    }
    _validate_expected_counts(summary, expected_counts)
    _validate_queue(review_events, question_queue, summary)
    summary["input_priority_batch"] = {
        "path": str(input_path.resolve()),
        "sha256": _sha256(input_path),
        "packet_count": len(packets),
    }
    summary["expected_question_tier_counts"] = {
        tier: count for tier, count in expected_counts.items() if count is not None
    }
    summary["human_review_policy"] = {
        "assistant_suggestions_are_authoritative": False,
        "source_claim_risk_labels_transfer_to_boundary_gold": False,
        "human_fields_blank_on_export": True,
        "training_eligibility_before_confirmation": False,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_NAMES.items()}
    write_jsonl(paths["events"], review_events)
    write_jsonl(paths["questions"], question_queue)
    csv_rows = [_csv_row(event) for event in review_events]
    _write_csv(paths["combined_csv"], csv_rows)
    _write_csv(paths["p0_csv"], [row for row in csv_rows if row["priority_tier"] == "P0"])
    _write_csv(paths["p1_csv"], [row for row in csv_rows if row["priority_tier"] == "P1"])
    _write_csv(paths["p2_csv"], [row for row in csv_rows if row["priority_tier"] == "P2"])
    paths["protocol"].write_text(_protocol_markdown(), encoding="utf-8")
    _write_json(paths["summary_json"], summary)
    paths["summary_markdown"].write_text(
        _summary_markdown(summary, question_queue), encoding="utf-8"
    )

    manifest = {
        "campaign_id": "boundary_annotation_review_v1_20260710",
        "parent_campaign_id": "boundary_annotation_contract_v1_20260710",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_contract_version": REVIEW_CONTRACT_VERSION,
        "input": summary["input_priority_batch"],
        "constraints": {
            "model_calls_executed": False,
            "retrieval_executed": False,
            "training_executed": False,
            "full_300_executed": False,
            "controller_behavior_changed": False,
            "human_verified_labels_created": False,
        },
        "output_counts": {
            "question_count": summary["question_count"],
            "event_count": summary["event_count"],
            "question_tier_counts": summary["question_tier_counts"],
            "event_tier_counts": summary["event_tier_counts"],
            "human_confirmed_event_count": summary["human_confirmed_event_count"],
            "training_eligible_event_count": summary["training_eligible_event_count"],
        },
        "outputs": {name: str(path.resolve()) for name, path in paths.items()},
    }
    _write_json(paths["manifest"], manifest)
    _validate_written_outputs(paths, summary)

    print(f"questions={summary['question_count']}")
    print(f"events={summary['event_count']}")
    print(
        "tiers="
        + ",".join(
            f"{tier}:{summary['question_tier_counts'].get(tier, 0)}"
            for tier in ("P0", "P1", "P2")
        )
    )
    print(
        "needs_human_adjudication_events="
        f"{summary['assistant_precheck_status_counts'].get('needs_human_adjudication', 0)}"
    )
    print(f"human_confirmed_events={summary['human_confirmed_event_count']}")
    print(f"training_eligible_events={summary['training_eligible_event_count']}")
    print(f"output_dir={output_dir.resolve()}")
    return 0


def _validate_expected_counts(
    summary: dict[str, Any],
    expected_counts: dict[str, int | None],
) -> None:
    actual = summary.get("question_tier_counts") or {}
    for tier, expected in expected_counts.items():
        if expected is not None and int(actual.get(tier, 0)) != expected:
            raise ValueError(
                f"Expected {expected} {tier} questions, found {int(actual.get(tier, 0))}"
            )


def _validate_queue(
    events: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    for event in events:
        validate_review_event(event)
    event_ids = [str(event.get("review_event_id") or "") for event in events]
    ledger_ids = [str(event.get("ledger_id") or "") for event in events]
    sample_ids = [str(question.get("sample_id") or "") for question in questions]
    referenced_event_ids = [
        str(event_id)
        for question in questions
        for event_id in question.get("review_event_ids") or []
    ]
    if len(event_ids) != len(set(event_ids)) or len(ledger_ids) != len(set(ledger_ids)):
        raise ValueError("Every ledger event must appear exactly once in the review queue")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Every question must appear exactly once in the review queue")
    if sorted(event_ids) != sorted(referenced_event_ids):
        raise ValueError("Question queue does not conserve review event membership")
    if not summary.get("review_order_is_p0_then_p1_then_p2"):
        raise ValueError("Review order must be P0, then P1, then P2")
    if int(summary.get("human_confirmed_event_count") or 0) != 0:
        raise ValueError("Automated export must not create human-confirmed events")
    if int(summary.get("training_eligible_event_count") or 0) != 0:
        raise ValueError("Unconfirmed review events must remain training-ineligible")


def _csv_row(event: dict[str, Any]) -> dict[str, Any]:
    machine = event.get("machine_boundary_event") or {}
    oracle = machine.get("oracle_evidence") or {}
    details = machine.get("candidate_state_details") or {}
    risk = event.get("source_risk_context") or {}
    assistant = event.get("assistant_suggestions") or {}
    flags = list(event.get("attention_flags") or [])
    return {
        "review_event_order": event.get("review_event_order"),
        "question_review_order": event.get("question_review_order"),
        "event_order_within_question": event.get("event_order_within_question"),
        "priority_tier": event.get("priority_tier"),
        "priority_score": event.get("priority_score"),
        "sample_id": event.get("sample_id"),
        "question": event.get("question"),
        "gold_answer": event.get("gold_answer"),
        "proposed_split": event.get("proposed_split"),
        "ledger_id": event.get("ledger_id"),
        "source_id": machine.get("source_id"),
        "source_kind": machine.get("source_kind"),
        "evidence_grade": machine.get("evidence_grade"),
        "round": machine.get("round"),
        "is_terminal": machine.get("is_terminal"),
        "runtime_action": machine.get("runtime_action"),
        "budget_remaining": machine.get("budget_remaining"),
        "coverage_rate": oracle.get("coverage_rate"),
        "coverage_count": oracle.get("coverage_count"),
        "required_count": oracle.get("required_count"),
        "machine_first_loss_boundary": machine.get("first_loss_boundary"),
        "machine_evidence_state": machine.get("evidence_state"),
        "machine_candidate_state": machine.get("candidate_state"),
        "machine_verifier_state": machine.get("verifier_state"),
        "machine_policy_state": machine.get("policy_state"),
        "machine_outcome_state": machine.get("outcome_state"),
        "machine_correct_candidate_values": _join_values(
            details.get("correct_final_candidate_values") or []
        ),
        "machine_wrong_candidate_values": _join_values(
            details.get("wrong_final_candidate_values") or []
        ),
        "source_conflict_context": risk.get("has_conflict_context"),
        "source_wrong_target_context": risk.get("has_wrong_target_context"),
        "source_risk_type_counts": json.dumps(
            risk.get("risk_type_counts") or {}, ensure_ascii=False, sort_keys=True
        ),
        "assistant_first_loss_boundary": assistant.get("first_loss_boundary"),
        "assistant_evidence_state": assistant.get("evidence_state"),
        "assistant_candidate_state": assistant.get("candidate_state"),
        "assistant_candidate_failure_subtype": assistant.get("candidate_failure_subtype"),
        "assistant_conflict_state": assistant.get("conflict_state"),
        "assistant_wrong_target": assistant.get("wrong_target"),
        "assistant_recommended_action": assistant.get("recommended_action") or "",
        "assistant_precheck_status": event.get("assistant_precheck_status"),
        "assistant_suggestion_confidence": event.get("assistant_suggestion_confidence"),
        "attention_flag_codes": _join_values(flag.get("code") for flag in flags),
        "attention_flag_details": _join_values(flag.get("detail") for flag in flags),
        "human_first_loss_boundary": "",
        "human_evidence_state": "",
        "human_candidate_state": "",
        "human_candidate_failure_subtype": "",
        "human_conflict_state": "",
        "human_wrong_target": "",
        "human_recommended_action": "",
        "human_review_decision": "",
        "human_review_status": "",
        "reviewer_id": "",
        "reviewed_at": "",
        "review_protocol_version": "",
        "human_review_notes": "",
        "eligible_for_training": False,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _protocol_markdown() -> str:
    return """# Priority Boundary Human Review Protocol v1

## Scope

Review all P0 events first, then P1, then P2. Each CSV row is one ledger boundary event inside an immutable question-grouped packet.

Assistant fields are non-authoritative suggestions. Source claim-risk records may contain human-verified fields, but those fields are context only and must not be copied into boundary labels without event-level confirmation.

## Required Human Fields

- `human_first_loss_boundary`
- `human_evidence_state`
- `human_candidate_state`
- `human_candidate_failure_subtype`
- `human_conflict_state`
- `human_wrong_target`
- `human_recommended_action`
- `human_review_decision`
- `human_review_status`
- `reviewer_id`
- `reviewed_at`
- `review_protocol_version`
- `human_review_notes`

## Decisions

- `accept_assistant_suggestion`: independently checked and accepted.
- `correct_labels`: one or more assistant suggestions are corrected in the human columns.
- `exclude_event`: dataset ambiguity, corrupted provenance, or non-comparable event prevents a valid label.
- `defer`: evidence is insufficient for adjudication and requires a second reviewer or source lookup.

Use `human_review_status=human_confirmed` only after all required labels and reviewer provenance are complete. Use `review_protocol_version=boundary_human_review_queue_v1`.

## Attention Flags

High and medium flags require an explicit note. In particular:

- A correct final answer with incomplete oracle evidence exposes a contract choice between answer-loss localization and evidence-safety diagnosis.
- `C_form`, unproven `C_align`, and `V` can expose a controller action-set gap. Do not invent a repair action merely to fill the field; record the gap and choose `defer` when necessary.
- Conflict and wrong-target context from another run/round must be re-confirmed for the current ledger event.

## Training Gate

All exported events remain `pending_human_confirmation` and `eligible_for_training=false`. Editing a CSV does not itself create training-ready data. A later importer must validate completed labels, reviewer provenance, question/component split grouping, and adjudication status before any training eligibility decision.
"""


def _summary_markdown(
    summary: dict[str, Any],
    questions: list[dict[str, Any]],
) -> str:
    lines = [
        "# Priority Boundary Review Precheck",
        "",
        "This is an automated, non-authoritative precheck. Human confirmation count remains zero.",
        "",
        "## Queue",
        "",
        "| Tier | Questions | Events |",
        "| --- | ---: | ---: |",
    ]
    for tier in ("P0", "P1", "P2"):
        lines.append(
            f"| `{tier}` | {summary['question_tier_counts'].get(tier, 0)} | "
            f"{summary['event_tier_counts'].get(tier, 0)} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            f"- Human-confirmed events: {summary['human_confirmed_event_count']}",
            f"- Training-eligible events: {summary['training_eligible_event_count']}",
            f"- Events needing human adjudication: {summary['assistant_precheck_status_counts'].get('needs_human_adjudication', 0)}",
            f"- Unresolved assistant action suggestions: {summary['assistant_unresolved_action_suggestion_count']}",
            "",
            "## Attention Flags",
            "",
            "| Flag | Events | Questions |",
            "| --- | ---: | ---: |",
        ]
    )
    all_codes = sorted(
        set(summary["assistant_attention_flag_event_counts"])
        | set(summary["assistant_attention_flag_question_counts"])
    )
    for code in all_codes:
        lines.append(
            f"| `{_md(code)}` | {summary['assistant_attention_flag_event_counts'].get(code, 0)} | "
            f"{summary['assistant_attention_flag_question_counts'].get(code, 0)} |"
        )
    critical_guidance = {
        "outcome_override_masks_incomplete_evidence": (
            "Keep answer correctness separate from evidence-safety state; decide whether the reviewed boundary field represents stage prerequisite failure or final answer loss."
        ),
        "dataset_evidence_ambiguity": (
            "Prefer `exclude_event` unless an independent source audit repairs the non-entailing gold support."
        ),
        "surface_near_match_requires_alias_check": (
            "Check whether the candidate is a legitimate alias before retaining C-align; a valid alias can move the failure to V or later."
        ),
        "false_accept_wrong_candidate": (
            "Confirm candidate target role and conflict status; these are the strongest wrong-target/unsafe-accept expansion candidates."
        ),
        "controller_action_gap_for_c_form": (
            "Do not force missing-hop repair when evidence is complete; record that candidate regeneration or answer extraction is absent from the action vocabulary."
        ),
        "controller_action_gap_for_c_align": (
            "Use conflict disambiguation only with event-level conflict evidence; otherwise record a target-alignment repair gap."
        ),
    }
    lines.extend(["", "## Decision-Critical Cases", ""])
    for code, guidance in critical_guidance.items():
        question_ids = summary["assistant_attention_flag_question_ids"].get(code, [])
        if not question_ids:
            continue
        lines.append(
            f"- `{code}`: {', '.join(f'`{_md(sample_id)}`' for sample_id in question_ids)}. {guidance}"
        )
    lines.extend(
        [
            "",
            "## Ordered Question Handoff",
            "",
            "| Order | Tier | Sample | Events | Needs adjudication | Terminal boundaries |",
            "| ---: | --- | --- | ---: | ---: | --- |",
        ]
    )
    for question in questions:
        lines.append(
            f"| {question['question_review_order']} | `{question['priority_tier']}` | "
            f"`{_md(question['sample_id'])}` | {question['event_count']} | "
            f"{question['assistant_precheck']['needs_human_adjudication_event_count']} | "
            f"{', '.join(f'`{_md(value)}`' for value in question['terminal_machine_boundaries'])} |"
        )
    lines.extend(
        [
            "",
            "Proceed through the tier-specific CSV sheets in P0, P1, P2 order. The automated campaign stops here; human sign-off remains required.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_written_outputs(paths: dict[str, Path], summary: dict[str, Any]) -> None:
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError(f"Missing review outputs: {missing}")
    events = [
        json.loads(line) for line in paths["events"].read_text(encoding="utf-8").splitlines()
    ]
    questions = [
        json.loads(line)
        for line in paths["questions"].read_text(encoding="utf-8").splitlines()
    ]
    with paths["combined_csv"].open(newline="", encoding="utf-8-sig") as handle:
        combined_rows = list(csv.DictReader(handle))
    tier_rows = {}
    for tier, key in (("P0", "p0_csv"), ("P1", "p1_csv"), ("P2", "p2_csv")):
        with paths[key].open(newline="", encoding="utf-8-sig") as handle:
            tier_rows[tier] = list(csv.DictReader(handle))
    json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    json.loads(paths["manifest"].read_text(encoding="utf-8"))
    if len(events) != int(summary["event_count"]) or len(combined_rows) != len(events):
        raise ValueError("Written review event counts do not match the validated queue")
    if len(questions) != int(summary["question_count"]):
        raise ValueError("Written question count does not match the validated queue")
    for tier, rows in tier_rows.items():
        if len(rows) != int(summary["event_tier_counts"].get(tier, 0)):
            raise ValueError(f"Written {tier} CSV event count mismatch")
    for row in combined_rows:
        human_columns = [
            row[f"human_{field}"]
            for field in HUMAN_REVIEW_FIELDS
        ] + [
            row["human_review_decision"],
            row["human_review_status"],
            row["reviewer_id"],
            row["reviewed_at"],
            row["review_protocol_version"],
            row["human_review_notes"],
        ]
        if any(value != "" for value in human_columns):
            raise ValueError("Automated export populated one or more human CSV fields")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _join_values(values: Any) -> str:
    return "; ".join(str(value) for value in values if value is not None and str(value) != "")


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
