from io import StringIO
import sys

import pytest

from mdformat._cli import run

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


def test_invalid_file(capsys):
    with pytest.raises(SystemExit):
        run(("this is not a valid filepath?`=|><@{[]\\/,.%¤#'",))
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
    run((str(tmp_path), "--check"))
    captured = capsys.readouterr()
    assert str(file_path1) in captured.err
    assert str(file_path2) in captured.err


def test_dash_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO(UNFORMATTED_MARKDOWN))
    run(("-",))
    captured = capsys.readouterr()
    assert captured.out == FORMATTED_MARKDOWN
