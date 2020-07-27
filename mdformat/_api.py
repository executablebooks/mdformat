from pathlib import Path
from typing import Union

from markdown_it import MarkdownIt

from mdformat._renderer import MDRenderer


def text(md: str) -> str:
    """Format a Markdown string."""
    return MarkdownIt(renderer_cls=MDRenderer).render(md)


def file(f: Union[str, Path]) -> None:
    """Format a Markdown file in place."""
    if isinstance(f, str):
        f = Path(f)
    if not f.is_file():
        raise ValueError(f'Can not format "{f}". It is not a file.')
    original_md = f.read_text(encoding="utf-8")
    formatted_md = text(original_md)
    f.write_text(formatted_md, encoding="utf-8")
