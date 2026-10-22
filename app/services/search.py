from typing import Any

from bson import ObjectId

from app.config import settings
from app.services.embeddings import embedding_service
from app.services.reranker import reranker_service
from app.services.vectors import vector_service


class SearchService:
    def search(
        self,
        query: str,
        limit: int = 5,
        document_id: ObjectId | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()

        if not query or limit <= 0:
            return []

        embedding = embedding_service.embed_one(query)
        sparse_embedding = embedding_service.embed_sparse([query])[0]

        search_limit = (
            max(limit, settings.reranker_top_k) if settings.reranker_enabled else limit
        )

        points = vector_service.hybrid_search(
            embedding=embedding,
            sparse_embedding=sparse_embedding,
            limit=search_limit,
            document_id=document_id,
        )

        results = [
            {
                "score": point.score,
                "chunk_id": (point.payload or {}).get("chunk_id"),
                "document_id": (point.payload or {}).get("document_id"),
                "chunk_index": (point.payload or {}).get("chunk_index"),
                "content": (point.payload or {}).get("content"),
                "metadata": (point.payload or {}).get("metadata", {}),
            }
            for point in points
        ]

        return reranker_service.rerank(
            query=query,
            results=results,
            limit=limit,
        )


search_service = SearchService()
