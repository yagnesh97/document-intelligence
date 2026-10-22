from app.services.parsers.base import BaseParser, ParsedDocument


class TextParser(BaseParser):
    """
    Parser for plain-text documents.
    """

    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")

        return ParsedDocument(
            content=text,
            metadata={
                "filename": filename,
                "content_type": content_type,
                "encoding": "utf-8",
            },
        )
