from __future__ import annotations

from dataclasses import dataclass, field
import re

from .schemas import Passage, Sample


@dataclass(frozen=True)
class CanonicalizedAnswer:
    answer: str
    changed: bool
    rule: str = ""
    before: str = ""
    evidence_ids: list[str] = field(default_factory=list)


def canonicalize_answer(
    sample: Sample,
    answer: str,
    evidence: list[Passage],
    target_type: str = "",
) -> CanonicalizedAnswer:
    answer = str(answer or "").strip()
    if not answer:
        return CanonicalizedAnswer(answer=answer, changed=False, before=answer)
    target_type = str(target_type or "").lower()
    if target_type == "century" or "century" in sample.question.lower():
        compact = _compact_century(answer)
        if compact != answer:
            return CanonicalizedAnswer(
                answer=compact,
                changed=True,
                rule="century_ordinal",
                before=answer,
            )
    prefixed = _supported_type_prefix_answer(answer, evidence)
    if prefixed is not None and prefixed[0] != answer:
        return CanonicalizedAnswer(
            answer=prefixed[0],
            changed=True,
            rule="supported_type_prefix",
            before=answer,
            evidence_ids=[prefixed[1]],
        )
    if target_type == "person" or sample.question.lower().lstrip().startswith("who "):
        expanded = _longest_supported_person_mention(answer, evidence)
        if expanded is not None and expanded[0] != answer:
            return CanonicalizedAnswer(
                answer=expanded[0],
                changed=True,
                rule="longest_supported_person_mention",
                before=answer,
                evidence_ids=[expanded[1]],
            )
    return CanonicalizedAnswer(answer=answer, changed=False, before=answer)


def relaxed_answer_match(prediction: str, gold: str) -> bool:
    pred_tokens = _tokens(prediction)
    gold_tokens = _tokens(gold)
    if not pred_tokens or not gold_tokens:
        return False
    if pred_tokens == gold_tokens:
        return True
    if _compact_century(prediction) == _compact_century(gold):
        return True
    if _strip_type_prefix(pred_tokens) == gold_tokens or _strip_type_prefix(gold_tokens) == pred_tokens:
        return True
    if _compatible_person_tokens(pred_tokens, gold_tokens):
        return True
    return False


_TYPE_PREFIXES = {
    "island",
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _compact_century(text: str) -> str:
    return re.sub(
        r"\b(\d{1,2}(?:st|nd|rd|th))\s+century\b",
        r"\1",
        str(text or "").strip(),
        flags=re.IGNORECASE,
    )


def _strip_type_prefix(tokens: list[str]) -> list[str]:
    if tokens and tokens[0] in _TYPE_PREFIXES:
        return tokens[1:]
    return tokens


def _compatible_person_tokens(left: list[str], right: list[str]) -> bool:
    if len(left) < 2 or len(right) < 2:
        return False
    if left[0] != right[0] or left[-1] != right[-1]:
        return False
    shorter, longer = sorted((left, right), key=len)
    return len(longer) > len(shorter) and _is_subsequence(shorter, longer)


def _is_subsequence(shorter: list[str], longer: list[str]) -> bool:
    position = 0
    for token in longer:
        if position < len(shorter) and shorter[position] == token:
            position += 1
    return position == len(shorter)


def _supported_type_prefix_answer(answer: str, evidence: list[Passage]) -> tuple[str, str] | None:
    escaped = re.escape(answer)
    prefix_pattern = "|".join(sorted(re.escape(prefix) for prefix in _TYPE_PREFIXES))
    pattern = re.compile(rf"\b({prefix_pattern})\s+({escaped})\b", flags=re.IGNORECASE)
    for passage in evidence:
        for text in (passage.title, passage.text):
            match = pattern.search(text)
            if match:
                return (match.group(0), passage.passage_id)
    return None


def _longest_supported_person_mention(answer: str, evidence: list[Passage]) -> tuple[str, str] | None:
    answer_tokens = _tokens(answer)
    if len(answer_tokens) < 2:
        return None
    best: tuple[str, str] | None = None
    best_len = len(answer_tokens)
    for passage in evidence:
        text = f"{passage.title}. {passage.text}"
        for mention in _capitalized_mentions(text):
            mention_tokens = _tokens(mention)
            if len(mention_tokens) <= best_len:
                continue
            if _compatible_person_tokens(answer_tokens, mention_tokens):
                best = (mention, passage.passage_id)
                best_len = len(mention_tokens)
    return best


def _capitalized_mentions(text: str) -> list[str]:
    pattern = re.compile(
        r"\b[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){1,4}\b"
    )
    return [match.group(0).strip() for match in pattern.finditer(text)]
