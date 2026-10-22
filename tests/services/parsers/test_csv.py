from app.services.parsers.csv import CsvParser


def test_csv_parser_extracts_content_and_metadata():
    content = b"date,description,amount\n2026-01-01,Salary,5000\n2026-01-02,Coffee,-5\n"

    parser = CsvParser()

    result = parser.parse(
        content=content,
        filename="transactions.csv",
        content_type="text/csv",
    )

    assert result.content.startswith("date,description,amount")
    assert result.metadata["filename"] == "transactions.csv"
    assert result.metadata["content_type"] == "text/csv"
    assert result.metadata["row_count"] == 2
    assert result.metadata["columns"] == [
        "date",
        "description",
        "amount",
    ]


def test_csv_parser_supports_utf8_bom():
    content = ("\ufeffdate,description,amount\n2026-01-01,Salary,5000\n").encode(
        "utf-8"
    )

    parser = CsvParser()

    result = parser.parse(
        content=content,
        filename="transactions.csv",
    )

    assert result.metadata["columns"] == [
        "date",
        "description",
        "amount",
    ]
    assert result.metadata["row_count"] == 1


def test_csv_parser_handles_empty_csv():
    parser = CsvParser()

    result = parser.parse(
        content=b"",
        filename="empty.csv",
    )

    assert result.content == ""
    assert result.metadata["row_count"] == 0
    assert result.metadata["columns"] == []
