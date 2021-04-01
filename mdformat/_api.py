from pathlib import Path
from typing import Any, ContextManager, Iterable, Mapping, Union

from mdformat._util import EMPTY_MAP, NULL_CTX, atomic_write, build_mdit
from mdformat.renderer import MDRenderer


def text(
    md: str,
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
    _first_pass_contextmanager: ContextManager = NULL_CTX,
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
    if options.get("wrap", "keep") != "keep":
        rendering = mdit.render(rendering)

    return rendering


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
    atomic_write(f, formatted_md)
