from __future__ import annotations

from .base import BaseAgent
from ..schemas import Sample, TrajectoryStep


class FixedKAgent(BaseAgent):
    method = "fixed_k"

    def run(self, sample: Sample):
        all_passages = []
        steps = []
        seen = set()
        for round_idx in range(1, self.max_rounds + 1):
            passages = self.search(sample, sample.question)
            new_ids = []
            for passage in passages:
                if passage.passage_id not in seen:
                    all_passages.append(passage)
                    seen.add(passage.passage_id)
                    new_ids.append(passage.passage_id)
            steps.append(
                TrajectoryStep(
                    round_idx,
                    sample.question,
                    [p.passage_id for p in passages],
                    {},
                    "continue_search" if round_idx < self.max_rounds else "answer",
                    self.max_rounds - round_idx,
                    float(bool(new_ids)),
                )
            )
        return self.result(sample, self.answer_from(sample, all_passages), "answer", steps)
