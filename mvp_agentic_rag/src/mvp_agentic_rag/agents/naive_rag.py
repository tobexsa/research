from __future__ import annotations

from .base import BaseAgent
from ..schemas import Sample, TrajectoryStep


class NaiveRagAgent(BaseAgent):
    method = "naive"

    def run(self, sample: Sample):
        passages = self.search(sample, sample.question)
        answer = self.answer_from(sample, passages)
        step = TrajectoryStep(1, sample.question, [p.passage_id for p in passages], {}, "answer", 0, 0.0)
        return self.result(sample, answer, "answer", [step])
