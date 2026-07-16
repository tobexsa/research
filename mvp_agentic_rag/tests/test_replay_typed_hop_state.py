from __future__ import annotations

from mvp_agentic_rag.slot_execution_state import SlotExecutionState
from scripts.replay_typed_hop_state import _terminal_invariant_violations


def test_terminal_replay_flags_r28_style_generic_answer() -> None:
    row = {
        "final_action": "answer",
        "trajectory": [
            {
                "controller_policy_v1_original_action": "abstain",
                "semantic_fusion_lane": "generic_compatibility",
                "retrieved_ids": ["p1"],
                "verifier_output": {
                    "need_more_evidence": True,
                    "claims": [
                        {
                            "claim": "7 October",
                            "status": "unclear",
                            "evidence_ids": [],
                            "is_critical": True,
                        }
                    ],
                },
                "slot_binding_verifier_result": {
                    "supports_slot": False,
                    "ordered_hop_binding": {"chain_complete": False},
                    "set_level_sufficiency": {"final_slot_covered": False},
                },
            }
        ],
    }

    violations = set(
        _terminal_invariant_violations(
            row,
            SlotExecutionState.empty("sample"),
            {"p1"},
        )
    )

    assert violations >= {
        "terminal_answer_overrides_abstain",
        "terminal_answer_needs_more_evidence",
        "terminal_answer_has_unsupported_claim",
        "terminal_answer_without_claim_evidence",
        "terminal_answer_without_slot_support",
        "terminal_answer_with_incomplete_chain",
        "terminal_answer_with_uncovered_final_slot",
        "terminal_answer_without_ancestor_closure",
    }


def test_terminal_replay_ignores_abstention() -> None:
    assert (
        _terminal_invariant_violations(
            {"final_action": "abstain", "trajectory": []},
            SlotExecutionState.empty("sample"),
            set(),
        )
        == ()
    )
