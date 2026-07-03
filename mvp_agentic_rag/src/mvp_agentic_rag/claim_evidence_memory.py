from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import VerifierOutput


@dataclass
class ClaimEvidenceRecord:
    claim: str
    status: str
    evidence_ids: list[str] = field(default_factory=list)
    source_query: str = ""
    critical: bool = False
    last_seen_step: int = 0
    missing_evidence: str = ""


@dataclass
class ClaimEvidenceMemory:
    enabled: bool = False
    query_style: str = "missing_evidence"
    records: dict[str, ClaimEvidenceRecord] = field(default_factory=dict)

    def update_from_verifier(self, verifier_output: VerifierOutput, source_query: str, round_idx: int) -> None:
        if not self.enabled:
            return
        for claim in verifier_output.claims:
            key = _key(claim.claim)
            self.records[key] = ClaimEvidenceRecord(
                claim=claim.claim,
                status=claim.status,
                evidence_ids=list(claim.evidence_ids),
                source_query=source_query,
                critical=claim.is_critical,
                last_seen_step=round_idx,
                missing_evidence=claim.missing_evidence,
            )

    def unresolved_critical_claims(self) -> list[ClaimEvidenceRecord]:
        if not self.enabled:
            return []
        return [
            record
            for record in self.records.values()
            if record.critical and record.status in {"unsupported", "unclear", "contradicted"}
        ]

    def supported_claims(self) -> list[ClaimEvidenceRecord]:
        if not self.enabled:
            return []
        return [record for record in self.records.values() if record.status == "supported" and record.evidence_ids]

    def next_query(self, fallback_query: str, verifier_suggested_query: str | None = None) -> str:
        unresolved = self.unresolved_critical_claims()
        if unresolved:
            return _claim_query(unresolved[0], style=self.query_style)
        return verifier_suggested_query or fallback_query


def _claim_query(record: ClaimEvidenceRecord, style: str = "missing_evidence") -> str:
    if style == "short":
        return _short_claim_query(record.claim) or record.source_query
    parts = [record.missing_evidence.strip(), record.claim.strip()]
    query = " ".join(part for part in parts if part)
    return query or record.source_query


def _key(claim: str) -> str:
    return " ".join(str(claim or "").lower().split())


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "who",
}


def _short_claim_query(claim: str, max_terms: int = 8) -> str:
    terms = []
    for raw_term in str(claim or "").replace("?", " ").replace(".", " ").split():
        term = raw_term.strip(" ,;:()[]{}\"'")
        if not term:
            continue
        if term.lower() in _STOPWORDS:
            continue
        terms.append(term)
        if len(terms) >= max_terms:
            break
    return " ".join(terms)
