from datetime import UTC, datetime

from bson import ObjectId

from app.db.mongodb import db
from app.models.document import Document, DocumentStatus


class DocumentService:
    def __init__(self):
        self.collection = db.documents

    def create(self, document: Document) -> ObjectId:
        data = document.model_dump(
            by_alias=True,
            exclude={"id"},
        )

        result = self.collection.insert_one(data)

        document.id = result.inserted_id

        return result.inserted_id

    def get(self, document_id: ObjectId) -> Document | None:
        data = self.collection.find_one({"_id": document_id})

        if data is None:
            return None

        return Document.model_validate(data)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: DocumentStatus | None = None,
    ) -> tuple[list[Document], int]:
        query: dict = {}

        if status is not None:
            query["status"] = status.value

        total = self.collection.count_documents(query)

        skip = (page - 1) * page_size

        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        documents = [Document.model_validate(data) for data in cursor]

        return documents, total

    def update_object_key(
        self,
        document_id: ObjectId,
        object_key: str,
    ) -> None:
        self.collection.update_one(
            {"_id": document_id},
            {"$set": {"object_key": object_key}},
        )

    def update_status(
        self,
        document_id: ObjectId,
        status: DocumentStatus,
        error: str | None = None,
    ) -> None:
        update = {"status": status.value}

        if status == DocumentStatus.COMPLETED:
            update["processed_at"] = datetime.now(UTC)

        if error is not None:
            update["error"] = error

        self.collection.update_one(
            {"_id": document_id},
            {"$set": update},
        )

    def update_result(
        self,
        document_id: ObjectId,
        content: str,
        metadata: dict,
    ) -> None:
        self.collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "content": content,
                    "metadata": metadata,
                }
            },
        )

    def delete(self, document_id: ObjectId) -> bool:
        result = self.collection.delete_one({"_id": document_id})
        return result.deleted_count == 1


document_service = DocumentService()
