from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalWorkingMemory:
    enabled: bool = False
    attempted_queries: set[str] = field(default_factory=set)
    low_yield_queries: set[str] = field(default_factory=set)
    query_to_passage_ids: dict[str, list[str]] = field(default_factory=dict)
    last_queries: list[str] = field(default_factory=list)

    def filter_queries(self, queries: list[str]) -> list[str]:
        if not self.enabled:
            return queries
        return [query for query in queries if _key(query) not in self.attempted_queries]

    def record_query_result(
        self,
        query: str,
        passage_ids: list[str],
        evidence_gain: float,
        retrieval_novelty: float,
    ) -> None:
        if not self.enabled:
            return
        query_key = _key(query)
        self.attempted_queries.add(query_key)
        self.query_to_passage_ids[query_key] = list(passage_ids)
        if evidence_gain <= 0 and retrieval_novelty <= 0:
            self.low_yield_queries.add(query_key)

    def update_last_query_yield(self, evidence_gain: float, retrieval_novelty: float) -> None:
        if not self.enabled:
            return
        if evidence_gain > 0 or retrieval_novelty > 0:
            return
        for query in self.last_queries:
            self.low_yield_queries.add(_key(query))


def _key(query: str) -> str:
    return " ".join(str(query or "").lower().split())
