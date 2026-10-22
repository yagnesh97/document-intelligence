from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    model_id: str
    document_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class ChatSource(BaseModel):
    document_id: str | None = None
    chunk_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
