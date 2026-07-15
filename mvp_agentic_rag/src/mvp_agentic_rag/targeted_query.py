from __future__ import annotations

import re

from .schemas import Passage


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "by",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
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


def generate_targeted_multi_hop_queries(
    question: str,
    retrieved_passages: list[Passage],
    query_history: list[str],
    max_queries: int = 2,
    max_terms: int = 12,
) -> list[str]:
    if max_queries <= 0:
        return []
    question_tokens = _content_tokens(question)
    question_terms = {_stem(token) for token in question_tokens}
    candidates: dict[str, tuple[float, str]] = {}
    for passage in retrieved_passages:
        title = " ".join(passage.title.split())
        title_key = _normalize(title)
        if not title_key or title_key in candidates:
            continue
        passage_terms = {_stem(token) for token in _content_tokens(f"{title} {passage.text}")}
        overlap = len(question_terms & passage_terms)
        if overlap <= 0:
            continue
        title_terms = {_stem(token) for token in _content_tokens(title)}
        title_is_novel = not (title_terms & question_terms)
        novelty_bonus = 10.0 if title_is_novel else 0.0
        candidates[title_key] = (novelty_bonus + overlap, title)

    history = {_normalize(query) for query in query_history if _normalize(query)}
    ordered = sorted(candidates.values(), key=lambda item: (-item[0], item[1].lower()))
    queries: list[str] = []
    target_terms = question_tokens[: max(max_terms, 1)]
    for _, title in ordered:
        query = _join_unique([*_tokens(title), *target_terms], max_terms=max_terms)
        key = _normalize(query)
        if not key or key in history:
            continue
        queries.append(query)
        history.add(key)
        if len(queries) >= max_queries:
            break
    return queries


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", str(text or ""))


def _content_tokens(text: str) -> list[str]:
    return [token for token in _tokens(text) if token.lower() not in _STOPWORDS]


def _stem(token: str) -> str:
    lowered = token.lower()
    if len(lowered) > 4 and lowered.endswith("s"):
        return lowered[:-1]
    return lowered


def _join_unique(tokens: list[str], max_terms: int) -> str:
    result = []
    seen = set()
    for token in tokens:
        key = token.lower()
        if key in seen:
            continue
        result.append(token)
        seen.add(key)
        if max_terms > 0 and len(result) >= max_terms:
            break
    return " ".join(result)


def _normalize(text: str) -> str:
    return " ".join(token.lower() for token in _tokens(text))
