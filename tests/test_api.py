import mdformat

UNFORMATTED_MARKDOWN = "\n\n# A header\n\n"
FORMATTED_MARKDOWN = "# A header\n"


def test_fmt_file(tmp_path):
    file_path = tmp_path / "test_markdown.md"

    # Use string argument
    file_path.write_text(UNFORMATTED_MARKDOWN)
    mdformat.file(str(file_path))
    assert file_path.read_text() == FORMATTED_MARKDOWN

    # Use pathlib.Path argument
    file_path.write_text(UNFORMATTED_MARKDOWN)
    mdformat.file(file_path)
    assert file_path.read_text() == FORMATTED_MARKDOWN


def test_fmt_string():
    assert mdformat.string(UNFORMATTED_MARKDOWN) == FORMATTED_MARKDOWN
