from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from .retriever import tokenize


class TextEncoder:
    backend = "base"

    @property
    def dimension(self) -> int:
        raise NotImplementedError

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        raise NotImplementedError


@dataclass
class HashingTextEncoder(TextEncoder):
    dimension: int = 768
    backend: str = "hashing"

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        vectors = [self._encode_one(text) for text in texts]
        if not vectors:
            return np.zeros((0, self.dimension), dtype="float32")
        return np.vstack(vectors).astype("float32")

    def _encode_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector


class SentenceTransformerTextEncoder(TextEncoder):
    backend = "sentence_transformers"

    def __init__(self, model_path: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.model_path = model_path
        self.model = SentenceTransformer(model_path, device=device)
        if hasattr(self.model, "get_embedding_dimension"):
            self._dimension = int(self.model.get_embedding_dimension())
        else:
            self._dimension = int(self.model.get_sentence_embedding_dimension())

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        matrix = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(matrix, dtype="float32")


def make_text_encoder(
    backend: str = "hashing",
    model_path: str = "",
    dimension: int = 768,
    device: str | None = None,
) -> TextEncoder:
    normalized = (backend or "hashing").lower()
    if normalized == "hashing":
        return HashingTextEncoder(dimension=dimension)
    if normalized in {"sentence_transformers", "sentence-transformers", "sbert"}:
        if not model_path:
            raise ValueError("model_path is required for sentence_transformers embedding backend")
        return SentenceTransformerTextEncoder(model_path, device=device)
    raise ValueError(f"Unknown embedding backend: {backend}")
