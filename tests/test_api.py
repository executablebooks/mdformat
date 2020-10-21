import pytest

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


def test_fmt_file__invalid_filename():
    with pytest.raises(ValueError) as exc_info:
        mdformat.file("this is not a valid filepath?`=|><@{[]\\/,.%¤#'")
    assert "not a file" in str(exc_info.value)


def test_fmt_string():
    assert mdformat.text(UNFORMATTED_MARKDOWN) == FORMATTED_MARKDOWN


def test_api_options():
    non_numbered = """\
0. a
0. b
0. c
"""
    numbered = """\
0. a
1. b
2. c
"""
    assert mdformat.text(non_numbered, options={"number": True}) == numbered
