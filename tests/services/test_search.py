from unittest.mock import Mock, patch

from app.services.search import SearchService


def test_search_returns_formatted_results():
    service = SearchService()
    embedding = [0.1, 0.2, 0.3]
    sparse_embedding = {"indices": [1, 2], "values": [0.5, 0.8]}

    result = Mock()
    result.score = 0.95
    result.payload = {
        "chunk_id": "chunk-123",
        "document_id": "document-123",
        "chunk_index": 0,
        "content": "Account Number: 123456",
        "metadata": {"filename": "statement.pdf"},
    }

    with (
        patch(
            "app.services.search.embedding_service.embed_one",
            return_value=embedding,
        ) as embed_one,
        patch(
            "app.services.search.embedding_service.embed_sparse",
            return_value=[sparse_embedding],
        ) as embed_sparse,
        patch(
            "app.services.search.vector_service.hybrid_search",
            return_value=[result],
        ) as vector_search,
        patch(
            "app.services.search.reranker_service.rerank",
            side_effect=lambda query, results, limit: results[:limit],
        ) as rerank,
    ):
        results = service.search(
            query="What is the account number?",
            limit=5,
        )

    assert results == [
        {
            "score": 0.95,
            "chunk_id": "chunk-123",
            "document_id": "document-123",
            "chunk_index": 0,
            "content": "Account Number: 123456",
            "metadata": {"filename": "statement.pdf"},
        }
    ]

    embed_one.assert_called_once_with("What is the account number?")
    embed_sparse.assert_called_once_with(["What is the account number?"])
    vector_search.assert_called_once_with(
        embedding=embedding,
        sparse_embedding=sparse_embedding,
        limit=10,
        document_id=None,
    )
    rerank.assert_called_once()


def test_search_strips_query_whitespace():
    service = SearchService()
    sparse_embedding = {"indices": [1], "values": [0.5]}

    with (
        patch(
            "app.services.search.embedding_service.embed_one",
            return_value=[0.1, 0.2],
        ) as embed_one,
        patch(
            "app.services.search.embedding_service.embed_sparse",
            return_value=[sparse_embedding],
        ) as embed_sparse,
        patch(
            "app.services.search.vector_service.hybrid_search",
            return_value=[],
        ) as vector_search,
    ):
        results = service.search("  account number  ")

    assert results == []

    embed_one.assert_called_once_with("account number")
    embed_sparse.assert_called_once_with(["account number"])
    vector_search.assert_called_once_with(
        embedding=[0.1, 0.2],
        sparse_embedding=sparse_embedding,
        limit=10,
        document_id=None,
    )


def test_search_returns_empty_for_blank_query():
    service = SearchService()

    with (
        patch(
            "app.services.search.embedding_service.embed_one",
        ) as embed_one,
        patch(
            "app.services.search.embedding_service.embed_sparse",
        ) as embed_sparse,
        patch(
            "app.services.search.vector_service.hybrid_search",
        ) as vector_search,
    ):
        results = service.search("   ")

    assert results == []
    embed_one.assert_not_called()
    embed_sparse.assert_not_called()
    vector_search.assert_not_called()


def test_search_uses_default_limit():
    service = SearchService()
    sparse_embedding = {"indices": [1], "values": [0.5]}

    with (
        patch(
            "app.services.search.embedding_service.embed_one",
            return_value=[0.1, 0.2],
        ),
        patch(
            "app.services.search.embedding_service.embed_sparse",
            return_value=[sparse_embedding],
        ),
        patch(
            "app.services.search.vector_service.hybrid_search",
            return_value=[],
        ) as vector_search,
    ):
        service.search("account number")

    vector_search.assert_called_once_with(
        embedding=[0.1, 0.2],
        sparse_embedding=sparse_embedding,
        limit=10,
        document_id=None,
    )


def test_search_filters_by_document_id():
    service = SearchService()
    embedding = [0.1, 0.2, 0.3]
    sparse_embedding = {"indices": [1], "values": [0.5]}
    document_id = "document-123"

    with (
        patch(
            "app.services.search.embedding_service.embed_one",
            return_value=embedding,
        ) as embed_one,
        patch(
            "app.services.search.embedding_service.embed_sparse",
            return_value=[sparse_embedding],
        ) as embed_sparse,
        patch(
            "app.services.search.vector_service.hybrid_search",
            return_value=[],
        ) as vector_search,
    ):
        results = service.search(
            query="What is the account number?",
            limit=10,
            document_id=document_id,
        )

    assert results == []
    embed_one.assert_called_once_with("What is the account number?")
    embed_sparse.assert_called_once_with(["What is the account number?"])
    vector_search.assert_called_once_with(
        embedding=embedding,
        sparse_embedding=sparse_embedding,
        limit=10,
        document_id=document_id,
    )
