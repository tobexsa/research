from __future__ import annotations

import unittest

from mvp_agentic_rag.claim_evidence_utilization import assess_evidence_utilization
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput


class ClaimEvidenceUtilizationTests(unittest.TestCase):
    def test_detects_unresolved_critical_claim_with_existing_evidence(self) -> None:
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Alice founded ExampleCo",
                    "unsupported",
                    evidence_ids=["p1"],
                    missing_evidence="evidence_present_but_reasoning_unresolved: use p1 to answer",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
        )

        assessment = assess_evidence_utilization(
            verifier_output,
            retrieved_evidence_ids={"p1", "p2"},
            accepted_evidence_ids={"p1"},
        )

        self.assertTrue(assessment.evidence_present_but_unresolved)
        self.assertEqual(["p1"], assessment.evidence_ids)
        self.assertEqual("evidence_present_but_unresolved", assessment.reason)

    def test_does_not_fire_for_only_retrieved_nonaccepted_evidence(self) -> None:
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Alice founded ExampleCo",
                    "unsupported",
                    evidence_ids=["p1"],
                    missing_evidence="evidence_present_but_reasoning_unresolved: p1 may help",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
        )

        assessment = assess_evidence_utilization(
            verifier_output,
            retrieved_evidence_ids={"p1"},
            accepted_evidence_ids=set(),
        )

        self.assertFalse(assessment.evidence_present_but_unresolved)
        self.assertEqual([], assessment.evidence_ids)

    def test_does_not_fire_when_unresolved_claim_has_no_existing_evidence(self) -> None:
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Alice founded ExampleCo",
                    "unsupported",
                    evidence_ids=[],
                    missing_evidence="missing_passage: need founder source",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
        )

        assessment = assess_evidence_utilization(
            verifier_output,
            retrieved_evidence_ids={"p1"},
            accepted_evidence_ids=set(),
        )

        self.assertFalse(assessment.evidence_present_but_unresolved)
        self.assertEqual([], assessment.evidence_ids)


if __name__ == "__main__":
    unittest.main()
