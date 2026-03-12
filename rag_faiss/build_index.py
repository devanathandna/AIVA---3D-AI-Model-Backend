"""
build_index.py – Read .txt sources, chunk them, embed via Gemini,
build a FAISS HNSW index, and persist pickle + mapping files.

Usage:
    python -m rag_faiss.build_index
"""

import os
import pickle
import time
import numpy as np
import faiss
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_faiss.config import (
    GEMINI_API_KEY,
    KNOWLEDGE_FILES,
    EMBEDDINGS_DIR,
    PICKLES_DIR,
    FAISS_INDEX_PATH,
    INDEX_MAP_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    HNSW_M,
    HNSW_EF_CONSTRUCTION,
    EMBEDDING_MODEL,
)

# ── Gemini setup ─────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _embed_texts(texts: list[str], batch_size: int = 10) -> np.ndarray:
    """Embed a list of texts using Gemini, respecting the free-tier 100 req/min limit."""
    all_embeddings: list[list[float]] = []
    requests_this_window = 0
    window_start = time.time()

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # If we're about to exceed 95 requests in this 60-second window, wait
        if requests_this_window + len(batch) > 95:
            elapsed = time.time() - window_start
            wait = max(0, 62 - elapsed)
            if wait > 0:
                print(f"[INDEX] Rate limit pause: {wait:.0f}s ...")
                time.sleep(wait)
            requests_this_window = 0
            window_start = time.time()

        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=batch,
        )
        all_embeddings.extend(result["embedding"])
        requests_this_window += len(batch)

        done = min(i + batch_size, len(texts))
        print(f"[INDEX] Embedded {done}/{len(texts)} chunks")

        # Small pause between batches
        if done < len(texts):
            time.sleep(0.5)

    return np.array(all_embeddings, dtype=np.float32)


def build():
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    os.makedirs(PICKLES_DIR, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    all_chunks: list[str] = []
    index_map: dict[int, tuple[str, int]] = {}
    global_id = 0

    for source_name, file_path in KNOWLEDGE_FILES.items():
        if not os.path.exists(file_path):
            print(f"[WARN] Skipping missing file: {file_path}")
            continue

        raw_text = _read_text_file(file_path)
        if not raw_text:
            continue

        chunks = splitter.split_text(raw_text)
        pickle_filename = f"{source_name}.pkl"

        # Save chunk texts as a pickle
        pickle_path = os.path.join(PICKLES_DIR, pickle_filename)
        with open(pickle_path, "wb") as pf:
            pickle.dump(chunks, pf)

        # Register each chunk in the global map
        for chunk_idx, chunk_text in enumerate(chunks):
            index_map[global_id] = (pickle_filename, chunk_idx)
            all_chunks.append(chunk_text)
            global_id += 1

        print(f"[INDEX] {source_name}: {len(chunks)} chunks → {pickle_filename}")

    if not all_chunks:
        print("[INDEX] No chunks to index.")
        return

    # ── Embed all chunks ─────────────────────────────────────────────
    print(f"[INDEX] Embedding {len(all_chunks)} chunks via {EMBEDDING_MODEL} ...")
    vectors = _embed_texts(all_chunks)
    dim = vectors.shape[1]
    print(f"[INDEX] Embedding dimension: {dim}")

    # ── Normalise for cosine similarity ──────────────────────────────
    faiss.normalize_L2(vectors)

    # ── Build HNSW index ─────────────────────────────────────────────
    index = faiss.IndexHNSWFlat(dim, HNSW_M, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
    index.add(vectors)
    print(f"[INDEX] FAISS HNSW index built with {index.ntotal} vectors")

    # ── Persist ──────────────────────────────────────────────────────
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(INDEX_MAP_PATH, "wb") as mf:
        pickle.dump(index_map, mf)

    print(f"[INDEX] Saved index  → {FAISS_INDEX_PATH}")
    print(f"[INDEX] Saved map    → {INDEX_MAP_PATH}")
    print("[INDEX] Done.")


if __name__ == "__main__":
    build()
