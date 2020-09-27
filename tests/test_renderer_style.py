from pathlib import Path

from markdown_it.utils import read_fixture_file
import pytest

from mdformat import text as render

STYLE_CASES = read_fixture_file(Path(__file__).parent / "data" / "fixtures.md")


@pytest.mark.parametrize(
    "line,title,text,expected", STYLE_CASES, ids=[f[1] for f in STYLE_CASES]
)
def test_renderer_style(line, title, text, expected):
    """Test Markdown renderer renders expected style."""
    md_new = render(text)
    print(md_new)
    assert md_new == expected
