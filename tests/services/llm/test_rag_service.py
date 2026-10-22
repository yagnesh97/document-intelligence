import importlib

import pytest
from bson import ObjectId

from app.models.llm_model import CredentialRef, LLMModel, OpenAIModel
from app.models.llm_provider import LLMProvider
from app.services.llm.rag_service import RAGService

rag_module = importlib.import_module("app.services.llm.rag_service")


def make_model() -> LLMModel:
    return LLMModel(
        _id=ObjectId(),
        name="test-model",
        provider=LLMProvider.OPENAI,
        model=OpenAIModel.GPT_4O_MINI_2024_07_18,
        credential_ref=CredentialRef.OPENAI_API_KEY,
        enabled=True,
    )


def make_search_result() -> dict:
    return {
        "score": 0.9,
        "chunk_id": str(ObjectId()),
        "document_id": str(ObjectId()),
        "chunk_index": 0,
        "content": "Salary credited to account: 12500.50",
        "metadata": {},
    }


def setup_rag(monkeypatch):
    service = RAGService()
    model_config = make_model()
    results = [make_search_result()]

    monkeypatch.setattr(
        service.model_service,
        "get_by_id",
        lambda model_id: model_config,
    )

    monkeypatch.setattr(
        rag_module.search_service,
        "search",
        lambda **kwargs: results,
    )

    monkeypatch.setattr(
        rag_module.prompt_service,
        "get",
        lambda name: "Test system prompt",
    )

    return service, model_config, results


def test_ask_returns_answer_and_sources(monkeypatch):
    service, model_config, results = setup_rag(monkeypatch)

    class FakeProvider:
        def generate(self, system_prompt, user_prompt):
            assert system_prompt == "Test system prompt"
            assert "12500.50" in user_prompt
            return "Salary credited: 12500.50"

    monkeypatch.setattr(
        rag_module.LLMFactory,
        "create",
        lambda config: FakeProvider(),
    )

    response = service.ask(
        question="What salary was credited?",
        model_id=str(model_config.id),
        limit=5,
        document_id=None,
    )

    assert response["answer"] == "Salary credited: 12500.50"
    assert len(response["sources"]) == 1
    assert response["sources"][0]["content"] == results[0]["content"]


def test_ask_returns_message_when_no_results(monkeypatch):
    service, model_config, _ = setup_rag(monkeypatch)

    monkeypatch.setattr(
        rag_module.search_service,
        "search",
        lambda **kwargs: [],
    )

    response = service.ask(
        question="What salary was credited?",
        model_id=str(model_config.id),
        limit=5,
        document_id=None,
    )

    assert "could not find relevant information" in response["answer"]
    assert response["sources"] == []


def test_ask_rejects_empty_question(monkeypatch):
    service, model_config, _ = setup_rag(monkeypatch)

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        service.ask(
            question="   ",
            model_id=str(model_config.id),
            limit=5,
            document_id=None,
        )


def test_ask_rejects_missing_model(monkeypatch):
    service, _, _ = setup_rag(monkeypatch)

    monkeypatch.setattr(
        service.model_service,
        "get_by_id",
        lambda model_id: None,
    )

    with pytest.raises(
        ValueError,
        match="LLM model configuration not found",
    ):
        service.ask(
            question="What salary was credited?",
            model_id=str(ObjectId()),
            limit=5,
            document_id=None,
        )


def test_ask_rejects_disabled_model(monkeypatch):
    service, model_config, _ = setup_rag(monkeypatch)

    model_config.enabled = False

    with pytest.raises(ValueError, match="disabled"):
        service.ask(
            question="What salary was credited?",
            model_id=str(model_config.id),
            limit=5,
            document_id=None,
        )


def test_stream_yields_tokens(monkeypatch):
    service, model_config, _ = setup_rag(monkeypatch)

    class FakeProvider:
        def stream(self, system_prompt, user_prompt):
            yield "Salary "
            yield "credited: "
            yield "12500.50"

    monkeypatch.setattr(
        rag_module.LLMFactory,
        "create",
        lambda config: FakeProvider(),
    )

    tokens = list(
        service.stream(
            question="What salary was credited?",
            model_id=str(model_config.id),
            limit=5,
            document_id=None,
        )
    )

    assert tokens == [
        "Salary ",
        "credited: ",
        "12500.50",
    ]


def test_stream_returns_message_when_no_results(monkeypatch):
    service, model_config, _ = setup_rag(monkeypatch)

    monkeypatch.setattr(
        rag_module.search_service,
        "search",
        lambda **kwargs: [],
    )

    tokens = list(
        service.stream(
            question="What salary was credited?",
            model_id=str(model_config.id),
            limit=5,
            document_id=None,
        )
    )

    assert len(tokens) == 1
    assert "could not find relevant information" in tokens[0]
