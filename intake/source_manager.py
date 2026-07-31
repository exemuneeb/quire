import os
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple

from config import REGISTRY_FILE, DOCUMENTS_DIR, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from intake.loaders import DocumentLoader, Doc, get_file_hash
from intake.chunker import TextChunker


class SourceManager:
    """Tracks active knowledge sources (files & URLs) and coordinates ingestion.

    The registry itself is a simple local JSON file — it only stores lightweight
    metadata (filename, size, chunk counts...). The actual vector embeddings
    live in ChromaDB, keyed by the same `source_id`, so deleting a source here
    can be paired with a purge in the vector store for a true delete.
    """

    def __init__(self, registry_file: str = REGISTRY_FILE, docs_dir: str = DOCUMENTS_DIR):
        self.registry_file = registry_file
        self.docs_dir = docs_dir
        os.makedirs(self.docs_dir, exist_ok=True)
        if not os.path.exists(self.registry_file):
            self._save_registry({})

    def _save_registry(self, registry: Dict[str, Dict[str, Any]]) -> None:
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)

    def load_registry(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_active_sources(self) -> List[Dict[str, Any]]:
        return list(self.load_registry().values())

    def add_file(
        self,
        file_name: str,
        file_bytes: bytes,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> Tuple[Dict[str, Any], List[Doc]]:
        """Persist an uploaded file briefly, extract + chunk it, and register it."""
        source_id = str(uuid.uuid4())[:8]
        file_hash = get_file_hash(file_bytes)

        save_path = os.path.join(self.docs_dir, f"{source_id}_{file_name}")
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        try:
            raw_docs = DocumentLoader.load_file(save_path)
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.split_documents(raw_docs, source_id=source_id)
        finally:
            try:
                os.remove(save_path)
            except OSError:
                pass

        source_info = {
            "source_id": source_id,
            "filename": file_name,
            "source_type": os.path.splitext(file_name)[1].lstrip(".").lower() or "file",
            "file_size": len(file_bytes),
            "file_hash": file_hash,
            "total_chunks": len(chunks),
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }

        registry = self.load_registry()
        registry[source_id] = source_info
        self._save_registry(registry)

        return source_info, chunks

    def add_url(
        self,
        url: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> Tuple[Dict[str, Any], List[Doc]]:
        """Fetch, extract, chunk, and register a web page as a knowledge source."""
        source_id = str(uuid.uuid4())[:8]
        raw_docs = DocumentLoader.load_url(url)
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.split_documents(raw_docs, source_id=source_id)

        total_chars = sum(len(d.page_content) for d in raw_docs)
        source_info = {
            "source_id": source_id,
            "filename": url,
            "source_type": "url",
            "file_size": total_chars,
            "file_hash": get_file_hash(url.encode("utf-8")),
            "total_chunks": len(chunks),
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }

        registry = self.load_registry()
        registry[source_id] = source_info
        self._save_registry(registry)

        return source_info, chunks

    def remove_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        registry = self.load_registry()
        info = registry.pop(source_id, None)
        if info is not None:
            self._save_registry(registry)
        return info

    def clear_all(self) -> None:
        self._save_registry({})
