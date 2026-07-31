import time
from typing import List

from intake.loaders import Doc
from config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


class TextChunker:
    """Pure-Python recursive character text splitter (no LangChain)."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def _split(self, text: str, separators: List[str]) -> List[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []
        pieces = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        buffer: List[str] = []
        buffer_len = 0

        for piece in pieces:
            item = piece + (sep if sep else "")
            item_len = len(item)

            if item_len > self.chunk_size:
                if buffer:
                    chunks.append("".join(buffer).strip())
                    buffer, buffer_len = [], 0
                if remaining_seps:
                    chunks.extend(self._split(piece, remaining_seps))
                else:
                    chunks.append(piece[: self.chunk_size])
            elif buffer_len + item_len <= self.chunk_size:
                buffer.append(item)
                buffer_len += item_len
            else:
                if buffer:
                    chunks.append("".join(buffer).strip())
                overlap_tail = "".join(buffer)[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                buffer = [overlap_tail, item] if overlap_tail else [item]
                buffer_len = len("".join(buffer))

        if buffer:
            tail = "".join(buffer).strip()
            if tail:
                chunks.append(tail)

        return [c for c in chunks if c.strip()]

    def split_documents(self, docs: List[Doc], source_id: str) -> List[Doc]:
        """Split documents into overlapping chunks, tagging each with lineage metadata."""
        chunked: List[Doc] = []
        timestamp = int(time.time())
        idx = 0

        for doc in docs:
            for split_text in self._split(doc.page_content, self.separators):
                meta = dict(doc.metadata)
                meta.update({
                    "source_id": source_id,
                    "chunk_id": f"{source_id}_chunk_{idx}",
                    "chunk_index": idx,
                    "chunk_size": len(split_text),
                    "ingested_at": timestamp,
                })
                chunked.append(Doc(page_content=split_text, metadata=meta))
                idx += 1

        return chunked
