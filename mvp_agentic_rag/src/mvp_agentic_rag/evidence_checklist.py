from __future__ import annotations

import re
from dataclasses import dataclass, field

from .schemas import VerifierOutput


@dataclass
class EvidenceNeedItem:
    claim: str
    status: str = "pending"
    evidence_ids: list[str] = field(default_factory=list)
    missing_evidence: str = ""
    source_query: str = ""
    source_round: int = 0
    last_seen_round: int = 0
    last_query: str = ""
    last_retrieved_ids: list[str] = field(default_factory=list)
    last_evidence_gain: float | None = None


@dataclass
class EvidenceChecklist:
    enabled: bool = False
    include_found_constraints: bool = False
    max_found_constraints: int = 2
    max_query_terms: int = 24
    rematch_min_overlap: float = 0.55
    fallback_on_repeated_query: bool = False
    exhaust_on_no_gain: bool = False
    exhaust_on_repeated_no_gain: bool = False
    exhaust_retrieval_novelty_threshold: float = 0.05
    items: dict[str, EvidenceNeedItem] = field(default_factory=dict)
    last_query_reason: str = "checklist_query"
    active_item_key: str = ""

    def update_from_verifier(self, verifier_output: VerifierOutput, source_query: str, round_idx: int) -> None:
        if not self.enabled:
            return
        for claim in verifier_output.claims:
            if not claim.is_critical:
                continue
            key = _key(claim.claim)
            existing = self.items.get(key)
            if claim.status == "supported" and claim.evidence_ids:
                rematched_key = self._find_best_match_key(claim.claim, status="pending")
                target_key = rematched_key or key
                matched = self.items.get(target_key)
                self.items[target_key] = EvidenceNeedItem(
                    claim=claim.claim,
                    status="found",
                    evidence_ids=list(claim.evidence_ids),
                    missing_evidence="",
                    source_query=matched.source_query if matched else (existing.source_query if existing else source_query),
                    source_round=matched.source_round if matched else (existing.source_round if existing else round_idx),
                    last_seen_round=round_idx,
                    last_query=matched.last_query if matched else (existing.last_query if existing else source_query),
                    last_retrieved_ids=list(matched.last_retrieved_ids if matched else []),
                    last_evidence_gain=matched.last_evidence_gain if matched else (
                        existing.last_evidence_gain if existing else None
                    ),
                )
                if target_key != key:
                    self.items.pop(key, None)
                continue
            if claim.status not in {"unsupported", "unclear", "contradicted"}:
                continue
            if existing is not None and existing.status == "found":
                continue
            if existing is not None and existing.status == "exhausted":
                continue
            if self._find_best_match_key(claim.claim, status="found"):
                continue
            if self._find_best_match_key(claim.claim, status="exhausted"):
                continue
            self.items[key] = EvidenceNeedItem(
                claim=claim.claim,
                status="pending",
                evidence_ids=list(claim.evidence_ids),
                missing_evidence=claim.missing_evidence,
                source_query=existing.source_query if existing else source_query,
                source_round=existing.source_round if existing else round_idx,
                last_seen_round=round_idx,
                last_query=existing.last_query if existing else source_query,
                last_retrieved_ids=list(existing.last_retrieved_ids if existing else []),
                last_evidence_gain=existing.last_evidence_gain if existing else None,
            )

    def pending_items(self) -> list[EvidenceNeedItem]:
        if not self.enabled:
            return []
        return [item for item in self.items.values() if item.status == "pending"]

    def exhausted_items(self) -> list[EvidenceNeedItem]:
        if not self.enabled:
            return []
        return [item for item in self.items.values() if item.status == "exhausted"]

    def found_items(self) -> list[EvidenceNeedItem]:
        if not self.enabled:
            return []
        return [item for item in self.items.values() if item.status == "found"]

    def next_query(self, fallback_query: str, verifier_suggested_query: str | None = None) -> str:
        self.last_query_reason = "fallback"
        self.active_item_key = ""
        if not self.enabled:
            return verifier_suggested_query or fallback_query
        pending = self.pending_items()
        if not pending:
            if self.exhausted_items():
                self.last_query_reason = "exhausted_pending"
            return verifier_suggested_query or fallback_query
        target = pending[0]
        self.active_item_key = _key(target.claim)
        parts = [_clean_query_text(target.missing_evidence), _clean_query_text(target.claim)]
        if self.include_found_constraints:
            parts.extend(_clean_query_text(item.claim) for item in self.found_items()[: self.max_found_constraints])
        query = " ".join(part for part in parts if part)
        query = _dedupe_terms(query)
        query = _limit_terms(query, self.max_query_terms)
        if (
            self.fallback_on_repeated_query
            and verifier_suggested_query
            and query
            and _key(query) == _key(target.last_query)
        ):
            self.last_query_reason = "repeated_checklist_query"
            target.last_query = verifier_suggested_query
            return verifier_suggested_query
        if (
            self.exhaust_on_repeated_no_gain
            and query
            and _key(query) == _key(target.last_query)
            and target.last_retrieved_ids
            and target.last_evidence_gain is not None
            and target.last_evidence_gain <= 0
        ):
            self.last_query_reason = "repeated_no_gain"
            target.status = "exhausted"
            return query
        self.last_query_reason = "checklist_query"
        target.last_query = query or verifier_suggested_query or fallback_query
        return target.last_query

    def record_retrieval_result(
        self,
        query: str,
        retrieved_ids: list[str],
        evidence_gain: float,
        retrieval_novelty: float,
        round_idx: int,
    ) -> None:
        if not self.enabled or not self.active_item_key:
            return
        item = self.items.get(self.active_item_key)
        if item is None or item.status != "pending":
            return
        item.last_query = query
        item.last_retrieved_ids = list(retrieved_ids)
        item.last_evidence_gain = evidence_gain
        item.last_seen_round = round_idx
        if (
            self.exhaust_on_no_gain
            and evidence_gain <= 0
            and retrieval_novelty <= self.exhaust_retrieval_novelty_threshold
        ):
            item.status = "exhausted"

    def to_metadata(self) -> dict[str, list[str]]:
        if not self.enabled:
            return {}
        return {
            "checklist_pending": [item.claim for item in self.pending_items()],
            "checklist_found": [item.claim for item in self.found_items()],
            "checklist_exhausted": [item.claim for item in self.exhausted_items()],
            "checklist_query_reason": self.last_query_reason,
        }

    def _find_best_match_key(self, claim: str, status: str) -> str:
        target_terms = _content_terms(claim)
        if not target_terms:
            return ""
        best_key = ""
        best_score = 0.0
        for key, item in self.items.items():
            if item.status != status:
                continue
            score = _overlap_score(target_terms, _content_terms(item.claim))
            if score > best_score:
                best_key = key
                best_score = score
        return best_key if best_score >= self.rematch_min_overlap else ""


