import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from intake.chunker import TextChunker
from intake.loaders import Doc, get_file_hash


def test_chunker_respects_chunk_size():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    long_text = "This is a sentence. " * 20
    doc = Doc(page_content=long_text, metadata={"filename": "sample.txt"})
    chunks = chunker.split_documents([doc], source_id="src1")

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.page_content) <= 60  # allow small overlap slack


def test_chunker_tags_metadata():
    chunker = TextChunker(chunk_size=1000, chunk_overlap=0)
    doc = Doc(page_content="short text", metadata={"filename": "a.txt"})
    chunks = chunker.split_documents([doc], source_id="abc123")

    assert len(chunks) == 1
    assert chunks[0].metadata["source_id"] == "abc123"
    assert chunks[0].metadata["chunk_id"] == "abc123_chunk_0"


def test_chunker_empty_text_returns_no_chunks():
    chunker = TextChunker()
    doc = Doc(page_content="", metadata={})
    chunks = chunker.split_documents([doc], source_id="empty")
    assert chunks == []


def test_file_hash_is_deterministic():
    data = b"hello world"
    assert get_file_hash(data) == get_file_hash(data)
    assert get_file_hash(data) != get_file_hash(b"hello world!")
