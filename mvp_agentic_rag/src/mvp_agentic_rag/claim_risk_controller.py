from __future__ import annotations

from dataclasses import dataclass

from .schemas import VerifierOutput


@dataclass
class ClaimRiskController:
    min_retrieval_novelty: float = 0.01
    low_yield_abstain_after_round: int = 2

    def decide(
        self,
        verifier_output: VerifierOutput,
        budget_remaining: int,
        evidence_gain: float,
        retrieval_novelty: float,
        round_idx: int = 1,
    ) -> str:
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
        low_yield = (
            round_idx >= self.low_yield_abstain_after_round
            and evidence_gain <= 0
            and retrieval_novelty <= self.min_retrieval_novelty
        )
        if low_yield:
            return "abstain"
        if "contradicted" in statuses or has_critical_unsupported:
            return "refine_query"
        if verifier_output.overall_sufficiency in {"insufficient", "unclear"}:
            return "continue_search"
        return "answer"
