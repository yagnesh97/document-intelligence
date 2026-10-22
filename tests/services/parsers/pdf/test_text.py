import pymupdf

from app.services.parsers.pdf.base import PdfType
from app.services.parsers.pdf.text import TextPdfParser


def create_text_pdf() -> bytes:
    document = pymupdf.open()

    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Bank Statement\n2026-01-01 Salary 5000\n2026-01-02 Coffee -5",
    )

    content = document.tobytes()
    document.close()

    return content


def test_text_pdf_parser_extracts_text():
    parser = TextPdfParser()

    result = parser.parse(
        content=create_text_pdf(),
        filename="statement.pdf",
        content_type="application/pdf",
    )

    assert result.pdf_type == PdfType.TEXT

    assert "Bank Statement" in result.content
    assert "Salary" in result.content
    assert "5000" in result.content
    assert "Coffee" in result.content

    assert result.metadata["filename"] == "statement.pdf"
    assert result.metadata["content_type"] == "application/pdf"
    assert result.metadata["page_count"] == 1
