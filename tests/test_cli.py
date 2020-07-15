from mdformat._cli import run


def test_no_files_passed():
    assert run(()) == 0


def test_format(tmp_path):
    unformatted_markdown = "\n\n# A header\n\n"
    formatted_markdown = "# A header\n"

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(unformatted_markdown)
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == formatted_markdown
