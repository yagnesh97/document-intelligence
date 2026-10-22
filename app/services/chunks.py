from bson import ObjectId

from app.db.mongodb import db
from app.models.chunk import DocumentChunk


class ChunkService:
    def __init__(self):
        self.collection = db.document_chunks

    def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        if not chunks:
            return []

        documents = [
            chunk.model_dump(
                by_alias=True,
                exclude={"id"},
            )
            for chunk in chunks
        ]

        result = self.collection.insert_many(documents)

        for chunk, chunk_id in zip(chunks, result.inserted_ids):
            chunk.id = chunk_id

        return chunks

    def get_by_document(
        self,
        document_id: ObjectId,
    ) -> list[DocumentChunk]:
        cursor = self.collection.find({"document_id": document_id}).sort(
            "chunk_index",
            1,
        )

        return [DocumentChunk.model_validate(data) for data in cursor]

    def delete_by_document(self, document_id: ObjectId) -> int:
        result = self.collection.delete_many({"document_id": document_id})
        return result.deleted_count


chunk_service = ChunkService()
