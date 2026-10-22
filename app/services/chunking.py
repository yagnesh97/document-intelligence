import re

from bson import ObjectId

from app.models.chunk import DocumentChunk


class ChunkingService:
    def chunk(
        self,
        document_id: ObjectId,
        content: str,
    ) -> list[DocumentChunk]:
        paragraphs = re.split(r"\n\s*\n", content.strip())

        chunks: list[DocumentChunk] = []

        for index, paragraph in enumerate(paragraphs):
            text = paragraph.strip()

            if not text:
                continue

            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=text,
                )
            )

        return chunks


chunking_service = ChunkingService()
