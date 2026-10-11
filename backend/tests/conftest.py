import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.rag import RagPipeline


@pytest.fixture
def settings() -> Settings:
    # Fresh in-memory collection per test; small chunks so tests exercise chunking.
    return Settings(
        qdrant_url=":memory:",
        collection=f"test-{uuid.uuid4().hex}",
        chunk_size=40,
        chunk_overlap=10,
    )


@pytest.fixture
def pipeline(settings) -> RagPipeline:
    return RagPipeline.from_settings(settings)


@pytest.fixture
def client(pipeline):
    with TestClient(app) as c:
        app.state.pipeline = pipeline  # override the one created at startup
        yield c
