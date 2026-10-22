import pytest
from bson import ObjectId
from qdrant_client import QdrantClient

from app.models.chunk import DocumentChunk
from app.services.vectors import VectorService


@pytest.fixture
def vector_service():
    client = QdrantClient(":memory:")
    service = VectorService()
    service.client = client
    service.ensure_collection()

    yield service

    client.close()


def test_bge_m3_embedding_can_be_stored_in_qdrant(vector_service):
    document_id = ObjectId()
    chunk_id = ObjectId()

    chunk = DocumentChunk(
        id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        content="Salary credited to account: 12500.50",
    )

    embedding = [0.1] * vector_service.VECTOR_SIZE
    sparse_embedding = {"indices": [1, 2], "values": [0.5, 0.8]}

    vector_service.upsert_chunks(
        chunks=[chunk],
        embeddings=[embedding],
        sparse_embeddings=[sparse_embedding],
    )

    results = vector_service.search(
        embedding=embedding,
        limit=1,
        document_id=document_id,
    )

    assert len(results) == 1

    result = results[0]
    assert result.payload["chunk_id"] == str(chunk_id)
    assert result.payload["document_id"] == str(document_id)
    assert result.payload["content"] == chunk.content


def test_search_can_filter_by_document_id(vector_service):
    first_document_id = ObjectId()
    second_document_id = ObjectId()

    first_chunk = DocumentChunk(
        id=ObjectId(),
        document_id=first_document_id,
        chunk_index=0,
        content="Salary credited to account: 12500.50",
    )

    second_chunk = DocumentChunk(
        id=ObjectId(),
        document_id=second_document_id,
        chunk_index=0,
        content="Electricity bill payment: 3200.00",
    )

    first_embedding = [0.1] * vector_service.VECTOR_SIZE
    second_embedding = [0.2] * vector_service.VECTOR_SIZE
    sparse_embedding = {"indices": [1, 2], "values": [0.5, 0.8]}

    vector_service.upsert_chunks(
        chunks=[first_chunk, second_chunk],
        embeddings=[first_embedding, second_embedding],
        sparse_embeddings=[sparse_embedding, sparse_embedding],
    )

    results = vector_service.search(
        embedding=first_embedding,
        limit=10,
        document_id=first_document_id,
    )

    assert results
    assert all(
        result.payload["document_id"] == str(first_document_id) for result in results
    )
