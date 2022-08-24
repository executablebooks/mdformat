import pytest

import mdformat
from mdformat._util import is_md_equal

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


def test_fmt_file__symlink(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    symlink_path = tmp_path / "symlink.md"
    symlink_path.symlink_to(file_path)

    with pytest.raises(ValueError) as exc_info:
        mdformat.file(symlink_path)
    assert "It is a symlink" in str(exc_info.value)


def test_fmt_string():
    assert mdformat.text(UNFORMATTED_MARKDOWN) == FORMATTED_MARKDOWN


def test_vertical_tab_only():
    input_ = "\x0b"
    output = mdformat.text(input_)
    assert is_md_equal(input_, output)


def test_no_codeblock_trailing_newline():
    input_ = "\t##"
    output = mdformat.text(input_)
    assert is_md_equal(input_, output)


@pytest.mark.parametrize(
    "input_",
    [
        pytest.param("\x1c\n\na"),
        pytest.param(">\x0b"),
        pytest.param("<!K"),
    ],
)
def test_cases_found_by_fuzzer(input_):
    output = mdformat.text(input_)
    assert is_md_equal(input_, output)


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


def test_eol__lf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\r\n")
    mdformat.file(str(file_path))
    assert file_path.read_bytes() == b"Oi\n"


def test_eol__crlf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\n")
    mdformat.file(str(file_path), options={"end_of_line": "crlf"})
    assert file_path.read_bytes() == b"Oi\r\n"
