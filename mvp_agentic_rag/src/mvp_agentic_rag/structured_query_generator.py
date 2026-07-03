from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .claim_evidence_memory import ClaimEvidenceMemory, ClaimEvidenceRecord
from .llm_client import LLMClient, make_llm_client
from .schemas import Sample


@dataclass(frozen=True)
class StructuredQuery:
    query: str
    payload: dict[str, Any] = field(default_factory=dict)


class StructuredQueryGenerator:
    def __init__(self, client: LLMClient):
        self.client = client

    def generate(self, sample: Sample, memory: ClaimEvidenceMemory, fallback_query: str = "") -> str:
        return self.generate_structured(sample, memory, fallback_query=fallback_query).query

    def generate_structured(
        self,
        sample: Sample,
        memory: ClaimEvidenceMemory,
        fallback_query: str = "",
    ) -> StructuredQuery:
        content = self.client.complete(build_structured_query_prompt(sample, memory, fallback_query))
        try:
            payload = _extract_json(content)
            query = str(payload.get("query", "")).strip()
            if not query:
                return StructuredQuery(fallback_query)
            return StructuredQuery(query, _normalize_payload(payload, query))
        except Exception:
            return StructuredQuery(fallback_query)


def build_structured_query_prompt(
    sample: Sample,
    memory: ClaimEvidenceMemory,
    fallback_query: str = "",
) -> list[dict[str, str]]:
    confirmed = _format_records(memory.supported_claims(), include_missing=False)
    gaps = _format_records(memory.unresolved_critical_claims(), include_missing=True)
    schema = {
        "entities": ["key entity or constraint"],
        "relation": "missing relation to search for",
        "target_attribute": "target answer attribute",
        "query": "one concise retrieval query",
    }
    return [
        {
            "role": "system",
            "content": (
                "You generate the next retrieval query for multi-hop QA. "
                "Use confirmed findings as constraints and retrieval gaps as the missing target. "
                "Return strict JSON only. Keep the query concise and search-engine-like. "
                "Decompose the query into entities, relation, target_attribute, and query."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n\n"
                f"Confirmed findings:\n{confirmed or '- none'}\n\n"
                f"Retrieval gaps:\n{gaps or '- none'}\n\n"
                f"Fallback query:\n{fallback_query or sample.question}\n\n"
                f"Return JSON with this schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        },
    ]


def make_structured_query_generator(config: dict) -> StructuredQueryGenerator:
    return StructuredQueryGenerator(make_llm_client(config, prefix="query_generator"))


def _format_records(records: list[ClaimEvidenceRecord], include_missing: bool) -> str:
    lines = []
    for record in records:
        if include_missing and record.missing_evidence:
            lines.append(f"- claim: {record.claim}\n  gap: {record.missing_evidence}")
        else:
            lines.append(f"- {record.claim}")
    return "\n".join(lines)


def _extract_json(content: str) -> dict:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end >= start:
        stripped = stripped[start : end + 1]
    return json.loads(stripped)


def _normalize_payload(payload: dict, query: str) -> dict[str, Any]:
    entities = payload.get("entities", [])
    if not isinstance(entities, list):
        entities = [str(entities)]
    return {
        "entities": [str(entity) for entity in entities if str(entity).strip()],
        "relation": str(payload.get("relation", "")).strip(),
        "target_attribute": str(payload.get("target_attribute", "")).strip(),
        "query": query,
    }
