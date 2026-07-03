from __future__ import annotations

import json

from .llm_client import LLMClient, make_llm_client
from .prompts import build_closure_verifier_prompt, build_verifier_prompt
from .retriever import tokenize
from .schemas import ClaimAssessment, Passage, Sample, VerifierOutput


class WeakClaimVerifier:
    """Heuristic verifier for offline MVP smoke tests."""

    def verify(self, sample: Sample, evidence: list[Passage], candidate_answer: str) -> VerifierOutput:
        evidence_text = " ".join(p.title + " " + p.text for p in evidence).lower()
        answer_tokens = [t for t in tokenize(candidate_answer) if len(t) > 2]
        gold_tokens = [t for t in tokenize(sample.gold_answer) if len(t) > 2]
        supporting_ids = [p.passage_id for p in evidence if p.passage_id in sample.supporting_passage_ids]

        if not evidence:
            status = "unsupported"
        elif supporting_ids and any(token in evidence_text for token in gold_tokens):
            status = "supported"
        elif answer_tokens and not any(token in evidence_text for token in answer_tokens):
            status = "unsupported"
        else:
            status = "unclear"

        missing = "" if status == "supported" else f"Need evidence for answer to: {sample.question}"
        claim = ClaimAssessment(
            claim=candidate_answer or f"Answer the question: {sample.question}",
            status=status,
            evidence_ids=supporting_ids,
            missing_evidence=missing,
            is_critical=status != "supported",
        )
        sufficient = status == "supported"
        return VerifierOutput(
            claims=[claim],
            overall_sufficiency="sufficient" if sufficient else "insufficient",
            need_more_evidence=not sufficient,
            suggested_query=missing or sample.question,
            risk_score=0.0 if sufficient else 0.8,
            expected_gain=0.0 if sufficient else 0.5,
        )

    def verify_closure(
        self,
        sample: Sample,
        evidence: list[Passage],
        candidate_answer: str,
        cited_evidence_ids: list[str],
        unresolved_claims: list[str],
    ) -> VerifierOutput:
        del cited_evidence_ids, unresolved_claims
        return self.verify(sample, evidence, candidate_answer)


class LLMClaimVerifier:
    def __init__(
        self,
        client: LLMClient,
        distinguish_utilization_gaps: bool = False,
        require_final_target_match: bool = False,
    ):
        self.client = client
        self.distinguish_utilization_gaps = distinguish_utilization_gaps
        self.require_final_target_match = require_final_target_match

    def verify(self, sample: Sample, evidence: list[Passage], candidate_answer: str) -> VerifierOutput:
        messages = build_verifier_prompt(
            sample,
            evidence,
            candidate_answer,
            distinguish_utilization_gaps=self.distinguish_utilization_gaps,
            require_final_target_match=self.require_final_target_match,
        )
        content = self.client.complete(messages)
        try:
            return _parse_verifier_output(content, sample, candidate_answer)
        except Exception:
            try:
                repaired = self.client.complete(_build_verifier_json_repair_prompt(messages, content))
                return _parse_verifier_output(repaired, sample, candidate_answer)
            except Exception:
                return _non_json_fallback(sample, candidate_answer)

    def verify_closure(
        self,
        sample: Sample,
        evidence: list[Passage],
        candidate_answer: str,
        cited_evidence_ids: list[str],
        unresolved_claims: list[str],
    ) -> VerifierOutput:
        messages = build_closure_verifier_prompt(
            sample,
            evidence,
            candidate_answer,
            cited_evidence_ids=cited_evidence_ids,
            unresolved_claims=unresolved_claims,
            require_final_target_match=self.require_final_target_match,
        )
        content = self.client.complete(messages)
        try:
            return _parse_verifier_output(content, sample, candidate_answer)
        except Exception:
            try:
                repaired = self.client.complete(_build_verifier_json_repair_prompt(messages, content))
                return _parse_verifier_output(repaired, sample, candidate_answer)
            except Exception:
                return _non_json_fallback(sample, candidate_answer)


