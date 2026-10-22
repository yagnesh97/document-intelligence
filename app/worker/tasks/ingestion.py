from bson import ObjectId
from celery import Task

from app.models.document import DocumentStatus
from app.services.chunking import chunking_service
from app.services.chunks import chunk_service
from app.services.documents import document_service
from app.services.embeddings import embedding_service
from app.services.parsers import ParserFactory
from app.services.storage import storage_service
from app.services.vectors import vector_service
from app.worker.celery import celery


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def ingest(self: Task, document_id: str):
    return _process_document(ObjectId(document_id))


def _process_document(document_id: ObjectId):
    document = document_service.get(document_id)

    if document is None:
        raise ValueError(f"Document not found: {document_id}")

    document_service.update_status(
        document_id,
        DocumentStatus.PROCESSING,
    )

    try:
        content = storage_service.download_file(document.object_key)

        parser = ParserFactory.get_parser(
            filename=document.filename,
            content_type=document.content_type,
        )

        parsed_document = parser.parse(
            content=content,
            filename=document.filename,
            content_type=document.content_type,
        )

        chunks = chunking_service.chunk(
            document_id=document_id,
            content=parsed_document.content,
        )

        chunks = chunk_service.create_many(chunks)

        if chunks:
            texts = [chunk.content for chunk in chunks]

            embeddings = embedding_service.embed(texts)
            sparse_embeddings = embedding_service.embed_sparse(texts)

            vector_service.ensure_collection()

            vector_service.upsert_chunks(
                chunks=chunks,
                embeddings=embeddings,
                sparse_embeddings=sparse_embeddings,
            )

        document_service.update_result(
            document_id=document_id,
            content=parsed_document.content,
            metadata=parsed_document.metadata,
        )

        document_service.update_status(
            document_id,
            DocumentStatus.COMPLETED,
        )

        return {
            "document_id": str(document_id),
            "status": DocumentStatus.COMPLETED.value,
            "content": parsed_document.content,
            "metadata": parsed_document.metadata,
        }

    except Exception as exc:
        document_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error=str(exc),
        )
        raise
