from pathlib import Path
from typing import Any, Iterable, Mapping, Union

from mdformat._util import EMPTY_MAP, build_mdit
from mdformat.renderer import MDRenderer


def text(
    md: str,
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> str:
    """Format a Markdown string."""
    mdit = build_mdit(
        MDRenderer,
        mdformat_opts=options,
        extensions=extensions,
        codeformatters=codeformatters,
    )
    return mdit.render(md)


def file(
    f: Union[str, Path],
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> None:
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
    formatted_md = text(
        original_md,
        options=options,
        extensions=extensions,
        codeformatters=codeformatters,
    )
    f.write_text(formatted_md, encoding="utf-8")
