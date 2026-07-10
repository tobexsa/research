from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Passage:
    passage_id: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Passage":
        return cls(
            passage_id=str(record.get("id") or record.get("passage_id")),
            title=str(record.get("title", "")),
            text=str(record.get("text", "")),
            metadata=dict(record.get("metadata", {})),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.passage_id,
            "title": self.title,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Sample:
    sample_id: str
    question: str
    gold_answer: str
    supporting_passage_ids: list[str] = field(default_factory=list)
    hop: int | None = None
    subset: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Sample":
        return cls(
            sample_id=str(record.get("id") or record.get("sample_id")),
            question=str(record["question"]),
            gold_answer=str(record.get("answer") or record.get("gold_answer", "")),
            supporting_passage_ids=[str(x) for x in record.get("supporting_passage_ids", [])],
            hop=record.get("hop"),
            subset=str(record.get("subset", "default")),
            metadata=dict(record.get("metadata", {})),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.sample_id,
            "question": self.question,
            "answer": self.gold_answer,
            "supporting_passage_ids": self.supporting_passage_ids,
            "hop": self.hop,
            "subset": self.subset,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ClaimAssessment:
    claim: str
    status: str
    evidence_ids: list[str] = field(default_factory=list)
    missing_evidence: str = ""
    is_critical: bool = False

    def to_record(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status,
            "evidence_ids": self.evidence_ids,
            "missing_evidence": self.missing_evidence,
            "is_critical": self.is_critical,
        }


@dataclass(frozen=True)
class VerifierOutput:
    claims: list[ClaimAssessment]
    overall_sufficiency: str
    need_more_evidence: bool
    suggested_query: str = ""
    risk_score: float = 0.0
    expected_gain: float = 0.0
    final_target_match: bool | None = None
    answer_slot: str = ""

    def to_record(self) -> dict[str, Any]:
        record = {
            "claims": [claim.to_record() for claim in self.claims],
            "overall_sufficiency": self.overall_sufficiency,
            "need_more_evidence": self.need_more_evidence,
            "suggested_query": self.suggested_query,
            "risk_score": self.risk_score,
            "expected_gain": self.expected_gain,
        }
        if self.final_target_match is not None:
            record["final_target_match"] = self.final_target_match
        if self.answer_slot:
            record["answer_slot"] = self.answer_slot
        return record


@dataclass
class TrajectoryStep:
    round: int
    query: str
    retrieved_ids: list[str]
    verifier_output: dict[str, Any]
    action: str
    budget_remaining: int
    evidence_gain: float
    query_source: str = ""
    query_metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = {
            "round": self.round,
            "query": self.query,
            "retrieved_ids": self.retrieved_ids,
            "verifier_output": self.verifier_output,
            "action": self.action,
            "budget_remaining": self.budget_remaining,
            "evidence_gain": self.evidence_gain,
        }
        if self.query_source:
            record["query_source"] = self.query_source
        record.update(self.query_metadata)
        return record


@dataclass
class AgentResult:
    sample_id: str
    question: str
    gold_answer: str
    method: str
    final_answer: str
    final_action: str
    trajectory: list[TrajectoryStep]
    cost: dict[str, int]
    supporting_passage_ids: list[str] = field(default_factory=list)
    hop: int | None = None
    subset: str = "default"
    sample_metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.sample_id,
            "question": self.question,
            "gold_answer": self.gold_answer,
            "method": self.method,
            "final_answer": self.final_answer,
            "final_action": self.final_action,
            "supporting_passage_ids": list(self.supporting_passage_ids),
            "hop": self.hop,
            "subset": self.subset,
            "sample_metadata": dict(self.sample_metadata),
            "trajectory": [step.to_record() for step in self.trajectory],
            "cost": self.cost,
        }
