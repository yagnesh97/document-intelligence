from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: ObjectId | None = Field(
        default=None,
        alias="_id",
    )

    filename: str
    object_key: str
    content_type: str
    size: int

    status: DocumentStatus = DocumentStatus.UPLOADED

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None
    error: str | None = None

    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
