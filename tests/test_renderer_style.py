from markdown_it import MarkdownIt
import pytest

from mdformat._renderer import MDRenderer

STYLE_CASES = (
    {
        "name": "strip paragraph lines",
        "input_md": "trailing whitespace \n"
        "at the end of paragraph lines \n"
        "should be stripped                   \n",
        "output_md": "trailing whitespace\n"
        "at the end of paragraph lines\n"
        "should be stripped\n",
    },
    {
        "name": "strip quotes",
        "input_md": "> Paragraph 1\n" "> \n" "> Paragraph 2\n",
        "output_md": "> Paragraph 1\n" ">\n" "> Paragraph 2\n",
    },
    {
        "name": "no escape ampersand",
        "input_md": "R&B, rock & roll\n",
        "output_md": "R&B, rock & roll\n",
    },
    {
        "name": "list whitespaces",
        "input_md": "- item one\n  \n- item two\n  - sublist\n    \n  - sublist\n",
        "output_md": "- item one\n\n- item two\n\n  - sublist\n\n  - sublist\n",
    },
    {
        "name": "convert setext to ATX heading",
        "input_md": "Top level heading\n=========\n\n2nd level heading\n---------",
        "output_md": "# Top level heading\n\n## 2nd level heading\n",
    },
)


@pytest.mark.parametrize("entry", STYLE_CASES, ids=[c["name"] for c in STYLE_CASES])
def test_renderer_style(entry):
    """Test Markdown renderer renders expected style."""
    md_original = entry["input_md"]
    md_new = MarkdownIt(renderer_cls=MDRenderer).render(md_original)
    expected_md = entry["output_md"]
    assert md_new == expected_md
