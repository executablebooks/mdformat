from pathlib import Path

from markdown_it.utils import read_fixture_file
import pytest

from mdformat._util import build_mdit
from mdformat.renderer import MDRenderer
from mdformat.renderer._util import CONSECUTIVE_KEY

STYLE_CASES = read_fixture_file(Path(__file__).parent / "data" / "fixtures.md")


@pytest.mark.parametrize(
    "line,title,text,expected", STYLE_CASES, ids=[f[1] for f in STYLE_CASES]
)
def test_renderer_style(line, title, text, expected):
    """Test Markdown renderer renders expected style."""
    mdit = build_mdit(MDRenderer)
    if "[consecutive]" in title:
        mdit.options["mdformat"] = {CONSECUTIVE_KEY: True}
    md_new = mdit.render(text)
    if not md_new == expected:
        print(md_new)
    assert md_new == expected
