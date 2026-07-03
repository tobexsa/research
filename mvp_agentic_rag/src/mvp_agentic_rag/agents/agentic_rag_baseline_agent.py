from __future__ import annotations

from .base import BaseAgent
from ..evidence_ledger import EvidenceLedger
from ..policy import RiskPolicy
from ..schemas import Sample, TrajectoryStep


class AgenticRagBaselineAgent(BaseAgent):
    method = "agentic_rag_baseline"

    def __init__(self, retriever, top_k: int = 5, max_rounds: int = 3, config: dict | None = None):
        super().__init__(retriever, top_k, max_rounds, config)
        self.policy = RiskPolicy()

    def run(self, sample: Sample):
        ledger = EvidenceLedger(sample=sample, budget_remaining=self.max_rounds)
        query = sample.question
        steps = []
        action = "abstain"
        answer = ""
        for round_idx in range(1, self.max_rounds + 1):
            ledger.round = round_idx
            passages = self.search(sample, query)
            gain = ledger.add_retrieved(passages)
            answer = self.answer_from(sample, ledger.retrieved_passages)
            verifier_output = self.verifier.verify(sample, ledger.retrieved_passages, answer)
            budget_remaining = self.max_rounds - round_idx
            action = self.policy.decide(verifier_output, budget_remaining, gain)
            steps.append(
                TrajectoryStep(
                    round_idx,
                    query,
                    [p.passage_id for p in passages],
                    verifier_output.to_record(),
                    action,
                    budget_remaining,
                    gain,
                )
            )
            if action in {"answer", "abstain"}:
                break
            query = verifier_output.suggested_query or sample.question
        return self.result(sample, answer if action == "answer" else "", action, steps)
