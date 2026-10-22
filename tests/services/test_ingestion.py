from io import BytesIO
from unittest.mock import patch

from bson import ObjectId

from app.models.document import Document, DocumentStatus
from app.services.ingestion import IngestionService


def test_ingest_uploads_file_creates_document_and_queues_task():
    service = IngestionService()

    file_object = BytesIO(b"hello world")

    document_id = ObjectId()

    document = Document(
        id=document_id,
        filename="statement.txt",
        object_key=f"uploads/{document_id}/original",
        content_type="text/plain",
        size=11,
        status=DocumentStatus.QUEUED,
    )

    with (
        patch(
            "app.services.ingestion.storage_service.upload_file",
        ) as upload_file,
        patch(
            "app.services.ingestion.document_service.create",
            return_value=document_id,
        ) as create_document,
        patch(
            "app.services.ingestion.document_service.update_object_key",
        ) as update_object_key,
        patch(
            "app.services.ingestion.document_service.get",
            return_value=document,
        ) as get_document,
        patch(
            "app.services.ingestion.ingest.delay",
        ) as queue_task,
    ):
        queue_task.return_value.id = "task-123"

        result_document, task_id = service.ingest(
            file_object=file_object,
            filename="statement.txt",
            content_type="text/plain",
            size=11,
        )

    assert result_document.id == document_id
    assert result_document.filename == "statement.txt"
    assert result_document.status == DocumentStatus.QUEUED

    assert task_id == "task-123"

    create_document.assert_called_once()

    created_document = create_document.call_args.args[0]

    assert created_document.id is None
    assert created_document.filename == "statement.txt"
    assert created_document.object_key == ""
    assert created_document.content_type == "text/plain"
    assert created_document.size == 11
    assert created_document.status == DocumentStatus.QUEUED

    upload_file.assert_called_once_with(
        file_object=file_object,
        object_name=f"uploads/{document_id}/original",
        content_type="text/plain",
    )

    update_object_key.assert_called_once_with(
        document_id,
        f"uploads/{document_id}/original",
    )

    get_document.assert_called_once_with(document_id)

    queue_task.assert_called_once_with(str(document_id))
