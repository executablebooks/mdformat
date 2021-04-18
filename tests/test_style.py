from pathlib import Path

from markdown_it.utils import read_fixture_file
import pytest

import mdformat
from mdformat.renderer._util import CONSECUTIVE_KEY


@pytest.mark.parametrize(
    "fixture_file,options",
    [
        ("default_style.md", {}),
        ("consecutive_numbering.md", {CONSECUTIVE_KEY: True}),
        ("wrap_width_50.md", {"wrap": 50}),
    ],
)
def test_style(fixture_file, options):
    """Test Markdown renderer renders expected style."""
    cases = read_fixture_file(Path(__file__).parent / "data" / fixture_file)
    for case in cases:
        line, title, text, expected = case
        md_new = mdformat.text(text, options=options)
        if md_new != expected:
            print(md_new)
        assert md_new == expected
