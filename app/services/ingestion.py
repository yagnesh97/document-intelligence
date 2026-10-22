from app.models.document import Document, DocumentStatus
from app.services.documents import document_service
from app.services.storage import storage_service
from app.worker.tasks.ingestion import ingest


class IngestionService:
    def ingest(
        self,
        file_object,
        filename: str,
        content_type: str,
        size: int,
    ) -> tuple[Document, str]:
        document = Document(
            filename=filename,
            object_key="",
            content_type=content_type,
            size=size,
            status=DocumentStatus.QUEUED,
        )

        document_id = document_service.create(document)

        object_key = f"uploads/{document_id}/original"

        storage_service.upload_file(
            file_object=file_object,
            object_name=object_key,
            content_type=content_type,
        )

        document_service.update_object_key(
            document_id,
            object_key,
        )

        document = document_service.get(document_id)

        if document is None:
            raise RuntimeError("Document could not be loaded after creation")

        task = ingest.delay(str(document_id))

        return document, task.id


ingestion_service = IngestionService()
