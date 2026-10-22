import pymupdf

from app.services.parsers.pdf.pdf_parser import PdfParser


def create_text_pdf() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Bank statement")
    content = document.tobytes()
    document.close()
    return content


def test_pdf_parser_parses_text_pdf():
    parser = PdfParser()

    result = parser.parse(
        content=create_text_pdf(),
        filename="statement.pdf",
        content_type="application/pdf",
    )

    assert result.content == "Bank statement"
    assert result.metadata["pdf_type"] == "text"
    assert result.metadata["page_count"] == 1
    assert result.metadata["ocr_page_count"] == 0
