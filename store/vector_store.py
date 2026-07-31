from typing import List, Tuple, Optional, Any

import chromadb

from intake.loaders import Doc
from config import CHROMA_DIR

COLLECTION_NAME = "nimbus_knowledge_base"


class VectorStore:
    """Native ChromaDB persistent-client adapter (no LangChain vectorstore wrapper)."""

    def __init__(self, embedder: Any = None, persist_dir: str = CHROMA_DIR):
        self.embedder = embedder
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        # embedding_function=None because we compute + pass embeddings ourselves
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks: List[Doc]) -> List[str]:
        """Embed and upsert document chunks into the collection."""
        if not chunks:
            return []

        texts = [c.page_content for c in chunks]
        embeddings = self.embedder.embed_documents(texts) if self.embedder else None

        ids, metadatas = [], []
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.metadata.get("chunk_id", f"chunk_{i}")
            ids.append(chunk_id)
            # Chroma metadata values must be str/int/float/bool
            safe_meta = {k: v for k, v in chunk.metadata.items() if isinstance(v, (str, int, float, bool))}
            metadatas.append(safe_meta)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return ids

    def delete_source(self, source_id: str) -> None:
        """Purge every chunk belonging to a given source_id."""
        try:
            self.collection.delete(where={"source_id": source_id})
        except Exception as e:
            print(f"Chroma delete_source error: {e}")

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Doc, float]]:
        """Semantic similarity search returning (Doc, cosine_distance) pairs."""
        if not self.embedder:
            return []

        query_embedding = self.embedder.embed_query(query)
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, count),
        )

        docs_with_scores: List[Tuple[Doc, float]] = []
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for content, meta, dist in zip(docs_list, metas_list, dists_list):
            docs_with_scores.append((Doc(page_content=content, metadata=meta or {}), float(dist)))

        return docs_with_scores

    def max_marginal_relevance_search(self, query: str, k: int = 4) -> List[Doc]:
        """Simple MMR-flavored fallback: over-fetch, then greedily diversify by content overlap."""
        candidates = self.similarity_search_with_score(query, k=max(k * 3, k))
        if not candidates:
            return []

        selected: List[Doc] = []
        pool = list(candidates)
        selected.append(pool.pop(0)[0])

        def token_overlap(a: str, b: str) -> float:
            sa, sb = set(a.lower().split()), set(b.lower().split())
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        while pool and len(selected) < k:
            best_idx, best_score = 0, -1.0
            for i, (doc, dist) in enumerate(pool):
                relevance = 1.0 - dist
                redundancy = max(token_overlap(doc.page_content, s.page_content) for s in selected)
                mmr_score = 0.7 * relevance - 0.3 * redundancy
                if mmr_score > best_score:
                    best_score, best_idx = mmr_score, i
            selected.append(pool.pop(best_idx)[0])

        return selected

    def reset(self) -> None:
        """Purge the entire collection."""
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0
