import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", str(DATA_DIR / "documents"))
CHROMA_DIR = os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma_db"))
REGISTRY_FILE = os.getenv("REGISTRY_FILE", str(DATA_DIR / "active_sources.json"))
PERFORMANCE_LOG_FILE = os.getenv("PERFORMANCE_LOG_FILE", str(DATA_DIR / "performance_logs.json"))

# Ensure required directories exist
for path_str in [DOCUMENTS_DIR, DATA_DIR, CHROMA_DIR]:
    os.makedirs(path_str, exist_ok=True)

# ─── Default Retrieval / Chunking Settings ─────────────────────────────────
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 6
DEFAULT_DISTANCE_THRESHOLD = 1.0  # cosine distance (0 = identical, 2 = opposite)

# ─── Embedding Models (local SentenceTransformer models) ──────────────────
EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2 (384d)": {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
    },
    "bge-small-en-v1.5 (384d)": {
        "name": "BAAI/bge-small-en-v1.5",
        "dimension": 384,
    },
    "all-mpnet-base-v2 (768d)": {
        "name": "sentence-transformers/all-mpnet-base-v2",
        "dimension": 768,
    },
}
DEFAULT_EMBEDDING_MODEL_KEY = "all-MiniLM-L6-v2 (384d)"

# ─── Groq LLM Models ────────────────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

# ─── Branding ───────────────────────────────────────────────────────────────
APP_NAME = "Quire"
APP_TAGLINE = "Grounded answers from your own documents"
