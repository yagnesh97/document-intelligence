import pytest

from app.models.llm_model import CredentialRef, GeminiModel, LLMModel, OpenAIModel
from app.models.llm_provider import LLMProvider
from app.services.llm.factory import LLMFactory


def make_model(**overrides) -> LLMModel:
    data = {
        "name": "test-model",
        "provider": LLMProvider.OPENAI,
        "model": OpenAIModel.GPT_4O_MINI_2024_07_18,
        "credential_ref": CredentialRef.OPENAI_API_KEY,
        "enabled": True,
    }
    data.update(overrides)
    return LLMModel(**data)


def test_create_openai_provider(monkeypatch):
    model_config = make_model()

    class FakeOpenAIProvider:
        def __init__(self, config):
            self.model_config = config

    monkeypatch.setitem(
        LLMFactory._providers,
        LLMProvider.OPENAI,
        FakeOpenAIProvider,
    )

    provider = LLMFactory.create(model_config)

    assert isinstance(provider, FakeOpenAIProvider)
    assert provider.model_config is model_config


def test_create_gemini_provider(monkeypatch):
    model_config = make_model(
        provider=LLMProvider.GEMINI,
        model=GeminiModel.GEMINI_3_8_FLASH,
        credential_ref=CredentialRef.GEMINI_API_KEY,
    )

    class FakeGeminiProvider:
        def __init__(self, config):
            self.model_config = config

    monkeypatch.setitem(
        LLMFactory._providers,
        LLMProvider.GEMINI,
        FakeGeminiProvider,
    )

    provider = LLMFactory.create(model_config)

    assert isinstance(provider, FakeGeminiProvider)
    assert provider.model_config is model_config


def test_disabled_model_raises_value_error():
    model_config = make_model(enabled=False)

    with pytest.raises(ValueError, match="disabled"):
        LLMFactory.create(model_config)


def test_invalid_provider_raises_value_error():
    model_config = make_model().model_copy(update={"provider": "unsupported"})

    with pytest.raises(ValueError):
        LLMFactory.create(model_config)
