import os
import sys
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from config.settings import get_rotating_key

# Fetching Gemini key using key rotation method (falls back to generic GEMINI_API_KEY if needed)
GEMINI_API_KEY = get_rotating_key("GEMINI_AI_API_KEY")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Source documents ─────────────────────────────────────────────────
DATA_DIR = os.path.join(BASE_DIR, "rag_faiss", "data")

KNOWLEDGE_FILES = {
    "Achievements": os.path.join(BASE_DIR, "Achievements.txt"),
    "Cutoffs": os.path.join(BASE_DIR, "Cutoffs.txt"),
    "Dataset": os.path.join(BASE_DIR, "Dataset.txt"),
    "Departments": os.path.join(BASE_DIR, "Departments.txt"),
    "Fees_Structure": os.path.join(BASE_DIR, "Fees_Structure.txt"),
    "Higher_Education": os.path.join(BASE_DIR, "Higher_Education.txt"),
    "Hostel": os.path.join(BASE_DIR, "Hostel.txt"),
    "Overview": os.path.join(BASE_DIR, "Overview.txt"),
}

# ── Persistence paths ────────────────────────────────────────────────
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "rag_faiss", "embeddings")
PICKLES_DIR = os.path.join(BASE_DIR, "rag_faiss", "pickles")

FAISS_INDEX_PATH = os.path.join(EMBEDDINGS_DIR, "faiss_index.bin")
INDEX_MAP_PATH = os.path.join(EMBEDDINGS_DIR, "index_map.pkl")

# ── Chunking ─────────────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 50

# ── FAISS HNSW tuning ────────────────────────────────────────────────
HNSW_M = 40
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 64

# ── Retrieval defaults ───────────────────────────────────────────────
TOP_K = 5

# ── Gemini embedding model ───────────────────────────────────────────
EMBEDDING_MODEL = "models/gemini-embedding-001"
