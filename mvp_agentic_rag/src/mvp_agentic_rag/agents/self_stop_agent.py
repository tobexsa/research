from __future__ import annotations

from .base import BaseAgent
from ..schemas import Sample, TrajectoryStep


class SelfStopAgent(BaseAgent):
    method = "self_stop"

    def run(self, sample: Sample):
        passages = self.search(sample, sample.question)
        answer = self.answer_from(sample, passages)
        action = "answer" if answer else "abstain"
        step = TrajectoryStep(1, sample.question, [p.passage_id for p in passages], {}, action, 0, float(bool(answer)))
        return self.result(sample, answer, action, [step])
