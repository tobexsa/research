from __future__ import annotations

from .schemas import VerifierOutput


class RiskPolicy:
    def decide(self, verifier_output: VerifierOutput, budget_remaining: int, recent_gain: float) -> str:
        statuses = {claim.status for claim in verifier_output.claims}
        has_critical_unsupported = any(
            claim.is_critical and claim.status in {"unsupported", "unclear"} for claim in verifier_output.claims
        )
        if (
            verifier_output.overall_sufficiency == "sufficient"
            and not has_critical_unsupported
            and "contradicted" not in statuses
        ):
            return "answer"
        if budget_remaining <= 0:
            return "abstain"
        if "contradicted" in statuses or has_critical_unsupported:
            return "refine_query"
        if verifier_output.overall_sufficiency in {"insufficient", "unclear"}:
            return "abstain" if recent_gain <= 0 else "continue_search"
        return "answer"
