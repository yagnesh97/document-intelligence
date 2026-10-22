import pymupdf

from app.services.parsers.pdf.base import (
    BasePdfParser,
    ParsedPdf,
    PdfAnalysis,
    PdfType,
)


class TextPdfParser(BasePdfParser):
    """
    Parser for digitally generated PDFs containing native text.
    """

    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
        analysis: PdfAnalysis | None = None,
    ) -> ParsedPdf:
        document = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        try:
            pages: list[str] = []

            for page in document:
                text = page.get_text("text").strip()

                if text:
                    pages.append(text)

            extracted_text = "\n\n".join(pages)

            return ParsedPdf(
                content=extracted_text,
                pdf_type=PdfType.TEXT,
                metadata={
                    "filename": filename,
                    "content_type": content_type,
                    "page_count": len(document),
                },
            )

        finally:
            document.close()
