from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Vector store: ":memory:" for tests/local dev, or e.g. "http://qdrant:6333"
    qdrant_url: str = ":memory:"
    collection: str = "ragdesk"

    # Embeddings: "hashing" (offline, deterministic) or "openai" (any OpenAI-compatible API)
    embedding_provider: str = "hashing"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 384

    # LLM: "extractive" (no model needed) or "openai" (OpenAI, Ollama, vLLM, LM Studio...)
    llm_provider: str = "extractive"
    llm_model: str = "llama3.2"
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"

    chunk_size: int = 200  # words
    chunk_overlap: int = 40  # words
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
