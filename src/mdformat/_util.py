from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import nullcontext
import re
from types import MappingProxyType
from typing import Any, Literal

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

import mdformat.plugins

NULL_CTX = nullcontext()
EMPTY_MAP: MappingProxyType = MappingProxyType({})
RE_NEWLINES = re.compile(r"\r\n|\r|\n")


def build_mdit(
    renderer_cls: Any,
    *,
    mdformat_opts: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> MarkdownIt:
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
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> bool:
    """Check if two Markdown produce the same HTML.

    Renders HTML from both Markdown strings, reduces consecutive
    whitespace to a single space and checks equality. Note that this is
    not a perfect solution, as there can be meaningful whitespace in
    HTML, e.g. in a <code> block.
    """
    html_texts = {}
    mdit = build_mdit(RendererHTML, mdformat_opts=options, extensions=extensions)
    for key, text in [("md1", md1), ("md2", md2)]:
        html = mdit.render(text)

        # The HTML can start with whitespace if Markdown starts with raw HTML
        # preceded by whitespace. This whitespace should be safe to lstrip.
        # Also, the trailing newline we add at the end of a document that ends
        # in a raw html block not followed by a newline, seems to propagate to
        # an HTML rendering. This newline should be safe to rstrip.
        html = html.strip()

        # Remove codeblocks because code formatter plugins do arbitrary changes.
        for codeclass in codeformatters:
            html = re.sub(
                f'<code class="language-{codeclass}">.*</code>',
                "",
                html,
                flags=re.DOTALL,
            )

        # Reduce all whitespace to a single space
        html = re.sub(r"\s+", " ", html)

        # Strip insignificant paragraph leading/trailing whitespace
        html = html.replace("<p> ", "<p>")
        html = html.replace(" </p>", "</p>")

        # Also strip whitespace leading/trailing the <p> elements so that we can
        # safely remove empty paragraphs below without introducing extra whitespace.
        html = html.replace(" <p>", "<p>")
        html = html.replace("</p> ", "</p>")

        # empty p elements should be ignored by user agents
        # (https://www.w3.org/TR/REC-html40/struct/text.html#edef-P)
        html = html.replace("<p></p>", "")

        # If it's nothing but whitespace, it's equal
        html = re.sub(r"^\s+$", "", html)

        html_texts[key] = html

    return html_texts["md1"] == html_texts["md2"]


def detect_newline_type(md: str, eol_setting: str) -> Literal["\n", "\r\n"]:
    """Returns the newline-character to be used for output.

    If `eol_setting == "keep"`, the newline character used in the passed
    markdown is detected and returned. Otherwise the character matching
    the passed setting is returned.
    """
    if eol_setting == "keep":
        first_eol = RE_NEWLINES.search(md)
        return "\r\n" if first_eol and first_eol.group() == "\r\n" else "\n"
    if eol_setting == "crlf":
        return "\r\n"
    return "\n"
