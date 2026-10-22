from typing import ClassVar

from app.models.llm_model import LLMModel
from app.models.llm_provider import LLMProvider
from app.services.llm.providers.base import BaseLLMProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.openai import OpenAIProvider


class LLMFactory:
    _providers: ClassVar[dict[LLMProvider, type[BaseLLMProvider]]] = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.GEMINI: GeminiProvider,
    }

    @classmethod
    def create(cls, model_config: LLMModel) -> BaseLLMProvider:
        if not model_config.enabled:
            raise ValueError("LLM model is disabled.")

        provider = LLMProvider(model_config.provider)
        provider_class = cls._providers.get(provider)

        if provider_class is None:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        return provider_class(model_config)
