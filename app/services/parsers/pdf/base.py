from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PdfType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    HYBRID = "hybrid"
    EMPTY = "empty"


@dataclass
class PdfPageAnalysis:
    page_number: int
    has_text: bool
    text_length: int
    image_count: int
    image_coverage: float
    requires_ocr: bool


@dataclass
class PdfAnalysis:
    pdf_type: PdfType
    pages: list[PdfPageAnalysis] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedPdf:
    content: str
    pdf_type: PdfType
    metadata: dict[str, Any] = field(default_factory=dict)


class BasePdfParser(ABC):
    @abstractmethod
    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
        analysis: PdfAnalysis | None = None,
    ) -> ParsedPdf:
        raise NotImplementedError
