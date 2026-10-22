from types import SimpleNamespace

import pytest

from app.config import settings
from app.models.llm_model import CredentialRef, GeminiModel, LLMModel, OpenAIModel
from app.models.llm_provider import LLMProvider
from app.services.llm.providers.base import BaseLLMProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.openai import OpenAIProvider


def make_model(**overrides) -> LLMModel:
    data = {
        "name": "test-model",
        "provider": LLMProvider.OPENAI,
        "model": OpenAIModel.GPT_4O_MINI_2024_07_18,
        "credential_ref": CredentialRef.OPENAI_API_KEY,
        "enabled": True,
        "temperature": 0.2,
        "max_tokens": 2000,
    }
    data.update(overrides)
    return LLMModel(**data)


class FakeProvider(BaseLLMProvider):
    def __init__(self, model=None):
        super().__init__(make_model())
        self.model = model


def test_extract_text_from_string():
    assert BaseLLMProvider._extract_text("Hello") == "Hello"


def test_extract_text_from_structured_content():
    content = [
        {"type": "text", "text": "Hello "},
        {"type": "text", "text": "world"},
        {"type": "image", "image_url": "ignored"},
    ]

    assert BaseLLMProvider._extract_text(content) == "Hello world"


def test_extract_text_from_empty_content():
    assert BaseLLMProvider._extract_text([]) == ""


def test_extract_text_from_none():
    assert BaseLLMProvider._extract_text(None) == ""


def test_extract_text_ignores_non_text_items():
    content = [
        {"type": "image", "url": "ignored"},
        {"type": "text", "text": "Financial data"},
        {"type": "text", "text": 123},
    ]

    assert BaseLLMProvider._extract_text(content) == "Financial data"


def test_messages_contain_system_and_user_prompts():
    messages = BaseLLMProvider._messages(
        "System instructions",
        "User question",
    )

    assert len(messages) == 2
    assert messages[0].content == "System instructions"
    assert messages[1].content == "User question"


def test_generate_extracts_response_text():
    fake_model = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(
            content=[
                {"type": "text", "text": "Salary credited: "},
                {"type": "text", "text": "12500.50"},
            ]
        )
    )

    provider = FakeProvider(fake_model)

    result = provider.generate("System", "Question")

    assert result == "Salary credited: 12500.50"


def test_stream_yields_text_chunks():
    chunks = [
        SimpleNamespace(content="Hello "),
        SimpleNamespace(content=[{"type": "text", "text": "world"}]),
        SimpleNamespace(content=""),
    ]

    fake_model = SimpleNamespace(stream=lambda messages: iter(chunks))

    provider = FakeProvider(fake_model)

    result = list(provider.stream("System", "Question"))

    assert result == ["Hello ", "world"]


def test_openai_rejects_wrong_credential_ref():
    with pytest.raises(ValueError):
        make_model(credential_ref="WRONG_KEY")


def test_openai_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(ValueError, match="Missing OPENAI_API_KEY"):
        OpenAIProvider(make_model())


def test_openai_initializes_client(monkeypatch):
    captured = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.llm.providers.openai.ChatOpenAI",
        fake_chat_openai,
    )

    provider = OpenAIProvider(make_model())

    assert provider.model is not None
    assert captured["model"] == OpenAIModel.GPT_4O_MINI_2024_07_18.value
    assert captured["api_key"] == "test-key"
    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 2000


def test_gemini_rejects_wrong_credential_ref():
    with pytest.raises(ValueError):
        make_model(
            provider=LLMProvider.GEMINI,
            model=GeminiModel.GEMINI_3_8_FLASH,
            credential_ref="WRONG_KEY",
        )


def test_gemini_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)

    model_config = make_model(
        provider=LLMProvider.GEMINI,
        model=GeminiModel.GEMINI_3_8_FLASH,
        credential_ref=CredentialRef.GEMINI_API_KEY,
    )

    with pytest.raises(ValueError, match="Missing GEMINI_API_KEY"):
        GeminiProvider(model_config)


def test_gemini_initializes_client(monkeypatch):
    captured = {}

    def fake_gemini(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.llm.providers.gemini.ChatGoogleGenerativeAI",
        fake_gemini,
    )

    model_config = make_model(
        provider=LLMProvider.GEMINI,
        model=GeminiModel.GEMINI_3_8_FLASH,
        credential_ref=CredentialRef.GEMINI_API_KEY,
    )

    provider = GeminiProvider(model_config)

    assert provider.model is not None
    assert captured["model"] == GeminiModel.GEMINI_3_8_FLASH.value
    assert captured["google_api_key"] == "test-key"
    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 2000


def test_gemini_passes_reasoning_effort(monkeypatch):
    captured = {}

    def fake_gemini(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.llm.providers.gemini.ChatGoogleGenerativeAI",
        fake_gemini,
    )

    model_config = make_model(
        provider=LLMProvider.GEMINI,
        model=GeminiModel.GEMINI_3_8_FLASH,
        credential_ref=CredentialRef.GEMINI_API_KEY,
        reasoning_effort="low",
    )

    GeminiProvider(model_config)

    assert captured["thinking_level"] == "low"
