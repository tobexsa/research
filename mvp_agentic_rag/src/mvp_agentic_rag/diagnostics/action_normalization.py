from __future__ import annotations


ACTION_MAP = {
    "answer": "answer",
    "final_answer": "answer",
    "continue_search": "refine_query",
    "refine_query": "refine_query",
    "refine_missing_hop": "repair_missing_hop",
    "ordered_hop_repair": "repair_missing_hop",
    "repair_next_hop": "repair_missing_hop",
    "partial_chain_next_hop_repair": "repair_missing_hop",
    "answer_extraction_repair": "repair_missing_hop",
    "read_more_chunks": "read_more",
    "read_more": "read_more",
    "disambiguate_conflict": "disambiguate_conflict",
    "abstain": "abstain",
}


def normalize_runtime_action(action: str) -> str:
    return ACTION_MAP.get(str(action or "").strip(), "unknown")


def normalize_allowed_actions(actions: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for action in actions:
        mapped = normalize_runtime_action(action)
        if mapped == "unknown" or mapped in seen:
            continue
        normalized.append(mapped)
        seen.add(mapped)
    return normalized
