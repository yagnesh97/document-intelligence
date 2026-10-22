from enum import StrEnum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.models.llm_provider import LLMProvider


class CredentialRef(StrEnum):
    OPENAI_API_KEY = "OPENAI_API_KEY"
    GEMINI_API_KEY = "GEMINI_API_KEY"
    ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"


class OpenAIModel(StrEnum):
    GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"


class GeminiModel(StrEnum):
    GEMINI_3_8_FLASH = "gemini-3.8-flash"


class LLMModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )

    id: ObjectId | None = Field(default=None, alias="_id")

    name: str
    provider: LLMProvider = LLMProvider.OPENAI
    model: OpenAIModel | GeminiModel
    credential_ref: CredentialRef

    # Generation parameters
    reasoning_effort: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None

    # Model metadata
    display_name: str | None = None
    description: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    context_window: int | None = None
    max_output_tokens: int | None = None

    enabled: bool = True
