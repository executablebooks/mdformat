from pathlib import Path

from markdown_it.utils import read_fixture_file
import pytest

import mdformat
import mdformat._cli


@pytest.mark.parametrize(
    "fixture_file,options",
    [
        ("default_style.md", []),
        ("consecutive_numbering.md", ["--number"]),
        ("wrap_width_50.md", ["--wrap=50"]),
    ],
)
def test_style(fixture_file, options, tmp_path):
    """Test Markdown renderer renders expected style."""
    file_path = tmp_path / "test_markdown.md"
    cases = read_fixture_file(Path(__file__).parent / "data" / fixture_file)
    for case in cases:
        line, title, text, expected = case
        file_path.write_bytes(text.encode())
        assert mdformat._cli.run([str(file_path), *options]) == 0
        md_new = file_path.read_bytes().decode()
        if md_new != expected:
            print("Formatted (unexpected) Markdown below:")
            print(md_new)
        assert md_new == expected
