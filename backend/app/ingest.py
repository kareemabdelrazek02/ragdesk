"""Turn uploaded files into page-aware text chunks."""

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int  # 1-based; plain-text files count as a single page
    index: int  # position of the chunk within the document


def extract_pages(filename: str, data: bytes) -> list[str]:
    """Return the text of each page. Raises ValueError for unsupported types."""
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return [page.extract_text() or "" for page in reader.pages]
    if name.endswith(".md"):
        text = data.decode("utf-8", errors="replace")
        # Drop heading markers, emphasis and link syntax so they don't leak into answers.
        text = re.sub(r"^\s{0,3}#{1,6}\s*(.*)$", r"\1.", text, flags=re.MULTILINE)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"[*_`]{1,3}", "", text)
        return [text]
    if name.endswith(".txt"):
        return [data.decode("utf-8", errors="replace")]
    raise ValueError(f"Unsupported file type: {filename}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(pages: list[str], size: int = 200, overlap: int = 40) -> list[Chunk]:
    """Split pages into overlapping word windows; a chunk never spans two pages,
    so every chunk can be cited back to an exact page."""
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and smaller than size")

    chunks: list[Chunk] = []
    step = size - overlap
    for page_no, page_text in enumerate(pages, start=1):
        words = _normalize(page_text).split(" ")
        if words == [""]:
            continue
        for start in range(0, len(words), step):
            window = words[start : start + size]
            chunks.append(Chunk(" ".join(window), page_no, len(chunks)))
            if start + size >= len(words):
                break
    return chunks
