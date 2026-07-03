from __future__ import annotations

import json

from .schemas import Passage, Sample
from .slot_ledger import SlotLedger


def format_evidence(evidence: list[Passage]) -> str:
    blocks = []
    for passage in evidence:
        blocks.append(f"[{passage.passage_id}] {passage.title}\n{passage.text}")
    return "\n\n".join(blocks)


def build_answer_prompt(sample: Sample, evidence: list[Passage], answer_style: str = "default") -> list[dict[str, str]]:
    if answer_style == "short":
        system_prompt = (
            "Answer the question using only the provided evidence. "
            "Return only the short answer. Do not explain. "
            "Do not include citations or evidence discussion. "
            "Return the entity or value that directly answers the question's requested type. "
            "Do not return a related broader entity, narrower entity, container, location, or explanation. "
            "If evidence is insufficient, return UNKNOWN."
        )
    else:
        system_prompt = "Answer the question using only the provided evidence. If evidence is insufficient, say UNKNOWN."
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"Question: {sample.question}\n\nEvidence:\n{format_evidence(evidence)}\n\nAnswer:",
        },
    ]


def build_answer_repair_prompt(
    sample: Sample,
    evidence: list[Passage],
    supported_claims: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Answer the question using only the provided evidence. "
                "The verifier found support for the listed claim(s), so ground the final answer in them. "
                "Return the entity or value that directly answers the question's requested type. "
                "Do not return a related broader entity, narrower entity, container, location, or explanation. "
                "Return only the short answer. Do not explain. Do not return UNKNOWN unless the listed "
                "supported claim(s) still do not answer the question."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n\n"
                f"Verifier supported claims:\n{_format_claims(supported_claims)}\n\n"
                f"Evidence:\n{format_evidence(evidence)}\n\n"
                "Repaired answer:"
            ),
        },
    ]


def build_answer_closure_prompt(
    sample: Sample,
    evidence: list[Passage],
    unresolved_claims: list[str],
    evidence_ids: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Answer the question using only the already-retrieved evidence. "
                "The verifier left the listed critical claim(s) unresolved even though they cite existing evidence IDs. "
                "Use those cited evidence IDs first, but do not invent facts beyond the evidence. "
                "Return the entity or value that directly answers the question's requested type. "
                "Return only the short answer. Do not explain. Do not include citations. "
                "Return UNKNOWN only if the cited evidence still does not answer the question."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n\n"
                f"Unresolved critical claims:\n{_format_claims(unresolved_claims)}\n\n"
                f"Cited evidence IDs:\n{_format_claims(evidence_ids)}\n\n"
                f"Already-retrieved evidence:\n{format_evidence(evidence)}\n\n"
                "Closed short answer:"
            ),
        },
    ]


def build_slot_answer_prompt(
    sample: Sample,
    evidence: list[Passage],
    slot_ledger: SlotLedger,
) -> list[dict[str, str]]:
    final_target_evidence = slot_ledger.final_target_evidence(evidence)
    return [
        {
            "role": "system",
            "content": (
                "Answer the question using only the explicit slot ledger and final-target evidence. "
                "Return only the short answer. Do not explain. Do not include citations. "
                "The answer must fill the final_target slot, not a bridge, intermediate entity, "
                "container, location, or date component. If the final_target evidence is insufficient, "
                "return UNKNOWN."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n\n"
                f"Slot ledger:\n{json.dumps(slot_ledger.to_record(), ensure_ascii=False)}\n\n"
                f"Final-target evidence:\n{format_evidence(final_target_evidence)}\n\n"
                "Final short answer:"
            ),
        },
    ]


