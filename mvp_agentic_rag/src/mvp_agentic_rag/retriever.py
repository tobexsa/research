from __future__ import annotations

import math
import re
from collections import Counter

from .schemas import Passage, Sample

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def reciprocal_rank_fusion(
    rankings: list[tuple[float, list[Passage]]],
    top_n: int,
    rrf_k: int = 60,
) -> list[Passage]:
    scores: dict[str, float] = {}
    passages: dict[str, Passage] = {}
    for weight, ranking in rankings:
        seen: set[str] = set()
        for rank, passage in enumerate(ranking, start=1):
            if passage.passage_id in seen:
                continue
            seen.add(passage.passage_id)
            passages[passage.passage_id] = passage
            scores[passage.passage_id] = scores.get(passage.passage_id, 0.0) + weight / (rrf_k + rank)
    ordered_ids = sorted(scores, key=lambda passage_id: (-scores[passage_id], passage_id))
    return [passages[passage_id] for passage_id in ordered_ids[:top_n]]


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


class ScopedLexicalRetriever:
    """BM25-like retrieval restricted to runtime-safe per-question contexts."""

    sample_aware = True

    def __init__(self, corpus: dict[str, Passage]):
        self.corpus = corpus
        self._scoped: dict[tuple[str, ...], LexicalRetriever] = {}

    def search(self, query: str, top_k: int) -> list[Passage]:
        return LexicalRetriever(self.corpus).search(query, top_k)

    def search_for_sample(self, sample: Sample, top_k: int, query: str | None = None) -> list[Passage]:
        metadata = sample.metadata if isinstance(sample.metadata, dict) else {}
        candidate_ids = tuple(
            str(value)
            for value in metadata.get("candidate_passage_ids", [])
            if str(value) in self.corpus
        )
        if not candidate_ids:
            raise ValueError("scoped_bm25 requires runtime-safe candidate_passage_ids")
        scoped = self._scoped.get(candidate_ids)
        if scoped is None:
            scoped = LexicalRetriever({passage_id: self.corpus[passage_id] for passage_id in candidate_ids})
            self._scoped[candidate_ids] = scoped
        return scoped.search(query or sample.question, top_k)


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
        self._search_cache: dict[tuple[str, int, int], tuple[Passage, ...]] = {}

    def search(self, query: str, top_k: int) -> list[Passage]:
        candidate_k = max(top_k, int(self.rerank_top_n or top_k))
        cache_key = (query, top_k, candidate_k)
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        vector = self.encoder.encode([query]).reshape(1, -1)
        scores, indices = self.index.search(vector, candidate_k)
        results = []
        for idx in indices[0]:
            if idx < 0:
                continue
            passage_id = self.passage_ids[int(idx)]
            if passage_id in self.corpus:
                results.append(self.corpus[passage_id])
        reranked = self.reranker.rerank(query, results, top_k)
        self._search_cache[cache_key] = tuple(reranked)
        return list(reranked)

    def search_for_sample(self, sample: Sample, top_k: int) -> list[Passage]:
        return self.search(sample.question, top_k)


class HybridRetriever:
    def __init__(
        self,
        corpus: dict[str, Passage],
        index_path: str,
        meta_path: str,
        embedding_backend: str = "",
        embedding_model: str = "",
        reranker_backend: str = "",
        reranker_model: str = "",
        candidate_top_k: int = 100,
        rerank_top_n: int | None = None,
        reranker_batch_size: int = 8,
        device: str | None = None,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
        dense_weight: float = 1.0,
    ):
        from .reranker import make_reranker

        self.lexical = LexicalRetriever(corpus)
        self.dense = DenseRetriever(
            corpus,
            index_path=index_path,
            meta_path=meta_path,
            embedding_backend=embedding_backend,
            embedding_model=embedding_model,
            device=device,
        )
        self.reranker = make_reranker(
            reranker_backend,
            reranker_model,
            device=device,
            batch_size=reranker_batch_size,
        )
        self.candidate_top_k = candidate_top_k
        self.rerank_top_n = rerank_top_n
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self._search_cache: dict[tuple[str, int, int, int], tuple[Passage, ...]] = {}

    def search(self, query: str, top_k: int) -> list[Passage]:
        fusion_top_n = max(top_k, int(self.rerank_top_n or top_k))
        candidate_k = max(top_k, self.candidate_top_k)
        cache_key = (query, top_k, candidate_k, fusion_top_n)
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        lexical_results = self.lexical.search(query, candidate_k)
        dense_results = self.dense.search(query, candidate_k)
        fused = reciprocal_rank_fusion(
            [
                (self.bm25_weight, lexical_results),
                (self.dense_weight, dense_results),
            ],
            top_n=fusion_top_n,
            rrf_k=self.rrf_k,
        )
        reranked = self.reranker.rerank(query, fused, top_k)
        self._search_cache[cache_key] = tuple(reranked)
        return list(reranked)

    def search_for_sample(self, sample: Sample, top_k: int) -> list[Passage]:
        return self.search(sample.question, top_k)


def make_retriever(name: str, corpus: dict[str, Passage], config: dict | None = None):
    config = config or {}
    normalized = name.lower()
    if normalized in {"bm25", "lexical"}:
        return LexicalRetriever(corpus)
    if normalized in {"scoped_bm25", "scoped_lexical"}:
        return ScopedLexicalRetriever(corpus)
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
    if normalized in {"hybrid", "bm25_bge_hybrid"}:
        return HybridRetriever(
            corpus,
            index_path=config.get("index_path", "indexes/faiss_musique.index"),
            meta_path=config.get("meta_path", "indexes/faiss_musique_meta.pkl"),
            embedding_backend=config.get("embedding_backend", ""),
            embedding_model=config.get("embedding_model", ""),
            reranker_backend=config.get("reranker_backend", ""),
            reranker_model=config.get("reranker_model", ""),
            candidate_top_k=int(config.get("hybrid_candidate_top_k", 100)),
            rerank_top_n=config.get("rerank_top_n"),
            reranker_batch_size=int(config.get("reranker_batch_size", 8)),
            device=config.get("device") or None,
            rrf_k=int(config.get("hybrid_rrf_k", 60)),
            bm25_weight=float(config.get("hybrid_bm25_weight", 1.0)),
            dense_weight=float(config.get("hybrid_dense_weight", 1.0)),
        )
    raise ValueError(f"Unknown retriever: {name}")
