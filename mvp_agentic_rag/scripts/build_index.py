from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.data_loader import load_corpus
from mvp_agentic_rag.dense_index import build_dense_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local 768-dim hashing FAISS index for the MVP corpus.")
    parser.add_argument("--corpus", default="data/musique_corpus.jsonl")
    parser.add_argument("--index", default="indexes/faiss_musique.index")
    parser.add_argument("--meta", default="indexes/faiss_musique_meta.pkl")
    parser.add_argument("--dimension", type=int, default=768)
    parser.add_argument("--embedding-backend", default="hashing")
    parser.add_argument("--embedding-model", default="")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="")
    args = parser.parse_args()
    corpus = load_corpus(args.corpus)
    summary = build_dense_index(
        corpus,
        args.index,
        args.meta,
        args.dimension,
        embedding_backend=args.embedding_backend,
        embedding_model=args.embedding_model,
        batch_size=args.batch_size,
        device=args.device or None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
