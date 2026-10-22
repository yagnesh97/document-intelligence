from pathlib import Path

import pytest

from app.services.parsers.pdf.analyzer import PdfAnalyzer
from app.services.parsers.pdf.base import PdfType

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "pdf" / "sample-files"


REAL_PDF_CASES = [
    (
        "001-trivial/minimal-document.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "002-trivial-libre-office-writer/002-trivial-libre-office-writer.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "003-pdflatex-image/pdflatex-image.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "004-pdflatex-4-pages/pdflatex-4-pages.pdf",
        PdfType.TEXT,
        4,
        0,
    ),
    (
        "006-pdflatex-outline/pdflatex-outline.pdf",
        PdfType.TEXT,
        4,
        0,
    ),
    (
        "007-imagemagick-images/imagemagick-ASCII85Decode.pdf",
        PdfType.IMAGE,
        1,
        1,
    ),
    (
        "007-imagemagick-images/imagemagick-CCITTFaxDecode.pdf",
        PdfType.IMAGE,
        1,
        1,
    ),
    (
        "007-imagemagick-images/imagemagick-images.pdf",
        PdfType.IMAGE,
        6,
        6,
    ),
    (
        "007-imagemagick-images/imagemagick-lzw.pdf",
        PdfType.IMAGE,
        1,
        1,
    ),
    (
        "008-reportlab-inline-image/inline-image.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "009-pdflatex-geotopo/GeoTopo-komprimiert.pdf",
        PdfType.TEXT,
        117,
        0,
    ),
    (
        "009-pdflatex-geotopo/GeoTopo.pdf",
        PdfType.TEXT,
        117,
        0,
    ),
    (
        "010-pdflatex-forms/pdflatex-forms.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "011-google-doc-document/google-doc-document.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "012-libreoffice-form/libreoffice-form.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "013-reportlab-overlay/reportlab-overlay.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "014-outlines/mistitled_outlines_example.pdf",
        PdfType.TEXT,
        4,
        0,
    ),
    (
        "015-arabic/habibi-oneline-cmap.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "015-arabic/habibi-rotated.pdf",
        PdfType.TEXT,
        4,
        0,
    ),
    (
        "015-arabic/habibi.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "016-libre-office-link/libre-office-link.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "017-unreadable-meta-data/unreadablemetadata.pdf",
        PdfType.EMPTY,
        0,
        0,
    ),
    (
        "018-base64-image/base64image.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "019-grayscale-image/grayscale-image.pdf",
        PdfType.IMAGE,
        1,
        1,
    ),
    (
        "020-xmp/output_with_metadata_pymupdf.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "021-pdfa/crazyones-pdfa.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "022-pdfkit/pdfkit.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "023-cmyk-image/cmyk-image.pdf",
        PdfType.IMAGE,
        1,
        1,
    ),
    (
        "024-annotations/annotated_pdf.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "025-attachment/with-attachment.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
    (
        "026-latex-multicolumn/multicolumn.pdf",
        PdfType.TEXT,
        3,
        0,
    ),
    (
        "027-cropped-rotated-scaled/cropped-rotated-scaled.pdf",
        PdfType.TEXT,
        4,
        0,
    ),
    (
        "028-image-references-deduplication/wrong-references.pdf",
        PdfType.TEXT,
        3,
        0,
    ),
    (
        "029-optional-content-groups/ocg_map_test.pdf",
        PdfType.TEXT,
        1,
        0,
    ),
]


@pytest.mark.parametrize(
    ("relative_path", "expected_type", "expected_pages", "expected_ocr_pages"),
    REAL_PDF_CASES,
)
def test_real_pdf_analysis(
    relative_path: str,
    expected_type: PdfType,
    expected_pages: int,
    expected_ocr_pages: int,
):
    pdf_path = FIXTURE_DIR / relative_path

    assert pdf_path.exists(), f"Missing fixture: {pdf_path}"

    analysis = PdfAnalyzer.analyze(pdf_path.read_bytes())

    assert analysis.pdf_type == expected_type
    assert analysis.metadata["page_count"] == expected_pages
    assert analysis.metadata["ocr_page_count"] == expected_ocr_pages
