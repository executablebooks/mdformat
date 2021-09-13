from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from mdformat._conf import DEFAULT_OPTS
from mdformat._util import EMPTY_MAP, NULL_CTX, atomic_write, build_mdit
from mdformat.renderer import MDRenderer


def text(
    md: str,
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
    _first_pass_contextmanager: AbstractContextManager = NULL_CTX,
) -> str:
    """Format a Markdown string."""
    with _first_pass_contextmanager:
        mdit = build_mdit(
            MDRenderer,
            mdformat_opts=options,
            extensions=extensions,
            codeformatters=codeformatters,
        )
        rendering = mdit.render(md)

    # If word wrap is changed, add a second pass of rendering.
    # Some escapes will be different depending on word wrap, so
    # rendering after 1st and 2nd pass will be different. Rendering
    # twice seems like the easiest way to achieve stable formatting.
    if options.get("wrap", DEFAULT_OPTS["wrap"]) != "keep":
        rendering = mdit.render(rendering)

    return rendering


def file(
    f: str | Path,
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
    if f.is_symlink():
        raise ValueError(f'Can not format "{f}". It is a symlink.')

    original_md = f.read_text(encoding="utf-8")
    formatted_md = text(
        original_md,
        options=options,
        extensions=extensions,
        codeformatters=codeformatters,
    )
    newline = (
        "\r\n"
        if options.get("end_of_line", DEFAULT_OPTS["end_of_line"]) == "crlf"
        else "\n"
    )
    atomic_write(f, formatted_md, newline)
