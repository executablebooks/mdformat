import re
from typing import Any, Iterable, Mapping

from markdown_it import MarkdownIt

import mdformat.plugins


def is_md_equal(
    md1: str,
    md2: str,
    options: Mapping[str, Any],
    *,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> bool:
    """Check if two Markdown produce the same HTML.

    Renders HTML from both Markdown strings, strips whitespace and
    checks equality. Note that this is not a perfect solution, as there
    can be meaningful whitespace in HTML, e.g. in a <code> block.
    """
    html_texts = {}
    mdit = MarkdownIt()
    mdit.options["mdformat"] = options
    for extension in extensions:
        mdformat.plugins.PARSER_EXTENSIONS[extension].update_mdit(mdit)
    for key, text in [("md1", md1), ("md2", md2)]:
        html = mdit.render(text)
        for codeclass in codeformatters:
            html = re.sub(f'<code class="language-{codeclass}">.*</code>', "", html)
        html = re.sub(r"\s+", "", html)
        html_texts[key] = html

    return html_texts["md1"] == html_texts["md2"]
