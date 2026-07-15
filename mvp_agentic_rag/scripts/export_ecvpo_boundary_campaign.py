from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.data_loader import read_jsonl, write_jsonl
from mvp_agentic_rag.diagnostics.boundary_ledger import (
    audit_grouped_splits,
    build_fixed_evidence_ledger,
    build_intervention_matrix,
    build_trajectory_ledger,
    summarize_boundary_ledger,
)


DEFAULT_STRATIFIED_SOURCE = "stratified45_v1_3_5_repair_closure_r2"
DEFAULT_TARGETED_SOURCE = "all_support_targeted7_v1_3_5_r1"
DEFAULT_FIXED_SOURCE = "fixed_gold_evidence_targeted5_structured_output_r1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export a read-only round-level E/C/V/P/O boundary analysis campaign."
    )
    parser.add_argument("--stratified-run", required=True)
    parser.add_argument("--stratified-dataset", required=True)
    parser.add_argument("--targeted-run", required=True)
    parser.add_argument("--targeted-dataset", required=True)
    parser.add_argument("--fixed-evidence-records", required=True)
    parser.add_argument("--diagnostic-dev", required=True)
    parser.add_argument("--diagnostic-test", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--intervention-count", type=int, default=25)
    parser.add_argument("--stratified-source-id", default=DEFAULT_STRATIFIED_SOURCE)
    parser.add_argument("--targeted-source-id", default=DEFAULT_TARGETED_SOURCE)
    parser.add_argument("--fixed-source-id", default=DEFAULT_FIXED_SOURCE)
    args = parser.parse_args(argv)

    paths = {
        "stratified_run": Path(args.stratified_run),
        "stratified_dataset": Path(args.stratified_dataset),
        "targeted_run": Path(args.targeted_run),
        "targeted_dataset": Path(args.targeted_dataset),
        "fixed_evidence_records": Path(args.fixed_evidence_records),
        "diagnostic_dev": Path(args.diagnostic_dev),
        "diagnostic_test": Path(args.diagnostic_test),
    }
    _require_files(paths)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stratified_samples = list(read_jsonl(paths["stratified_dataset"]))
    targeted_samples = list(read_jsonl(paths["targeted_dataset"]))
    ambiguity_overrides = _ambiguity_overrides(targeted_samples)
    stratified_ledger = build_trajectory_ledger(
        args.stratified_source_id,
        read_jsonl(paths["stratified_run"]),
        stratified_samples,
        ambiguity_overrides=ambiguity_overrides,
    )
    targeted_ledger = build_trajectory_ledger(
        args.targeted_source_id,
        read_jsonl(paths["targeted_run"]),
        targeted_samples,
        ambiguity_overrides=ambiguity_overrides,
    )
    fixed_ledger = build_fixed_evidence_ledger(
        args.fixed_source_id,
        read_jsonl(paths["fixed_evidence_records"]),
        targeted_samples,
        ambiguity_overrides=ambiguity_overrides,
    )
    trajectory_ledger = stratified_ledger + targeted_ledger
    combined_ledger = trajectory_ledger + fixed_ledger
    interventions = build_intervention_matrix(
        trajectory_ledger,
        fixed_ledger,
        target_count=args.intervention_count,
    )
    split_audit = audit_grouped_splits(
        read_jsonl(paths["diagnostic_dev"]),
        read_jsonl(paths["diagnostic_test"]),
    )
    distribution = summarize_boundary_ledger(combined_ledger)
    distribution["source_summaries"] = {
        args.stratified_source_id: summarize_boundary_ledger(stratified_ledger),
        args.targeted_source_id: summarize_boundary_ledger(targeted_ledger),
        args.fixed_source_id: summarize_boundary_ledger(fixed_ledger),
    }
    distribution["intervention_summary"] = _intervention_summary(interventions)
    distribution["terminal_trajectory_boundary_counts"] = dict(
        sorted(
            Counter(
                str(row.get("first_loss_boundary") or "unknown")
                for row in trajectory_ledger
                if row.get("is_terminal")
            ).items()
        )
    )

    output_paths = {
        "boundary_label_contract": output_dir / "boundary_label_contract.md",
        "boundary_ledger": output_dir / "boundary_ledger.jsonl",
        "boundary_distribution_json": output_dir / "boundary_distribution.json",
        "boundary_distribution_markdown": output_dir / "boundary_distribution.md",
        "intervention_matrix_jsonl": output_dir / "intervention_matrix.jsonl",
        "intervention_matrix_markdown": output_dir / "intervention_matrix.md",
        "grouped_split_audit_json": output_dir / "grouped_split_audit.json",
        "grouped_split_audit_markdown": output_dir / "grouped_split_audit.md",
        "campaign_summary": output_dir / "campaign_summary.md",
        "campaign_manifest": output_dir / "campaign_manifest.json",
    }
    write_jsonl(output_paths["boundary_ledger"], combined_ledger)
    write_jsonl(output_paths["intervention_matrix_jsonl"], interventions)
    _write_json(output_paths["boundary_distribution_json"], distribution)
    _write_json(output_paths["grouped_split_audit_json"], split_audit)
    output_paths["boundary_label_contract"].write_text(_label_contract_markdown(), encoding="utf-8")
    output_paths["boundary_distribution_markdown"].write_text(
        _distribution_markdown(distribution), encoding="utf-8"
    )
    output_paths["intervention_matrix_markdown"].write_text(
        _intervention_markdown(interventions, distribution["intervention_summary"]),
        encoding="utf-8",
    )
    output_paths["grouped_split_audit_markdown"].write_text(
        _split_audit_markdown(split_audit), encoding="utf-8"
    )
    output_paths["campaign_summary"].write_text(
        _campaign_summary_markdown(distribution, split_audit), encoding="utf-8"
    )
    manifest = {
        "campaign_id": "ecvpo_boundary_audit_v0_20260710",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {name: str(path.resolve()) for name, path in paths.items()},
        "source_ids": {
            "stratified": args.stratified_source_id,
            "targeted": args.targeted_source_id,
            "fixed_evidence": args.fixed_source_id,
        },
        "constraints": {
            "training_executed": False,
            "full_300_executed": False,
            "controller_behavior_changed": False,
            "network_required": False,
        },
        "counts": {
            "stratified_ledger": len(stratified_ledger),
            "targeted_ledger": len(targeted_ledger),
            "fixed_evidence_ledger": len(fixed_ledger),
            "combined_ledger": len(combined_ledger),
            "interventions": len(interventions),
            "unique_intervention_questions": len({row["sample_id"] for row in interventions}),
        },
        "outputs": {name: str(path.resolve()) for name, path in output_paths.items()},
    }
    _write_json(output_paths["campaign_manifest"], manifest)

    print(f"ledger_records={len(combined_ledger)}")
    print(f"intervention_records={len(interventions)}")
    print(f"unique_intervention_questions={manifest['counts']['unique_intervention_questions']}")
    print(f"label_coverage_rate={distribution['label_coverage_rate']:.4f}")
    print(
        "fixed_evidence_correct_candidates="
        f"{distribution['fixed_evidence_correct_candidate_count']}/"
        f"{distribution['fixed_evidence_probe_count']}"
    )
    print(f"output_dir={output_dir.resolve()}")
    return 0


def _require_files(paths: dict[str, Path]) -> None:
    missing = [f"{name}={path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing campaign input files: " + ", ".join(missing))


def _ambiguity_overrides(samples: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for sample in samples:
        issue = (sample.get("metadata") or {}).get("evaluation_issue") or {}
        if isinstance(issue, dict) and (
            issue.get("exclude_from_acceptance") is True
            or issue.get("category") == "dataset_evidence_ambiguity"
        ):
            sample_id = str(sample.get("id") or sample.get("sample_id") or "")
            if sample_id:
                result[sample_id] = dict(issue)
    return result


def _intervention_summary(interventions: list[dict[str, Any]]) -> dict[str, Any]:
    fixed_available = [
        row["observed_fixed_evidence"]
        for row in interventions
        if row["observed_fixed_evidence"].get("available")
    ]
    transitions = [
        row["observed_trajectory_transition"]
        for row in interventions
        if row["observed_trajectory_transition"].get("available")
    ]
    oracle = [
        row["oracle_stage_restoration"]
        for row in interventions
        if row["oracle_stage_restoration"].get("available")
    ]
    return {
        "record_count": len(interventions),
        "unique_question_count": len({row["sample_id"] for row in interventions}),
        "observed_fixed_evidence_count": len(fixed_available),
        "observed_fixed_evidence_correct_candidate_present_count": sum(
            bool(item.get("correct_candidate_present_after")) for item in fixed_available
        ),
        "observed_fixed_evidence_correct_candidate_newly_recovered_count": sum(
            bool(item.get("correct_candidate_newly_recovered")) for item in fixed_available
        ),
        "observed_fixed_evidence_boundary_advance_count": sum(
            bool(item.get("boundary_advanced")) for item in fixed_available
        ),
        "observed_transition_count": len(transitions),
        "observed_transition_boundary_advance_count": sum(
            bool(item.get("boundary_advanced")) for item in transitions
        ),
        "oracle_restoration_count": len(oracle),
        "oracle_target_boundary_clear_count": sum(
            bool(item.get("clears_target_boundary")) for item in oracle
        ),
        "oracle_single_restoration_safe_answer_count": sum(
            bool(item.get("reaches_safe_answer_after_single_restoration")) for item in oracle
        ),
        "oracle_probe_is_runtime_evidence": False,
    }


def _label_contract_markdown() -> str:
    return """# E/C/V/P/O Boundary Label Contract

## Purpose

This contract localizes the earliest observable loss of a correct answer in stored multi-hop RAG artifacts. Oracle fields are for offline diagnosis only and must not be used as runtime controller inputs.

| Label | Definition | Oracle dependency | Runtime observable |
| --- | --- | --- | --- |
| `E` | Required answer-entailing gold support is not fully retrieved | gold support IDs and ambiguity audit | no |
| `C_form` | Evidence is complete but no final-slot candidate is formed | gold support completeness | candidate absence is observable |
| `C_align` | Final-slot candidates exist but none match gold or aliases | gold answer or aliases | target-alignment estimate only |
| `V` | A correct final candidate exists but no verifier acceptance signal applies to it | gold answer or aliases | verifier disposition is observable |
| `P` | A correct candidate is accepted but the policy does not emit a correct answer | gold answer or aliases | action is observable |
| `O` | The emitted answer is alias/relaxed-correct but not an exact primary-answer surface | gold answer or aliases | surface form is observable |
| `none` | No loss is observed through the available boundary | gold answer or aliases | only partially |
| `ambiguous` | Dataset evidence is non-entailing or required gold support metadata is absent | dataset audit | no |

## Candidate Contract

- Candidate state is set-valued and provenance-preserving.
- Bridge or distractor candidates do not count as final-slot candidates.
- `correct_present` means a final-slot candidate matches the gold answer or a recorded alias.
- `wrong_only` means final-slot candidates exist but none matches gold or aliases.
- `surface_near_match` flags an unmatched final candidate with token F1 at least 0.8. It remains `wrong_only` until an alias contract or human audit validates it.

## Evidence Grades

| Grade | Meaning | Claim allowed |
| --- | --- | --- |
| `observed_fixed_evidence` | Completed Targeted5 execution with fixed gold evidence | observed E-to-C/V behavior only |
| `observed_trajectory_transition` | Adjacent stored rounds from a real trajectory | natural boundary movement, not isolated causality |
| `oracle_stage_restoration` | Deterministic mutation of the factorized state | contract/mechanics check only; never runtime recovery |

## Ordering And Masks

The first-loss order is `E -> C_form/C_align -> V -> P -> O`. A downstream boundary is assessed only when its prerequisites are present. Fixed-evidence gate rows are observable through `V`; they do not establish final-policy recovery.
"""


def _distribution_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# E/C/V/P/O Boundary Distribution",
        "",
        f"- ledger records: {summary['record_count']}",
        f"- unique questions: {summary['unique_question_count']}",
        f"- terminal records: {summary['terminal_record_count']}",
        f"- explicitly excluded ambiguity records: {summary['explicit_ambiguity_count']}",
        f"- non-ambiguous record rate: {summary['non_ambiguous_record_rate']:.4f}",
        f"- eligible label coverage after exclusions: {summary['label_coverage_rate']:.4f}",
        f"- fixed-evidence correct candidates: {summary['fixed_evidence_correct_candidate_count']}/{summary['fixed_evidence_probe_count']}",
        f"- terminal surface-near-match records: {summary['terminal_surface_near_match_record_count']}",
        "",
        "## All Rounds",
        "",
        "| Boundary | Count |",
        "| --- | ---: |",
    ]
    for label, count in summary.get("boundary_counts", {}).items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(["", "## Terminal Trajectory States", "", "| Boundary | Count |", "| --- | ---: |"])
    for label, count in summary.get("terminal_trajectory_boundary_counts", {}).items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(["", "## Sources", "", "| Source | Records | Questions | Coverage |", "| --- | ---: | ---: | ---: |"])
    for source, source_summary in summary.get("source_summaries", {}).items():
        lines.append(
            f"| `{source}` | {source_summary['record_count']} | {source_summary['unique_question_count']} | "
            f"{source_summary['label_coverage_rate']:.4f} |"
        )
    return "\n".join(lines) + "\n"


def _intervention_markdown(
    interventions: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# Minimum-Restoration Intervention Matrix",
        "",
        f"- selected unique questions: {summary['unique_question_count']}",
        f"- observed fixed-evidence probes: {summary['observed_fixed_evidence_count']}",
        f"- observed fixed-evidence correct candidates produced: {summary['observed_fixed_evidence_correct_candidate_present_count']}",
        f"- observed fixed-evidence newly recovered correct candidates: {summary['observed_fixed_evidence_correct_candidate_newly_recovered_count']}",
        f"- observed trajectory transitions: {summary['observed_transition_count']}",
        f"- observed transition boundary advances: {summary['observed_transition_boundary_advance_count']}",
        f"- oracle stage-restoration probes: {summary['oracle_restoration_count']}",
        "",
        "> `oracle_stage_restoration` is a deterministic state-contract probe. It is not an executed runtime intervention and is never included in observed recovery counts.",
        "",
        "| Sample | Baseline | observed_fixed_evidence | observed_trajectory_transition | oracle_stage_restoration |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in interventions:
        fixed = row["observed_fixed_evidence"]
        transition = row["observed_trajectory_transition"]
        oracle = row["oracle_stage_restoration"]
        fixed_text = (
            f"{fixed.get('before_boundary')} -> {fixed.get('after_boundary')}; "
            f"candidate_after={fixed.get('correct_candidate_present_after')}; "
            f"new_recovery={fixed.get('correct_candidate_newly_recovered')}"
            if fixed.get("available")
            else "not available"
        )
        transition_text = (
            f"{transition.get('before_boundary')} -> {transition.get('after_boundary')}"
            if transition.get("available")
            else "not available"
        )
        oracle_text = (
            f"{oracle.get('target_boundary')} -> {oracle.get('after_single_boundary_restoration')}"
            if oracle.get("available")
            else "not applicable"
        )
        lines.append(
            f"| `{row['sample_id']}` | `{row['baseline']['first_loss_boundary']}` | "
            f"{fixed_text} | {transition_text} | {oracle_text} |"
        )
    return "\n".join(lines) + "\n"


def _split_audit_markdown(audit: dict[str, Any]) -> str:
    overlap_ids = ", ".join(f"`{value}`" for value in audit["overlapping_question_ids"]) or "none"
    decomposition = ", ".join(f"`{value}`" for value in audit["overlapping_decomposition_ids"]) or "none"
    return "\n".join(
        [
            "# Grouped Split Audit",
            "",
            f"- dev records: {audit['dev_record_count']}",
            f"- test records: {audit['test_record_count']}",
            f"- dev unique questions: {audit['dev_unique_question_count']}",
            f"- test unique questions: {audit['test_unique_question_count']}",
            f"- overlapping questions: {audit['overlapping_question_count']}",
            f"- question-group split clean: {audit['question_group_split_is_clean']}",
            "",
            f"Overlapping question IDs: {overlap_ids}",
            "",
            f"Overlapping decomposition IDs: {decomposition}",
            "",
            "Required future split rule: keep every round, source run, fixed-evidence result, and perturbation for one `sample_id` in the same split. For a stricter MuSiQue split, group connected questions that share decomposition IDs.",
        ]
    ) + "\n"


def _campaign_summary_markdown(
    distribution: dict[str, Any],
    split_audit: dict[str, Any],
) -> str:
    intervention = distribution["intervention_summary"]
    terminal_counts = distribution.get("terminal_trajectory_boundary_counts", {})
    dominant = max(terminal_counts.items(), key=lambda item: item[1])[0] if terminal_counts else "unknown"
    coverage_pass = distribution.get("label_coverage_rate", 0.0) >= 0.95
    decision = "CONDITIONAL GO" if coverage_pass else "NO-GO"
    return "\n".join(
        [
            "# ECVPO Boundary Audit v0 Summary",
            "",
            f"Decision: **{decision}** for boundary-data refinement; model training remains blocked.",
            "",
            f"The dominant terminal trajectory boundary is `{dominant}`. The fixed-evidence gate produced a correct candidate in "
            f"{intervention['observed_fixed_evidence_correct_candidate_present_count']}/"
            f"{intervention['observed_fixed_evidence_count']} completed observed probes, but only "
            f"{intervention['observed_fixed_evidence_correct_candidate_newly_recovered_count']} was newly recovered relative to the anchor run.",
            "",
            "## Evidence Separation",
            "",
            f"- `observed_fixed_evidence`: {intervention['observed_fixed_evidence_count']} probes",
            f"- `observed_trajectory_transition`: {intervention['observed_transition_count']} probes",
            f"- `oracle_stage_restoration`: {intervention['oracle_restoration_count']} probes",
            "",
            f"Observed trajectory transitions advanced the recorded boundary in "
            f"{intervention['observed_transition_boundary_advance_count']}/"
            f"{intervention['observed_transition_count']} available probes. These are natural multi-variable transitions, not isolated causal interventions.",
            "",
            "Oracle stage restoration must not be counted as observed runtime recovery. It validates label mechanics and identifies which boundary-specific estimator would be needed next.",
            "",
            "## Training Gate",
            "",
            f"- explicitly excluded ambiguity records: {distribution['explicit_ambiguity_count']}",
            f"- non-ambiguous record rate: {distribution['non_ambiguous_record_rate']:.4f}",
            f"- eligible label coverage after exclusions: {distribution['label_coverage_rate']:.4f}",
            f"- terminal surface-near-match records requiring alias review: {distribution['terminal_surface_near_match_record_count']}",
            f"- diagnostic dev/test overlapping questions: {split_audit['overlapping_question_count']}",
            "- no training was executed in this campaign",
            "- no full-300 run was executed",
            "- no controller behavior was changed",
            "",
            "Next action: inspect candidate provenance and boundary ambiguity in this ledger, then create a question-grouped annotation/data contract before any Runtime Boundary Estimator training.",
        ]
    ) + "\n"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
