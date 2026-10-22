import pymupdf

from app.services.parsers.pdf.analyzer import PdfAnalyzer
from app.services.parsers.pdf.base import PdfType


def create_text_pdf() -> bytes:
    document = pymupdf.open()

    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Bank Statement\nDate Description Amount",
    )

    content = document.tobytes()
    document.close()

    return content


def create_image_pdf() -> bytes:
    document = pymupdf.open()

    page = document.new_page()

    # Create a large raster image covering most of the page.
    image_document = pymupdf.open()
    image_page = image_document.new_page(width=600, height=800)
    image_page.draw_rect(
        pymupdf.Rect(0, 0, 600, 800),
        color=(0, 0, 0),
        fill=(1, 1, 1),
    )

    image_bytes = image_document.convert_to_pdf()
    image_document.close()

    image_pdf = pymupdf.open(stream=image_bytes, filetype="pdf")
    image_page = image_pdf[0]

    pixmap = image_page.get_pixmap(matrix=pymupdf.Matrix(1, 1))
    image = pixmap.tobytes("png")

    page.insert_image(
        page.rect,
        stream=image,
    )

    content = document.tobytes()

    document.close()

    return content


def test_analyzer_detects_text_pdf():
    analysis = PdfAnalyzer.analyze(create_text_pdf())

    assert analysis.pdf_type == PdfType.TEXT
    assert len(analysis.pages) == 1
    assert analysis.metadata["page_count"] == 1
    assert analysis.metadata["ocr_page_count"] == 0

    page = analysis.pages[0]

    assert page.has_text is True
    assert page.text_length > 0
    assert page.requires_ocr is False


def test_analyzer_detects_image_pdf():
    analysis = PdfAnalyzer.analyze(create_image_pdf())

    assert analysis.pdf_type == PdfType.IMAGE
    assert len(analysis.pages) == 1

    page = analysis.pages[0]

    assert page.has_text is False
    assert page.image_count >= 1
    assert page.requires_ocr is True


def test_analyzer_detects_page_number_over_full_page_image():
    document = pymupdf.open(
        stream=create_image_pdf(),
        filetype="pdf",
    )

    try:
        document[0].insert_text(
            (72, 72),
            "113",
        )
        content = document.tobytes()
    finally:
        document.close()

    analysis = PdfAnalyzer.analyze(content)

    assert analysis.pdf_type == PdfType.IMAGE
    assert analysis.metadata["ocr_page_count"] == 1

    page = analysis.pages[0]

    assert page.has_text is True
    assert page.text_length == 3
    assert page.image_coverage >= 0.50
    assert page.requires_ocr is True
