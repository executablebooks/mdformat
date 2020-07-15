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


def test_invalid_file():
    assert run(("this is not a valid filepath?`=|><@{[]\\/,.%¤#'",)) == 1


def test_check(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(FORMATTED_MARKDOWN)
    assert run((str(file_path), "--check")) == 0


def test_check__fail(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(file_path), "--check")) == 1
