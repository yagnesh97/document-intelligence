from datetime import UTC, datetime
from unittest.mock import Mock, patch

from bson import ObjectId

from app.models.document import DocumentStatus
from app.services.documents import DocumentService


def test_update_status_sets_processed_at_when_completed():
    service = DocumentService()

    document_id = ObjectId()

    with patch.object(
        service.collection,
        "update_one",
        new_callable=Mock,
    ) as update_one:
        service.update_status(
            document_id,
            DocumentStatus.COMPLETED,
        )

    update_one.assert_called_once()

    call = update_one.call_args

    assert call.args[0] == {
        "_id": document_id,
    }

    update = call.args[1]["$set"]

    assert update["status"] == DocumentStatus.COMPLETED.value
    assert "processed_at" in update
    assert update["processed_at"] is not None


def test_update_result_persists_content_and_metadata():
    service = DocumentService()

    document_id = ObjectId()

    with patch.object(
        service.collection,
        "update_one",
        new_callable=Mock,
    ) as update_one:
        service.update_result(
            document_id=document_id,
            content="hello world",
            metadata={
                "encoding": "utf-8",
            },
        )

    update_one.assert_called_once_with(
        {"_id": document_id},
        {
            "$set": {
                "content": "hello world",
                "metadata": {
                    "encoding": "utf-8",
                },
            }
        },
    )


def test_list_returns_documents_newest_first():
    service = DocumentService()

    first_document = {
        "_id": ObjectId(),
        "filename": "older.pdf",
        "object_key": "uploads/older/original",
        "content_type": "application/pdf",
        "size": 100,
        "status": "COMPLETED",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "processed_at": None,
        "error": None,
        "content": None,
        "metadata": {},
    }

    second_document = {
        "_id": ObjectId(),
        "filename": "newer.pdf",
        "object_key": "uploads/newer/original",
        "content_type": "application/pdf",
        "size": 200,
        "status": "PROCESSING",
        "created_at": datetime(2026, 1, 2, tzinfo=UTC),
        "processed_at": None,
        "error": None,
        "content": None,
        "metadata": {},
    }

    with (
        patch.object(
            service.collection,
            "count_documents",
            return_value=2,
        ) as count_documents,
        patch.object(service.collection, "find") as find,
    ):
        cursor = Mock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = [
            second_document,
            first_document,
        ]
        find.return_value = cursor

        documents, total = service.list(
            page=1,
            page_size=20,
        )

    assert total == 2
    assert [document.filename for document in documents] == [
        "newer.pdf",
        "older.pdf",
    ]

    count_documents.assert_called_once_with({})

    find.assert_called_once_with({})

    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.skip.assert_called_once_with(0)
    cursor.limit.assert_called_once_with(20)
