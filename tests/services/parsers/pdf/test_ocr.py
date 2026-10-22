from pathlib import Path

from app.services.parsers.pdf.pdf_parser import PdfParser

OCR_FIXTURE = Path("tests/fixtures/pdf/ocr/simple-text-image.pdf")

HYBRID_FIXTURE = Path("tests/fixtures/pdf/ocr/hybrid-text-image.pdf")


def test_image_pdf_parser_extracts_text():
    result = PdfParser().parse(
        content=OCR_FIXTURE.read_bytes(),
        filename=OCR_FIXTURE.name,
        content_type="application/pdf",
    )

    assert result.metadata["pdf_type"] == "image"
    assert result.metadata["ocr"] is True
    assert result.metadata["ocr_page_count"] == 1

    assert "SMART FINANCE" in result.content
    assert "Account Number: 123456" in result.content
    assert "Statement Date: 2026-01-31" in result.content
    assert "Amount: 12500.50" in result.content


def test_hybrid_pdf_parser_extracts_native_and_ocr_text():
    result = PdfParser().parse(
        content=HYBRID_FIXTURE.read_bytes(),
        filename=HYBRID_FIXTURE.name,
        content_type="application/pdf",
    )

    assert result.metadata["pdf_type"] == "hybrid"
    assert result.metadata["ocr"] is True
    assert result.metadata["ocr_page_count"] == 1

    assert "Native PDF text - no OCR required" in result.content
    assert "SMART FINANCE" in result.content
    assert "Account Number: 123456" in result.content
    assert "Amount: 12500.50" in result.content