def build_closure_verifier_prompt(
    sample: Sample,
    evidence: list[Passage],
    candidate_answer: str,
    cited_evidence_ids: list[str],
    unresolved_claims: list[str],
    require_final_target_match: bool = False,
) -> list[dict[str, str]]:
    schema = {
        "claims": [
            {
                "claim": "atomic claim text",
                "status": "supported|unsupported|contradicted|unclear",
                "evidence_ids": ["passage id"],
                "missing_evidence": "what is missing",
                "is_critical": True,
            }
        ],
        "overall_sufficiency": "sufficient|insufficient|conflicting|unclear",
        "need_more_evidence": True,
        "suggested_query": "targeted follow-up query",
        "risk_score": 0.0,
        "expected_gain": 0.0,
    }
    if require_final_target_match:
        schema["final_target_match"] = True
        schema["answer_slot"] = "final requested target|intermediate entity|bridge relation|container/location|date component|unknown"
    return [
        {
            "role": "system",
            "content": (
                "You are a closure verifier. Return strict JSON only. "
                "Your task is narrower than general retrieval planning: decide whether the candidate short answer "
                "is supported by the cited evidence IDs and the already-retrieved evidence. "
                "The candidate must directly answer the original question's requested target attribute, not only "
                "name an intermediate entity, related character, related work, container, location, date component, "
                "or bridge fact. "
                "For multi-hop or nested questions, mark sufficient only when the evidence supports both the bridge "
                "entity/relation and the final requested answer. "
                "Use only the provided evidence. Do not require new passages if the cited evidence directly supports "
                "the candidate answer for the question. "
                "overall_sufficiency may be sufficient only when every critical claim needed for the candidate answer "
                "is supported with non-empty evidence_ids. If not, use insufficient, conflicting, or unclear."
                + (
                    " Also set final_target_match to true only if the candidate answer fills the final requested target "
                    "of the original question. Set it to false when the candidate is an intermediate entity, bridge "
                    "relation, container/location, date component, or any other non-final slot; describe that slot in "
                    "answer_slot."
                    if require_final_target_match
                    else ""
                )
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n"
                f"Candidate short answer: {candidate_answer}\n\n"
                f"Previously unresolved claims:\n{_format_claims(unresolved_claims)}\n\n"
                f"Cited evidence IDs:\n{_format_claims(cited_evidence_ids)}\n\n"
                f"Already-retrieved evidence:\n{format_evidence(evidence)}\n\n"
                f"Return JSON with this schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        },
    ]


def build_verifier_prompt(
    sample: Sample,
    evidence: list[Passage],
    candidate_answer: str,
    distinguish_utilization_gaps: bool = False,
    require_final_target_match: bool = False,
) -> list[dict[str, str]]:
    schema = {
        "claims": [
            {
                "claim": "atomic claim text",
                "status": "supported|unsupported|contradicted|unclear",
                "evidence_ids": ["passage id"],
                "missing_evidence": "what is missing",
                "is_critical": True,
            }
        ],
        "overall_sufficiency": "sufficient|insufficient|conflicting|unclear",
        "need_more_evidence": True,
        "suggested_query": "targeted follow-up query",
        "risk_score": 0.0,
        "expected_gain": 0.0,
    }
    if require_final_target_match:
        schema["final_target_match"] = True
        schema["answer_slot"] = "final requested target|intermediate entity|bridge relation|container/location|date component|unknown"
    system_prompt = (
        "You are a claim-level evidence verifier. Every response must be one valid JSON object "
        "that matches the requested schema exactly. Return strict JSON only. "
        "Do not wrap the JSON in Markdown or code fences. Do not add prose before or after the JSON. "
        "Do not return a bare answer, UNKNOWN, or a single claim string; even when uncertain, fill the full JSON schema. "
        "Use status values supported, unsupported, contradicted, or unclear. "
        'overall_sufficiency may be "sufficient" only if every critical claim needed for the answer has '
        "status supported. If any critical claim is unsupported, contradicted, or unclear, "
        'overall_sufficiency must be "insufficient", "conflicting", or "unclear". '
        "For multi-hop questions, split the verification into atomic bridge claims instead of judging only the final answer. "
        "suggested_query must target one missing entity or relation needed for the next hop. "
        "Do not repeat the full original question as suggested_query unless no narrower missing entity or relation can be identified."
    )
    if require_final_target_match:
        system_prompt += (
            " Also decide whether the candidate answer fills the final requested target of the original question. "
            "Return final_target_match true only when the candidate answer is the final requested target, not an "
            "intermediate entity, bridge relation, container/location, date component, or other supporting slot. "
            "Return answer_slot with a short label for the slot the candidate fills."
        )
    if distinguish_utilization_gaps:
        system_prompt += (
            " For missing_evidence, distinguish missing passages from utilization failures: "
            "write 'missing_passage: ...' when the provided evidence lacks the needed fact, "
            "and write 'evidence_present_but_reasoning_unresolved: ...' when relevant evidence "
            "is already present but the candidate answer or reasoning has not used it correctly."
        )
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                f"Question: {sample.question}\n"
                f"Candidate answer: {candidate_answer}\n\n"
                f"Evidence:\n{format_evidence(evidence)}\n\n"
                f"Return JSON with this schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        },
    ]


def _format_claims(claims: list[str]) -> str:
    return "\n".join(f"- {claim}" for claim in claims) if claims else "- none"
