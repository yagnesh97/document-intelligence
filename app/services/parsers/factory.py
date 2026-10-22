from pathlib import Path
from typing import ClassVar

from app.services.parsers.base import BaseParser


class ParserFactory:
    """
    Creates the appropriate parser for an uploaded document.
    """

    _parsers: ClassVar[dict[str, type[BaseParser]]] = {}

    @classmethod
    def register(
        cls,
        extensions: list[str],
        parser: type[BaseParser],
    ) -> None:
        """
        Register a parser for one or more file extensions.
        """

        for extension in extensions:
            normalized_extension = extension.lower()

            if not normalized_extension.startswith("."):
                normalized_extension = f".{normalized_extension}"

            cls._parsers[normalized_extension] = parser

    @classmethod
    def get_parser(
        cls,
        filename: str,
        content_type: str | None = None,
    ) -> BaseParser:
        """
        Return the parser appropriate for the supplied file.
        """

        extension = Path(filename).suffix.lower()

        parser_class = cls._parsers.get(extension)

        if parser_class is None:
            raise ValueError(
                f"No parser available for file type: {extension or 'unknown'}"
            )

        return parser_class()
