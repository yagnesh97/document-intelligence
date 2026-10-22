from bson import ObjectId

from app.services.chunks import chunk_service
from app.services.documents import document_service
from app.services.storage import storage_service
from app.services.vectors import vector_service


class DocumentDeletionService:
    def delete(self, document_id: ObjectId) -> bool:
        document = document_service.get(document_id)

        if document is None:
            return False

        vector_service.delete_by_document(document_id)
        chunk_service.delete_by_document(document_id)

        if document.object_key:
            storage_service.delete_file(document.object_key)

        return document_service.delete(document_id)


document_deletion_service = DocumentDeletionService()
