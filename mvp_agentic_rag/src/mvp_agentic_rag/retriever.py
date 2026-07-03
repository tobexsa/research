from __future__ import annotations

import math
import re
from collections import Counter

from .schemas import Passage, Sample

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class LexicalRetriever:
    """Small BM25-like retriever for smoke runs without external dependencies."""

    def __init__(self, corpus: dict[str, Passage]):
        self.corpus = corpus
        self.doc_terms = {pid: Counter(tokenize(p.title + " " + p.text)) for pid, p in corpus.items()}
        self.doc_freq = Counter()
        for terms in self.doc_terms.values():
            for term in terms:
                self.doc_freq[term] += 1
        self.num_docs = max(len(corpus), 1)

    def search(self, query: str, top_k: int) -> list[Passage]:
        query_terms = Counter(tokenize(query))
        scored: list[tuple[float, str]] = []
        for pid, terms in self.doc_terms.items():
            score = 0.0
            length_norm = 1.0 + math.log(sum(terms.values()) + 1)
            for term, qtf in query_terms.items():
                if term not in terms:
                    continue
                idf = math.log((self.num_docs + 1) / (self.doc_freq[term] + 0.5))
                score += qtf * terms[term] * max(idf, 0.05) / length_norm
            scored.append((score, pid))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [self.corpus[pid] for score, pid in scored[:top_k] if score > 0]

    def search_for_sample(self, sample: Sample, top_k: int) -> list[Passage]:
        return self.search(sample.question, top_k)


class OracleRetriever:
    sample_aware = True

    def __init__(self, corpus: dict[str, Passage]):
        self.corpus = corpus
        self.fallback = LexicalRetriever(corpus)

    def search(self, query: str, top_k: int) -> list[Passage]:
        return self.fallback.search(query, top_k)

    def search_for_sample(self, sample: Sample, top_k: int) -> list[Passage]:
        ordered = [self.corpus[pid] for pid in sample.supporting_passage_ids if pid in self.corpus]
        seen = {passage.passage_id for passage in ordered}
        for passage in self.fallback.search(sample.question, top_k):
            if passage.passage_id not in seen:
                ordered.append(passage)
                seen.add(passage.passage_id)
        return ordered[:top_k]


class DenseRetriever:
    def __init__(
        self,
        corpus: dict[str, Passage],
        index_path: str = "indexes/faiss_musique.index",
        meta_path: str = "indexes/faiss_musique_meta.pkl",
        embedding_backend: str = "",
        embedding_model: str = "",
        reranker_backend: str = "",
        reranker_model: str = "",
        rerank_top_n: int | None = None,
        reranker_batch_size: int = 8,
        device: str | None = None,
    ):
        from .dense_index import load_dense_index
        from .embeddings import make_text_encoder
        from .reranker import make_reranker

        self.corpus = corpus
        self.index, self.meta = load_dense_index(index_path, meta_path)
        self.dimension = int(self.meta["dimension"])
        self.passage_ids = list(self.meta["passage_ids"])
        backend = embedding_backend or self.meta.get("embedding_backend", "hashing")
        model = embedding_model or self.meta.get("embedding_model", "")
        self.encoder = make_text_encoder(backend, model, dimension=self.dimension, device=device)
        self.reranker = make_reranker(
            reranker_backend,
            reranker_model,
            device=device,
            batch_size=reranker_batch_size,
        )
        self.rerank_top_n = rerank_top_n

    def search(self, query: str, top_k: int) -> list[Passage]:
        candidate_k = max(top_k, int(self.rerank_top_n or top_k))
        vector = self.encoder.encode([query]).reshape(1, -1)
        scores, indices = self.index.search(vector, candidate_k)
        results = []
        for idx in indices[0]:
            if idx < 0:
                continue
            passage_id = self.passage_ids[int(idx)]
            if passage_id in self.corpus:
                results.append(self.corpus[passage_id])
        return self.reranker.rerank(query, results, top_k)

    def search_for_sample(self, sample: Sample, top_k: int) -> list[Passage]:
        return self.search(sample.question, top_k)


def make_retriever(name: str, corpus: dict[str, Passage], config: dict | None = None):
    config = config or {}
    normalized = name.lower()
    if normalized in {"bm25", "lexical"}:
        return LexicalRetriever(corpus)
    if normalized == "oracle":
        return OracleRetriever(corpus)
    if normalized == "dense":
        return DenseRetriever(
            corpus,
            index_path=config.get("index_path", "indexes/faiss_musique.index"),
            meta_path=config.get("meta_path", "indexes/faiss_musique_meta.pkl"),
            embedding_backend=config.get("embedding_backend", ""),
            embedding_model=config.get("embedding_model", ""),
            reranker_backend=config.get("reranker_backend", ""),
            reranker_model=config.get("reranker_model", ""),
            rerank_top_n=config.get("rerank_top_n"),
            reranker_batch_size=int(config.get("reranker_batch_size", 8)),
            device=config.get("device") or None,
        )
    raise ValueError(f"Unknown retriever: {name}")
