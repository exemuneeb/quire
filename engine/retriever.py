import time
from typing import List, Tuple, Dict, Any

from store.vector_store import VectorStore


class Retriever:
    """Semantic retrieval with distance-threshold filtering + lightweight telemetry."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        search_type: str = "Similarity Search",
        distance_threshold: float = 1.0,
    ) -> Tuple[List[Dict[str, Any]], str, float, Dict[str, Any]]:
        """
        Run retrieval and return (retrieved_items, formatted_context, retrieval_ms, stats).
        """
        start = time.time()

        if search_type == "Maximal Marginal Relevance (MMR)":
            raw_docs = self.vector_store.max_marginal_relevance_search(query, k=top_k)
            doc_score_pairs = [(doc, 0.0) for doc in raw_docs]
        else:
            doc_score_pairs = self.vector_store.similarity_search_with_score(query, k=top_k)

        retrieval_ms = (time.time() - start) * 1000.0

        retrieved_items: List[Dict[str, Any]] = []
        context_parts: List[str] = []
        raw_chars = 0

        for idx, (doc, score) in enumerate(doc_score_pairs):
            if score > distance_threshold:
                continue

            filename = doc.metadata.get("filename", "Unknown Source")
            page = doc.metadata.get("page", 1)
            chunk_id = doc.metadata.get("chunk_id", f"chunk_{idx}")
            raw_chars += len(doc.page_content)

            retrieved_items.append({
                "chunk_id": chunk_id,
                "content": doc.page_content,
                "filename": filename,
                "page": page,
                "score": float(score),
                "char_count": len(doc.page_content),
                "metadata": doc.metadata,
            })
            context_parts.append(f"[Chunk {idx + 1} | {filename} (p.{page})]\n{doc.page_content}")

        formatted_context = "\n\n---\n\n".join(context_parts) if context_parts else "NO_RELEVANT_CONTEXT_FOUND"

        stats = {
            "retrieved_nodes": len(retrieved_items),
            "payload_char_count": len(formatted_context),
            "raw_retrieved_chars": raw_chars,
        }

        return retrieved_items, formatted_context, retrieval_ms, stats
