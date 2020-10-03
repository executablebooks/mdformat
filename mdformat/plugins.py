import argparse
import sys
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from markdown_it import MarkdownIt
from markdown_it.token import Token

from mdformat.renderer import MDRenderer

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
    from typing import Protocol
else:
    import importlib_metadata
    from typing_extensions import Protocol


def _load_codeformatters() -> Dict[str, Callable[[str, str], str]]:
    codeformatter_entrypoints = importlib_metadata.entry_points().get(
        "mdformat.codeformatter", ()
    )
    return {ep.name: ep.load() for ep in codeformatter_entrypoints}


CODEFORMATTERS: Mapping[str, Callable[[str, str], str]] = _load_codeformatters()


class ParserExtensionInterface(Protocol):
    """A interface for parser extension plugins."""

    # Does the plugin's formatting change Markdown AST or not?
    # (optional, default: False)
    CHANGES_AST: bool = False

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        """Add options to the mdformat CLI, to be stored in
        mdit.options["mdformat"] (optional)"""

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> None:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""

    @staticmethod
    def render_token(
        renderer: MDRenderer,
        tokens: Sequence[Token],
        index: int,
        options: Mapping[str, Any],
        env: dict,
    ) -> Optional[Tuple[str, int]]:
        """Convert token(s) to a string, or return None if no render method
        available.

        :returns: (text, index) where index is of the final "consumed" token
        """


def _load_parser_extensions() -> Dict[str, ParserExtensionInterface]:
    parser_extension_entrypoints = importlib_metadata.entry_points().get(
        "mdformat.parser_extension", ()
    )
    return {ep.name: ep.load() for ep in parser_extension_entrypoints}


PARSER_EXTENSIONS: Mapping[str, ParserExtensionInterface] = _load_parser_extensions()
