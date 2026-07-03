import unittest

from mvp_agentic_rag.policy import RiskPolicy
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput


class RiskPolicyTests(unittest.TestCase):
    def test_answers_when_sufficient_and_supported(self):
        output = VerifierOutput(
            claims=[ClaimAssessment("Paris is the answer", "supported", ["p1"], "", True)],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            suggested_query="",
        )
        self.assertEqual(RiskPolicy().decide(output, budget_remaining=1, recent_gain=1), "answer")

    def test_refines_when_critical_claim_is_unsupported(self):
        output = VerifierOutput(
            claims=[ClaimAssessment("Bridge claim", "unsupported", [], "Need bridge", True)],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Bridge claim",
        )
        self.assertEqual(RiskPolicy().decide(output, budget_remaining=1, recent_gain=1), "refine_query")

    def test_abstains_when_budget_is_exhausted(self):
        output = VerifierOutput(
            claims=[ClaimAssessment("Bridge claim", "unsupported", [], "Need bridge", True)],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Bridge claim",
        )
        self.assertEqual(RiskPolicy().decide(output, budget_remaining=0, recent_gain=1), "abstain")

    def test_abstains_when_evidence_gain_is_low(self):
        output = VerifierOutput(
            claims=[ClaimAssessment("Unknown claim", "unclear", [], "Need source", False)],
            overall_sufficiency="unclear",
            need_more_evidence=True,
            suggested_query="Unknown claim",
        )
        self.assertEqual(RiskPolicy().decide(output, budget_remaining=2, recent_gain=0), "abstain")

