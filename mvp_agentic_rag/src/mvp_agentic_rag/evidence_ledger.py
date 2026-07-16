from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Passage, Sample


@dataclass
class EvidenceLedger:
    sample: Sample
    use_gold_support_gain: bool = True
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
            if (
                self.use_gold_support_gain
                and passage.passage_id in self.sample.supporting_passage_ids
                and passage.passage_id not in before
            ):
                self.accepted_evidence_ids.append(passage.passage_id)
        if self.use_gold_support_gain:
            gained = len(set(self.accepted_evidence_ids) - before)
            gain = gained / max(len(self.sample.supporting_passage_ids), 1)
        else:
            gain = novelty
        self.evidence_gain_history.append(gain)
        self.retrieval_novelty_history.append(novelty)
        self.new_passage_count_history.append(len(new_passage_ids))
        self.duplicate_passage_count_history.append(duplicate_count)
        return gain

    def accept_verifier_evidence(self, evidence_ids: list[str]) -> None:
        """Record model-cited local evidence without consulting gold labels."""

        retrieved_ids = {passage.passage_id for passage in self.retrieved_passages}
        accepted = set(self.accepted_evidence_ids)
        for evidence_id in evidence_ids:
            normalized = str(evidence_id or "").strip()
            if normalized and normalized in retrieved_ids and normalized not in accepted:
                self.accepted_evidence_ids.append(normalized)
                accepted.add(normalized)
