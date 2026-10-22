from unittest.mock import Mock, patch

from bson import ObjectId

from app.models.chunk import DocumentChunk
from app.services.chunks import ChunkService


def test_create_many_inserts_chunks():
    service = ChunkService()

    document_id = ObjectId()
    first_chunk_id = ObjectId()
    second_chunk_id = ObjectId()

    chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            content="First paragraph.",
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=1,
            content="Second paragraph.",
        ),
    ]

    with patch.object(
        service.collection,
        "insert_many",
        new_callable=Mock,
    ) as insert_many:
        insert_many.return_value.inserted_ids = [
            first_chunk_id,
            second_chunk_id,
        ]

        result = service.create_many(chunks)

    assert result == chunks

    assert chunks[0].id == first_chunk_id
    assert chunks[1].id == second_chunk_id

    insert_many.assert_called_once()

    inserted_documents = insert_many.call_args.args[0]

    assert inserted_documents == [
        {
            "document_id": document_id,
            "chunk_index": 0,
            "content": "First paragraph.",
            "created_at": chunks[0].created_at,
            "metadata": {},
        },
        {
            "document_id": document_id,
            "chunk_index": 1,
            "content": "Second paragraph.",
            "created_at": chunks[1].created_at,
            "metadata": {},
        },
    ]


def test_create_many_returns_empty_list_for_empty_input():
    service = ChunkService()

    with patch.object(
        service.collection,
        "insert_many",
        new_callable=Mock,
    ) as insert_many:
        result = service.create_many([])

    assert result == []
    insert_many.assert_not_called()
