from __future__ import annotations

from mvp_agentic_rag.diagnostics.full_batch import (
    export_full_batch_preflight,
    export_full_review_summary,
    filter_human_verified_records,
    full_batch_preflight_to_markdown,
)
from mvp_agentic_rag.diagnostics.checkpoint_a import merge_review_csv_into_records
from tests.claim_risk_test_helpers import _record


def test_full_batch_preflight_reports_coverage_and_go() -> None:
    records = [
        _record("r1", "supported_answer", "answer", 2),
        _record("r2", "wrong_target", "disambiguate_conflict", 2),
        _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
        _record("r4", "critical_gap", "refine_query", 3),
        _record("r5", "answer_extraction_failure", "answer", 2),
    ]
    candidate_pool_quality = {
        "records_by_risk_type": {
            "supported_answer": 10,
            "wrong_target": 10,
            "repairable_missing_hop": 3,
            "critical_gap": 2,
            "answer_extraction_failure": 1,
        }
    }

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=5,
        max_total=10,
    )

    assert summary["total_count"] == 5
    assert summary["schema_issue_count"] == 0
    assert summary["available_risk_type_count"] == 5
    assert summary["represented_available_risk_type_count"] == 5
    assert summary["missing_available_risk_types"] == []
    assert summary["gate_checks"]["has_4hop_or_repairable_record"]["passed"] is True
    assert summary["go_or_no_go_for_review"] == "go"


def test_preflight_warns_but_does_not_block_when_answer_extraction_bucket_is_unavailable() -> None:
    records = [
        _record("r1", "supported_answer", "answer"),
        _record("r2", "wrong_target", "disambiguate_conflict"),
        _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
    ]
    candidate_pool_quality = {
        "records_by_risk_type": {
            "supported_answer": 20,
            "wrong_target": 179,
            "repairable_missing_hop": 7,
        }
    }

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=3,
        max_total=10,
    )

    assert summary["gate_checks"]["has_answer_extraction_failure_if_available"]["passed"] is True
    assert "answer_extraction_failure unavailable in candidate_pool_quality" in summary["coverage_warnings"]
    assert summary["go_or_no_go_for_review"] == "go"


def test_full_batch_preflight_blocks_duplicate_ids_and_schema_issues() -> None:
    records = [_record("dup"), _record("dup")]
    del records[1]["state"]["allowed_actions"]
    candidate_pool_quality = {"records_by_risk_type": {"supported_answer": 2}}

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=2,
        max_total=10,
    )

    assert summary["duplicate_id_count"] == 1
    assert summary["schema_issue_count"] >= 1
    assert summary["go_or_no_go_for_review"] == "no_go"


def test_full_batch_preflight_markdown_contains_gate_status() -> None:
    summary = export_full_batch_preflight(
        [
            _record("r1", "supported_answer", "answer"),
            _record("r2", "wrong_target", "disambiguate_conflict"),
            _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
            _record("r4", "no_new_evidence", "abstain"),
            _record("r5", "insufficient_evidence", "refine_query"),
        ],
        candidate_pool_quality={
            "records_by_risk_type": {
                "supported_answer": 1,
                "wrong_target": 1,
                "repairable_missing_hop": 1,
                "no_new_evidence": 1,
                "insufficient_evidence": 1,
            }
        },
        min_total=5,
        max_total=10,
    )

    markdown = full_batch_preflight_to_markdown(summary)

    assert "# Claim-Risk Full Batch Preflight" in markdown
    assert "go_or_no_go_for_review: go" in markdown
    assert "| schema_issue_count | 0 | == 0 | True |" in markdown


def test_review_csv_merge_sets_human_review_provenance_and_excludes_drop() -> None:
    records = [_record("ok"), _record("bad")]
    csv_text = (
        "id,annotation_status,risk_type,oracle_action,notes\n"
        "ok,reviewed_ok,supported_answer,answer,looks good\n"
        "bad,drop,wrong_target,disambiguate_conflict,dataset issue\n"
    )

    merged = merge_review_csv_into_records(records, csv_text)

    assert merged[0]["annotation_status"] == "human_verified"
    assert merged[0]["label_provenance"]["uses_human_review"] is True
    assert merged[1]["annotation_status"] == "excluded"
    assert merged[1]["label_provenance"]["uses_human_review"] is True


def test_needs_fix_remains_adjudication_needed_until_corrected() -> None:
    records = [_record("fix-me", "repairable_missing_hop", "repair_missing_hop")]
    csv_text = "id,annotation_status,risk_type,oracle_action,notes\nfix-me,needs_fix,repairable_missing_hop,repair_missing_hop,needs label fix\n"

    merged = merge_review_csv_into_records(records, csv_text)

    assert merged[0]["annotation_status"] == "adjudication_needed"


def test_full_review_summary_counts_valid_excluded_and_adjudication() -> None:
    ok = _record("ok", "supported_answer", "answer")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = True
    excluded = _record("excluded", "wrong_target", "disambiguate_conflict")
    excluded["annotation_status"] = "excluded"
    excluded["label_provenance"]["uses_human_review"] = True
    adjudication = _record("adj", "repairable_missing_hop", "repair_missing_hop", 4)
    adjudication["annotation_status"] = "adjudication_needed"
    adjudication["label_provenance"]["uses_human_review"] = True

    summary = export_full_review_summary(
        [ok, excluded, adjudication],
        min_annotated=3,
        min_human_verified=1,
        max_adjudication_rate=0.50,
        max_excluded_rate=0.50,
        min_valid_risk_types=1,
    )

    assert summary["annotated_count"] == 3
    assert summary["human_verified_count"] == 1
    assert summary["excluded_count"] == 1
    assert summary["adjudication_needed_count"] == 1
    assert summary["schema_issue_count"] == 0
    assert summary["human_review_provenance_issue_count"] == 0
    assert summary["go_or_no_go_for_checkpoint_c"] == "go"


def test_full_review_summary_blocks_verified_records_without_human_review_provenance() -> None:
    ok = _record("ok", "supported_answer", "answer")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = False

    summary = export_full_review_summary(
        [ok],
        min_annotated=1,
        min_human_verified=1,
        min_valid_risk_types=1,
    )

    assert summary["human_review_provenance_issue_count"] == 1
    assert summary["go_or_no_go_for_checkpoint_c"] == "no_go"


def test_filter_human_verified_records_excludes_unresolved_and_drop() -> None:
    ok = _record("ok")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = True
    excluded = _record("excluded")
    excluded["annotation_status"] = "excluded"
    adjudication = _record("adj")
    adjudication["annotation_status"] = "adjudication_needed"

    filtered = filter_human_verified_records([ok, excluded, adjudication])

    assert [record["id"] for record in filtered] == ["ok"]
