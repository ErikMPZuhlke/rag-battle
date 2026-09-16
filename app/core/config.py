"""Central configuration loaded from environment variables (.env in local/dev)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-20b"

    chroma_persist_dir: str = ".chroma"
    chroma_collection: str = "acme_kb"
    knowledge_base_dir: str = "data/knowledge-base"

    top_k: int = 5
    chunk_size_chars: int = 1800  # ~= 300-400 words, baseline is intentionally coarse

    # Per-question resource budget (see app/core/budget.py)
    max_llm_calls: int = 3
    max_retrievals: int = 10
    max_input_tokens: int = 4000

    no_answer_text: str = "The documentation does not specify this."


settings = Settings()
