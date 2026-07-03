from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Passage, Sample


@dataclass
class EvidenceLedger:
    sample: Sample
    round: int = 0
    retrieved_passages: list[Passage] = field(default_factory=list)
    accepted_evidence_ids: list[str] = field(default_factory=list)
    evidence_gain_history: list[float] = field(default_factory=list)
    retrieval_novelty_history: list[float] = field(default_factory=list)
    new_passage_count_history: list[int] = field(default_factory=list)
    duplicate_passage_count_history: list[int] = field(default_factory=list)
    tool_call_history: list[str] = field(default_factory=list)
    budget_remaining: int = 0

    def add_retrieved(self, passages: list[Passage]) -> float:
        before = set(self.accepted_evidence_ids)
        seen_passage_ids = {p.passage_id for p in self.retrieved_passages}
        new_passage_ids = [passage.passage_id for passage in passages if passage.passage_id not in seen_passage_ids]
        duplicate_count = len(passages) - len(new_passage_ids)
        novelty = len(new_passage_ids) / max(len(passages), 1)
        for passage in passages:
            if passage.passage_id not in seen_passage_ids:
                self.retrieved_passages.append(passage)
                seen_passage_ids.add(passage.passage_id)
            if passage.passage_id in self.sample.supporting_passage_ids and passage.passage_id not in before:
                self.accepted_evidence_ids.append(passage.passage_id)
        gained = len(set(self.accepted_evidence_ids) - before)
        gain = gained / max(len(self.sample.supporting_passage_ids), 1)
        self.evidence_gain_history.append(gain)
        self.retrieval_novelty_history.append(novelty)
        self.new_passage_count_history.append(len(new_passage_ids))
        self.duplicate_passage_count_history.append(duplicate_count)
        return gain
