from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.model: SentenceTransformer | None = None
        self.sparse_model: SparseTextEmbedding | None = None

    def _get_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(
                settings.embedding_model,
                token=settings.hf_token,
            )
        return self.model

    def _get_sparse_model(self) -> SparseTextEmbedding:
        if self.sparse_model is None:
            self.sparse_model = SparseTextEmbedding(
                model_name=settings.sparse_embedding_model,
            )
        return self.sparse_model

    def warm_up(self) -> None:
        self._get_model()
        self._get_sparse_model()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self._get_model().encode(
            texts,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed_sparse(
        self,
        texts: list[str],
    ) -> list[dict[str, list[int] | list[float]]]:
        if not texts:
            return []

        embeddings = list(self._get_sparse_model().embed(texts))

        return [
            {
                "indices": embedding.indices.tolist(),
                "values": embedding.values.tolist(),
            }
            for embedding in embeddings
        ]


embedding_service = EmbeddingService()
