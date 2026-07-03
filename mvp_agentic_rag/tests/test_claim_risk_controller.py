from __future__ import annotations

import unittest

from mvp_agentic_rag.claim_risk_controller import ClaimRiskController
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput


class ClaimRiskControllerTests(unittest.TestCase):
    def test_answers_when_sufficient_and_no_critical_unsupported(self) -> None:
        controller = ClaimRiskController()
        output = VerifierOutput(
            claims=[ClaimAssessment("x", "supported", is_critical=True)],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
        )

        action = controller.decide(output, budget_remaining=2, evidence_gain=0.5, retrieval_novelty=1.0)

        self.assertEqual("answer", action)

    def test_abstains_when_budget_exhausted(self) -> None:
        controller = ClaimRiskController()

        action = controller.decide(_verifier(), budget_remaining=0, evidence_gain=0.0, retrieval_novelty=0.0)

        self.assertEqual("abstain", action)

    def test_abstains_after_low_yield_retrieval_with_critical_missing_claim(self) -> None:
        controller = ClaimRiskController(min_retrieval_novelty=0.01)

        action = controller.decide(
            _verifier(),
            budget_remaining=1,
            evidence_gain=0.0,
            retrieval_novelty=0.0,
            round_idx=2,
        )

        self.assertEqual("abstain", action)

    def test_refines_when_missing_critical_claim_and_retrieval_is_still_novel(self) -> None:
        controller = ClaimRiskController(min_retrieval_novelty=0.01)

        action = controller.decide(
            _verifier(),
            budget_remaining=1,
            evidence_gain=0.0,
            retrieval_novelty=0.8,
            round_idx=2,
        )

        self.assertEqual("refine_query", action)

    def test_continues_for_noncritical_insufficient_evidence_with_retrieval_value(self) -> None:
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        output = _verifier(claims=[ClaimAssessment("x", "unsupported", is_critical=False)])

        action = controller.decide(
            output,
            budget_remaining=1,
            evidence_gain=0.0,
            retrieval_novelty=0.8,
            round_idx=2,
        )

        self.assertEqual("continue_search", action)

    def test_does_not_answer_when_sufficient_but_critical_claim_is_unsupported(self) -> None:
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        output = _verifier(sufficiency="sufficient")

        action = controller.decide(
            output,
            budget_remaining=1,
            evidence_gain=0.0,
            retrieval_novelty=0.8,
            round_idx=2,
        )

        self.assertEqual("refine_query", action)

    def test_abstains_when_sufficient_but_critical_claim_is_unsupported_and_low_yield(self) -> None:
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        output = _verifier(sufficiency="sufficient")

        action = controller.decide(
            output,
            budget_remaining=1,
            evidence_gain=0.0,
            retrieval_novelty=0.0,
            round_idx=2,
        )

        self.assertEqual("abstain", action)


def _verifier(sufficiency: str = "insufficient", claims: list[ClaimAssessment] | None = None) -> VerifierOutput:
    return VerifierOutput(
        claims=claims or [ClaimAssessment("x", "unsupported", is_critical=True)],
        overall_sufficiency=sufficiency,
        need_more_evidence=sufficiency != "sufficient",
        suggested_query="follow up",
    )


if __name__ == "__main__":
    unittest.main()
