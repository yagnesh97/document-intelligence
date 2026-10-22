from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.llm_model import CredentialRef, LLMModel
from app.services.llm.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_config: LLMModel):
        super().__init__(model_config)

        if model_config.credential_ref != CredentialRef.OPENAI_API_KEY:
            raise ValueError("Unsupported OpenAI credential reference.")

        if not settings.openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY.")

        parameters = model_config.model_dump(
            include={"temperature", "max_tokens", "top_p"},
            exclude_none=True,
        )

        self.model = ChatOpenAI(
            model=str(model_config.model),
            api_key=settings.openai_api_key,
            **parameters,
        )
