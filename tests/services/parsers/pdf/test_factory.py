import pymupdf

from app.services.parsers.pdf.analyzer import PdfAnalyzer
from app.services.parsers.pdf.factory import PdfParserFactory
from app.services.parsers.pdf.text import TextPdfParser


def create_text_pdf() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Test statement")
    content = document.tobytes()
    document.close()
    return content


def test_pdf_parser_factory_returns_text_parser_for_text_pdf():
    content = create_text_pdf()

    analysis = PdfAnalyzer.analyze(content)

    parser = PdfParserFactory.get_parser(analysis)

    assert isinstance(parser, TextPdfParser)