def _parse_verifier_output(content: str, sample: Sample, candidate_answer: str) -> VerifierOutput:
    payload = _extract_json(content)
    claims = [
        ClaimAssessment(
            claim=str(item.get("claim", "")),
            status=_safe_status(str(item.get("status", "unclear"))),
            evidence_ids=[str(value) for value in item.get("evidence_ids", [])],
            missing_evidence=str(item.get("missing_evidence", "")),
            is_critical=bool(item.get("is_critical", False)),
        )
        for item in payload.get("claims", [])
    ]
    if not claims:
        claims = [ClaimAssessment(candidate_answer or sample.question, "unclear", [], "No claims returned", True)]
    return VerifierOutput(
        claims=claims,
        overall_sufficiency=_safe_sufficiency(str(payload.get("overall_sufficiency", "unclear"))),
        need_more_evidence=bool(payload.get("need_more_evidence", True)),
        suggested_query=str(payload.get("suggested_query", "")),
        risk_score=float(payload.get("risk_score", 0.5)),
        expected_gain=float(payload.get("expected_gain", 0.0)),
        final_target_match=_optional_bool(payload.get("final_target_match")),
        answer_slot=str(payload.get("answer_slot", "")),
    )


def _build_verifier_json_repair_prompt(
    original_messages: list[dict[str, str]],
    invalid_content: str,
) -> list[dict[str, str]]:
    original_user = next((message.get("content", "") for message in reversed(original_messages) if message.get("role") == "user"), "")
    return [
        {
            "role": "system",
            "content": (
                "Previous verifier output was not valid JSON. Convert it into exactly one valid JSON object "
                "matching the requested schema. Do not answer the question directly. Do not use Markdown. "
                "If the previous output was a bare answer or UNKNOWN, represent it as an unclear critical claim "
                "with empty evidence_ids, need_more_evidence true, overall_sufficiency unclear, and a targeted suggested_query."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original verifier request:\n{original_user}\n\n"
                f"Invalid verifier output:\n{invalid_content}\n\n"
                "Return repaired JSON only:"
            ),
        },
    ]


def _non_json_fallback(sample: Sample, candidate_answer: str) -> VerifierOutput:
    claim_text = (candidate_answer or "").strip() or f"Answer the question: {sample.question}"
    return VerifierOutput(
        claims=[
            ClaimAssessment(
                claim=claim_text,
                status="unclear",
                evidence_ids=[],
                missing_evidence="Verifier returned non-JSON after repair",
                is_critical=True,
            )
        ],
        overall_sufficiency="unclear",
        need_more_evidence=True,
        suggested_query=_fallback_suggested_query(claim_text, sample.question),
        risk_score=0.8,
        expected_gain=0.0,
        final_target_match=None,
        answer_slot="unknown",
    )


def _fallback_suggested_query(claim_text: str, question: str) -> str:
    normalized = " ".join(str(claim_text or "").split())
    if normalized and normalized.upper() != "UNKNOWN" and len(normalized) <= 80:
        return f"Evidence supporting {normalized}"
    return question


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


def _safe_status(status: str) -> str:
    return status if status in {"supported", "unsupported", "contradicted", "unclear"} else "unclear"


def _safe_sufficiency(value: str) -> str:
    return value if value in {"sufficient", "insufficient", "conflicting", "unclear"} else "unclear"


def _optional_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def make_verifier(config: dict):
    backend = str(config.get("verifier_backend", "weak")).lower()
    if backend in {"", "weak", "heuristic"}:
        return WeakClaimVerifier()
    if backend in {"fake_llm", "openai_compatible", "openai-compatible"}:
        return LLMClaimVerifier(
            make_llm_client(config, prefix="verifier"),
            distinguish_utilization_gaps=bool(config.get("claim_evidence_utilization_gate", False)),
            require_final_target_match=bool(config.get("claim_evidence_final_target_binding_gate", False)),
        )
    raise ValueError(f"Unknown verifier backend: {backend}")
