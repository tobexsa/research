from __future__ import annotations

import math

from scripts.analyze_online_stability_protocol import (
    _assess_certificate,
    _decide_campaign,
    _metric_stats,
)


def _complete_binding(*, evidence_ids: list[str] | None = None) -> dict:
    return {
        "supports_slot": True,
        "bound_value": "Person B",
        "evidence_ids": evidence_ids or ["sample::p1", "sample::p2"],
        "ordered_hop_binding": {
            "chain_complete": True,
            "missing_critical_hops": [],
        },
        "set_level_sufficiency": {
            "final_slot_covered": True,
            "all_required_hops_covered": True,
            "evidence_set_sufficient": True,
            "conflict_on_final_slot": False,
            "conflict_on_bridge": False,
        },
    }


def test_certificate_assessment_separates_completion_from_correctness() -> None:
    assessment = _assess_certificate(
        _complete_binding(),
        {"sample::p1", "sample::p2"},
        gold_answer="Person B",
    )

    assert assessment["complete"] is True
    assert assessment["correct"] is True
    assert assessment["failure_category"] == "none"


def test_certificate_assessment_rejects_nonlocal_evidence() -> None:
    assessment = _assess_certificate(
        _complete_binding(evidence_ids=["sample::p1", "foreign::p9"]),
        {"sample::p1", "sample::p2"},
        gold_answer="Person B",
    )

    assert assessment["complete"] is False
    assert assessment["correct"] is False
    assert assessment["failure_category"] == "nonlocal_evidence"


def test_metric_stats_use_sample_standard_deviation() -> None:
    stats = _metric_stats([0.4, 0.6])

    assert stats["mean"] == 0.5
    assert math.isclose(stats["sample_sd"], math.sqrt(0.02))
    assert stats["min"] == 0.4
    assert stats["max"] == 0.6


def test_campaign_decision_requires_both_paired_blocks_to_be_positive() -> None:
    assert (
        _decide_campaign(
            all_runs_valid=True,
            paired_correct_certificate_deltas=[0.1, 0.05],
            paired_answer_f1_deltas=[0.08, 0.02],
            aggregate_answer_f1_delta=0.05,
            aggregate_coverage_delta=0.03,
            answer_without_certificate_total=0,
            safety_violation_total=0,
        )
        == "pass_to_matched_modern_baselines"
    )
    assert (
        _decide_campaign(
            all_runs_valid=True,
            paired_correct_certificate_deltas=[0.1, -0.01],
            paired_answer_f1_deltas=[0.08, -0.02],
            aggregate_answer_f1_delta=0.03,
            aggregate_coverage_delta=0.02,
            answer_without_certificate_total=0,
            safety_violation_total=0,
        )
        == "unstable_stop_no_extra_draw"
    )


def test_campaign_decision_prioritizes_safety_failure() -> None:
    assert (
        _decide_campaign(
            all_runs_valid=False,
            paired_correct_certificate_deltas=[0.1, 0.1],
            paired_answer_f1_deltas=[0.1, 0.1],
            aggregate_answer_f1_delta=0.1,
            aggregate_coverage_delta=0.1,
            answer_without_certificate_total=1,
            safety_violation_total=1,
        )
        == "safety_or_validity_failure_return_to_diagnosis"
    )
