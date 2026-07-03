from __future__ import annotations

from dataclasses import dataclass

import torch

from .retriever import tokenize
from .schemas import Passage


class Reranker:
    def rerank(self, query: str, passages: list[Passage], top_k: int) -> list[Passage]:
        raise NotImplementedError


class NoopReranker(Reranker):
    def rerank(self, query: str, passages: list[Passage], top_k: int) -> list[Passage]:
        return passages[:top_k]


class LexicalReranker(Reranker):
    def rerank(self, query: str, passages: list[Passage], top_k: int) -> list[Passage]:
        q_terms = set(tokenize(query))
        scored = []
        for passage in passages:
            p_terms = set(tokenize(passage.title + " " + passage.text))
            scored.append((len(q_terms & p_terms), passage.passage_id, passage))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored[:top_k]]


@dataclass
class TransformersSequenceReranker(Reranker):
    model_path: str
    device: str | None = None
    batch_size: int = 8
    max_length: int = 512

    def __post_init__(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.device_name = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device_name)
        self.model.eval()

    def rerank(self, query: str, passages: list[Passage], top_k: int) -> list[Passage]:
        if not passages:
            return []
        scores: list[float] = []
        with torch.no_grad():
            for start in range(0, len(passages), self.batch_size):
                batch = passages[start : start + self.batch_size]
                pairs = [(query, passage.title + " " + passage.text) for passage in batch]
                inputs = self.tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                )
                inputs = {key: value.to(self.device_name) for key, value in inputs.items()}
                logits = self.model(**inputs).logits
                if logits.shape[-1] == 1:
                    batch_scores = logits.squeeze(-1)
                else:
                    batch_scores = logits[:, -1]
                scores.extend(float(score) for score in batch_scores.detach().cpu())
        ordered = sorted(zip(scores, passages), key=lambda item: item[0], reverse=True)
        return [passage for _, passage in ordered[:top_k]]


def make_reranker(
    backend: str = "",
    model_path: str = "",
    device: str | None = None,
    batch_size: int = 8,
    max_length: int = 512,
) -> Reranker:
    normalized = (backend or "").lower()
    if not normalized or normalized == "none":
        return NoopReranker()
    if normalized == "lexical":
        return LexicalReranker()
    if normalized in {"transformers", "sequence_classification", "cross_encoder"}:
        if not model_path:
            raise ValueError("model_path is required for transformers reranker backend")
        return TransformersSequenceReranker(model_path, device=device, batch_size=batch_size, max_length=max_length)
    raise ValueError(f"Unknown reranker backend: {backend}")
