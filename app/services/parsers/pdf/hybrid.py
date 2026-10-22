import pymupdf

from app.services.parsers.pdf.base import (
    BasePdfParser,
    ParsedPdf,
    PdfAnalysis,
    PdfType,
)


class HybridPdfParser(BasePdfParser):
    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
        analysis: PdfAnalysis | None = None,
    ) -> ParsedPdf:
        if analysis is None:
            raise ValueError("PDF analysis is required for hybrid parsing")

        document = pymupdf.open(stream=content, filetype="pdf")

        try:
            pages: list[str] = []

            for page_analysis, page in zip(analysis.pages, document):
                if page_analysis.requires_ocr:
                    text_page = page.get_textpage_ocr(full=True, dpi=300)
                    text = page.get_text("text", textpage=text_page).strip()
                else:
                    text = page.get_text("text").strip()

                if text:
                    pages.append(text)

            return ParsedPdf(
                content="\n\n".join(pages),
                pdf_type=PdfType.HYBRID,
                metadata={
                    "filename": filename,
                    "content_type": content_type,
                    "page_count": len(document),
                    "ocr": any(page.requires_ocr for page in analysis.pages),
                },
            )
        finally:
            document.close()
