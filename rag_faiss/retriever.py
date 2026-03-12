"""
retriever.py – Load FAISS index once, then answer queries with
sub-50 ms retrieval by looking up pickle chunks via the index map.

Usage (standalone test):
    python -m rag_faiss.retriever
"""

import os
import pickle
import numpy as np
import faiss
import google.generativeai as genai

from rag_faiss.config import (
    GEMINI_API_KEY,
    FAISS_INDEX_PATH,
    INDEX_MAP_PATH,
    PICKLES_DIR,
    TOP_K,
    HNSW_EF_SEARCH,
    EMBEDDING_MODEL,
)

# ── Gemini setup ─────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)

# ── Module-level singletons (loaded once) ────────────────────────────
_faiss_index: faiss.Index | None = None
_index_map: dict[int, tuple[str, int]] | None = None
_pickle_cache: dict[str, list[str]] = {}


def _ensure_loaded():
    """Load FAISS index and index map into memory on first call."""
    global _faiss_index, _index_map

    if _faiss_index is not None:
        return

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(
            f"FAISS index not found at {FAISS_INDEX_PATH}. Run build_index first."
        )

    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    _faiss_index.hnsw.efSearch = HNSW_EF_SEARCH

    with open(INDEX_MAP_PATH, "rb") as f:
        _index_map = pickle.load(f)


def _load_pickle(pickle_filename: str) -> list[str]:
    """Load a pickle file, caching it for repeat access."""
    if pickle_filename not in _pickle_cache:
        path = os.path.join(PICKLES_DIR, pickle_filename)
        with open(path, "rb") as f:
            _pickle_cache[pickle_filename] = pickle.load(f)
    return _pickle_cache[pickle_filename]


def _embed_query(text: str) -> np.ndarray:
    """Embed a single query string and normalise for cosine similarity."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
    )
    vec = np.array([result["embedding"]], dtype=np.float32)
    faiss.normalize_L2(vec)
    return vec


def retrieve(query: str, top_k: int = TOP_K) -> dict:
    """
    Retrieve the most relevant chunks for a query.

    Returns:
        {
            "context": "...concatenated chunk text...",
            "sources": ["Achievements.txt", ...]
        }
    """
    _ensure_loaded()

    query_vec = _embed_query(query)
    distances, ids = _faiss_index.search(query_vec, top_k)

    chunks: list[str] = []
    sources_seen: list[str] = []

    for faiss_id in ids[0]:
        if faiss_id == -1:
            continue

        pickle_filename, chunk_idx = _index_map[int(faiss_id)]
        pickle_chunks = _load_pickle(pickle_filename)
        chunks.append(pickle_chunks[chunk_idx])

        source_txt = pickle_filename.replace(".pkl", ".txt")
        if source_txt not in sources_seen:
            sources_seen.append(source_txt)

    return {
        "context": "\n\n".join(chunks),
        "sources": sources_seen,
    }


# ── Quick CLI test ───────────────────────────────────────────────────
if __name__ == "__main__":
    import time

    _ensure_loaded()
    print(f"[RETRIEVER] FAISS index loaded: {_faiss_index.ntotal} vectors")

    test_queries = [
        "What awards did students win?",
        "CSE Department BC cutoff mark?",
    ]

    for q in test_queries:
        start = time.perf_counter()
        result = retrieve(q)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"\nQuery: {q}")
        print(f"Sources: {result['sources']}")
        print(f"Latency: {elapsed_ms:.1f} ms")
        print(f"Context (first 300 chars): {result['context'][:300]}")
