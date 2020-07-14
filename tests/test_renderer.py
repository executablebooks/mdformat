import json
from pathlib import Path

from markdown_it import MarkdownIt
import pytest

from mdformat._renderer import RendererCmark

SPECTESTS_PATH = Path(__file__).parent.joinpath("data/spec.json")
SPECTESTS_CASES = tuple(
    {"name": str(entry["example"]), "md": entry["markdown"]}
    for entry in json.loads(SPECTESTS_PATH.read_text())
)
MY_TEST_CASES = (
    {
        "name": "titles",
        "md": "# BIG Title\n"
        "## smaller\n"
        "### even smaller\n"
        "#### 4th level\n"
        "##### 5th level\n"
        "###### the smallest (6th level)\n",
    },
    {"name": "emphasis", "md": "*emphasized*\n" "**STRONGLY emphasized**\n"},
    {
        "name": "simple",
        "md": "# BIG Title\n" "> a quote here\n\n" "Paragraph is here.\n",
    },
    {"name": "strikethrough", "md": "# Testing strikethrough\n" "~~here goes~~\n"},
    {"name": "inline code", "md": "`print('Hello World!)`\n"},
    {"name": "escape char", "md": "\\*not emphasized\\*\n"},
    {
        "name": "fenced code",
        "md": "## Here's a code block\n"
        "```python\n"
        "print('Hello world!')\n"
        "```\n",
    },
    {"name": "paragraph line feeds", "md": "first paragraph\n\n" "second one\n"},
    {"name": "thematic break", "md": "thematic break\n\n" "---\n" "above\n"},
    {"name": "autolink", "md": "<http://foo.bar.baz>\n"},
    {"name": "link", "md": '[link](/uri "title")\n' "[link](/uri)\n" "[link]()\n"},
    {"name": "image", "md": '![foo](/url "title")\n' "![foo [bar](/url)](/url2)\n"},
    {"name": "unordered list", "md": "- item1\n" "- item2\n"},
    {"name": "unordered loose list", "md": "- item1\n" "\n" "- item2\n"},
    {"name": "ordered list", "md": "1. item1\n" "1. item2\n"},
    {"name": "ordered list 2", "md": "10021. item1\n" "10021. item2\n"},
    {"name": "ordered list zero", "md": "0. item1\n" "0. item2\n"},
    {"name": "whitespace preserve", "md": "- foo\n\n\tbar\n"},
    {"name": "debug", "md": "> ```\n> a\n> \n> \n> ```\n"},
    {"name": "list indentation", "md": "- foo\n\n\t\tbar\n"},
    {"name": "list in quote", "md": "> -"},
    {"name": "reference link", "md": '[foo][bar]\n\n[bar]: /url "title"\n'},
    {"name": "empty file", "md": ""},
    {"name": "whitespace only", "md": "  \n\n \n  \n"},
    {"name": "soft breaks", "md": "this is\nall one\nparagraph\n"},
    {"name": "escape underscore", "md": "# foo _bar_ \\_baz\\_\n"},
)


ALL_TESTS = MY_TEST_CASES + SPECTESTS_CASES


@pytest.mark.parametrize("entry", ALL_TESTS, ids=[c["name"] for c in ALL_TESTS])
def test_cmark_renderer(entry):
    """Test Markdown renderer against the Commonmark spec.

    Test that:
    1. HTML is the same before and after RendererCmark
    2. Markdown after 1st pass and 2nd pass of RendererCmark are equal
    """
    md_original = entry["md"]
    html_original = MarkdownIt().render(md_original)
    md_new = MarkdownIt(renderer_cls=RendererCmark).render(md_original)
    md_2nd_pass = MarkdownIt(renderer_cls=RendererCmark).render(md_new)
    html_new = MarkdownIt().render(md_new)

    equal_html = html_original == html_new
    equal_md_2nd_pass = md_new == md_2nd_pass

    if not equal_html:
        # These tests have only insignificant whitespace diff in HTML.
        # Lets make the whitespace equal and see if HTML is equal then.
        if entry["name"] == "51":
            equal_html = html_original.replace("bar\nbaz", "bar baz") == html_new
        elif entry["name"] == "52":
            equal_html = html_original.replace("bar\nbaz", "bar baz") == html_new
        elif entry["name"] == "65":
            equal_html = html_original.replace("Foo\nBar", "Foo Bar") == html_new

    assert equal_html
    assert equal_md_2nd_pass
