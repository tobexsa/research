from __future__ import annotations

import json
import re

from .llm_client import make_llm_client
from .schemas import Sample


class QueryDecomposer:
    def decompose(self, sample: Sample, query: str) -> list[str]:
        return _unique_nonempty([query])


class HeuristicQueryDecomposer(QueryDecomposer):
    def __init__(self, max_subqueries: int = 4):
        self.max_subqueries = max_subqueries

    def decompose(self, sample: Sample, query: str) -> list[str]:
        candidates = [query]
        candidates.extend(_split_on_conjunctions(query))
        return _unique_nonempty(candidates)[: self.max_subqueries]


class LLMQueryDecomposer(QueryDecomposer):
    def __init__(self, config: dict):
        self.client = make_llm_client(config, prefix="decomposer")
        self.max_subqueries = int(config.get("max_subqueries", 4))

    def decompose(self, sample: Sample, query: str) -> list[str]:
        response = self.client.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Decompose a multi-hop question into concise retrieval subqueries. "
                        "Return only a JSON array of strings."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {sample.question}\nCurrent query: {query}",
                },
            ]
        )
        return _unique_nonempty([query, *_parse_json_list(response)])[: self.max_subqueries]


def make_query_decomposer(config: dict | None = None) -> QueryDecomposer:
    config = config or {}
    mode = str(config.get("query_decomposition", "none")).lower()
    if mode in {"", "none", "off", "false"}:
        return QueryDecomposer()
    if mode in {"heuristic", "rule", "rules"}:
        return HeuristicQueryDecomposer(max_subqueries=int(config.get("max_subqueries", 4)))
    if mode in {"llm", "openai_compatible", "openai-compatible"}:
        return LLMQueryDecomposer(config)
    raise ValueError(f"Unknown query_decomposition mode: {mode}")


def _split_on_conjunctions(query: str) -> list[str]:
    compact = " ".join(query.split())
    parts = re.split(r"\b(?:and|then|after|before|where|that|which)\b", compact, flags=re.IGNORECASE)
    return [part.strip(" ,") for part in parts if part.strip(" ,")]


def _parse_json_list(text: str) -> list[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [line.strip("-* \t") for line in text.splitlines()]
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("queries", "subqueries", "sub_questions", "subquestions"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]
    return []


def _unique_nonempty(queries: list[str]) -> list[str]:
    seen = set()
    unique = []
    for query in queries:
        normalized = " ".join(str(query or "").split())
        key = normalized.lower()
        if normalized and key not in seen:
            unique.append(normalized)
            seen.add(key)
    return unique
