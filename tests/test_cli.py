from io import StringIO
import sys
from unittest.mock import patch

import pytest

import mdformat
from mdformat._cli import run, wrap_paragraphs
from mdformat.plugins import CODEFORMATTERS

UNFORMATTED_MARKDOWN = "\n\n# A header\n\n"
FORMATTED_MARKDOWN = "# A header\n"


def test_no_files_passed():
    assert run(()) == 0


def test_format(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == FORMATTED_MARKDOWN


def test_format__folder(tmp_path):
    file_path_1 = tmp_path / "test_markdown1.md"
    file_path_2 = tmp_path / "test_markdown2.md"
    file_path_3 = tmp_path / "not_markdown3"
    file_path_1.write_text(UNFORMATTED_MARKDOWN)
    file_path_2.write_text(UNFORMATTED_MARKDOWN)
    file_path_3.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(tmp_path),)) == 0
    assert file_path_1.read_text() == FORMATTED_MARKDOWN
    assert file_path_2.read_text() == FORMATTED_MARKDOWN
    assert file_path_3.read_text() == UNFORMATTED_MARKDOWN


def test_format__symlinks(tmp_path):
    # Create two MD files
    file_path_1 = tmp_path / "test_markdown1.md"
    file_path_2 = tmp_path / "test_markdown2.md"
    file_path_1.write_text(UNFORMATTED_MARKDOWN)
    file_path_2.write_text(UNFORMATTED_MARKDOWN)

    # Create a symlink to both files: one in the root folder, one in a sub folder
    subdir_path = tmp_path / "subdir"
    subdir_path.mkdir()
    symlink_1 = subdir_path / "symlink1.md"
    symlink_1.symlink_to(file_path_1)
    symlink_2 = tmp_path / "symlink2.md"
    symlink_2.symlink_to(file_path_2)

    # Format file 1 via directory of the symlink, and file 2 via symlink
    assert run([str(subdir_path), str(symlink_2)]) == 0

    # Assert that files are formatted and symlinks are not overwritten
    assert file_path_1.read_text() == FORMATTED_MARKDOWN
    assert file_path_2.read_text() == FORMATTED_MARKDOWN
    assert symlink_1.is_symlink()
    assert symlink_2.is_symlink()


def test_invalid_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(("this is not a valid filepath?`=|><@{[]\\/,.%¤#'",))
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_check(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(FORMATTED_MARKDOWN)
    assert run((str(file_path), "--check")) == 0


def test_check__fail(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(file_path), "--check")) == 1


def test_check__multi_fail(capsys, tmp_path):
    """Test for --check flag when multiple files are unformatted.

    Test that the names of all unformatted files are listed when using
    --check.
    """
    file_path1 = tmp_path / "test_markdown1.md"
    file_path2 = tmp_path / "test_markdown2.md"
    file_path1.write_text(UNFORMATTED_MARKDOWN)
    file_path2.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(tmp_path), "--check")) == 1
    captured = capsys.readouterr()
    assert str(file_path1) in captured.err
    assert str(file_path2) in captured.err


def example_formatter(code, info):
    return "dummy\n"


def test_formatter_plugin(tmp_path, monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "lang", example_formatter)
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("```lang\nother\n```\n")
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "```lang\ndummy\n```\n"


def test_dash_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO(UNFORMATTED_MARKDOWN))
    assert run(("-",)) == 0
    captured = capsys.readouterr()
    assert captured.out == FORMATTED_MARKDOWN


def test_wrap_paragraphs():
    with patch("shutil.get_terminal_size", return_value=(72, 24)):
        assert wrap_paragraphs(
            [
                'Error: Could not format "/home/user/file_name_longer_than_wrap_width--------------------------------------.md".',  # noqa: E501
                "The formatted Markdown renders to different HTML than the input Markdown. "  # noqa: E501
                "This is likely a bug in mdformat. "
                "Please create an issue report here: "
                "https://github.com/executablebooks/mdformat/issues",
            ]
        ) == (
            "Error: Could not format\n"
            '"/home/user/file_name_longer_than_wrap_width--------------------------------------.md".\n'  # noqa: E501
            "\n"
            "The formatted Markdown renders to different HTML than the input\n"
            "Markdown. This is likely a bug in mdformat. Please create an issue\n"
            "report here: https://github.com/executablebooks/mdformat/issues\n"
        )


def test_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith(f"mdformat {mdformat.__version__}")


def test_no_wrap(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(
        "all\n"
        "these newlines\n"
        "except the one in this hardbreak  \n"
        "should be\n"
        "removed because they are\n"
        "in the same paragraph\n"
        "\n"
        "This however is the next\n"
        "paragraph.    Whitespace should  be collapsed\n"
        "    \t here\n"
    )
    assert run([str(file_path), "--wrap=no"]) == 0
    assert (
        file_path.read_text()
        == "all these newlines except the one in this hardbreak\\\n"
        "should be removed because they are in the same paragraph\n"
        "\n"
        "This however is the next paragraph. Whitespace should be collapsed here\n"
    )


def test_wrap(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(
        "This\n"
        "text\n"
        "should\n"
        "be wrapped again so that wrap width is whatever is defined below. "
        "Also     whitespace            should\t\tbe             collapsed. "
        "Next up a second paragraph:\n"
        "\n"
        "This paragraph should also be wrapped. "
        "Here's some more text to wrap.  "
        "Here's some more text to wrap.  "
        "Here's some more text to wrap.  "
    )
    assert run([str(file_path), "--wrap=60"]) == 0
    assert (
        file_path.read_text()
        == "This text should be wrapped again so that wrap width is\n"
        "whatever is defined below. Also whitespace should be\n"
        "collapsed. Next up a second paragraph:\n"
        "\n"
        "This paragraph should also be wrapped. Here's some more text\n"
        "to wrap. Here's some more text to wrap. Here's some more\n"
        "text to wrap.\n"
    )


def test_consecutive_wrap_width_lines(tmp_path):
    """Test a case where two consecutive lines' width equals wrap width.

    There was a bug where this would cause an extra newline and split
    the paragraph, hence the test.
    """
    wrap_width = 20
    file_path = tmp_path / "test_markdown.md"
    text = "A" * wrap_width + "\n" + "A" * wrap_width + "\n"
    file_path.write_text(text)
    assert run([str(file_path), f"--wrap={wrap_width}"]) == 0
    assert file_path.read_text() == text


def test_eol__lf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\r\n")
    assert run([str(file_path)]) == 0
    assert file_path.read_bytes() == b"Oi\n"


def test_eol__crlf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\n")
    assert run([str(file_path), "--end-of-line=crlf"]) == 0
    assert file_path.read_bytes() == b"Oi\r\n"
