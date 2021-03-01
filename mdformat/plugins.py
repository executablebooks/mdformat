import argparse
import sys
from typing import Callable, Dict, Mapping

from markdown_it import MarkdownIt

from mdformat.renderer.typing import RendererFunc

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
    from typing import Protocol
else:
    import importlib_metadata
    from typing_extensions import Protocol


def _load_codeformatters() -> Dict[str, Callable[[str, str], str]]:
    codeformatter_entrypoints = importlib_metadata.entry_points().get(  # type: ignore
        "mdformat.codeformatter", ()
    )
    return {ep.name: ep.load() for ep in codeformatter_entrypoints}


CODEFORMATTERS: Mapping[str, Callable[[str, str], str]] = _load_codeformatters()


class ParserExtensionInterface(Protocol):
    """A interface for parser extension plugins."""

    # Does the plugin's formatting change Markdown AST or not?
    # (optional, default: False)
    CHANGES_AST: bool = False

    # A mapping from `RenderTreeNode.type` to a `RendererFunc` that can
    # render the given `RenderTreeNode` type. These override the default
    # `RendererFunc`s defined in `mdformat.renderer.DEFAULT_RENDERER_FUNCS`.
    RENDERER_FUNCS: Mapping[str, RendererFunc]

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        """Add options to the mdformat CLI, to be stored in
        mdit.options["mdformat"] (optional)"""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> None:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""


def _load_parser_extensions() -> Dict[str, ParserExtensionInterface]:
    parser_extension_entrypoints = importlib_metadata.entry_points().get(  # type: ignore  # noqa: E501
        "mdformat.parser_extension", ()
    )
    return {ep.name: ep.load() for ep in parser_extension_entrypoints}


PARSER_EXTENSIONS: Mapping[str, ParserExtensionInterface] = _load_parser_extensions()
