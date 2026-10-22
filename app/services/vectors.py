import uuid

from bson import ObjectId
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    Fusion,
    FusionQuery,
    MatchValue,
    PointStruct,
    Prefetch,
    ScoredPoint,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.config import settings
from app.models.chunk import DocumentChunk


class VectorService:
    VECTOR_SIZE = 1024
    DENSE_VECTOR_NAME = "dense"
    SPARSE_VECTOR_NAME = "sparse"

    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection

    def health_check(self) -> bool:
        self.client.get_collections()
        return True

    def ensure_collection(self) -> None:
        collections = self.client.get_collections()
        exists = any(
            collection.name == self.collection_name
            for collection in collections.collections
        )

        if exists:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                self.DENSE_VECTOR_NAME: VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                self.SPARSE_VECTOR_NAME: SparseVectorParams(
                    index=SparseIndexParams(),
                )
            },
        )

    def recreate_collection(self) -> None:
        """Destructively recreate the collection with hybrid vector support."""
        collections = self.client.get_collections()
        exists = any(
            collection.name == self.collection_name
            for collection in collections.collections
        )

        if exists:
            self.client.delete_collection(
                collection_name=self.collection_name,
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                self.DENSE_VECTOR_NAME: VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                self.SPARSE_VECTOR_NAME: SparseVectorParams(
                    index=SparseIndexParams(),
                )
            },
        )

    @staticmethod
    def _point_id(chunk_id: ObjectId) -> str:
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_OID,
                str(chunk_id),
            )
        )

    def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
        sparse_embeddings: list[dict[str, list[int] | list[float]]],
    ) -> None:
        if not chunks:
            return

        if not (len(chunks) == len(embeddings) == len(sparse_embeddings)):
            raise ValueError(
                "Chunks, dense embeddings, and sparse embeddings "
                "must have the same length"
            )

        points = []

        for chunk, embedding, sparse_embedding in zip(
            chunks,
            embeddings,
            sparse_embeddings,
            strict=True,
        ):
            if chunk.id is None:
                raise ValueError(
                    "Chunk must have an ID before it can be stored in Qdrant"
                )

            points.append(
                PointStruct(
                    id=self._point_id(chunk.id),
                    vector={
                        self.DENSE_VECTOR_NAME: embedding,
                        self.SPARSE_VECTOR_NAME: SparseVector(
                            indices=sparse_embedding["indices"],
                            values=sparse_embedding["values"],
                        ),
                    },
                    payload={
                        "chunk_id": str(chunk.id),
                        "document_id": str(chunk.document_id),
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        embedding: list[float],
        limit: int = 5,
        document_id: ObjectId | None = None,
    ) -> list[ScoredPoint]:
        """Dense-only search, retained for compatibility."""
        if not embedding or limit <= 0:
            return []

        query_filter = self._document_filter(document_id)

        return self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            using=self.DENSE_VECTOR_NAME,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

    def hybrid_search(
        self,
        embedding: list[float],
        sparse_embedding: dict[str, list[int] | list[float]],
        limit: int = 5,
        document_id: ObjectId | None = None,
    ) -> list[ScoredPoint]:
        if not embedding or limit <= 0:
            return []

        sparse_vector = SparseVector(
            indices=sparse_embedding["indices"],
            values=sparse_embedding["values"],
        )

        query_filter = self._document_filter(document_id)
        candidate_limit = max(limit, 20)

        return self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=embedding,
                    using=self.DENSE_VECTOR_NAME,
                    filter=query_filter,
                    limit=candidate_limit,
                ),
                Prefetch(
                    query=sparse_vector,
                    using=self.SPARSE_VECTOR_NAME,
                    filter=query_filter,
                    limit=candidate_limit,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

    @staticmethod
    def _document_filter(
        document_id: ObjectId | None,
    ) -> Filter | None:
        if document_id is None:
            return None

        return Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=str(document_id)),
                )
            ]
        )

    def delete_by_document(self, document_id: ObjectId) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=self._document_filter(document_id),
            ),
        )


vector_service = VectorService()
