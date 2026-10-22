from io import BytesIO

import ocrmypdf
import pymupdf

from app.services.parsers.pdf.base import (
    BasePdfParser,
    ParsedPdf,
    PdfAnalysis,
    PdfType,
)


class ImagePdfParser(BasePdfParser):
    """
    Parser for scanned/image-based PDFs.

    OCRmyPDF is used to create an OCR text layer, which is then
    extracted using PyMuPDF.
    """

    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
        analysis: PdfAnalysis | None = None,
    ) -> ParsedPdf:
        ocr_output = BytesIO()

        ocrmypdf.ocr(
            BytesIO(content),
            ocr_output,
            output_type="pdf",
            skip_text=True,
            deskew=True,
            rotate_pages=True,
        )

        ocr_output.seek(0)

        document = pymupdf.open(
            stream=ocr_output.read(),
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
                pdf_type=PdfType.IMAGE,
                metadata={
                    "filename": filename,
                    "content_type": content_type,
                    "page_count": len(document),
                    "ocr": True,
                },
            )

        finally:
            document.close()
