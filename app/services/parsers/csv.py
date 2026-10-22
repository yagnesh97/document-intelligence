import csv
import io

from app.services.parsers.base import BaseParser, ParsedDocument


class CsvParser(BaseParser):
    """
    Parser for CSV documents.

    Converts the CSV into a normalized text representation while
    preserving the original column structure.
    """

    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        text = content.decode("utf-8-sig", errors="replace")

        reader = csv.DictReader(io.StringIO(text))

        rows: list[dict[str, str | None]] = list(reader)

        return ParsedDocument(
            content=text,
            metadata={
                "filename": filename,
                "content_type": content_type,
                "row_count": len(rows),
                "columns": reader.fieldnames or [],
            },
        )
