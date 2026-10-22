from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.models.llm_model import CredentialRef, LLMModel
from app.services.llm.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_config: LLMModel):
        super().__init__(model_config)

        if model_config.credential_ref != CredentialRef.GEMINI_API_KEY:
            raise ValueError("Unsupported Gemini credential reference.")

        if not settings.gemini_api_key:
            raise ValueError("Missing GEMINI_API_KEY.")

        parameters = model_config.model_dump(
            include={"temperature", "max_tokens", "top_p"},
            exclude_none=True,
        )

        if model_config.reasoning_effort:
            parameters["thinking_level"] = model_config.reasoning_effort

        self.model = ChatGoogleGenerativeAI(
            model=str(model_config.model),
            google_api_key=settings.gemini_api_key,
            **parameters,
        )
