"""Thin wrapper around Qdrant for storing and searching chunks."""

import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from .ingest import Chunk


@dataclass
class Hit:
    text: str
    document: str
    document_id: str
    page: int
    score: float


class VectorStore:
    def __init__(self, url: str, collection: str, dim: int):
        self.client = QdrantClient(location=url) if url == ":memory:" else QdrantClient(url=url)
        self.collection = collection
        if not self.client.collection_exists(collection):
            self.client.create_collection(
                collection,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def add(
        self, document: str, chunks: list[Chunk], vectors: list[list[float]], document_id: str
    ) -> None:
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": c.text,
                    "page": c.page,
                    "chunk": c.index,
                    "document": document,
                    "document_id": document_id,
                },
            )
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(self.collection, points=points, wait=True)

    def search(self, vector: list[float], top_k: int) -> list[Hit]:
        result = self.client.query_points(
            self.collection, query=vector, limit=top_k, with_payload=True
        )
        return [
            Hit(
                text=p.payload["text"],
                document=p.payload["document"],
                document_id=p.payload["document_id"],
                page=p.payload["page"],
                score=float(p.score),
            )
            for p in result.points
        ]

    def documents(self) -> list[dict]:
        """List distinct documents with their chunk counts."""
        counts: dict[str, dict] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                self.collection, limit=256, offset=offset, with_payload=True, with_vectors=False
            )
            for p in points:
                doc_id = p.payload["document_id"]
                entry = counts.setdefault(
                    doc_id, {"document_id": doc_id, "filename": p.payload["document"], "chunks": 0}
                )
                entry["chunks"] += 1
            if offset is None:
                break
        return sorted(counts.values(), key=lambda d: d["filename"])

    def delete_document(self, document_id: str) -> None:
        self.client.delete(
            self.collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id", match=models.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
            wait=True,
        )