def _key(claim: str) -> str:
    return " ".join(str(claim or "").lower().split())


_EXPLANATION_PATTERNS = [
    r"\bthe evidence provided does not mention\b",
    r"\bthe evidence does not provide information (?:on|about)\b",
    r"\bthe evidence does not provide\b",
    r"\bthe provided evidence does not contain\b",
    r"\bthe evidence does not specify\b",
    r"\bthe evidence provided indicates\b",
    r"\bnot\s+(?:the\s+)?[A-Za-z0-9]+(?:st|nd|rd|th)?(?:\s+century)?\b",
    r"\binformation (?:on|about)\b",
    r"\bis not provided(?: in the given evidence)?\b",
    r"\bin the given evidence\b",
    r"\bprovided evidence\b",
    r"\bgiven evidence\b",
    r"\bcandidate answer\b",
]

_STOPWORDS = {
    "a",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "by",
    "contain",
    "contains",
    "contained",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "not",
    "that",
    "the",
    "their",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "with",
}

_DROP_TERMS = {
    "unknown",
    "specific",
    "specify",
    "specifies",
    "specified",
    "provided",
    "given",
    "evidence",
    "claim",
    "claims",
    "contradict",
    "contradicted",
    "contradicting",
    "indicate",
    "indicates",
    "indicated",
    "mention",
    "mentions",
    "mentioned",
    "information",
    "provide",
    "provides",
}


def _clean_query_text(text: str) -> str:
    cleaned = str(text or "")
    for pattern in _EXPLANATION_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    terms = []
    seen = set()
    for term in _tokenize(cleaned):
        lowered = term.lower()
        if lowered in _STOPWORDS or lowered in _DROP_TERMS:
            continue
        if lowered in seen:
            continue
        terms.append(term)
        seen.add(lowered)
    return " ".join(terms)


def _content_terms(text: str) -> set[str]:
    return {
        term.lower()
        for term in _tokenize(_clean_query_text(text))
        if term.lower() not in _STOPWORDS and term.lower() not in _DROP_TERMS
    }


def _overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _limit_terms(text: str, max_terms: int) -> str:
    if max_terms <= 0:
        return text
    return " ".join(text.split()[:max_terms])


def _dedupe_terms(text: str) -> str:
    terms = []
    seen = set()
    for term in str(text or "").split():
        key = term.lower()
        if key in seen:
            continue
        terms.append(term)
        seen.add(key)
    return " ".join(terms)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?|[\u4e00-\u9fff]+", str(text or ""))
