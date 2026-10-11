"""FastAPI application exposing the RAG pipeline over HTTP."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import get_settings
from .ingest import SUPPORTED_EXTENSIONS
from .rag import RagPipeline

MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pipeline = RagPipeline.from_settings(get_settings())
    yield


app = FastAPI(title="ragdesk", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pipeline(request: Request) -> RagPipeline:
    return request.app.state.pipeline


Pipeline = Annotated[RagPipeline, Depends(get_pipeline)]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    document: str
    page: int
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/documents", status_code=201)
async def upload(file: Annotated[UploadFile, File()], rag: Pipeline) -> dict:
    name = file.filename or ""
    if not any(name.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        raise HTTPException(415, f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 20 MB)")
    try:
        return rag.ingest(name, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/documents")
def list_documents(rag: Pipeline) -> list[dict]:
    return rag.store.documents()


@app.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, rag: Pipeline) -> None:
    rag.store.delete_document(document_id)


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, rag: Pipeline) -> AskResponse:
    result = rag.ask(body.question, body.top_k)
    return AskResponse(
        answer=result.answer,
        sources=[
            Source(document=h.document, page=h.page, score=h.score, text=h.text)
            for h in result.sources
        ],
    )
