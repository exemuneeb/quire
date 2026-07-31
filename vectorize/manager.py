from typing import List

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL_KEY


class LocalEmbedder:
    """Native wrapper around a local SentenceTransformer model (no LangChain)."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self.model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        return vector.tolist()


class EmbeddingManager:
    """Factory for local embedding models keyed by the friendly names in config."""

    @staticmethod
    def get_embedder(model_key: str) -> LocalEmbedder:
        if model_key not in EMBEDDING_MODELS:
            model_key = DEFAULT_EMBEDDING_MODEL_KEY
        model_name = EMBEDDING_MODELS[model_key]["name"]
        return LocalEmbedder(model_name=model_name)

    @staticmethod
    def get_dimension(model_key: str) -> int:
        return EMBEDDING_MODELS.get(model_key, EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL_KEY])["dimension"]
