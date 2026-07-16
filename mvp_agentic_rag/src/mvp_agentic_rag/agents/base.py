from __future__ import annotations

from ..answer_generator import make_answer_generator
from ..query_decomposer import make_query_decomposer
from ..schemas import AgentResult, Sample, TrajectoryStep
from ..verifier import make_verifier


class BaseAgent:
    method = "base"

    def __init__(self, retriever, top_k: int = 5, max_rounds: int = 3, config: dict | None = None):
        self.retriever = retriever
        self.top_k = top_k
        self.max_rounds = max_rounds
        self.config = config or {}
        self.verifier = make_verifier(self.config)
        self.answer_generator = make_answer_generator(self.config)
        self.query_decomposer = make_query_decomposer(self.config)
        self.per_subquery_top_k = int(self.config.get("per_subquery_top_k", self.top_k))

    def search(self, sample: Sample, query: str, memory=None):
        if getattr(self.retriever, "sample_aware", False) and hasattr(self.retriever, "search_for_sample"):
            try:
                return self.retriever.search_for_sample(sample, self.top_k, query=query)
            except TypeError:
                try:
                    return self.retriever.search_for_sample(sample, self.top_k)
                except TypeError:
                    pass
        queries = self.query_decomposer.decompose(sample, query)
        if memory is not None:
            queries = memory.filter_queries(queries)
        if not queries:
            if memory is not None and getattr(memory, "enabled", False):
                memory.last_queries = []
                return []
            queries = [query]
        if memory is not None:
            memory.last_queries = list(queries)
        passages = []
        seen = set()
        for subquery in queries:
            subquery_passages = self.retriever.search(subquery, self.per_subquery_top_k)
            if memory is not None:
                memory.record_query_result(
                    subquery,
                    [passage.passage_id for passage in subquery_passages],
                    evidence_gain=0.0,
                    retrieval_novelty=1.0 if subquery_passages else 0.0,
                )
            for passage in subquery_passages:
                if passage.passage_id in seen:
                    continue
                passages.append(passage)
                seen.add(passage.passage_id)
                if len(passages) >= self.top_k:
                    return passages
        return passages

    def result(self, sample: Sample, answer: str, action: str, trajectory: list[TrajectoryStep]) -> AgentResult:
        return AgentResult(
            sample_id=sample.sample_id,
            question=sample.question,
            gold_answer=sample.gold_answer,
            method=self.method,
            final_answer=answer,
            final_action=action,
            trajectory=trajectory,
            supporting_passage_ids=list(sample.supporting_passage_ids),
            hop=sample.hop,
            subset=sample.subset,
            sample_metadata=dict(sample.metadata),
            cost={
                "retrieval_calls": len(trajectory),
                "llm_calls": sum(1 for step in trajectory if step.verifier_output),
                "retrieved_passages": sum(len(step.retrieved_ids) for step in trajectory),
                "tokens": sum(len(step.query.split()) for step in trajectory) * 4,
            },
        )

    def answer_from(self, sample: Sample, evidence):
        return self.answer_generator.generate(sample, evidence)
