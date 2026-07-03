from __future__ import annotations

import re

from .llm_client import LLMClient, make_llm_client
from .prompts import (
    build_answer_closure_prompt,
    build_answer_prompt,
    build_answer_repair_prompt,
    build_slot_answer_prompt,
)
from .retriever import tokenize
from .schemas import Passage, Sample


def generate_answer(sample: Sample, evidence: list[Passage]) -> str:
    gold_tokens = set(tokenize(sample.gold_answer))
    for passage in evidence:
        text = passage.title + " " + passage.text
        if gold_tokens and gold_tokens.issubset(set(tokenize(text))):
            return sample.gold_answer
    for passage in evidence:
        sentence = re.split(r"(?<=[.!?])\s+", passage.text.strip())[0]
        if sentence:
            return sentence
    return ""


class HeuristicAnswerGenerator:
    def generate(self, sample: Sample, evidence: list[Passage]) -> str:
        return generate_answer(sample, evidence)

    def generate_from_slot_ledger(self, sample: Sample, evidence: list[Passage], slot_ledger) -> str:
        return generate_answer(sample, slot_ledger.final_target_evidence(evidence))

    def repair(self, sample: Sample, evidence: list[Passage], verifier_output) -> str:
        return self.generate(sample, evidence)

    def close(self, sample: Sample, evidence: list[Passage], unresolved_claims: list[str], evidence_ids: list[str]) -> str:
        del unresolved_claims, evidence_ids
        return self.generate(sample, evidence)


class LLMAnswerGenerator:
    def __init__(self, client: LLMClient, answer_style: str = "default"):
        self.client = client
        self.answer_style = answer_style

    def generate(self, sample: Sample, evidence: list[Passage]) -> str:
        return self.client.complete(build_answer_prompt(sample, evidence, answer_style=self.answer_style)).strip()

    def generate_from_slot_ledger(self, sample: Sample, evidence: list[Passage], slot_ledger) -> str:
        return self.client.complete(build_slot_answer_prompt(sample, evidence, slot_ledger)).strip()

    def repair(self, sample: Sample, evidence: list[Passage], verifier_output) -> str:
        supported_claims = [
            claim.claim
            for claim in verifier_output.claims
            if claim.status == "supported" and claim.is_critical and claim.evidence_ids
        ]
        return self.client.complete(build_answer_repair_prompt(sample, evidence, supported_claims)).strip()

    def close(self, sample: Sample, evidence: list[Passage], unresolved_claims: list[str], evidence_ids: list[str]) -> str:
        return self.client.complete(
            build_answer_closure_prompt(sample, evidence, unresolved_claims, evidence_ids)
        ).strip()


def make_answer_generator(config: dict):
    backend = str(config.get("answer_backend", "heuristic")).lower()
    if backend in {"", "heuristic", "weak"}:
        return HeuristicAnswerGenerator()
    if backend in {"fake_llm", "openai_compatible", "openai-compatible"}:
        return LLMAnswerGenerator(make_llm_client(config, prefix="answer"), answer_style=str(config.get("answer_style", "default")))
    raise ValueError(f"Unknown answer backend: {backend}")
