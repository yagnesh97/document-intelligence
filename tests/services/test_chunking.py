from bson import ObjectId

from app.services.chunking import ChunkingService


def test_chunk_splits_paragraphs():
    service = ChunkingService()

    document_id = ObjectId()

    content = """First paragraph.

Second paragraph.

Third paragraph."""

    chunks = service.chunk(
        document_id=document_id,
        content=content,
    )

    assert len(chunks) == 3

    assert chunks[0].document_id == document_id
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == "First paragraph."

    assert chunks[1].document_id == document_id
    assert chunks[1].chunk_index == 1
    assert chunks[1].content == "Second paragraph."

    assert chunks[2].document_id == document_id
    assert chunks[2].chunk_index == 2
    assert chunks[2].content == "Third paragraph."

    assert chunks[0].id is None
    assert chunks[1].id is None
    assert chunks[2].id is None


def test_chunk_ignores_empty_paragraphs():
    service = ChunkingService()

    document_id = ObjectId()

    content = """

First paragraph.


Second paragraph.


"""

    chunks = service.chunk(
        document_id=document_id,
        content=content,
    )

    assert len(chunks) == 2

    assert chunks[0].document_id == document_id
    assert chunks[0].content == "First paragraph."

    assert chunks[1].document_id == document_id
    assert chunks[1].content == "Second paragraph."


def test_chunk_returns_empty_list_for_empty_content():
    service = ChunkingService()

    document_id = ObjectId()

    chunks = service.chunk(
        document_id=document_id,
        content="",
    )

    assert chunks == []
