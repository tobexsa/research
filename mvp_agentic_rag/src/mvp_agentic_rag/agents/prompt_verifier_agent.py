from __future__ import annotations

from .base import BaseAgent
from ..schemas import Sample, TrajectoryStep


class PromptVerifierAgent(BaseAgent):
    method = "prompt_verifier"

    def run(self, sample: Sample):
        passages = self.search(sample, sample.question)
        answer = self.answer_from(sample, passages)
        verifier_output = self.verifier.verify(sample, passages, answer)
        action = "answer" if verifier_output.overall_sufficiency == "sufficient" else "abstain"
        step = TrajectoryStep(
            1,
            sample.question,
            [p.passage_id for p in passages],
            verifier_output.to_record(),
            action,
            0,
            float(verifier_output.overall_sufficiency == "sufficient"),
        )
        return self.result(sample, answer if action == "answer" else "", action, [step])
