from mvp_agentic_rag.diagnostics.action_normalization import (
    normalize_allowed_actions,
    normalize_runtime_action,
)


def test_normalizes_runtime_repair_actions_to_diagnostic_action() -> None:
    assert normalize_runtime_action("ordered_hop_repair") == "repair_missing_hop"
    assert normalize_runtime_action("repair_next_hop") == "repair_missing_hop"
    assert normalize_runtime_action("partial_chain_next_hop_repair") == "repair_missing_hop"
    assert normalize_runtime_action("answer_extraction_repair") == "repair_missing_hop"


def test_normalizes_search_and_answer_actions() -> None:
    assert normalize_runtime_action("continue_search") == "refine_query"
    assert normalize_runtime_action("refine_missing_hop") == "repair_missing_hop"
    assert normalize_runtime_action("read_more_chunks") == "read_more"
    assert normalize_runtime_action("final_answer") == "answer"
    assert normalize_runtime_action("not_a_real_action") == "unknown"


def test_normalizes_allowed_actions_without_duplicates() -> None:
    assert normalize_allowed_actions(["continue_search", "refine_query", "ordered_hop_repair"]) == [
        "refine_query",
        "repair_missing_hop",
    ]
