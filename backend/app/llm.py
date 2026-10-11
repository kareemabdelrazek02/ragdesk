"""Answer generators: an offline extractive fallback and any OpenAI-compatible chat model."""

import re
from typing import Protocol

import httpx

from .store import Hit

SYSTEM_PROMPT = (
    "You answer questions using ONLY the numbered context passages. "
    "Cite every claim with the passage number in square brackets, e.g. [1] or [2][3]. "
    "If the context does not contain the answer, say you could not find it in the documents."
)


def build_prompt(question: str, hits: list[Hit]) -> str:
    context = "\n\n".join(
        f"[{i}] ({h.document}, page {h.page})\n{h.text}" for i, h in enumerate(hits, start=1)
    )
    return f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"


class Generator(Protocol):
    def answer(self, question: str, hits: list[Hit]) -> str: ...


class ExtractiveGenerator:
    """No-LLM fallback: returns the sentences that best overlap the question, with citations.
    Keeps the app usable (and testable) without any model or API key."""

    _word = re.compile(r"[a-z0-9]+")

    def answer(self, question: str, hits: list[Hit]) -> str:
        if not hits:
            return "I could not find anything relevant in the uploaded documents."
        q = set(self._word.findall(question.lower()))
        scored = []
        for i, hit in enumerate(hits, start=1):
            for sentence in re.split(r"(?<=[.!?])\s+", hit.text):
                overlap = len(q & set(self._word.findall(sentence.lower())))
                if overlap:
                    scored.append((overlap, -i, sentence.strip(), i))
        if not scored:
            return "I could not find anything relevant in the uploaded documents."
        best = sorted(scored, reverse=True)[:2]
        return " ".join(f"{s} [{i}]" for _, _, s, i in best)


class OpenAICompatibleGenerator:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._client = httpx.Client(
            base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=120
        )

    def answer(self, question: str, hits: list[Hit]) -> str:
        resp = self._client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_prompt(question, hits)},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def build_generator(settings) -> Generator:
    if settings.llm_provider == "extractive":
        return ExtractiveGenerator()
    if settings.llm_provider == "openai":
        return OpenAICompatibleGenerator(
            settings.openai_base_url, settings.openai_api_key, settings.llm_model
        )
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
