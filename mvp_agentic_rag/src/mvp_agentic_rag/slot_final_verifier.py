from __future__ import annotations

import json

from .llm_client import LLMClient, make_llm_client
from .prompts import format_evidence
from .schemas import Passage, Sample, VerifierOutput
from .slot_ledger import SlotLedger
from .verifier import _build_verifier_json_repair_prompt, _non_json_fallback, _parse_verifier_output


class LLMSlotFinalVerifier:
    def __init__(self, client: LLMClient):
        self.client = client

    def verify_final_slot(
        self,
        sample: Sample,
        evidence: list[Passage],
        candidate_answer: str,
        slot_ledger: SlotLedger,
    ) -> VerifierOutput:
        messages = _build_slot_final_verifier_prompt(sample, evidence, candidate_answer, slot_ledger)
        content = self.client.complete(messages)
        try:
            return _parse_verifier_output(content, sample, candidate_answer)
        except Exception:
            try:
                repaired = self.client.complete(_build_verifier_json_repair_prompt(messages, content))
                return _parse_verifier_output(repaired, sample, candidate_answer)
            except Exception:
                return _non_json_fallback(sample, candidate_answer)


def _build_slot_final_verifier_prompt(
    sample: Sample,
    evidence: list[Passage],
    candidate_answer: str,
    slot_ledger: SlotLedger,
) -> list[dict[str, str]]:
    schema = {
        "claims": [
            {
                "claim": "candidate answer fills final_target",
                "status": "supported|unsupported|contradicted|unclear",
                "evidence_ids": ["passage id from final-target evidence"],
                "missing_evidence": "what final-target evidence is missing",
                "is_critical": True,
            }
        ],
        "overall_sufficiency": "sufficient|insufficient|conflicting|unclear",
        "need_more_evidence": True,
        "suggested_query": "targeted follow-up query, or empty string",
        "risk_score": 0.0,
        "expected_gain": 0.0,
        "final_target_match": True,
        "answer_slot": "final requested target|intermediate entity|bridge relation|container/location|date component|unknown",
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a narrow slot-aware final verifier. Return strict JSON only. "
                "Your only task is to decide whether the candidate short answer is supported by the provided "
                "final-target evidence for the final_target slot in the slot ledger. "
                "Do not re-verify the full multi-hop chain. Do not require bridge evidence beyond what is already "
                "encoded in the slot ledger. Do not generate or repair the answer. "
                "When the final_target claim contains a typed binding certificate, use it to identify the already "
                "validated final relation object and bound bridge values. Audit the candidate against the cited "
                "final-target evidence. Do not reject solely because a bridge hop is not restated as a separate "
                "claim in this narrow verification step. "
                "Mark overall_sufficiency sufficient only if the candidate answer is explicitly supported by "
                "the final-target evidence IDs and fills the original question's final requested target. "
                "Set final_target_match false when the candidate is an intermediate entity, bridge relation, "
                "container/location, date component, or any other non-final slot. "
                "Use only the provided final-target evidence IDs."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n"
                f"Candidate short answer: {candidate_answer}\n\n"
                f"Slot ledger:\n{json.dumps(slot_ledger.to_record(), ensure_ascii=False)}\n\n"
                f"Final-target evidence only:\n{format_evidence(evidence)}\n\n"
                f"Return JSON with this schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        },
    ]


def make_slot_final_verifier(config: dict) -> LLMSlotFinalVerifier:
    return LLMSlotFinalVerifier(make_llm_client(config, prefix="slot_final_verifier"))
