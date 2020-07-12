import re

from markdown_it import MarkdownIt


def is_md_equal(md1: str, md2: str) -> bool:
    """Check if two Markdown produce the same HTML.

    Renders HTML from both Markdown strings, strips whitespace and
    checks equality. Note that this is not a perfect solution, as there
    can be meaningful whitespace in HTML, e.g. in a <code> block.
    """
    html1 = MarkdownIt().render(md1)
    html2 = MarkdownIt().render(md2)
    html1 = re.sub(r"\s+", "", html1)
    html2 = re.sub(r"\s+", "", html2)
    return html1 == html2
