import os
from pathlib import Path
import re
import tempfile
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

from mdformat._compat import nullcontext
import mdformat.plugins

NULL_CTX = nullcontext()
EMPTY_MAP: MappingProxyType = MappingProxyType({})


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
        for codeclass in codeformatters:
            html = re.sub(
                f'<code class="language-{codeclass}">.*</code>',
                "",
                html,
                flags=re.DOTALL,
            )
        html = re.sub(r"\s+", " ", html)

        # Strip insignificant paragraph leading/trailing whitespace
        html = html.replace("<p> ", "<p>")
        html = html.replace(" </p>", "</p>")

        html_texts[key] = html

    return html_texts["md1"] == html_texts["md2"]


def atomic_write(path: Path, text: str) -> None:
    """An atomic function for writing to a file.

    Writes a temporary file first and then replaces the original file
    with the temporary one. This is to avoid a moment where only empty
    or partial content exists on disk.
    """
    fd, tmp_path = tempfile.mkstemp(dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except BaseException:
        os.remove(tmp_path)
        raise
