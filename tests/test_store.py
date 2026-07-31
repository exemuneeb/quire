import os
import sys
import tempfile
import shutil

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from store.vector_store import VectorStore
from intake.loaders import Doc


class FakeEmbedder:
    """Deterministic fake embedder so tests don't need to download models."""

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)

    @staticmethod
    def _vec(text):
        # crude deterministic embedding based on character codes
        base = [0.0] * 8
        for i, ch in enumerate(text[:64]):
            base[i % 8] += ord(ch) / 1000.0
        return base


@pytest.fixture
def temp_store():
    tmp_dir = tempfile.mkdtemp()
    store = VectorStore(embedder=FakeEmbedder(), persist_dir=tmp_dir)
    yield store
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_add_and_count(temp_store):
    docs = [
        Doc("Cats are great pets.", {"chunk_id": "c1", "source_id": "s1", "filename": "pets.txt"}),
        Doc("Dogs are loyal companions.", {"chunk_id": "c2", "source_id": "s1", "filename": "pets.txt"}),
    ]
    ids = temp_store.add_documents(docs)
    assert len(ids) == 2
    assert temp_store.count() == 2


def test_delete_source_removes_chunks(temp_store):
    docs = [
        Doc("Cats are great pets.", {"chunk_id": "c1", "source_id": "s1", "filename": "pets.txt"}),
        Doc("Rockets go to space.", {"chunk_id": "c2", "source_id": "s2", "filename": "space.txt"}),
    ]
    temp_store.add_documents(docs)
    temp_store.delete_source("s1")
    assert temp_store.count() == 1


def test_similarity_search_returns_results(temp_store):
    docs = [Doc("The sky is blue.", {"chunk_id": "c1", "source_id": "s1", "filename": "sky.txt"})]
    temp_store.add_documents(docs)
    results = temp_store.similarity_search_with_score("sky color", k=1)
    assert len(results) == 1
    assert results[0][0].page_content == "The sky is blue."


def test_reset_clears_collection(temp_store):
    docs = [Doc("hello world", {"chunk_id": "c1", "source_id": "s1", "filename": "a.txt"})]
    temp_store.add_documents(docs)
    temp_store.reset()
    assert temp_store.count() == 0
