from app.services.parsers.pdf.analyzer import PdfAnalysis
from app.services.parsers.pdf.base import BasePdfParser, PdfType


class PdfParserFactory:
    @classmethod
    def get_parser(cls, analysis: PdfAnalysis) -> BasePdfParser:
        if analysis.pdf_type == PdfType.TEXT:
            from app.services.parsers.pdf.text import TextPdfParser

            return TextPdfParser()

        if analysis.pdf_type == PdfType.IMAGE:
            from app.services.parsers.pdf.image import ImagePdfParser

            return ImagePdfParser()

        if analysis.pdf_type == PdfType.HYBRID:
            from app.services.parsers.pdf.hybrid import HybridPdfParser

            return HybridPdfParser()

        raise ValueError(f"Unsupported PDF type: {analysis.pdf_type}")
