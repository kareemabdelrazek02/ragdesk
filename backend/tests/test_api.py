def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_list_ask_delete_flow(client):
    text = b"A multi-stage Dockerfile copies only build output into a small runtime image."
    resp = client.post("/documents", files={"file": ("docker.md", text, "text/markdown")})
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["filename"] == "docker.md" and doc["chunks"] == 1

    assert client.get("/documents").json() == [doc]

    resp = client.post("/ask", json={"question": "Why use a multi-stage Dockerfile?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources"][0]["document"] == "docker.md"
    assert "[1]" in body["answer"]

    assert client.delete(f"/documents/{doc['document_id']}").status_code == 204
    assert client.get("/documents").json() == []


def test_rejects_unsupported_file_type(client):
    resp = client.post("/documents", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
    assert resp.status_code == 415


def test_rejects_empty_document(client):
    resp = client.post("/documents", files={"file": ("empty.txt", b"   ", "text/plain")})
    assert resp.status_code == 422


def test_validates_question(client):
    assert client.post("/ask", json={"question": "x"}).status_code == 422
    assert client.post("/ask", json={"question": "valid question", "top_k": 99}).status_code == 422
