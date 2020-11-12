import re
from typing import Any, Iterable, Mapping, Optional

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

import mdformat.plugins


def build_mdit(
    renderer_cls: Any,
    *,
    mdformat_opts: Optional[Mapping[str, Any]] = None,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> MarkdownIt:
    if mdformat_opts is None:
        mdformat_opts = {}

    mdit = MarkdownIt(renderer_cls=renderer_cls)
    mdit.options["mdformat"] = mdformat_opts
    # store reference labels in link/image tokens
    mdit.options["store_labels"] = True

    mdit.options["parser_extension"] = []
    for name in extensions:
        plugin = mdformat.plugins.PARSER_EXTENSIONS[name]
        if plugin not in mdit.options["parser_extension"]:
            mdit.options["parser_extension"].append(plugin)
            plugin.update_mdit(mdit)

    mdit.options["codeformatters"] = {
        lang: mdformat.plugins.CODEFORMATTERS[lang] for lang in codeformatters
    }

    return mdit


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
    mdit = build_mdit(RendererHTML, mdformat_opts=options, extensions=extensions)
    for key, text in [("md1", md1), ("md2", md2)]:
        html = mdit.render(text)
        for codeclass in codeformatters:
            html = re.sub(
                f'<code class="language-{codeclass}">.*</code>',
                "",
                html,
                flags=re.DOTALL,
            )
        html = re.sub(r"\s+", "", html)
        html_texts[key] = html

    return html_texts["md1"] == html_texts["md2"]
