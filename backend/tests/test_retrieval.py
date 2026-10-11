import numpy as np

from app.embeddings import HashingEmbedder
from app.llm import ExtractiveGenerator, build_prompt
from app.store import Hit


def test_hashing_embedder_is_deterministic_and_normalized():
    emb = HashingEmbedder(dim=64)
    a, b = emb.embed(["docker compose file", "docker compose file"])
    assert a == b
    assert np.isclose(np.linalg.norm(a), 1.0)


def test_similar_texts_score_higher():
    emb = HashingEmbedder()
    q, near, far = (
        np.array(v)
        for v in emb.embed(
            [
                "parameterized sql queries",
                "use parameterized queries against sql injection",
                "the robot follows a global path",
            ]
        )
    )
    assert q @ near > q @ far


def test_pipeline_retrieves_the_right_document(pipeline):
    pipeline.ingest("robots.md", b"Nav2 uses a global planner and a local controller.")
    pipeline.ingest("security.md", b"Prevent SQL injection with parameterized queries.")
    hits = pipeline.retrieve("how to prevent SQL injection", top_k=1)
    assert hits[0].document == "security.md"
    assert hits[0].page == 1


def test_extractive_answer_cites_sources():
    hits = [Hit("Docker images package dependencies. Unrelated sentence.", "a.md", "1", 1, 0.9)]
    answer = ExtractiveGenerator().answer("what do docker images package", hits)
    assert "Docker images package dependencies." in answer
    assert "[1]" in answer


def test_extractive_answer_without_hits():
    assert "could not find" in ExtractiveGenerator().answer("anything", [])


def test_prompt_numbers_passages_with_document_and_page():
    prompt = build_prompt("q?", [Hit("text", "a.pdf", "1", 3, 0.5)])
    assert "[1] (a.pdf, page 3)" in prompt
