from app.services.parsers.base import BaseParser, ParsedDocument
from app.services.parsers.pdf.analyzer import PdfAnalyzer
from app.services.parsers.pdf.factory import PdfParserFactory


class PdfParser(BaseParser):
    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        analysis = PdfAnalyzer.analyze(content)

        parser = PdfParserFactory.get_parser(analysis)

        parsed_pdf = parser.parse(
            content=content,
            filename=filename,
            content_type=content_type,
            analysis=analysis,
        )

        return ParsedDocument(
            content=parsed_pdf.content,
            metadata={
                **parsed_pdf.metadata,
                "pdf_type": parsed_pdf.pdf_type.value,
                **analysis.metadata,
            },
        )
