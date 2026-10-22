import pytest

from app.services.parsers import (
    CsvParser,
    ExcelParser,
    ParserFactory,
    PdfParser,
    TextParser,
)


@pytest.mark.parametrize(
    ("filename", "expected_parser"),
    [
        ("statement.txt", TextParser),
        ("statement.csv", CsvParser),
        ("statement.xlsx", ExcelParser),
        ("statement.xls", ExcelParser),
        ("statement.pdf", PdfParser),
    ],
)
def test_parser_factory_returns_expected_parser(filename, expected_parser):
    parser = ParserFactory.get_parser(filename)

    assert isinstance(parser, expected_parser)


def test_parser_factory_is_case_insensitive():
    parser = ParserFactory.get_parser("STATEMENT.PDF")

    assert isinstance(parser, PdfParser)


def test_parser_factory_uses_filename_extension():
    parser = ParserFactory.get_parser("statement.csv", "application/octet-stream")

    assert isinstance(parser, CsvParser)


def test_parser_factory_rejects_unknown_extension():
    with pytest.raises(ValueError, match="No parser available"):
        ParserFactory.get_parser("statement.xyz")


def test_parser_factory_rejects_filename_without_extension():
    with pytest.raises(ValueError, match="No parser available"):
        ParserFactory.get_parser("statement")
