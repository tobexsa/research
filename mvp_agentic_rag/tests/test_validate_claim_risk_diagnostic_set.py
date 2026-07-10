from __future__ import annotations

from mvp_agentic_rag.diagnostics.full_batch import split_human_verified_records, validate_human_verified_dataset
from tests.claim_risk_test_helpers import _record


def _verified(record_id: str, risk_type: str, hop: int = 2) -> dict:
    record = _record(record_id, risk_type=risk_type, hop=hop)
    record["annotation_status"] = "human_verified"
    record["label_provenance"]["uses_human_review"] = True
    return record


def test_split_is_deterministic_and_disjoint() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(10)]

    first = split_human_verified_records(records, dev_ratio=0.3, seed=13)
    second = split_human_verified_records(records, dev_ratio=0.3, seed=13)

    assert [r["id"] for r in first["dev"]] == [r["id"] for r in second["dev"]]
    assert [r["id"] for r in first["test"]] == [r["id"] for r in second["test"]]
    assert {r["id"] for r in first["dev"]}.isdisjoint({r["id"] for r in first["test"]})


def test_validation_rejects_non_human_verified_records() -> None:
    records = [_verified("ok", "supported_answer")]
    records.append(_verified("bad", "wrong_target"))
    records[1]["annotation_status"] = "adjudication_needed"

    report = validate_human_verified_dataset(records)

    assert report["valid"] is False
    assert "bad" in report["status_issue_records"]


def test_validation_rejects_duplicate_ids() -> None:
    records = [_verified("dup", "supported_answer"), _verified("dup", "wrong_target")]

    report = validate_human_verified_dataset(records)

    assert report["valid"] is False
    assert report["duplicate_ids"] == ["dup"]


def test_validation_allows_scarce_contradiction_bucket() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(8)]

    split = split_human_verified_records(records, dev_ratio=0.25, seed=13)
    report = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types={"supported_answer", "wrong_target", "contradiction"},
        scarce_risk_types={"contradiction"},
    )

    assert report["valid"] is True


def test_validation_rejects_missing_expected_test_bucket_when_not_scarce() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(8)]
    split = split_human_verified_records(records, dev_ratio=0.25, seed=13)

    report = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types={"supported_answer", "wrong_target", "contradiction"},
        scarce_risk_types=set(),
    )

    assert report["valid"] is False
    assert report["missing_test_risk_types"] == ["contradiction"]


def test_validation_report_includes_split_counts() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(10)]
    split = split_human_verified_records(records, dev_ratio=0.3, seed=13)

    report = validate_human_verified_dataset(records, dev_records=split["dev"], test_records=split["test"])

    assert report["record_count"] == 10
    assert report["dev_count"] + report["test_count"] == 10
    assert report["schema_issue_count"] == 0
