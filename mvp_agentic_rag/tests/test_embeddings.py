import tempfile
import unittest
from pathlib import Path

import numpy as np

from mvp_agentic_rag.data_loader import load_corpus
from mvp_agentic_rag.dense_index import build_dense_index
from mvp_agentic_rag.embeddings import HashingTextEncoder, make_text_encoder


class EmbeddingBackendTests(unittest.TestCase):
    def test_hashing_encoder_returns_normalized_matrix(self):
        encoder = HashingTextEncoder(dimension=16)
        matrix = encoder.encode(["alpha beta", "gamma"], batch_size=2)

        self.assertEqual(matrix.shape, (2, 16))
        self.assertEqual(matrix.dtype, np.float32)
        self.assertAlmostEqual(float(np.linalg.norm(matrix[0])), 1.0, places=5)

    def test_backend_factory_builds_hashing_encoder(self):
        encoder = make_text_encoder("hashing", dimension=32)
        self.assertEqual(encoder.dimension, 32)

    def test_dense_index_metadata_records_embedding_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_path = Path(tmp) / "corpus.jsonl"
            corpus_path.write_text(
                '{"id":"p1","title":"A","text":"alpha beta"}\n',
                encoding="utf-8",
            )
            corpus = load_corpus(corpus_path)
            summary = build_dense_index(
                corpus,
                Path(tmp) / "index.faiss",
                Path(tmp) / "meta.pkl",
                dimension=32,
                embedding_backend="hashing",
                embedding_model="",
            )

        self.assertEqual(summary["embedding_backend"], "hashing")
        self.assertEqual(summary["dimension"], 32)
