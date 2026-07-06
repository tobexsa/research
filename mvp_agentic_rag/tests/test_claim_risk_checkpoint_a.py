import json
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import (
    audit_trajectory_fields,
    build_candidates,
    check_source_runs,
    compact_review_form_to_markdown,
    export_annotation_sheet,
    review_records_to_csv,
    export_candidate_pool_quality,
    sample_candidates,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _run_dir(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    run_dir = tmp_path / name
    run_dir.mkdir()
    _write_jsonl(run_dir / "trajectories.jsonl", rows)
    (run_dir / "metrics.json").write_text(json.dumps({"count": len(rows)}), encoding="utf-8")
    return run_dir


def _trajectory(sample_id: str = "s1", action: str = "answer") -> dict:
    return {
        "id": sample_id,
        "method": "claim_risk",
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "final_answer": "Ada",
        "final_action": action,
        "trajectory": [
            {
                "round": 1,
                "action": action,
                "budget_remaining": 2,
                "evidence_gain": 1.0,
                "retrieved_ids": [f"{sample_id}::p1"],
                "verifier_output": {
                    "overall_sufficiency": "sufficient",
                    "need_more_evidence": False,
                    "final_target_match": True,
                    "claims": [
                        {
                            "claim": "Ada founded X.",
                            "status": "supported",
                            "evidence_ids": [f"{sample_id}::p1"],
                            "is_critical": True,
                            "missing_evidence": "",
                        }
                    ],
                },
                "slot_binding_verifier_result": {
                    "ordered_hop_binding": {
                        "bound_bridge_values": [],
                        "missing_critical_hops": [],
                        "final_relation": "founded by",
                    }
                },
                "repair_query_quality_bucket": "useful",
            }
        ],
    }


def test_empty_candidate_answer_is_not_prelabelled_as_answer(tmp_path: Path) -> None:
    row = _trajectory("s-empty", action="abstain")
    row["final_answer"] = ""
    run_a = _run_dir(tmp_path, "run-empty", [row])

    candidate = build_candidates([run_a])[0]

    assert candidate["candidate_answer"] == ""
    assert candidate["oracle_action"] != "answer"
    assert candidate["final_answer_supported"] is False


def test_check_source_runs_reports_rows_and_overlap(tmp_path: Path) -> None:
    run_a = _run_dir(tmp_path, "run-a", [_trajectory("s1"), _trajectory("s2")])
    run_b = _run_dir(tmp_path, "run-b", [_trajectory("s2")])

    report = check_source_runs([run_a, run_b])

    assert report["runs"][0]["row_count"] == 2
    assert report["runs"][0]["has_trajectories"] is True
    assert report["pairwise_overlap"][0]["overlap_count"] == 1


def test_audit_trajectory_fields_counts_nested_paths(tmp_path: Path) -> None:
    run_a = _run_dir(tmp_path, "run-a", [_trajectory("s1")])

    audit = audit_trajectory_fields([run_a], max_records_per_run=5)

    fields = audit["runs"][0]["path_stats"]
    assert fields["trajectory[].verifier_output.claims[].status"]["present_count"] == 1
    assert fields["trajectory[].slot_binding_verifier_result.ordered_hop_binding.final_relation"]["present_count"] == 1


def test_build_candidates_preserves_required_review_fields(tmp_path: Path) -> None:
    run_a = _run_dir(tmp_path, "run-a", [_trajectory("s1")])
    corpus = {"s1::p1": {"id": "s1::p1", "title": "Real title", "text": "Ada founded X in 1900."}}

    candidates = build_candidates([run_a], corpus=corpus)

    assert candidates
    first = candidates[0]
    assert first["claims"][0]["claim_id"] == "c1"
    assert first["evidence"][0]["title"] == "Real title"
    assert first["evidence"][0]["text"] == "Ada founded X in 1900."
    assert first["metadata"]["risk_type"] == "supported_answer"
    assert first["mining_reason"]["rule"] == "supported_answer"
    assert first["label_provenance"]["uses_model_output"] is True
    assert first["state"]["allowed_actions"]


def test_quality_sampling_and_annotation_export(tmp_path: Path) -> None:
    candidates = []
    for index in range(4):
        candidate = build_candidates([_run_dir(tmp_path, f"run-{index}", [_trajectory(f"s{index}")])])[0]
        candidate["risk_type"] = "supported_answer" if index % 2 == 0 else "critical_gap"
        candidate["metadata"]["risk_type"] = candidate["risk_type"]
        candidates.append(candidate)

    quality = export_candidate_pool_quality(candidates)
    sample = sample_candidates(candidates, target_total=3, seed=13)
    sheet = export_annotation_sheet(sample)

    assert quality["total_candidates"] == 4
    assert len(sample) == 3
    assert "## Record" in sheet["markdown"]
    assert len(sheet["review_records"]) == 3
    assert "annotation_status" in sheet["review_records"][0]


def test_compact_annotation_export_truncates_evidence_preview() -> None:
    record = {
        "id": "rec-compact",
        "sample_id": "s1",
        "source_run": "run-a",
        "risk_type": "critical_gap",
        "oracle_action": "repair_missing_hop",
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "candidate_answer": "",
        "claims": [{"claim_id": "c1", "text": "Ada founded X.", "role": "critical", "source": "verifier_output"}],
        "claim_support": {"c1": "unclear"},
        "evidence": [{"id": "p1", "title": "Long passage", "text": "A" * 80}],
        "mining_reason": {"rule": "critical_gap", "matched_fields": ["x"], "confidence": "medium"},
        "label_provenance": {"runtime_available": True},
        "annotation_status": "pending_review",
        "notes": "",
    }

    sheet = export_annotation_sheet([record], max_evidence_chars=20, compact=True)
    review = sheet["review_records"][0]

    assert "evidence" not in review
    assert review["evidence_preview"][0]["text_preview"] == "A" * 20
    assert review["evidence_preview"][0]["truncated"] is True
    assert review["evidence_full_ref"]["passage_ids"] == ["p1"]
    assert "A" * 30 not in sheet["markdown"]


def test_review_records_to_csv_flattens_human_edit_fields() -> None:
    record = {
        "id": "rec-compact",
        "sample_id": "s1",
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "candidate_answer": "",
        "risk_type": "critical_gap",
        "oracle_action": "repair_missing_hop",
        "claim_support": {"c1": "unclear"},
        "claims": [{"claim_id": "c1", "text": "Ada founded X.", "role": "critical"}],
        "evidence_preview": [{"id": "p1", "title": "Long passage", "text_preview": "Ada founded", "truncated": True}],
        "oracle_repair_target": {"suggested_query": "Ada founded X"},
        "annotation_status": "pending_review",
        "notes": "",
    }

    csv_text = review_records_to_csv([record])

    assert "id,sample_id,question" in csv_text
    assert "rec-compact" in csv_text
    assert "c1=unclear" in csv_text
    assert "p1 | Long passage | Ada founded [truncated]" in csv_text
    assert "pending_review" in csv_text


def test_compact_review_form_preserves_unicode_text() -> None:
    record = {
        "id": "rec-unicode",
        "sample_id": "s-unicode",
        "source_run": "run-a",
        "question": "Where did B\u00e9la live?",
        "gold_answer": "upper 40s\u2013lower 50s \u00b0F",
        "candidate_answer": "",
        "hop": 2,
        "round": 1,
        "risk_type": "repairable_missing_hop",
        "oracle_action": "repair_missing_hop",
        "claims": [{"claim_id": "c1", "text": "B\u00e9la lived where it was 8\u201312 \u00b0C."}],
        "claim_support": {"c1": "unclear"},
        "critical_missing_claims": ["c1"],
        "noncritical_missing_claims": [],
        "contradicted_claims": [],
        "wrong_target": False,
        "bridge_as_final": False,
        "final_answer_supported": False,
        "evidence_sufficiency": "insufficient",
        "oracle_repair_target": {"suggested_query": "B\u00e9la location"},
        "evidence_preview": [
            {
                "id": "p1",
                "title": "B\u00e9la Linder",
                "text_preview": "Temperature was upper 40s\u2013lower 50s \u00b0F.",
                "truncated": False,
            }
        ],
        "mining_reason": {"rule": "repairable_missing_hop"},
        "label_provenance": {"uses_model_output": True},
        "annotation_status": "pending_review",
        "notes": "",
    }

    markdown = compact_review_form_to_markdown([record])

    assert "B\u00e9la" in markdown
    assert "upper 40s\u2013lower 50s \u00b0F" in markdown
    assert "8\u201312 \u00b0C" in markdown
    assert "\u9225" not in markdown
    assert "\u8305" not in markdown
    assert "\u63b3" not in markdown
