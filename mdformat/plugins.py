import argparse
from typing import Callable, Dict, Mapping

from markdown_it import MarkdownIt

from mdformat._compat import Protocol, importlib_metadata
from mdformat.renderer.typing import Postprocess, Render


def _load_codeformatters() -> Dict[str, Callable[[str, str], str]]:
    codeformatter_entrypoints = importlib_metadata.entry_points(
        group="mdformat.codeformatter"
    )
    return {ep.name: ep.load() for ep in codeformatter_entrypoints}


CODEFORMATTERS: Mapping[str, Callable[[str, str], str]] = _load_codeformatters()


class ParserExtensionInterface(Protocol):
    """A interface for parser extension plugins."""

    # Does the plugin's formatting change Markdown AST or not?
    # (optional, default: False)
    CHANGES_AST: bool = False

    # A mapping from `RenderTreeNode.type` to a `Render` function that can
    # render the given `RenderTreeNode` type. These override the default
    # `Render` funcs defined in `mdformat.renderer.DEFAULT_RENDERERS`.
    RENDERERS: Mapping[str, Render]

    # A mapping from `RenderTreeNode.type` to a `Postprocess` that does
    # postprocessing for the output of the `Render` function. Unlike
    # `Render` funcs, `Postprocess` funcs are collaborative: any number of
    # plugins can define a postprocessor for a syntax type and all of them
    # will run in series.
    # (optional)
    POSTPROCESSORS: Mapping[str, Postprocess]

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        """Add options to the mdformat CLI, to be stored in
        mdit.options["mdformat"] (optional)"""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> None:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""


def _load_parser_extensions() -> Dict[str, ParserExtensionInterface]:
    parser_extension_entrypoints = importlib_metadata.entry_points(
        group="mdformat.parser_extension"
    )
    return {ep.name: ep.load() for ep in parser_extension_entrypoints}


PARSER_EXTENSIONS: Mapping[str, ParserExtensionInterface] = _load_parser_extensions()
