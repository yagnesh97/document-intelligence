from app.services.parsers.base import BaseParser, ParsedDocument
from app.services.parsers.csv import CsvParser
from app.services.parsers.excel import ExcelParser
from app.services.parsers.factory import ParserFactory
from app.services.parsers.image import ImageParser
from app.services.parsers.pdf.pdf_parser import PdfParser
from app.services.parsers.powerpoint import PowerPointParser
from app.services.parsers.text import TextParser
from app.services.parsers.word import WordParser

ParserFactory.register(
    extensions=[".txt"],
    parser=TextParser,
)

ParserFactory.register(
    extensions=[".csv"],
    parser=CsvParser,
)

ParserFactory.register(
    extensions=[".xls", ".xlsx"],
    parser=ExcelParser,
)

ParserFactory.register(
    extensions=[".pdf"],
    parser=PdfParser,
)

ParserFactory.register(
    extensions=[".docx"],
    parser=WordParser,
)

ParserFactory.register(
    extensions=[".pptx"],
    parser=PowerPointParser,
)

ParserFactory.register(
    extensions=[
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
        ".gif",
    ],
    parser=ImageParser,
)

__all__ = [
    "BaseParser",
    "CsvParser",
    "ExcelParser",
    "ImageParser",
    "ParsedDocument",
    "ParserFactory",
    "PdfParser",
    "PowerPointParser",
    "TextParser",
    "WordParser",
]
