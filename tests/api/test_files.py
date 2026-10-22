from unittest.mock import Mock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.main import app
from app.models.document import Document, DocumentStatus

client = TestClient(app)


def test_upload_file():
    document_id = ObjectId()

    document = Document(
        id=document_id,
        filename="statement.txt",
        object_key=f"uploads/{document_id}/original",
        content_type="text/plain",
        size=11,
        status=DocumentStatus.QUEUED,
    )

    with patch(
        "app.api.routes.files.ingestion_service.ingest",
        new_callable=Mock,
        return_value=(document, "task-123"),
    ) as ingest:
        response = client.post(
            "/files",
            files={
                "files": (
                    "statement.txt",
                    b"hello world",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "count": 1,
        "files": [
            {
                "document_id": str(document_id),
                "task_id": "task-123",
                "filename": "statement.txt",
                "size": 11,
                "status": "QUEUED",
            }
        ],
    }

    ingest.assert_called_once()


def test_upload_file_rejects_too_many_files():
    files = [
        (
            "files",
            (
                f"file-{index}.txt",
                b"hello",
                "text/plain",
            ),
        )
        for index in range(11)
    ]

    response = client.post("/files", files=files)

    assert response.status_code == 400
    assert "Maximum" in response.json()["detail"]


def test_upload_file_rejects_file_too_large():
    with patch(
        "app.api.routes.files.settings.max_file_size",
        5,
    ):
        response = client.post(
            "/files",
            files={
                "files": (
                    "statement.txt",
                    b"hello world",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 400
    assert "exceeds the maximum file size" in response.json()["detail"]


def test_get_file():
    document_id = ObjectId()

    document = Document(
        id=document_id,
        filename="statement.txt",
        object_key=f"uploads/{document_id}/original",
        content_type="text/plain",
        size=11,
        status=DocumentStatus.COMPLETED,
        content="hello world",
        metadata={
            "encoding": "utf-8",
        },
    )

    with patch(
        "app.api.routes.files.document_service.get",
        new_callable=Mock,
        return_value=document,
    ) as get_document:
        response = client.get(
            f"/files/{document_id}",
        )

    assert response.status_code == 200

    assert response.json() == {
        "document_id": str(document_id),
        "filename": "statement.txt",
        "content_type": "text/plain",
        "size": 11,
        "status": "COMPLETED",
        "created_at": document.created_at.isoformat(),
        "processed_at": None,
        "error": None,
        "content": "hello world",
        "metadata": {
            "encoding": "utf-8",
        },
    }

    get_document.assert_called_once_with(document_id)


def test_get_file_returns_400_for_invalid_document_id():
    with patch(
        "app.api.routes.files.document_service.get",
        new_callable=Mock,
    ) as get_document:
        response = client.get(
            "/files/document-does-not-exist",
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid document_id",
    }

    get_document.assert_not_called()


def test_get_file_returns_404_when_not_found():
    document_id = ObjectId()

    with patch(
        "app.api.routes.files.document_service.get",
        new_callable=Mock,
        return_value=None,
    ) as get_document:
        response = client.get(
            f"/files/{document_id}",
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document not found",
    }

    get_document.assert_called_once_with(document_id)


def test_list_files():
    first_document = Document(
        id=ObjectId(),
        filename="newer.pdf",
        object_key="uploads/newer/original",
        content_type="application/pdf",
        size=200,
        status=DocumentStatus.COMPLETED,
    )

    second_document = Document(
        id=ObjectId(),
        filename="older.pdf",
        object_key="uploads/older/original",
        content_type="application/pdf",
        size=100,
        status=DocumentStatus.PROCESSING,
    )

    with patch(
        "app.api.routes.files.document_service.list",
        return_value=([first_document, second_document], 2),
    ) as list_documents:
        response = client.get(
            "/files?page=1&page_size=20",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 2

    assert data["items"][0]["document_id"] == str(first_document.id)
    assert data["items"][0]["filename"] == "newer.pdf"
    assert data["items"][0]["status"] == "COMPLETED"

    assert data["items"][1]["document_id"] == str(second_document.id)
    assert data["items"][1]["filename"] == "older.pdf"
    assert data["items"][1]["status"] == "PROCESSING"

    list_documents.assert_called_once_with(
        page=1,
        page_size=20,
        status=None,
    )


def test_list_files_filters_by_status():
    document = Document(
        id=ObjectId(),
        filename="statement.pdf",
        object_key="uploads/statement/original",
        content_type="application/pdf",
        size=200,
        status=DocumentStatus.COMPLETED,
    )

    with patch(
        "app.api.routes.files.document_service.list",
        return_value=([document], 1),
    ) as list_documents:
        response = client.get(
            "/files?page=2&page_size=10&status=COMPLETED",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["page_size"] == 10
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "COMPLETED"

    list_documents.assert_called_once_with(
        page=2,
        page_size=10,
        status=DocumentStatus.COMPLETED,
    )
