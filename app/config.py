"""Central configuration loaded from environment variables (.env in local/dev)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", ".chroma")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "acme_kb")
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "data/knowledge-base")

TOP_K = _int_env("TOP_K", 5)
CHUNK_SIZE_CHARS = _int_env("CHUNK_SIZE_CHARS", 1800)  # ~= 300-400 words, baseline is intentionally coarse

# Per-question resource budget (see app/budget.py)
MAX_LLM_CALLS = _int_env("MAX_LLM_CALLS", 3)
MAX_RETRIEVALS = _int_env("MAX_RETRIEVALS", 10)
MAX_INPUT_TOKENS = _int_env("MAX_INPUT_TOKENS", 4000)

NO_ANSWER_TEXT = "The documentation does not specify this."
