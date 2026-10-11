"""Embedding providers behind a common interface."""

import hashlib
import re
from typing import Protocol

import httpx
import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic bag-of-words embedding via feature hashing (unigrams + bigrams).

    Needs no model download, so tests and CI run fully offline. It captures lexical
    overlap only; switch to a neural embedder for semantic search in production.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _features(self, text: str) -> list[str]:
        tokens = _TOKEN.findall(text.lower())
        return tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:], strict=False)]

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            for feat in self._features(text):
                h = int.from_bytes(hashlib.md5(feat.encode()).digest()[:8], "little")
                vec[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
            norm = np.linalg.norm(vec)
            out.append((vec / norm if norm else vec).tolist())
        return out


class OpenAICompatibleEmbedder:
    """Calls any OpenAI-compatible /embeddings endpoint (OpenAI, Ollama, vLLM...)."""

    def __init__(self, base_url: str, api_key: str, model: str, dim: int):
        self.dim = dim
        self.model = model
        self._client = httpx.Client(
            base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=60
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.post("/embeddings", json={"model": self.model, "input": texts})
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]


def build_embedder(settings) -> Embedder:
    if settings.embedding_provider == "hashing":
        return HashingEmbedder(settings.embedding_dim)
    if settings.embedding_provider == "openai":
        return OpenAICompatibleEmbedder(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.embedding_model,
            settings.embedding_dim,
        )
    raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")
