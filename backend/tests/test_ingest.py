import io

import pytest
from pypdf import PdfWriter

from app.ingest import chunk_pages, extract_pages


def test_chunks_overlap_and_cover_all_words():
    words = [f"w{i}" for i in range(100)]
    chunks = chunk_pages([" ".join(words)], size=30, overlap=10)
    assert [len(c.text.split()) for c in chunks][:-1] == [30, 30, 30, 30]
    assert chunks[1].text.split()[:10] == chunks[0].text.split()[-10:]  # overlap
    covered = {w for c in chunks for w in c.text.split()}
    assert covered == set(words)


def test_chunks_never_span_pages_and_keep_page_numbers():
    chunks = chunk_pages(["alpha beta gamma", "", "delta epsilon"], size=10, overlap=2)
    assert [(c.page, c.text) for c in chunks] == [(1, "alpha beta gamma"), (3, "delta epsilon")]
    assert [c.index for c in chunks] == [0, 1]


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, 10), (10, -1)])
def test_invalid_chunk_params(size, overlap):
    with pytest.raises(ValueError):
        chunk_pages(["text"], size=size, overlap=overlap)


def test_extract_plain_text():
    assert extract_pages("notes.txt", b"# Hi\nthere") == ["# Hi\nthere"]


def test_extract_markdown_strips_syntax():
    md = b"# Title\nUse **bold** and a [link](https://x.io) with `code`."
    assert extract_pages("notes.md", md) == ["Title.\nUse bold and a link with code."]


def test_extract_pdf_pages():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    assert len(extract_pages("doc.pdf", buf.getvalue())) == 2


def test_unsupported_type():
    with pytest.raises(ValueError):
        extract_pages("image.png", b"...")
