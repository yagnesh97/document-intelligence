from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedDocument:
    """
    Common representation returned by document parsers.

    The parser extracts the document content.
    Financial interpretation happens in a later stage.
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """
    Base interface for all document parsers.
    """

    @abstractmethod
    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        """
        Parse raw document bytes into a ParsedDocument.
        """
        raise NotImplementedError
