"""The retrieval-augmented generation pipeline."""

import uuid
from dataclasses import dataclass

from .config import Settings
from .embeddings import Embedder, build_embedder
from .ingest import chunk_pages, extract_pages
from .llm import Generator, build_generator
from .store import Hit, VectorStore


@dataclass
class Answer:
    answer: str
    sources: list[Hit]


class RagPipeline:
    def __init__(
        self, settings: Settings, embedder: Embedder, store: VectorStore, generator: Generator
    ):
        self.settings = settings
        self.embedder = embedder
        self.store = store
        self.generator = generator

    @classmethod
    def from_settings(cls, settings: Settings) -> "RagPipeline":
        embedder = build_embedder(settings)
        store = VectorStore(settings.qdrant_url, settings.collection, embedder.dim)
        return cls(settings, embedder, store, build_generator(settings))

    def ingest(self, filename: str, data: bytes) -> dict:
        pages = extract_pages(filename, data)
        chunks = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            raise ValueError("No extractable text found (scanned PDFs need OCR first).")
        vectors = self.embedder.embed([c.text for c in chunks])
        document_id = str(uuid.uuid4())
        self.store.add(filename, chunks, vectors, document_id)
        return {"document_id": document_id, "filename": filename, "chunks": len(chunks)}

    def retrieve(self, question: str, top_k: int | None = None) -> list[Hit]:
        [vector] = self.embedder.embed([question])
        return self.store.search(vector, top_k or self.settings.top_k)

    def ask(self, question: str, top_k: int | None = None) -> Answer:
        hits = self.retrieve(question, top_k)
        return Answer(self.generator.answer(question, hits), hits)
