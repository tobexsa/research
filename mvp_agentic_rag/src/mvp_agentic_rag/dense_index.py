from __future__ import annotations

import pickle
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np

from .embeddings import HashingTextEncoder, make_text_encoder
from .schemas import Passage


def hashed_embedding(text: str, dimension: int = 768) -> np.ndarray:
    return HashingTextEncoder(dimension=dimension).encode([text])[0]


def build_matrix(
    passages: Iterable[Passage],
    dimension: int = 768,
    embedding_backend: str = "hashing",
    embedding_model: str = "",
    batch_size: int = 32,
    device: str | None = None,
) -> tuple[np.ndarray, list[str], int]:
    ids = []
    texts = []
    for passage in passages:
        ids.append(passage.passage_id)
        texts.append(passage.title + " " + passage.text)
    encoder = make_text_encoder(embedding_backend, embedding_model, dimension=dimension, device=device)
    if not texts:
        return np.zeros((0, encoder.dimension), dtype="float32"), ids, encoder.dimension
    return encoder.encode(texts, batch_size=batch_size), ids, encoder.dimension


def build_dense_index(
    corpus: dict[str, Passage],
    index_path: str | Path,
    meta_path: str | Path,
    dimension: int = 768,
    embedding_backend: str = "hashing",
    embedding_model: str = "",
    batch_size: int = 32,
    device: str | None = None,
) -> dict:
    index_path = Path(index_path)
    meta_path = Path(meta_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    passages = [corpus[pid] for pid in sorted(corpus)]
    matrix, passage_ids, actual_dimension = build_matrix(
        passages,
        dimension=dimension,
        embedding_backend=embedding_backend,
        embedding_model=embedding_model,
        batch_size=batch_size,
        device=device,
    )
    index = faiss.IndexFlatIP(actual_dimension)
    index.add(matrix)
    faiss.write_index(index, str(index_path))
    with meta_path.open("wb") as handle:
        pickle.dump(
            {
                "dimension": actual_dimension,
                "passage_ids": passage_ids,
                "embedding_backend": embedding_backend,
                "embedding_model": embedding_model,
            },
            handle,
        )
    return {
        "documents": len(passage_ids),
        "dimension": actual_dimension,
        "index_path": str(index_path),
        "meta_path": str(meta_path),
        "embedding_backend": embedding_backend,
        "embedding_model": embedding_model,
    }


def load_dense_index(index_path: str | Path, meta_path: str | Path):
    index = faiss.read_index(str(index_path))
    with Path(meta_path).open("rb") as handle:
        meta = pickle.load(handle)
    return index, meta
