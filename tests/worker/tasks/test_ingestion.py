from unittest.mock import patch

import pytest
from bson import ObjectId

from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus
from app.services.parsers import ParsedDocument
from app.worker.tasks.ingestion import _process_document


def test_process_document_completes_successfully():
    document_id = ObjectId()

    document = Document(
        id=document_id,
        filename="statement.txt",
        object_key=f"uploads/{document_id}/original",
        content_type="text/plain",
        size=11,
        status=DocumentStatus.QUEUED,
    )

    chunk = DocumentChunk(
        id=ObjectId(),
        document_id=document_id,
        chunk_index=0,
        content="hello world",
    )

    parsed_document = ParsedDocument(
        content="hello world",
        metadata={"encoding": "utf-8"},
    )

    embeddings = [[0.1] * 1024]
    sparse_embeddings = [{"indices": [1, 2], "values": [0.5, 0.8]}]

    with (
        patch(
            "app.worker.tasks.ingestion.document_service.get",
            return_value=document,
        ) as get_document,
        patch(
            "app.worker.tasks.ingestion.document_service.update_status",
        ) as update_status,
        patch(
            "app.worker.tasks.ingestion.storage_service.download_file",
            return_value=b"hello world",
        ) as download_file,
        patch(
            "app.worker.tasks.ingestion.ParserFactory.get_parser",
        ) as get_parser,
        patch(
            "app.worker.tasks.ingestion.chunking_service.chunk",
            return_value=[chunk],
        ) as chunk_document,
        patch(
            "app.worker.tasks.ingestion.chunk_service.create_many",
            return_value=[chunk],
        ) as create_chunks,
        patch(
            "app.worker.tasks.ingestion.embedding_service.embed",
            return_value=embeddings,
        ) as embed,
        patch(
            "app.worker.tasks.ingestion.embedding_service.embed_sparse",
            return_value=sparse_embeddings,
        ) as embed_sparse,
        patch(
            "app.worker.tasks.ingestion.vector_service.ensure_collection",
        ) as ensure_collection,
        patch(
            "app.worker.tasks.ingestion.vector_service.upsert_chunks",
        ) as upsert_chunks,
        patch(
            "app.worker.tasks.ingestion.document_service.update_result",
        ) as update_result,
    ):
        parser = get_parser.return_value
        parser.parse.return_value = parsed_document

        result = _process_document(document_id)

    assert result == {
        "document_id": str(document_id),
        "status": DocumentStatus.COMPLETED.value,
        "content": "hello world",
        "metadata": {"encoding": "utf-8"},
    }

    get_document.assert_called_once_with(document_id)
    download_file.assert_called_once_with(document.object_key)

    get_parser.assert_called_once_with(
        filename=document.filename,
        content_type=document.content_type,
    )
    parser.parse.assert_called_once_with(
        content=b"hello world",
        filename=document.filename,
        content_type=document.content_type,
    )

    chunk_document.assert_called_once_with(
        document_id=document_id,
        content="hello world",
    )
    create_chunks.assert_called_once_with([chunk])

    embed.assert_called_once_with(["hello world"])
    embed_sparse.assert_called_once_with(["hello world"])

    ensure_collection.assert_called_once()
    upsert_chunks.assert_called_once_with(
        chunks=[chunk],
        embeddings=embeddings,
        sparse_embeddings=sparse_embeddings,
    )

    update_result.assert_called_once_with(
        document_id=document_id,
        content="hello world",
        metadata={"encoding": "utf-8"},
    )

    update_status.assert_any_call(
        document_id,
        DocumentStatus.PROCESSING,
    )
    update_status.assert_any_call(
        document_id,
        DocumentStatus.COMPLETED,
    )


def test_process_document_marks_failed_when_parsing_fails():
    document_id = ObjectId()

    document = Document(
        id=document_id,
        filename="statement.txt",
        object_key=f"uploads/{document_id}/original",
        content_type="text/plain",
        size=11,
        status=DocumentStatus.QUEUED,
    )

    parsing_error = ValueError("Unable to parse document")

    with (
        patch(
            "app.worker.tasks.ingestion.document_service.get",
            return_value=document,
        ),
        patch(
            "app.worker.tasks.ingestion.document_service.update_status",
        ) as update_status,
        patch(
            "app.worker.tasks.ingestion.storage_service.download_file",
            return_value=b"hello world",
        ),
        patch(
            "app.worker.tasks.ingestion.ParserFactory.get_parser",
        ) as get_parser,
    ):
        parser = get_parser.return_value
        parser.parse.side_effect = parsing_error

        with pytest.raises(ValueError, match="Unable to parse document"):
            _process_document(document_id)

    update_status.assert_any_call(
        document_id,
        DocumentStatus.PROCESSING,
    )
    update_status.assert_any_call(
        document_id,
        DocumentStatus.FAILED,
        error="Unable to parse document",
    )
