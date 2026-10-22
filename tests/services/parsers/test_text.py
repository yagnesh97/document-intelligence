from app.services.parsers.text import TextParser


def test_text_parser_decodes_utf8():
    parser = TextParser()

    result = parser.parse(
        content=b"Hello world\nSecond line",
        filename="test.txt",
        content_type="text/plain",
    )

    assert result.content == "Hello world\nSecond line"
    assert result.metadata["filename"] == "test.txt"
    assert result.metadata["content_type"] == "text/plain"
    assert result.metadata["encoding"] == "utf-8"


def test_text_parser_replaces_invalid_utf8():
    parser = TextParser()

    result = parser.parse(
        content=b"hello\xffworld",
        filename="test.txt",
    )

    assert "hello" in result.content
    assert "world" in result.content
