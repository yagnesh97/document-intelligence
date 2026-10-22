from app.services.parsers import (
    CsvParser,
    ExcelParser,
    ParserFactory,
    PdfParser,
    TextParser,
)
from app.services.parsers.pdf.base import (
    BasePdfParser,
    ParsedPdf,
    PdfAnalysis,
    PdfPageAnalysis,
    PdfType,
)


def test_parser_package_imports():
    assert TextParser is not None
    assert CsvParser is not None
    assert ExcelParser is not None
    assert PdfParser is not None
    assert ParserFactory is not None


def test_pdf_package_imports():
    assert BasePdfParser is not None
    assert ParsedPdf is not None
    assert PdfAnalysis is not None
    assert PdfPageAnalysis is not None
    assert PdfType is not None
