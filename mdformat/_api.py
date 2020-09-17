from pathlib import Path
from typing import Iterable, Union

from markdown_it import MarkdownIt

from mdformat._renderer import MDRenderer
import mdformat.plugins


def text(md: str, *, codeformatters: Iterable[str] = ()) -> str:
    """Format a Markdown string."""
    markdown_it = MarkdownIt(renderer_cls=MDRenderer)
    markdown_it.options["codeformatters"] = {
        lang: mdformat.plugins.CODEFORMATTERS[lang] for lang in codeformatters
    }
    return markdown_it.render(md)


def file(f: Union[str, Path], *, codeformatters: Iterable[str] = ()) -> None:
    """Format a Markdown file in place."""
    if isinstance(f, str):
        f = Path(f)
    try:
        is_file = f.is_file()
    except OSError:  # Catch "OSError: [WinError 123]" on Windows
        is_file = False
    if not is_file:
        raise ValueError(f'Can not format "{f}". It is not a file.')
    original_md = f.read_text(encoding="utf-8")
    formatted_md = text(original_md, codeformatters=codeformatters)
    f.write_text(formatted_md, encoding="utf-8")
